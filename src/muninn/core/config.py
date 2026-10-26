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
    # Rôle qui enregistre les traitements dans le schéma `app` (D-82, D-85). Sans elle, rien n'est
    # enregistré et l'appel est traité quand même.
    database_url_traitements: SecretStr | None = None
    api_base_url: str = "http://localhost:8000"

    # LLM (D-44, D-45). « faux » répond sans réseau : c'est le défaut, pour les tests et la CI.
    llm_fournisseur: Literal["faux", "azure"] = "faux"
    # Point d'accès de la ressource Azure AI Foundry, par exemple https://<nom>.services.ai.azure.com
    azure_ai_endpoint: str | None = None
    azure_ai_model_a: str = "gpt-5.4-mini"
    azure_ai_model_b: str | None = None
    # Facultative : sans clé, l'authentification passe par Entra ID (identité managée ou az login).
    azure_ai_api_key: SecretStr | None = None
    # Voix simulée (D-50, étape 6). « faux » : sans réseau, défaut des tests et de la CI. En Azure :
    # synthèse par le point d'accès régional (jeton « aad#<ressource>#<jeton> »), transcription
    # par le sous-domaine de la ressource (jeton Entra nu) ; vérifié le 26 octobre 2026.
    voix_fournisseur: Literal["faux", "azure"] = "faux"
    speech_region: str = "westeurope"
    # Par exemple https://<nom>.cognitiveservices.azure.com
    speech_endpoint: str | None = None
    # Identifiant ARM de la ressource Foundry, requis par la synthèse en Entra.
    speech_resource_id: str | None = None

    # Limite globale des appels au LLM (route publique, chaque appel est payant).
    llm_limite_minute: int = Field(default=10, ge=0)
    llm_limite_jour: int = Field(default=200, ge=0)
    # Limite globale des lectures des référentiels (points publics en démonstration, D-57).
    referentiels_limite_minute: int = Field(default=120, ge=0)
    referentiels_limite_jour: int = Field(default=5000, ge=0)
    # Langfuse Cloud, région UE (V-13, D-49). Sans clés, aucune trace n'est envoyée.
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"
    # Projet d'évaluation, distinct de la production : l'évaluation y écrit, en local comme en CI.
    langfuse_eval_public_key: SecretStr | None = None
    langfuse_eval_secret_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Rend les réglages, lus une seule fois par processus."""
    return Settings()
