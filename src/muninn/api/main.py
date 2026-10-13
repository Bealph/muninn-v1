"""Point d'entrée de l'API Muninn."""

from fastapi import FastAPI

from muninn import __version__
from muninn.core.config import get_settings

app = FastAPI(title="Muninn API", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que le processus répond."""
    settings = get_settings()
    return {"status": "ok", "environment": settings.environment}
