"""Base officielle des codes postaux de La Poste (SRC-06).

Le fichier est en ISO-8859-1, séparateur point-virgule, alors que le serveur l'annonce en UTF-8 :
l'encodage est imposé ici, jamais lu dans l'en-tête HTTP (VD-02). Les codes restent du texte
(VD-01). Contrôles de la phase 1 : VD-01 à VD-08.
"""

import csv
import io
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from muninn.ingestion.telechargement import FichierRecu
from muninn.ingestion.versions import Connexion, Controle, Lecture, Rejet, valeur

JEU = "postal_codes"
SOURCE = "SRC-06"
URL = "https://www.data.gouv.fr/api/1/datasets/r/008a2dda-2c60-4b63-b910-998f6f818089"
ENCODAGE = "iso-8859-1"
ENTETE = [
    "#Code_commune_INSEE",
    "Nom_de_la_commune",
    "Code_postal",
    "Libellé_d_acheminement",
    "Ligne_5",
]
CODE_POSTAL = re.compile(r"[0-9]{5}")
CODE_COMMUNE = re.compile(r"[0-9][0-9AB][0-9]{3}")
# Liste figée (phase 1, principe 5) : collectivités d'outre-mer et Monaco, qui ont des codes
# postaux mais pas de communes au COG. Constat du 15 octobre 2026 : 267 lignes.
HORS_COG = ("975", "977", "978", "986", "987", "988", "989")
MONACO = "99138"
ATTENDU_LIGNES = 39_192  # mesuré le 12 octobre 2026 (VD-04), rapporté
PART_REJETS_MAX = 0.005  # VD-03, au-delà : gravité majeure


@dataclass(frozen=True)
class CodePostal:
    code_postal: str
    code_commune: str
    nom_la_poste: str
    libelle: str
    ligne_5: str | None


def hors_cog(code_commune: str) -> bool:
    return code_commune.startswith(HORS_COG) or code_commune == MONACO


def lire(contenu: bytes, communes_cog: set[str]) -> Lecture[CodePostal]:
    """Lit le fichier ; `communes_cog` contient les codes de la version servie du COG."""
    lecture: Lecture[CodePostal] = Lecture()
    texte = contenu.decode(ENCODAGE)
    lecteur = csv.reader(io.StringIO(texte, newline=""), delimiter=";")
    entete = next(lecteur, None)
    if entete != ENTETE:
        raise ValueError(f"Codes postaux : en-tête inattendu {entete}")
    vus: set[tuple[str, str, str, str | None]] = set()
    commencant_par_zero = 0
    for numero, champs in enumerate(lecteur, start=2):
        lecture.lues += 1
        brut = ";".join(champs)
        if len(champs) != len(ENTETE):
            lecture.rejets.append(Rejet(numero, "bad_format", brut))
            continue
        commune, nom, code_postal, libelle, ligne_5 = (c.strip() for c in champs)
        if code_postal.startswith("0"):
            commencant_par_zero += 1
        cle = (code_postal, commune, libelle, ligne_5 or None)
        if not commune or not code_postal or not nom or not libelle:
            lecture.rejets.append(Rejet(numero, "missing_field", brut))
        elif not CODE_POSTAL.fullmatch(code_postal) or not CODE_COMMUNE.fullmatch(commune):
            lecture.rejets.append(Rejet(numero, "bad_format", brut))
        elif hors_cog(commune):
            lecture.filtrees += 1
        elif commune not in communes_cog:
            lecture.rejets.append(Rejet(numero, "unknown_commune", brut))
        elif cle in vus:
            lecture.rejets.append(Rejet(numero, "duplicate", brut))
        else:
            vus.add(cle)
            lecture.lignes.append(CodePostal(code_postal, commune, nom, libelle, ligne_5 or None))
    lecture.rapport = {
        "encodage": ENCODAGE,
        "filtre": "collectivités d'outre-mer et Monaco, absentes du COG (liste figée)",
        "codes_postaux_commencant_par_0_dans_le_fichier": commencant_par_zero,
        "lignes_attendues": ATTENDU_LIGNES,
    }
    return lecture


def inserer(conn: Connexion, version_id: int, codes: list[CodePostal]) -> None:
    with conn.cursor().copy(
        "COPY ref.postal_codes (version_id, postal_code, insee_code, laposte_name,"
        " routing_label, line_5) FROM STDIN"
    ) as copie:
        for c in codes:
            copie.write_row(
                [version_id, c.code_postal, c.code_commune, c.nom_la_poste, c.libelle, c.ligne_5]
            )


def controleur(
    lecture: Lecture[CodePostal], version_cog: int
) -> Callable[[Connexion, int], list[Controle]]:
    """Fabrique le contrôle de la version, qui connaît la lecture et la version du COG."""

    def controler(conn: Connexion, version_id: int) -> list[Controle]:
        zeros = valeur(
            conn,
            "SELECT count(*) FROM ref.postal_codes"
            " WHERE version_id = %s AND postal_code LIKE '0%%'",
            [version_id],
        )
        # Communes sans code postal, directement ou par leurs arrondissements (VD-08).
        sans_code = valeur(
            conn,
            "SELECT array_agg(c.insee_code ORDER BY c.insee_code) FROM ref.communes c"
            " WHERE c.version_id = %s AND c.commune_type = 'COM'"
            " AND NOT EXISTS (SELECT 1 FROM ref.postal_codes p WHERE p.version_id = %s"
            " AND p.insee_code = c.insee_code)"
            " AND NOT EXISTS (SELECT 1 FROM ref.communes a JOIN ref.postal_codes p"
            " ON p.version_id = %s AND p.insee_code = a.insee_code"
            " WHERE a.version_id = c.version_id AND a.commune_type = 'ARM'"
            " AND a.parent_insee_code = c.insee_code)",
            [version_cog, version_id, version_id],
        )
        # Aucun zéro initial perdu entre la lecture en texte et la base (VD-01).
        zeros_lus = sum(1 for c in lecture.lignes if c.code_postal.startswith("0"))
        part = len(lecture.rejets) / lecture.lues if lecture.lues else 0.0
        manquantes = list(sans_code or [])
        return [
            Controle(
                "VD-01",
                zeros == zeros_lus and zeros_lus > 0,
                True,
                f"{zeros} codes commençant par 0 en base, {zeros_lus} parmi les lignes gardées",
            ),
            Controle(
                "VD-03",
                part <= PART_REJETS_MAX,
                False,
                f"{len(lecture.rejets)} rejets sur {lecture.lues} lignes ({part:.2%})",
            ),
            Controle(
                "VD-04",
                lecture.lues == ATTENDU_LIGNES,
                False,
                f"{lecture.lues} lignes lues, {ATTENDU_LIGNES} mesurées le 12 octobre 2026",
            ),
            Controle(
                "VD-08",
                not manquantes,
                False,
                f"{len(manquantes)} communes sans code postal : {manquantes[:10]}",
            ),
        ]

    return controler


def date_source(fichier: FichierRecu) -> date:
    if fichier.date_source is None:
        raise ValueError("Codes postaux : en-tête Last-Modified absent, date de la source inconnue")
    return fichier.date_source
