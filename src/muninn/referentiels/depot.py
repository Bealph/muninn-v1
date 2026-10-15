"""Lectures dans les référentiels : SQL sécurisé (D-56).

Garde-fous, cumulés :
- requêtes paramétrées seulement : aucune valeur reçue n'entre dans le texte SQL ;
- connexion en lecture seule (`default_transaction_read_only`), quel que soit le rôle de l'URL ;
  en production, le rôle lui-même est `<base>_lecture` ;
- délai maximal par requête (`statement_timeout`) ;
- seules les versions publiées sont lues.
Les valeurs reçues ne sont ni journalisées, ni stockées (contrat d'API, TA-23).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from muninn.core.config import get_settings
from muninn.ingestion.normalisation import normaliser_nom

Connexion = psycopg.Connection[dict[str, Any]]
DELAI_MS = 3000

# Métadonnées des sources (registre des sources du sprint 3) : ce que cite chaque réponse.
SOURCES: dict[str, dict[str, str]] = {
    "SRC-07": {
        "titre": "Code officiel géographique 2026",
        "editeur": "Insee",
        "licence": "Licence Ouverte 2.0",
    },
    "SRC-06": {
        "titre": "Base officielle des codes postaux",
        "editeur": "La Poste",
        "licence": "Licence Ouverte 2.0",
    },
    "SRC-12": {
        "titre": "Wiktionnaire, Lexique en français de la plomberie",
        "editeur": "Wikimédia",
        "licence": "CC BY-SA 4.0",
    },
    "SRC-11": {"titre": "Wikidata", "editeur": "Wikimédia", "licence": "CC0 1.0"},
    "SRC-01": {
        "titre": "Stock Sirene des établissements et des unités légales",
        "editeur": "Insee",
        "licence": "Licence Ouverte 2.0",
    },
}


class BaseIndisponible(Exception):
    """La base des référentiels ne répond pas."""


def connecter() -> Connexion:
    url = get_settings().database_url
    if url is None:
        raise BaseIndisponible("DATABASE_URL n'est pas définie")
    try:
        return psycopg.connect(
            url.get_secret_value(),
            autocommit=True,
            row_factory=dict_row,
            connect_timeout=5,
            options=f"-c default_transaction_read_only=on -c statement_timeout={DELAI_MS}",
        )
    except psycopg.OperationalError as erreur:
        raise BaseIndisponible(str(erreur)) from erreur


@dataclass
class Version:
    """Version publiée d'un jeu : ce qu'une réponse cite comme source."""

    jeu: str
    source_id: str
    url: str
    date_source: date
    publiee_le: datetime
    version: int

    def citation(self, table: str) -> dict[str, Any]:
        return {
            "jeu": self.jeu,
            "source_id": self.source_id,
            **SOURCES[self.source_id],
            "url": self.url,
            "date_source": self.date_source.isoformat(),
            "charge_le": self.publiee_le.isoformat(),
            "version": self.version,
            "table": table,
        }


def version_publiee(conn: Connexion, jeu: str) -> Version | None:
    ligne = conn.execute(
        "SELECT id, source_id, source_url, source_date, published_at FROM ref.dataset_versions"
        " WHERE dataset = %s AND channel = 'production' AND status = 'published'",
        [jeu],
    ).fetchone()
    if ligne is None:
        return None
    return Version(
        jeu,
        ligne["source_id"],
        ligne["source_url"],
        ligne["source_date"],
        ligne["published_at"],
        ligne["id"],
    )


@dataclass
class Candidate:
    nom: str
    code_insee: str
    departement: str
    codes_postaux: list[str] = field(default_factory=list)
    via: str = "nom officiel"
    references: list[dict[str, str]] = field(default_factory=list)


def chercher_communes(
    conn: Connexion, communes: Version, codes: Version, nom: str | None, code_postal: str | None
) -> tuple[list[Candidate], bool]:
    """Communes candidates pour un nom, un code postal, ou les deux.

    Le nom est comparé après normalisation (N1 à N3, N5), par égalité exacte : aucune recherche
    approchée (dossier V1, § 3.1). Une commune déléguée, associée ou un arrondissement renvoie à
    sa commune parente (VD-11). Rend les candidates et, si les deux valeurs sont données, si au
    moins une candidate les accorde.
    """
    trouvees: dict[str, Candidate] = {}
    if nom is not None:
        for ligne in conn.execute(
            "SELECT d.commune_type, d.insee_code, d.name, p.insee_code AS code, p.name AS nom,"
            " p.department_code AS departement"
            " FROM ref.communes d"
            " JOIN ref.communes p ON p.version_id = d.version_id AND p.commune_type = 'COM'"
            " AND p.insee_code = COALESCE(d.parent_insee_code, d.insee_code)"
            " WHERE d.version_id = %s AND d.name_normalized = %s"
            " ORDER BY p.department_code, p.insee_code",
            [communes.version, normaliser_nom(nom)],
        ):
            via = "nom officiel" if ligne["commune_type"] == "COM" else (
                f"{ligne['name']} ({ligne['commune_type']} {ligne['insee_code']})"
            )  # fmt: skip
            trouvees.setdefault(
                ligne["code"],
                Candidate(ligne["nom"], ligne["code"], ligne["departement"], via=via),
            )
    if code_postal is not None and nom is None:
        for ligne in conn.execute(
            "SELECT DISTINCT p.insee_code AS code, p.name AS nom,"
            " p.department_code AS departement"
            " FROM ref.postal_codes cp"
            " JOIN ref.communes c ON c.version_id = %s AND c.insee_code = cp.insee_code"
            " JOIN ref.communes p ON p.version_id = c.version_id AND p.commune_type = 'COM'"
            " AND p.insee_code = COALESCE(c.parent_insee_code, c.insee_code)"
            " WHERE cp.version_id = %s AND cp.postal_code = %s"
            " ORDER BY p.insee_code",
            [communes.version, codes.version, code_postal],
        ):
            trouvees.setdefault(
                ligne["code"],
                Candidate(ligne["nom"], ligne["code"], ligne["departement"], via="code postal"),
            )
    for candidate in trouvees.values():
        completer(conn, communes, codes, candidate)
    accord = True
    if nom is not None and code_postal is not None:
        accord = any(code_postal in c.codes_postaux for c in trouvees.values())
    return list(trouvees.values()), accord


def completer(conn: Connexion, communes: Version, codes: Version, candidate: Candidate) -> None:
    """Ajoute les codes postaux d'une commune (et de ses arrondissements) et leurs références."""
    for ligne in conn.execute(
        "SELECT DISTINCT cp.postal_code, cp.id FROM ref.postal_codes cp"
        " WHERE cp.version_id = %s AND (cp.insee_code = %s OR cp.insee_code IN ("
        " SELECT insee_code FROM ref.communes WHERE version_id = %s AND commune_type = 'ARM'"
        " AND parent_insee_code = %s))"
        " ORDER BY cp.postal_code, cp.id",
        [codes.version, candidate.code_insee, communes.version, candidate.code_insee],
    ):
        if ligne["postal_code"] not in candidate.codes_postaux:
            candidate.codes_postaux.append(ligne["postal_code"])
            candidate.references.append({"table": "ref.postal_codes", "cle": f"id {ligne['id']}"})
    candidate.references.insert(
        0,
        {
            "table": "ref.communes",
            "cle": f"version {communes.version}, COM {candidate.code_insee}",
        },
    )


@dataclass
class LexiquePublie:
    id: int
    version: str
    publie_le: datetime
    rapport: dict[str, Any]


def lexique_publie(conn: Connexion, metier: str) -> LexiquePublie | None:
    ligne = conn.execute(
        "SELECT id, version, published_at, report FROM ref.trade_lexicons"
        " WHERE trade = %s AND status = 'published'",
        [metier],
    ).fetchone()
    if ligne is None:
        return None
    return LexiquePublie(ligne["id"], ligne["version"], ligne["published_at"], ligne["report"])


def terme_le_plus_proche(conn: Connexion, lexique_id: int, mot: str) -> dict[str, Any] | None:
    """Terme accepté de plus forte similarité trigramme avec le mot normalisé (N1 à N3)."""
    return conn.execute(
        "SELECT id, term, source_id, source_ref, license, category,"
        " similarity(term_normalized, %s) AS similarite"
        " FROM ref.lexicon_terms WHERE lexicon_id = %s AND review_status = 'accepted'"
        " ORDER BY similarite DESC, term LIMIT 1",
        [normaliser_nom(mot, abreviations=False), lexique_id],
    ).fetchone()


def execution_sirene(conn: Connexion) -> dict[str, Any] | None:
    return conn.execute(
        "SELECT id, stock_date, source_url, published_at, small_cell_threshold, report"
        " FROM market.sirene_runs WHERE status = 'published' AND naf_revision = 'rev2'"
    ).fetchone()


def comptages_sirene(conn: Connexion, execution: int, metier: str) -> list[dict[str, Any]]:
    return conn.execute(
        "SELECT naf_code, headcount_band, legal_category_group, department_code,"
        " establishments_count, legal_units_count, is_masked"
        " FROM market.sirene_counts WHERE run_id = %s AND trade = %s"
        " ORDER BY department_code, headcount_band, legal_category_group",
        [execution, metier],
    ).fetchall()
