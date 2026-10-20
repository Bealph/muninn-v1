"""Routes de l'agent (sprint 4, étape 8) : contrat, erreurs, en-têtes, périmètre (P4)."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from muninn.api.agent import get_referentiels
from muninn.api.limites import LimiteurDebit
from muninn.api.main import app as api
from muninn.api.main import get_fournisseur, get_limiteur
from muninn.demo import PERIMETRE, charger_scenarios
from muninn.extraction.evaluateur import MESSAGE_REFUS_CONTENU
from muninn.llm.fournisseur import FauxFournisseur, RefusContenu, reponse_faux

RACINE = Path(__file__).parents[1]


class ReferentielsHorsLigne:
    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")


@pytest.fixture(autouse=True)
def referentiels_hors_ligne() -> None:
    api.dependency_overrides[get_referentiels] = ReferentielsHorsLigne


def avec_fournisseur(*reponses: Any) -> FauxFournisseur:
    f = FauxFournisseur(
        scenario=[r if isinstance(r, Exception) else reponse_faux(contenu=r) for r in reponses]
    )
    api.dependency_overrides[get_fournisseur] = lambda: f
    return f


def erreur(reponse: httpx.Response, statut: int, code: str) -> dict[str, Any]:
    assert reponse.status_code == statut, reponse.text
    corps: dict[str, Any] = reponse.json()
    assert corps["code"] == code and corps["request_id"] == reponse.headers["X-Request-Id"]
    assert uuid.UUID(corps["request_id"])
    assert reponse.headers["Cache-Control"] == "no-store"
    return corps


def test_extraction_rend_brouillon_enveloppe_et_mesures(client_api: TestClient) -> None:
    r = client_api.post("/v1/extract/text", json={"text": "Bonjour, fuite sous l'évier."})
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    corps = r.json()
    assert set(corps) == {"draft", "envelope", "run"}
    assert corps["run"]["status"] == "partial_after_retry"  # le faux rend « {} » : hors schéma
    assert corps["draft"]["needs_review"] is True and uuid.UUID(r.headers["X-Request-Id"])


def test_entree_sans_contenu(client_api: TestClient) -> None:
    corps = erreur(client_api.post("/v1/extract/text", json={"text": "..."}), 422,
                   "content_unprocessable")  # fmt: skip
    assert corps["message"].startswith("Aucun contenu exploitable")


def test_validation_au_format_du_contrat(client_api: TestClient) -> None:
    corps = erreur(client_api.post("/v1/extract/text", json={"text": "x" * 9000, "bidule": 1}),
                   422, "validation_failed")  # fmt: skip
    assert {"field": "body.text", "issue": "too_long"} in corps["details"]
    assert {"field": "body.bidule", "issue": "unknown_field"} in corps["details"]
    assert "xxxx" not in json.dumps(corps)  # jamais un fragment de l'entrée (TA-38)


def test_contenu_refuse(client_api: TestClient) -> None:
    avec_fournisseur(RefusContenu("filtre"))
    corps = erreur(client_api.post("/v1/extract/text", json={"text": "Bonjour, une fuite."}),
                   422, "content_refused")  # fmt: skip
    assert corps["message"] == MESSAGE_REFUS_CONTENU


def test_limite_de_debit(client_api: TestClient) -> None:
    api.dependency_overrides[get_limiteur] = lambda: LimiteurDebit([(60, 0)])
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    corps = erreur(r, 429, "rate_limited")
    assert corps["retry_after_s"] == int(r.headers["Retry-After"]) == 60


def test_scenario_inconnu(client_api: TestClient) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-99"})
    erreur(r, 404, "scenario_not_found")


def test_transcription_absente(client_api: TestClient) -> None:
    corps = erreur(client_api.post("/v1/demo/runs", json={"mode": "transcript"}), 422,
                   "validation_failed")  # fmt: skip
    assert corps["details"] == [{"field": "body.transcript", "issue": "required"}]


def test_demo_message_d_un_fournisseur(client_api: TestClient) -> None:
    avec_fournisseur(
        json.dumps(
            {
                "categorie": "fournisseur",
                "confiance": 0.95,
                "nom_appelant": "Julie Lambert",
                "societe": None,
                "numero_dicte": None,
                "message": "Livraison jeudi.",
                "rappel_souhaite": True,
            }
        )  # fmt: skip
    )
    r = client_api.post("/v1/demo/runs", json={
        "mode": "transcript", "transcript": "Appelant : Julie Lambert, livraison jeudi.",
        "caller_number": "+33699000011"})  # fmt: skip
    corps = r.json()
    assert r.status_code == 200 and corps["issue"] == "message" and corps["draft"] is None
    assert corps["message"]["numero_rappel"] == "+33699000011"
    assert corps["plaintext_draft_notice"] == "P-03" and corps["conformity"] is None


def test_perimetre_p4_outil_refuse_et_borne(
    client_api: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Critère P4 : outil hors liste refusé, appel au-delà de la borne arrêté, journalisé."""
    with caplog.at_level(logging.INFO):
        r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": PERIMETRE})
    corps = r.json()
    assert r.status_code == 200 and corps["simulated_model"] is True
    appels = corps["tool_calls"]
    assert appels[0]["nom"] == "lire_base" and appels[0]["statut"] == "outil_inconnu"
    assert len(appels) == 6 and corps["tool_limit_reached"] is True
    assert corps["conformity"] == {"compliant": True, "gaps": []}
    journaux = "\n".join(r.getMessage() for r in caplog.records)
    assert "agent.outil nom=inconnu statut=outil_inconnu" in journaux  # nom jamais recopié
    assert "borne=True" in journaux


def test_scenarios_identiques_aux_jeux_figes() -> None:
    """La copie embarquée dans l'image reste identique aux jeux figés de `eval/`."""
    sources = {
        s["id"]: s["transcription"]
        for f in ("eval/t06/scenarios.json", "eval/qualification/scenarios.json")
        for s in json.loads((RACINE / f).read_text(encoding="utf-8"))["scenarios"]
    }
    embarques = {i: s.transcription for i, s in charger_scenarios().items() if i != PERIMETRE}
    assert embarques == sources and len(embarques) == 16


def test_routes_anterieures_gardent_leur_format(client_api: TestClient) -> None:
    r = client_api.post("/llm/essai", json={})
    assert r.status_code == 422 and "detail" in r.json()
    assert "X-Request-Id" in r.headers and "Cache-Control" not in r.headers


def test_openapi_decrit_les_routes(client_api: TestClient) -> None:
    chemins = client_api.get("/openapi.json").json()["paths"]
    assert {"/v1/extract/text", "/v1/demo/runs"} <= set(chemins)
    assert "422" in chemins["/v1/demo/runs"]["post"]["responses"]
