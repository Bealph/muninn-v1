"""Code officiel géographique de l'INSEE (SRC-07) : communes, déléguées, associées, arrondissements.

Fichier CSV en UTF-8, séparateur virgule, valeurs entre guillemets (registre des sources du
sprint 3). Contrôles de la phase 1 : VD-01, VD-04, VD-05, VD-06, VD-10, VD-11.
"""

import csv
import io
import re
from dataclasses import dataclass
from datetime import date

from muninn.ingestion.normalisation import normaliser_nom
from muninn.ingestion.telechargement import FichierRecu
from muninn.ingestion.versions import Connexion, Controle, Lecture, Rejet, valeur

JEU = "communes"
SOURCE = "SRC-07"
URL = "https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv"
# Le COG est un millésime au 1er janvier ; l'INSEE ne publie pas d'en-tête Last-Modified.
DATE_MILLESIME = date(2026, 1, 1)
ENTETE = [
    "TYPECOM", "COM", "REG", "DEP", "CTCD", "ARR", "TNCC", "NCC", "NCCENR", "LIBELLE", "CAN",
    "COMPARENT",
]  # fmt: skip
TYPES = {"COM", "COMD", "COMA", "ARM"}
CODE = re.compile(r"[0-9][0-9AB][0-9]{3}")
# Comptages mesurés le 12 octobre 2026 (phase 1, VD-04) : rapportés, non bloquants.
ATTENDU = {"COM": 34_875, "COMD": 2_105, "COMA": 471, "ARM": 45}


@dataclass(frozen=True)
class Commune:
    type: str
    code: str
    nom: str
    departement: str | None
    parent: str | None


def lire(contenu: bytes) -> Lecture[Commune]:
    """Lit le fichier ; chaque ligne est gardée ou rejetée avec son motif, jamais perdue."""
    lecture: Lecture[Commune] = Lecture()
    try:
        texte = contenu.decode("utf-8")
    except UnicodeDecodeError as erreur:
        raise ValueError(f"COG : encodage UTF-8 attendu ({erreur})") from erreur
    lecteur = csv.reader(io.StringIO(texte, newline=""))
    entete = next(lecteur, None)
    if entete != ENTETE:
        raise ValueError(f"COG : en-tête inattendu {entete}")
    vus: set[tuple[str, str]] = set()
    for numero, champs in enumerate(lecteur, start=2):
        lecture.lues += 1
        brut = ",".join(champs)
        if len(champs) != len(ENTETE):
            lecture.rejets.append(Rejet(numero, "bad_format", brut))
            continue
        ligne = dict(zip(ENTETE, champs, strict=True))
        type_, code, nom = ligne["TYPECOM"], ligne["COM"], ligne["LIBELLE"].strip()
        departement, parent = ligne["DEP"] or None, ligne["COMPARENT"] or None
        if not code or not nom or (type_ == "COM" and not departement):
            lecture.rejets.append(Rejet(numero, "missing_field", brut))
        elif type_ not in TYPES or not CODE.fullmatch(code):
            lecture.rejets.append(Rejet(numero, "bad_format", brut))
        elif type_ != "COM" and parent is None:
            lecture.rejets.append(Rejet(numero, "missing_field", brut))
        elif (type_, code) in vus:
            lecture.rejets.append(Rejet(numero, "duplicate", brut))
        else:
            vus.add((type_, code))
            lecture.lignes.append(Commune(type_, code, nom, departement, parent))
    comptes = {t: sum(1 for c in lecture.lignes if c.type == t) for t in sorted(TYPES)}
    lecture.rapport = {"encodage": "utf-8", "comptes_par_type": comptes, "attendus": ATTENDU}
    return lecture


def inserer(conn: Connexion, version_id: int, communes: list[Commune]) -> None:
    with conn.cursor().copy(
        "COPY ref.communes (version_id, commune_type, insee_code, name, name_normalized,"
        " department_code, parent_insee_code) FROM STDIN"
    ) as copie:
        for c in communes:
            copie.write_row(
                [version_id, c.type, c.code, c.nom, normaliser_nom(c.nom), c.departement, c.parent]
            )


def controler(conn: Connexion, version_id: int) -> list[Controle]:
    comptes: dict[str, int] = {
        str(type_): int(n)
        for type_, n in conn.execute(
            "SELECT commune_type, count(*) FROM ref.communes WHERE version_id = %s GROUP BY 1",
            [version_id],
        ).fetchall()
    }
    ecarts = {t: comptes.get(t, 0) - n for t, n in ATTENDU.items() if comptes.get(t, 0) != n}
    orphelines = valeur(
        conn,
        "SELECT count(*) FROM ref.communes d WHERE d.version_id = %s AND d.commune_type <> 'COM'"
        " AND NOT EXISTS (SELECT 1 FROM ref.communes c WHERE c.version_id = d.version_id"
        " AND c.commune_type = 'COM' AND c.insee_code = d.parent_insee_code)",
        [version_id],
    )
    mal_decodes = valeur(
        conn,
        "SELECT count(*) FROM ref.communes WHERE version_id = %s"
        " AND (name LIKE '%%Ã%%' OR name LIKE '%%' || chr(65533) || '%%')",
        [version_id],
    )
    return [
        Controle(
            "VD-04",
            not ecarts,
            False,
            f"écarts aux comptages du 12 octobre 2026 : {ecarts}" if ecarts else "conformes",
        ),
        Controle("VD-11", orphelines == 0, True, f"{orphelines} sans commune parente"),
        Controle("VD-02", mal_decodes == 0, True, f"{mal_decodes} noms mal décodés"),
    ]


def date_source(fichier: FichierRecu) -> date:
    return fichier.date_source or DATE_MILLESIME
