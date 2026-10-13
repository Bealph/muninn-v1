"""Point d'entrée de la console de démonstration."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from muninn import __version__

app = FastAPI(title="Muninn console", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que le processus répond."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def accueil() -> str:
    """Page d'accueil provisoire ; elle appellera l'API à l'étape 2."""
    return (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Muninn, console</title></head>"
        "<body><main><h1>Muninn</h1><p>Console de démonstration.</p></main></body></html>"
    )
