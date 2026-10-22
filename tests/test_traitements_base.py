"""Schéma `app` et rôle des traitements, avec PostgreSQL (sprint 5, étape 1 ; D-82, D-85).

Demande `TEST_DATABASE_URL` (voir `outils_base.py`) ; ignoré sans elle, sauf en CI.
"""

from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict

from muninn.core.config import get_settings
from muninn.db import roles
from muninn.demo import charger_scenarios
from muninn.traitements import enregistrement
from outils_base import base_migree, exiger_base, url_postgres

exiger_base()

MDP = {"api": "api-" + "a" * 28, "ingestion": "ingestion-" + "b" * 22,
       "traitements": "traitements-" + "c" * 20}  # fmt: skip
TABLES_APP = {"traitements", "dossiers", "messages", "corrections"}


@pytest.fixture(scope="module")
def base() -> Iterator[str]:
    with base_migree() as nom:
        url = url_postgres(nom)
        assert roles.preparer_roles(url, MDP) == [f"{nom}_api", f"{nom}_ingestion",
                                                  f"{nom}_traitements"]  # fmt: skip
        yield nom


def url_role(base: str, suffixe: str) -> str:
    return roles.url_du_role(url_postgres(base), f"{base}_{suffixe}", MDP[suffixe])


@pytest.fixture
def traitements_actifs(base: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """L'API enregistre ses traitements dans la base de test, avec le rôle dédié."""
    # Format `postgresql://`, celui des secrets d'Azure : SQLAlchemy ne lit pas la forme libpq.
    p = conninfo_to_dict(exiger_base())
    url = (f"postgresql://{base}_traitements:{MDP['traitements']}"
           f"@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{base}")  # fmt: skip
    monkeypatch.setenv("DATABASE_URL_TRAITEMENTS", url)
    get_settings.cache_clear()
    enregistrement.moteur.cache_clear()
    yield base
    enregistrement.moteur.cache_clear()


def test_schema_app_cree(base: str) -> None:
    with psycopg.connect(url_postgres(base)) as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'app'"
        )}  # fmt: skip
    assert tables == TABLES_APP


def test_le_role_des_traitements_n_ecrit_que_dans_app(base: str) -> None:
    with psycopg.connect(url_role(base, "traitements"), autocommit=True) as conn:
        conn.execute(
            "INSERT INTO app.traitements (request_id, route, issue, duree_ms)"
            " VALUES ('essai-role', 'demo', 'trace', 1)"
        )
        conn.execute("DELETE FROM app.traitements WHERE request_id = 'essai-role'")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT 1 FROM ref.communes LIMIT 1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("CREATE TABLE app.intrus (id int)")


def test_le_role_de_l_api_ne_voit_pas_app(base: str) -> None:
    with psycopg.connect(url_role(base, "api"), autocommit=True) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT 1 FROM app.traitements LIMIT 1")


def test_un_appel_est_enregistre_sans_sa_transcription(
    traitements_actifs: str, client_api: TestClient
) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    assert r.status_code == 200, r.text
    rid = r.headers["X-Request-Id"]
    with psycopg.connect(url_postgres(traitements_actifs)) as conn:
        issue, statut, duree = conn.execute(
            "SELECT issue, statut, duree_ms FROM app.traitements WHERE request_id = %s", [rid]
        ).fetchone() or (None, None, None)
        etat, brouillon = conn.execute(
            "SELECT etat, brouillon::text FROM app.dossiers WHERE request_id = %s", [rid]
        ).fetchone() or (None, "")
        tout = " ".join(str(v) for row in conn.execute(
            "SELECT t::text FROM app.traitements t UNION ALL SELECT d::text FROM app.dossiers d"
        ) for v in row)  # fmt: skip
    assert issue == "dossier" and statut is not None and isinstance(duree, int)
    assert etat == "brouillon" and "schema_version" in str(brouillon)
    # La transcription n'est jamais gardée : aucune de ses répliques n'apparaît telle quelle.
    for replique in charger_scenarios()["SC-01"].transcription.splitlines():
        assert replique not in tout


def test_un_texte_libre_ne_laisse_que_ses_mesures(
    traitements_actifs: str, client_api: TestClient
) -> None:
    """D-82 : un texte libre peut porter de vraies données personnelles ; ni dossier ni message."""
    for route, corps in [
        (
            "/v1/demo/runs",
            {"mode": "transcript", "transcript": "Appelant : Jean Dupont, fuite à Lyon."},
        ),
        ("/v1/extract/text", {"text": "Jean Dupont, fuite sous l'évier à Lyon 69003."}),
    ]:
        r = client_api.post(route, json=corps)
        assert r.status_code == 200, r.text
        with psycopg.connect(url_postgres(traitements_actifs)) as conn:
            rid = r.headers["X-Request-Id"]
            mesures = conn.execute(
                "SELECT count(*) FROM app.traitements WHERE request_id = %s", [rid]
            ).fetchone()
            contenu = conn.execute(
                "SELECT (SELECT count(*) FROM app.dossiers WHERE request_id = %s)"
                " + (SELECT count(*) FROM app.messages WHERE request_id = %s)", [rid, rid],
            ).fetchone()  # fmt: skip
        assert mesures == (1,) and contenu == (0,), route


def test_un_refus_est_enregistre(traitements_actifs: str, client_api: TestClient) -> None:
    r = client_api.post("/v1/extract/text", json={"text": "   "})
    assert r.status_code == 422
    with psycopg.connect(url_postgres(traitements_actifs)) as conn:
        ligne = conn.execute(
            "SELECT issue, code_refus FROM app.traitements WHERE request_id = %s",
            [r.headers["X-Request-Id"]],
        ).fetchone()
    assert ligne == ("refus", "content_unprocessable")


def test_purge_au_dela_de_30_jours(traitements_actifs: str, client_api: TestClient) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    rid = r.headers["X-Request-Id"]
    with psycopg.connect(url_postgres(traitements_actifs), autocommit=True) as conn:
        conn.execute(
            "UPDATE app.traitements SET recu_le = now() - interval '31 days'"
            " WHERE request_id = %s", [rid],
        )  # fmt: skip
    moteur = enregistrement.moteur()
    assert moteur is not None
    assert enregistrement.purger(moteur) >= 1
    with psycopg.connect(url_postgres(traitements_actifs)) as conn:
        restant = conn.execute(
            "SELECT count(*) FROM app.dossiers WHERE request_id = %s", [rid]
        ).fetchone()
    assert restant == (0,)
