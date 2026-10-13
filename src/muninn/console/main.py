"""Point d'entrée de la console de démonstration (ADR-09 : processus séparé de l'API).

La console ne parle qu'à l'API, jamais directement au LLM.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from muninn import __version__
from muninn.core.config import get_settings

app = FastAPI(title="Muninn console", version=__version__)
gabarits = Jinja2Templates(directory=Path(__file__).parent / "templates")


def get_client_api() -> Iterator[httpx.Client]:
    """Client HTTP vers l'API ; remplacé dans les tests par un client branché sur l'API."""
    with httpx.Client(
        base_url=get_settings().api_base_url, timeout=httpx.Timeout(40.0, connect=5.0)
    ) as client:
        yield client


ClientAPI = Annotated[httpx.Client, Depends(get_client_api)]


def _version_api(client: httpx.Client) -> dict[str, Any]:
    try:
        reponse = client.get("/version")
        reponse.raise_for_status()
        donnees: dict[str, Any] = reponse.json()
        return donnees
    except (httpx.HTTPError, ValueError):
        return {"version": "injoignable", "git_sha": "injoignable", "environment": "inconnu"}


def _page(request: Request, client: httpx.Client, **contexte: Any) -> HTMLResponse:
    settings = get_settings()
    return gabarits.TemplateResponse(
        request,
        "accueil.html",
        {
            "api": _version_api(client),
            "console": {"version": __version__, "git_sha": settings.git_sha},
            "question": "",
            "modele": "A",
            **contexte,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que le processus répond."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def accueil(request: Request, client: ClientAPI) -> HTMLResponse:
    """Page d'essai : version livrée et formulaire d'appel au LLM."""
    return _page(request, client)


@app.post("/essai", response_class=HTMLResponse)
def essai(
    request: Request,
    client: ClientAPI,
    question: Annotated[str, Form(min_length=1, max_length=500)],
    modele: Annotated[str, Form(pattern="^[AB]$")] = "A",
) -> HTMLResponse:
    """Transmet la question à l'API et affiche la réponse du LLM."""
    resultat: dict[str, Any] | None = None
    erreur: str | None = None
    try:
        reponse = client.post("/llm/essai", json={"question": question, "modele": modele})
        if reponse.status_code == 200:
            resultat = reponse.json()
        else:
            erreur = str(reponse.json().get("detail", f"Erreur {reponse.status_code}."))
    except (httpx.HTTPError, ValueError):
        erreur = "L'API est injoignable."
    return _page(
        request, client, question=question, modele=modele, resultat=resultat, erreur=erreur
    )
