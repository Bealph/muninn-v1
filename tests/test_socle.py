"""Tests du socle : les deux processus répondent."""

from fastapi.testclient import TestClient

from muninn.api.main import app as api
from muninn.console.main import app as console


def test_api_health() -> None:
    reponse = TestClient(api).get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "ok"


def test_console_accueil() -> None:
    reponse = TestClient(console).get("/")
    assert reponse.status_code == 200
    assert "Muninn" in reponse.text
