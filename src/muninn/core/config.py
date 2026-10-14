"""Configuration lue dans l'environnement ; aucun secret n'a de valeur par défaut."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Réglages de l'application, lus dans les variables d'environnement ou le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    git_sha: str = "local"
    database_url: SecretStr | None = None
    api_base_url: str = "http://localhost:8000"

    # LLM (D-44, D-45). « faux » répond sans réseau : c'est le défaut, pour les tests et la CI.
    llm_fournisseur: Literal["faux", "azure"] = "faux"
    # Point d'accès de la ressource Azure AI Foundry, par exemple https://<nom>.services.ai.azure.com
    azure_ai_endpoint: str | None = None
    azure_ai_model_a: str = "gpt-5.4-mini"
    azure_ai_model_b: str | None = None
    # Facultative : sans clé, l'authentification passe par Entra ID (identité managée ou az login).
    azure_ai_api_key: SecretStr | None = None
    # Limite globale des appels au LLM (route publique, chaque appel est payant).
    llm_limite_minute: int = Field(default=10, ge=0)
    llm_limite_jour: int = Field(default=200, ge=0)


@lru_cache
def get_settings() -> Settings:
    """Rend les réglages, lus une seule fois par processus."""
    return Settings()
