"""Correction et validation d'un dossier (sprint 5, étape 2 ; V-09, CA-5, D-86), avec PostgreSQL.

La revue rejoue le contrôle de la commune et du code postal avec un double fidèle de l'API des
référentiels (`test_evaluateur.Referentiels`). Demande `TEST_DATABASE_URL` ; ignoré sans elle,
sauf en CI.
"""

import html
import logging
import re
import uuid
from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser
from psycopg.conninfo import conninfo_to_dict

from muninn.api.agent import get_referentiels
from muninn.api.main import app as api
from muninn.core.config import get_settings
from muninn.db import roles
from muninn.traitements import enregistrement
from outils_base import base_migree, exiger_base, url_postgres
from test_accessibilite import _violations, navigateur  # noqa: F401 : fixture partagée
from test_evaluateur import Referentiels

exiger_base()

MDP = {"api": "api-" + "a" * 28, "ingestion": "ingestion-" + "b" * 22,
       "traitements": "traitements-" + "c" * 20}  # fmt: skip


@pytest.fixture(scope="module")
def base() -> Iterator[str]:
    with base_migree() as nom:
        roles.preparer_roles(url_postgres(nom), MDP)
        yield nom


@pytest.fixture
def actifs(base: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    p = conninfo_to_dict(exiger_base())
    url = (f"postgresql://{base}_traitements:{MDP['traitements']}"
           f"@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{base}")  # fmt: skip
    monkeypatch.setenv("DATABASE_URL_TRAITEMENTS", url)
    get_settings.cache_clear()
    enregistrement.moteur.cache_clear()
    api.dependency_overrides[get_referentiels] = lambda: Referentiels()
    yield base
    enregistrement.moteur.cache_clear()


def dossier(client: TestClient) -> dict[str, Any]:
    r = client.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    assert r.status_code == 200, r.text
    corps: dict[str, Any] = r.json()
    assert corps["review_available"] is True
    return corps


def lire(base: str, sql: str, *params: object) -> list[tuple[Any, ...]]:
    with psycopg.connect(url_postgres(base)) as conn:
        return list(conn.execute(sql, params))


def test_validation_sans_correction_puis_conflit(actifs: str, client_api: TestClient) -> None:
    draft_id = dossier(client_api)["draft"]["draft_id"]
    r = client_api.post(f"/v1/demo/runs/{draft_id}/review", json={"decision": "validated"})
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "validated" and r.json()["corrected_fields"] == []
    assert lire(actifs, "SELECT etat FROM app.dossiers WHERE draft_id = %s", draft_id) == [
        ("valide",)
    ]
    second = client_api.post(f"/v1/demo/runs/{draft_id}/review", json={"decision": "validated"})
    assert second.status_code == 409 and second.json()["code"] == "conflict"


def test_correction_rejoue_le_controle_sans_garder_la_valeur(
    actifs: str, client_api: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """CA-5 : le code postal corrigé en 93170, la commune et le code postal passent « vérifié »,
    une correction de plus par champ ; « 93170 » n'est ni dans les corrections ni dans les
    journaux."""
    draft_id = dossier(client_api)["draft"]["draft_id"]
    champs = ["client.adresse.code_postal", "client.adresse.commune"]
    with caplog.at_level(logging.INFO):
        r = client_api.post(f"/v1/demo/runs/{draft_id}/review", json={
            "decision": "validated_with_corrections", "corrected_fields": champs,
            "values": {"client.adresse.code_postal": "93170", "client.adresse.commune": "Bagnolet"},
        })  # fmt: skip
    assert r.status_code == 200, r.text
    corps = r.json()
    controles = corps["draft"]["checks"]
    assert controles["client.adresse.code_postal"]["status"] == "verified"
    assert controles["client.adresse.commune"]["status"] == "verified"
    assert corps["envelope"]["provenance"]["client.adresse.code_postal"] == {
        "origine": "corrige", "auteur": "artisan"
    }  # fmt: skip
    assert corps["draft"]["client"]["adresse"]["code_postal"]["value"] == "93170"
    corrections = lire(actifs, "SELECT champ FROM app.corrections WHERE draft_id = %s", draft_id)
    assert sorted(c[0] for c in corrections) == sorted(champs)
    assert "93170" not in str(lire(actifs, "SELECT * FROM app.corrections"))
    # D-82 : la valeur corrigée n'est gardée nulle part, pas même dans le dossier validé.
    assert "93170" not in str(
        lire(actifs, "SELECT * FROM app.dossiers WHERE draft_id = %s", draft_id)
    )
    assert lire(actifs, "SELECT etat FROM app.dossiers WHERE draft_id = %s", draft_id) == [
        ("valide",)
    ]
    assert "93170" not in caplog.text and "revue.fin" in caplog.text


def test_une_incoherence_reste_signalee(actifs: str, client_api: TestClient) -> None:
    """Le serveur rejoue le contrôle honnêtement : une paire fausse reste « incohérent »."""
    draft_id = dossier(client_api)["draft"]["draft_id"]
    r = client_api.post(f"/v1/demo/runs/{draft_id}/review", json={
        "decision": "validated_with_corrections",
        "corrected_fields": ["client.adresse.commune", "client.adresse.code_postal"],
        "values": {"client.adresse.commune": "Bagnolet", "client.adresse.code_postal": "93100"},
    })  # fmt: skip
    assert r.status_code == 200, r.text
    assert r.json()["draft"]["checks"]["client.adresse.commune"]["status"] == "mismatch"


AVEC = "validated_with_corrections"
CP = "client.adresse.code_postal"


@pytest.mark.parametrize(
    ("corps", "champ"),
    [
        ({"decision": "validated", "corrected_fields": ["client.nom"]}, None),
        ({"decision": AVEC, "corrected_fields": ["client.nom"]}, None),
        ({"decision": AVEC, "corrected_fields": ["client.telephone"],
          "values": {"client.telephone": "pas un numéro"}}, "body.values.client.telephone"),
        ({"decision": AVEC, "corrected_fields": [CP], "values": {CP: "931"}}, f"body.values.{CP}"),
        ({"decision": "rejected"}, None),
    ],
)  # fmt: skip
def test_corps_refuse(
    actifs: str, client_api: TestClient, corps: dict[str, Any], champ: str | None
) -> None:
    draft_id = dossier(client_api)["draft"]["draft_id"]
    r = client_api.post(f"/v1/demo/runs/{draft_id}/review", json=corps)
    assert r.status_code == 422 and r.json()["code"] == "validation_failed", r.text
    if champ:
        assert r.json()["details"] == [{"field": champ, "issue": "invalid_format"}]
    assert lire(actifs, "SELECT etat FROM app.dossiers WHERE draft_id = %s", draft_id) == [
        ("brouillon",)
    ]


def test_dossier_inconnu(actifs: str, client_api: TestClient) -> None:
    r = client_api.post(f"/v1/demo/runs/{uuid.uuid4()}/review", json={"decision": "validated"})
    assert r.status_code == 404 and r.json()["code"] == "draft_not_found"


def test_un_texte_libre_n_est_pas_validable(actifs: str, client_api: TestClient) -> None:
    corps = {"mode": "transcript", "transcript": "Appelant : fuite à Bagnolet."}
    r = client_api.post("/v1/demo/runs", json=corps)
    assert r.status_code == 200 and r.json()["review_available"] is False


def test_parcours_de_la_console(
    actifs: str,
    client_console: TestClient,
    navigateur: Browser,  # noqa: F811
) -> None:
    """De la console : traiter SC-01, corriger le code postal et la commune, valider."""
    page = client_console.post("/agent/executer", data={"mode": "scenario", "scenario_id": "SC-01"})
    assert "Valider le dossier" in page.text
    draft_id = re.search(r'name="draft_id" value="([0-9a-f-]{36})"', page.text)
    origine = re.search(r'name="origine" value="([^"]*)"', page.text)
    assert draft_id and origine
    valide = client_console.post("/agent/valider", data={
        "draft_id": draft_id.group(1), "origine": html.unescape(origine.group(1)),
        "scenario_id": "SC-01", "client.adresse.code_postal": "93170",
        "client.adresse.commune": "Bagnolet", "demande.urgence": "urgent", "confirme": "oui",
    })  # fmt: skip
    assert valide.status_code == 200
    assert "Dossier validé" in valide.text and "client.adresse.code_postal" in valide.text
    nombre, rapport = _violations(navigateur, valide.text)
    assert nombre == 0, rapport
