"""Rôles de connexion et commande `muninn-donnees` de la tâche (sprint 3, étape 10)."""

from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg import errors

from muninn import donnees
from muninn.core.config import get_settings
from muninn.db import roles
from muninn.ingestion import lexique, sirene
from outils_base import base_migree, connecter, exiger_base, url_postgres
from test_ingestion_base import TOUT, servir
from test_sirene import ecrire_stock

exiger_base()

MDP_API = "api-" + "a" * 28
MDP_INGESTION = "ingestion-" + "b" * 22


@pytest.fixture
def base(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[str]:
    stock = ecrire_stock(tmp_path)
    monkeypatch.setattr(sirene, "localiser", lambda client: stock)
    with base_migree() as nom:
        monkeypatch.setenv("DATABASE_URL", url_postgres(nom))
        monkeypatch.setenv("MUNINN_MDP_API", MDP_API)
        monkeypatch.setenv("MUNINN_MDP_INGESTION", MDP_INGESTION)
        get_settings.cache_clear()
        yield nom
        with connecter("postgres") as admin:  # rôles propres à cette base de test
            for suffixe in ("api", "ingestion"):
                admin.execute(f'DROP ROLE IF EXISTS "{nom}_{suffixe}"')
    get_settings.cache_clear()


def test_roles_crees_et_relancables(base: str) -> None:
    url = url_postgres(base)
    assert roles.preparer_roles(url, roles.mots_de_passe()) == [f"{base}_api", f"{base}_ingestion"]
    assert roles.preparer_roles(url, roles.mots_de_passe())  # second passage : aucune erreur
    with psycopg.connect(roles.url_du_role(url, f"{base}_api", MDP_API), autocommit=True) as api:
        assert api.execute("SELECT count(*) FROM ref.naf_trades").fetchone() == (4,)
        assert api.execute("SHOW default_transaction_read_only").fetchone() == ("on",)
        assert api.execute("SHOW statement_timeout").fetchone() == ("5s",)
        with pytest.raises(errors.ReadOnlySqlTransaction):
            api.execute("DELETE FROM ref.communes")


def test_mot_de_passe_change_au_second_passage(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    url = url_postgres(base)
    roles.preparer_roles(url, roles.mots_de_passe())
    nouveau = "api-" + "z" * 28
    monkeypatch.setenv("MUNINN_MDP_API", nouveau)
    roles.preparer_roles(url, roles.mots_de_passe())
    with pytest.raises(psycopg.OperationalError):
        psycopg.connect(roles.url_du_role(url, f"{base}_api", MDP_API)).close()
    psycopg.connect(roles.url_du_role(url, f"{base}_api", nouveau)).close()


@pytest.mark.parametrize("variable", ["MUNINN_MDP_API", "MUNINN_MDP_INGESTION"])
def test_mot_de_passe_trop_court_refuse(monkeypatch: pytest.MonkeyPatch, variable: str) -> None:
    monkeypatch.setenv("MUNINN_MDP_API", MDP_API)
    monkeypatch.setenv("MUNINN_MDP_INGESTION", MDP_INGESTION)
    monkeypatch.setenv(variable, "court")
    with pytest.raises(RuntimeError, match="moins de 24"):
        roles.mots_de_passe()


def test_commande_de_la_tache(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Migrations, rôles, puis ingestion avec le seul rôle d'écriture."""
    servir(monkeypatch, TOUT)
    monkeypatch.setattr(
        lexique, "evaluation", lambda signature: {"rapport": "t", "date": "d", "seuil": 0.55}
    )
    assert donnees.main() == 0
    with connecter(base) as conn:
        assert conn.execute("SELECT count(*) FROM ref.dataset_versions").fetchone() == (3,)
        assert conn.execute(
            "SELECT count(*) FROM market.sirene_runs WHERE status = 'published'"
        ).fetchone() == (1,)
        # Les lignes ont été écrites par le rôle d'ingestion, sans droit sur le schéma.
        assert conn.execute(
            "SELECT pg_has_role(%s, %s, 'member')", [f"{base}_ingestion", f"{base}_ecriture"]
        ).fetchone() == (True,)
