"""Tests du socle : les deux processus répondent, la version livrée est lisible."""

from fastapi.testclient import TestClient

from muninn import __version__
from muninn.api.main import app as api
from muninn.console.main import app as console


def test_api_health() -> None:
    reponse = TestClient(api).get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "ok"


def test_api_version() -> None:
    reponse = TestClient(api).get("/version")
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["version"] == __version__
    assert set(donnees) == {"version", "git_sha", "environment"}


def test_console_health() -> None:
    reponse = TestClient(console).get("/health")
    assert reponse.status_code == 200
