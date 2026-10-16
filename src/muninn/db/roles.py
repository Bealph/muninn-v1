"""Rôles de connexion de la base (sprint 3, étape 10 ; D-56).

Les migrations créent deux rôles de groupe sans connexion, `<base>_lecture` et `<base>_ecriture`.
Ce module crée, ou met à jour, les rôles qui se connectent :
- `<base>_api`, membre de `<base>_lecture` : celui de l'API ;
- `<base>_ingestion`, membre de `<base>_ecriture` : celui de l'ingestion.
Les mots de passe viennent de variables d'environnement (`MUNINN_MDP_API`,
`MUNINN_MDP_INGESTION`), alimentées par des secrets : jamais du dépôt, jamais d'un journal.
L'exécution demande un rôle autorisé à créer des rôles (l'administrateur du serveur).
"""

import os
import re

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from muninn.core.config import get_settings

LONGUEUR_MIN = 24
# Délai par requête imposé au rôle lui-même. L'API ne fait que des lectures courtes : 5 s.
# L'ingestion contrôle des dizaines de milliers de lignes sur un serveur Burstable : un délai
# court y annulait le contrôle VD-11 du COG (constaté le 16 octobre 2026) ; borné à 15 min.
DELAI_API = "5s"
DELAI_INGESTION = "15min"


def mots_de_passe() -> dict[str, str]:
    """Mots de passe des deux rôles ; refuse un mot de passe absent ou trop court."""
    valeurs = {
        "api": os.environ.get("MUNINN_MDP_API", ""),
        "ingestion": os.environ.get("MUNINN_MDP_INGESTION", ""),
    }
    for nom, valeur in valeurs.items():
        if len(valeur) < LONGUEUR_MIN:
            raise RuntimeError(
                f"Mot de passe du rôle {nom} absent ou de moins de {LONGUEUR_MIN} caractères"
            )
    return valeurs


def url_admin() -> str:
    url = get_settings().database_url
    if url is None:
        raise RuntimeError("DATABASE_URL n'est pas définie")
    return url.get_secret_value()


def nom_base(url: str) -> str:
    base = str(conninfo_to_dict(url).get("dbname") or "")
    if not re.fullmatch(r"[a-z0-9_]{1,40}", base):
        raise RuntimeError(f"Nom de base inattendu : {base!r}")
    return base


def preparer_roles(url: str, mots: dict[str, str]) -> list[str]:
    """Crée ou met à jour les rôles de connexion ; rend leurs noms. Relançable."""
    base = nom_base(url)
    roles = [(f"{base}_api", f"{base}_lecture", mots["api"], True, DELAI_API),
             (f"{base}_ingestion", f"{base}_ecriture", mots["ingestion"], False,
              DELAI_INGESTION)]  # fmt: skip
    with psycopg.connect(url, autocommit=True) as conn:
        for role, groupe, mot, lecture_seule, delai in roles:
            existe = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role]).fetchone()
            ordre = "ALTER ROLE {} WITH LOGIN PASSWORD {}" if existe else (
                "CREATE ROLE {} WITH LOGIN PASSWORD {}"
            )  # fmt: skip
            conn.execute(sql.SQL(ordre).format(sql.Identifier(role), sql.Literal(mot)))
            conn.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(groupe), sql.Identifier(role))
            )
            conn.execute(
                sql.SQL("ALTER ROLE {} SET statement_timeout = {}").format(
                    sql.Identifier(role), sql.Literal(delai)
                )
            )
            if lecture_seule:
                conn.execute(
                    sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(
                        sql.Identifier(role)
                    )
                )
    return [role for role, *_ in roles]


def url_du_role(url: str, role: str, mot: str) -> str:
    """URL de connexion d'un rôle sur le même serveur et la même base."""
    return make_conninfo(url, user=role, password=mot)
