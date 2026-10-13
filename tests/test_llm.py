"""Tests de l'appel au LLM : route de l'API et fournisseur Azure, sans réseau."""

import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from muninn.core.config import Settings
from muninn.llm.fournisseur import (
    ErreurFournisseur,
    FauxFournisseur,
    FournisseurAzure,
    construire_fournisseur,
)

QUESTION_SENSIBLE = "Monsieur Exemple, 06 00 00 00 00, fuite rue des Tests"


def test_route_llm_rend_la_reponse_du_faux(client_api: TestClient) -> None:
    reponse = client_api.post("/llm/essai", json={"question": "Bonjour", "modele": "A"})
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["fournisseur"] == "faux"
    assert donnees["reponse"].startswith("Réponse simulée")


@pytest.mark.parametrize("question", ["", "x" * 501])
def test_route_llm_borne_la_question(client_api: TestClient, question: str) -> None:
    reponse = client_api.post("/llm/essai", json={"question": question})
    assert reponse.status_code == 422


def test_route_llm_refuse_un_modele_inconnu(client_api: TestClient) -> None:
    reponse = client_api.post("/llm/essai", json={"question": "Bonjour", "modele": "C"})
    assert reponse.status_code == 422


def _azure(gestionnaire: httpx.MockTransport) -> FournisseurAzure:
    return FournisseurAzure(
        "https://exemple.services.ai.azure.com/",
        lambda: {"Authorization": "Bearer jeton-de-test"},
        client=httpx.Client(transport=gestionnaire),
    )


def test_azure_envoie_le_format_openai_v1_et_lit_la_reponse() -> None:
    recu: dict[str, object] = {}

    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        recu["url"] = str(requete.url)
        recu["auth"] = requete.headers["Authorization"]
        recu["corps"] = json.loads(requete.content)
        return httpx.Response(
            200,
            json={
                "model": "gpt-5.4-mini-2026-03-17",
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 1},
            },
        )

    r = _azure(httpx.MockTransport(gestionnaire)).repondre("ping", "gpt-5.4-mini")
    assert r.texte == "pong"
    assert r.modele == "gpt-5.4-mini-2026-03-17"
    assert recu["url"] == "https://exemple.services.ai.azure.com/openai/v1/chat/completions"
    assert recu["auth"] == "Bearer jeton-de-test"
    corps = recu["corps"]
    assert isinstance(corps, dict)
    assert corps["model"] == "gpt-5.4-mini"
    assert corps["messages"][-1] == {"role": "user", "content": "ping"}


@pytest.mark.parametrize(
    "reponse",
    [httpx.Response(429, json={"error": "trop"}), httpx.Response(200, json={"rien": 1})],
)
def test_azure_traduit_les_echecs(reponse: httpx.Response) -> None:
    fournisseur = _azure(httpx.MockTransport(lambda _: reponse))
    with pytest.raises(ErreurFournisseur):
        fournisseur.repondre("ping", "gpt-5.4-mini")


def test_azure_service_injoignable() -> None:
    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refus", request=requete)

    with pytest.raises(ErreurFournisseur):
        _azure(httpx.MockTransport(gestionnaire)).repondre("ping", "gpt-5.4-mini")


def test_journaux_sans_contenu_echange(caplog: pytest.LogCaptureFixture) -> None:
    """R4 : ni la question ni la réponse n'apparaissent dans les journaux, succès ou échec."""
    reponses = iter(
        [
            httpx.Response(
                200, json={"model": "m", "choices": [{"message": {"content": "SECRET-REPONSE"}}]}
            ),
            httpx.Response(500, text=QUESTION_SENSIBLE),
        ]
    )
    fournisseur = _azure(httpx.MockTransport(lambda _: next(reponses)))
    with caplog.at_level(logging.DEBUG):
        fournisseur.repondre(QUESTION_SENSIBLE, "m")
        with pytest.raises(ErreurFournisseur):
            fournisseur.repondre(QUESTION_SENSIBLE, "m")
    assert caplog.records, "les appels doivent être tracés"
    journaux = "\n".join(r.getMessage() for r in caplog.records)
    assert "06 00 00 00 00" not in journaux
    assert "Exemple" not in journaux
    assert "SECRET-REPONSE" not in journaux
    assert "jeton-de-test" not in journaux


def test_construire_fournisseur() -> None:
    assert isinstance(construire_fournisseur(Settings()), FauxFournisseur)
    with pytest.raises(ValueError, match="AZURE_AI_ENDPOINT"):
        construire_fournisseur(Settings(llm_fournisseur="azure"))
    azure = construire_fournisseur(
        Settings(
            llm_fournisseur="azure",
            azure_ai_endpoint="https://exemple.services.ai.azure.com",
            azure_ai_api_key=SecretStr("cle-de-test"),
        )
    )
    assert isinstance(azure, FournisseurAzure)
