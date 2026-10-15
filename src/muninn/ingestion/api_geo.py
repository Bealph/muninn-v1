"""Communes de l'API Découpage administratif, dite API Géo (SRC-03) : recoupement avec le COG.

L'API ne sert qu'à vérifier le COG et les codes postaux (registre des sources du sprint 3, § 3) :
aucune donnée qu'elle seule fournit n'est servie. On garde la version de l'appel et les écarts
(`ref.commune_source_gaps`) ; `rows_loaded` compte les communes comparées. Contrôle VD-09.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from muninn.ingestion.telechargement import FichierRecu
from muninn.ingestion.versions import Connexion, Controle, Lecture, Rejet, valeur

JEU = "geo_api_communes"
SOURCE = "SRC-03"
# Champs utiles seulement : ni population, ni géométrie (minimisation des volumes).
URL = "https://geo.api.gouv.fr/communes?fields=nom,code,codesPostaux,codeDepartement"
CODE = re.compile(r"[0-9][0-9AB][0-9]{3}")
# Communes des collectivités d'outre-mer et des TAAF, absentes du COG des communes (liste figée,
# constat du 15 octobre 2026 : 94 codes).
HORS_COG = ("975", "977", "978", "984", "986", "987", "988", "989")


@dataclass(frozen=True)
class CommuneGeo:
    code: str
    nom: str
    codes_postaux: tuple[str, ...]


def lire(contenu: bytes) -> Lecture[CommuneGeo]:
    """Lit la réponse JSON ; le « numéro de ligne » d'un rejet est le rang dans la liste."""
    lecture: Lecture[CommuneGeo] = Lecture()
    donnees = json.loads(contenu.decode("utf-8"))
    if not isinstance(donnees, list):
        raise ValueError("API Géo : liste de communes attendue")
    vus: set[str] = set()
    for rang, commune in enumerate(donnees, start=1):
        lecture.lues += 1
        brut = json.dumps(commune, ensure_ascii=False)
        code = commune.get("code") if isinstance(commune, dict) else None
        nom = commune.get("nom") if isinstance(commune, dict) else None
        if not isinstance(code, str) or not isinstance(nom, str) or not code or not nom:
            lecture.rejets.append(Rejet(rang, "missing_field", brut))
        elif not CODE.fullmatch(code):
            lecture.rejets.append(Rejet(rang, "bad_format", brut))
        elif code in vus:
            lecture.rejets.append(Rejet(rang, "duplicate", brut))
        else:
            vus.add(code)
            codes_postaux = tuple(sorted(commune.get("codesPostaux") or []))
            lecture.lignes.append(CommuneGeo(code, nom, codes_postaux))
    lecture.rapport = {"format": "json", "communes_sans_code_postal": sum(
        1 for c in lecture.lignes if not c.codes_postaux
    )}  # fmt: skip
    return lecture


def ecarts(communes: list[CommuneGeo], cog: dict[str, str]) -> list[tuple[str, str, str | None]]:
    """Écarts entre l'API Géo et les communes `COM` du COG (code vers nom officiel)."""
    geo = {c.code: c.nom for c in communes}
    resultat: list[tuple[str, str, str | None]] = []
    for code in sorted(geo.keys() - cog.keys()):
        resultat.append((code, "absent_from_cog", geo[code]))
    for code in sorted(cog.keys() - geo.keys()):
        resultat.append((code, "absent_from_geo_api", None))
    for code in sorted(cog.keys() & geo.keys()):
        if cog[code] != geo[code]:
            resultat.append((code, "name_differs", geo[code]))
    return resultat


def inserateur(cog: dict[str, str]) -> Callable[[Connexion, int, list[CommuneGeo]], None]:
    """Fabrique l'écriture des écarts, qui connaît les communes du COG servi."""

    def inserer(conn: Connexion, version_id: int, communes: list[CommuneGeo]) -> None:
        with conn.cursor().copy(
            "COPY ref.commune_source_gaps (version_id, insee_code, gap_type, geo_api_name)"
            " FROM STDIN"
        ) as copie:
            for code, type_, nom in ecarts(communes, cog):
                copie.write_row([version_id, code, type_, nom])

    return inserer


def controleur(
    communes: list[CommuneGeo], version_codes_postaux: int | None
) -> Callable[[Connexion, int], list[Controle]]:
    """Fabrique les contrôles VD-09 et le recoupement des codes postaux avec La Poste."""

    def controler(conn: Connexion, version_id: int) -> list[Controle]:
        comptes: dict[str, int] = {
            str(type_): int(n)
            for type_, n in conn.execute(
                "SELECT gap_type, count(*) FROM ref.commune_source_gaps WHERE version_id = %s"
                " GROUP BY 1",
                [version_id],
            ).fetchall()
        }
        hors_liste = valeur(
            conn,
            "SELECT count(*) FROM ref.commune_source_gaps WHERE version_id = %s"
            " AND gap_type = 'absent_from_cog' AND NOT (left(insee_code, 3) = ANY(%s))",
            [version_id, list(HORS_COG)],
        )
        controles = [
            Controle(
                "VD-09",
                comptes.get("absent_from_geo_api", 0) == 0
                and comptes.get("name_differs", 0) == 0
                and hors_liste == 0,
                False,
                f"{comptes.get('absent_from_geo_api', 0)} communes du COG absentes de l'API,"
                f" {comptes.get('name_differs', 0)} noms différents,"
                f" {comptes.get('absent_from_cog', 0)} codes en plus dans l'API, dont"
                f" {hors_liste} hors de la liste figée de l'outre-mer",
            )
        ]
        if version_codes_postaux is not None:
            controles.append(recouper_codes_postaux(conn, communes, version_codes_postaux))
        return controles

    return controler


def recouper_codes_postaux(
    conn: Connexion, communes: list[CommuneGeo], version_codes_postaux: int
) -> Controle:
    """Communes dont les codes postaux diffèrent entre l'API Géo et La Poste (rapporté)."""
    la_poste: dict[str, set[str]] = {}
    for code, code_postal in conn.execute(
        "SELECT insee_code, postal_code FROM ref.postal_codes WHERE version_id = %s",
        [version_codes_postaux],
    ):
        la_poste.setdefault(str(code), set()).add(str(code_postal))
    differentes = [
        c.code for c in communes if c.code in la_poste and set(c.codes_postaux) != la_poste[c.code]
    ]
    return Controle(
        "SRC-03 et SRC-06",
        not differentes,
        False,
        f"{len(differentes)} communes aux codes postaux différents entre l'API Géo et La Poste :"
        f" {differentes[:10]}",
    )


def date_source(fichier: FichierRecu) -> date:
    """L'API ne publie pas de date de modification : la date de collecte en tient lieu."""
    return fichier.date_source or fichier.recupere_le.date()
