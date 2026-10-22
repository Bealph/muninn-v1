"""Outils communs aux tests qui demandent un PostgreSQL 16.

`TEST_DATABASE_URL` désigne un rôle autorisé à créer des bases et des rôles. Sans elle, ces
tests sont ignorés, sauf si `MUNINN_TESTS_BASE=obligatoire` (en CI) : ils échouent alors.
"""

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
import pytest
from alembic import command
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from muninn.db.migrer import configuration

URL_ADMIN = os.environ.get("TEST_DATABASE_URL")


def exiger_base() -> str:
    """Rend l'URL d'administration, ou ignore le module de test qui l'appelle."""
    if URL_ADMIN is None:
        if os.environ.get("MUNINN_TESTS_BASE") == "obligatoire":
            raise RuntimeError("TEST_DATABASE_URL manque alors que les tests de base sont exigés")
        pytest.skip("TEST_DATABASE_URL absente : tests de base ignorés", allow_module_level=True)
    return URL_ADMIN


def connecter(base: str, **options: str) -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(make_conninfo(exiger_base(), dbname=base, **options), autocommit=True)


def url_postgres(base: str) -> str:
    """URL `postgresql://` de la base de test, pour Alembic et pour `DATABASE_URL`."""
    p = conninfo_to_dict(exiger_base())
    return (
        f"postgresql://{p.get('user', '')}:{p.get('password', '')}"
        f"@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{base}"
    )


@contextmanager
def base_migree() -> Iterator[str]:
    """Base neuve, migrée jusqu'à la dernière révision ; supprimée avec ses rôles à la fin."""
    nom = f"muninn_test_{uuid.uuid4().hex[:8]}"
    with connecter("postgres") as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nom)))
    try:
        command.upgrade(configuration(url_postgres(nom)), "head")
        yield nom
    finally:
        with connecter("postgres") as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(nom)))
            for suffixe in ("lecture", "ecriture", "app", "api", "ingestion", "traitements"):
                admin.execute(
                    sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(f"{nom}_{suffixe}"))
                )
