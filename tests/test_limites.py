"""Tests de la limite de débit des appels au LLM."""

import pytest
from fastapi.testclient import TestClient

from muninn.api.limites import LimiteurDebit
from muninn.api.main import app as api
from muninn.api.main import get_fournisseur, get_limiteur
from muninn.core.config import get_settings
from muninn.llm.fournisseur import FauxFournisseur, ReponseLLM


class Horloge:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


def test_fenetre_minute() -> None:
    horloge = Horloge()
    limiteur = LimiteurDebit([(60, 3)], horloge)
    assert [limiteur.reserver() for _ in range(3)] == [None, None, None]
    horloge.t += 10
    assert limiteur.reserver() == 50  # le premier appel sort de la fenêtre dans 50 s
    horloge.t += 50
    assert limiteur.reserver() is None


def test_fenetre_jour_plus_stricte_que_la_minute() -> None:
    horloge = Horloge()
    limiteur = LimiteurDebit([(60, 10), (86_400, 2)], horloge)
    assert limiteur.reserver() is None
    horloge.t += 120
    assert limiteur.reserver() is None
    horloge.t += 120
    assert limiteur.reserver() == 86_400 - 240
    horloge.t += 86_400
    assert limiteur.reserver() is None


def test_refus_non_compte() -> None:
    """Un appel refusé ne consomme pas de place : sinon un client insistant se bloquerait seul."""
    horloge = Horloge()
    limiteur = LimiteurDebit([(60, 1)], horloge)
    assert limiteur.reserver() is None
    for _ in range(5):
        assert limiteur.reserver() is not None
    horloge.t += 60
    assert limiteur.reserver() is None


class FournisseurCompteur(FauxFournisseur):
    def __init__(self) -> None:
        self.appels = 0

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        self.appels += 1
        return super().repondre(question, modele)


def test_route_rend_429_sans_appeler_le_modele(client_api: TestClient) -> None:
    fournisseur = FournisseurCompteur()
    api.dependency_overrides[get_fournisseur] = lambda: fournisseur
    limiteur = LimiteurDebit([(60, 2)])  # une seule instance, comme en production
    api.dependency_overrides[get_limiteur] = lambda: limiteur
    corps = {"question": "Bonjour", "modele": "A"}
    assert [client_api.post("/llm/essai", json=corps).status_code for _ in range(2)] == [200, 200]
    refus = client_api.post("/llm/essai", json=corps)
    assert refus.status_code == 429
    assert int(refus.headers["Retry-After"]) > 0
    assert "réessayer dans" in refus.json()["detail"]
    assert fournisseur.appels == 2


def test_limite_nulle_coupe_les_appels() -> None:
    assert LimiteurDebit([(60, 0)]).reserver() == 60


def test_console_affiche_la_limite(client_console: TestClient) -> None:
    coupe = LimiteurDebit([(60, 0)])
    api.dependency_overrides[get_limiteur] = lambda: coupe
    reponse = client_console.post("/essai", data={"question": "Bonjour", "modele": "A"})
    assert reponse.status_code == 200
    assert "Trop de demandes au modèle" in reponse.text


def test_limiteur_reel_lit_la_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans substitution : LLM_LIMITE_MINUTE est bien appliquée par la dépendance réelle."""
    monkeypatch.setenv("LLM_LIMITE_MINUTE", "1")
    get_settings.cache_clear()
    get_limiteur.cache_clear()
    limiteur = get_limiteur()
    assert limiteur.reserver() is None
    assert limiteur.reserver() is not None
