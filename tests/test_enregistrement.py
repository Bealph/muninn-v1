"""Enregistrement des traitements, sans base (sprint 5, étape 1 ; D-82, D-85).

Ce qui ne dépend pas de PostgreSQL : rien n'est enregistré sans configuration, une base
injoignable ne fait jamais échouer un appel, et la ligne enregistrée ne porte aucun contenu.
"""

import logging
import re

import pytest
from fastapi.testclient import TestClient

import muninn.api.agent as routes
from muninn.core.config import get_settings
from muninn.traitements import enregistrement
from muninn.traitements.enregistrement import Enregistrement, enregistrer, ligne


@pytest.fixture
def captures(monkeypatch: pytest.MonkeyPatch) -> list[Enregistrement]:
    vus: list[Enregistrement] = []

    def capturer(e: Enregistrement) -> bool:
        vus.append(e)
        return True

    monkeypatch.setattr(routes, "enregistrer", capturer)
    return vus


def test_sans_configuration_rien_n_est_enregistre() -> None:
    assert enregistrer(Enregistrement("r-1", "demo", 10)) is False


def test_base_injoignable_ne_fait_pas_echouer(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL_TRAITEMENTS", "postgresql://x:y@127.0.0.1:1/z?connect_timeout=2"
    )
    get_settings.cache_clear()
    enregistrement.moteur.cache_clear()
    with caplog.at_level(logging.WARNING, logger="muninn.traitements.enregistrement"):
        assert enregistrer(Enregistrement("r-2", "demo", 10)) is False
    assert "traitements.echec request_id=r-2" in caplog.text


def test_un_appel_de_demonstration_est_enregistre_sans_contenu(
    client_api: TestClient, captures: list[Enregistrement]
) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    assert r.status_code == 200, r.text
    assert len(captures) == 1
    e = captures[0]
    assert e.request_id == r.headers["X-Request-Id"] and e.route == "demo"
    assert e.scenario_id == "SC-01" and e.code_refus is None
    valeurs = ligne(e)
    assert valeurs["issue"] == "dossier" and valeurs["categorie"] is not None
    # Aucune valeur de la ligne ne reprend un passage de l'appel : des codes sans espace, des
    # nombres et des booléens seulement.
    for nom, v in valeurs.items():
        for texte in v if isinstance(v, list) else [v]:
            if isinstance(texte, str) and nom != "request_id":
                assert re.fullmatch(r"[A-Za-z0-9_.\-]{1,40}", texte), (nom, texte)


@pytest.mark.parametrize(
    ("corps", "code"),
    [({"text": "   "}, "content_unprocessable"), ({"text": "allo ?"}, "content_unprocessable")],
)
def test_un_refus_est_enregistre_avec_son_code(
    client_api: TestClient, captures: list[Enregistrement], corps: dict[str, str], code: str
) -> None:
    r = client_api.post("/v1/extract/text", json=corps)
    assert r.status_code == 422
    assert [e.code_refus for e in captures] == [code]
    assert ligne(captures[0])["issue"] == "refus"
