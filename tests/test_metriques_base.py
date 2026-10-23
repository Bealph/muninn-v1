"""Métriques tirées de la base (sprint 5, étape 3 ; V-10, TB-6), avec PostgreSQL.

Des traitements aux valeurs connues sont écrits directement dans `app.traitements`, puis les
métriques sont comparées au calcul attendu. Demande `TEST_DATABASE_URL` ; ignoré sans elle, sauf
en CI.
"""

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict

import muninn.api.agent as routes
from muninn.core.config import get_settings
from muninn.db import roles
from muninn.traitements import enregistrement
from muninn.traitements.metriques import calculer
from outils_base import base_migree, exiger_base, url_postgres

exiger_base()

MDP = {"api": "api-" + "a" * 28, "ingestion": "ingestion-" + "b" * 22,
       "traitements": "traitements-" + "c" * 20}  # fmt: skip

# (issue, statut, a_verifier, duree_ms, cout, garde_fous, simule, il_y_a_heures, code_refus)
LIGNES = [
    ("dossier", "complete", False, 1000, 4000, [], False, 1, None),
    ("dossier", "complete", True, 2000, 4000, ["gaz"], False, 1, None),
    ("dossier", "fallback_no_llm", True, 3000, 0, [], False, 2, None),
    ("dossier", "partial_after_retry", False, 4000, 5000, ["invention", "gaz"], False, 2, None),
    ("message", None, None, 500, 1000, [], False, 3, None),
    ("refus", None, None, 5, 0, [], False, 3, "too_long"),
    ("dossier", "complete", False, 99000, 9000, [], True, 1, None),  # modèle simulé : exclu
    ("dossier", "complete", True, 7000, 3000, [], False, 30, None),  # hors des 24 h
]


@pytest.fixture(scope="module")
def base() -> Iterator[str]:
    with base_migree() as nom:
        roles.preparer_roles(url_postgres(nom), MDP)
        with psycopg.connect(url_postgres(nom), autocommit=True) as conn:
            for issue, statut, av, duree, cout, gf, simule, heures, refus in LIGNES:
                conn.execute(
                    "INSERT INTO app.traitements (request_id, recu_le, route, modele_simule,"
                    " issue, code_refus, statut, a_verifier, garde_fous, duree_ms, cout_micro_eur)"
                    " VALUES (%s, now() - make_interval(hours => %s), 'demo', %s, %s, %s, %s, %s,"
                    " %s, %s, %s)",
                    [str(uuid.uuid4()), heures, simule, issue, refus, statut, av, gf, duree, cout],
                )
            rid = str(uuid.uuid4())
            draft = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO app.traitements (request_id, route, issue, duree_ms)"
                " VALUES (%s, 'demo', 'dossier', 1500)", [rid],
            )  # fmt: skip
            conn.execute(
                "INSERT INTO app.dossiers (draft_id, request_id, brouillon, enveloppe, etat,"
                " valide_le) VALUES (%s, %s, '{}', '{}', 'valide', now())", [draft, rid],
            )  # fmt: skip
            for champ in ("client.adresse.code_postal", "client.adresse.code_postal", "client.nom"):
                conn.execute(
                    "INSERT INTO app.corrections (draft_id, champ) VALUES (%s, %s)", [draft, champ]
                )
        yield nom


@pytest.fixture
def actifs(base: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    p = conninfo_to_dict(exiger_base())
    url = (f"postgresql://{base}_traitements:{MDP['traitements']}"
           f"@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{base}")  # fmt: skip
    monkeypatch.setenv("DATABASE_URL_TRAITEMENTS", url)
    get_settings.cache_clear()
    enregistrement.moteur.cache_clear()
    routes._cache_metriques.clear()
    yield base
    enregistrement.moteur.cache_clear()
    routes._cache_metriques.clear()


def test_metriques_sur_24_heures(actifs: str) -> None:
    m = enregistrement.moteur()
    assert m is not None
    r = calculer(m, 24)
    # Six lignes du tableau dans la fenêtre (simulé et trop ancien exclus), plus le dossier validé.
    assert (r.total, r.dossiers, r.messages, r.refus) == (7, 5, 1, 1)
    assert r.taux_refus == round(1 / 7, 4)
    assert (r.secours, r.relances, r.taux_erreur) == (1, 1, round(2 / 5, 4))
    assert (r.a_verifier, r.part_a_verifier) == (2, round(2 / 5, 4))
    # Médiane des durées hors refus : 500, 1000, 1500, 2000, 3000, 4000 -> 1750.
    assert r.latence_p50_ms == 1750
    assert {(g.nom, g.nombre) for g in r.garde_fous} == {("gaz", 2), ("invention", 1)}
    assert {(c.nom, c.nombre) for c in r.corrections_par_champ} == {
        ("client.adresse.code_postal", 2), ("client.nom", 1)
    }  # fmt: skip
    assert (r.dossiers_valides, r.champs_corriges) == (1, 3)
    assert sum(p.total for p in r.serie) == 7


def test_la_fenetre_d_une_semaine_inclut_le_traitement_ancien(actifs: str) -> None:
    m = enregistrement.moteur()
    assert m is not None
    assert calculer(m, 24 * 7).total == 8


def test_route_qualite(actifs: str, client_api: TestClient) -> None:
    r = client_api.get("/v1/demo/quality", params={"heures": 24})
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 7 and r.json()["part_a_verifier"] == 0.4
    mauvais = client_api.get("/v1/demo/quality", params={"heures": 5})
    assert mauvais.status_code == 422 and mauvais.json()["code"] == "validation_failed"
