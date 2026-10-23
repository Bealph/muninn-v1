"""Montage commun : l'API utilise toujours le faux fournisseur, la console parle à cette API."""

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from muninn import observabilite, telemetrie
from muninn.api.limites import LimiteurDebit
from muninn.api.main import app as api
from muninn.api.main import get_fournisseur, get_limiteur
from muninn.console.main import app as console
from muninn.console.main import get_client_api
from muninn.core.config import Settings, get_settings
from muninn.llm.fournisseur import FauxFournisseur
from muninn.traitements import enregistrement

VARIABLES_MUNINN = (
    "ENVIRONMENT",
    "GIT_SHA",
    "LLM_FOURNISSEUR",
    "AZURE_AI_ENDPOINT",
    "AZURE_AI_MODEL_A",
    "AZURE_AI_MODEL_B",
    "AZURE_AI_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_EVAL_PUBLIC_KEY",
    "LANGFUSE_EVAL_SECRET_KEY",
    "DATABASE_URL_TRAITEMENTS",
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
)


@pytest.fixture(autouse=True)
def configuration_isolee(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Les tests ignorent le .env et l'environnement du poste : résultat identique partout."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for nom in VARIABLES_MUNINN:
        monkeypatch.delenv(nom, raising=False)
    get_settings.cache_clear()
    get_limiteur.cache_clear()
    observabilite.client.cache_clear()
    enregistrement.moteur.cache_clear()
    telemetrie.traceur.cache_clear()
    monkeypatch.setattr(observabilite, "_contenu_synthetique", False)
    yield
    get_settings.cache_clear()
    get_limiteur.cache_clear()
    enregistrement.moteur.cache_clear()


@pytest.fixture(autouse=True)
def faux_fournisseur() -> Iterator[None]:
    """Faux fournisseur et limite neuve à chaque test : aucun test ne dépend d'un autre."""
    api.dependency_overrides[get_fournisseur] = lambda: FauxFournisseur()
    limiteur = LimiteurDebit([(60, 1000)])
    api.dependency_overrides[get_limiteur] = lambda: limiteur
    yield
    api.dependency_overrides.clear()


@pytest.fixture
def client_api() -> TestClient:
    return TestClient(api)


@pytest.fixture
def client_console(client_api: TestClient) -> Iterator[TestClient]:
    """Console dont les appels HTTP vers l'API sont servis en mémoire par l'API elle-même."""

    def _client() -> httpx.Client:
        return client_api

    console.dependency_overrides[get_client_api] = _client
    yield TestClient(console)
    console.dependency_overrides.clear()
