"""Configuration lue dans l'environnement, jamais dans le code (R8)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application. Les secrets ne sont jamais affichés ni journalisés."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    git_sha: str = "local"
    database_url: SecretStr | None = None
    api_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    """Rend une configuration unique par processus."""
    return Settings()
