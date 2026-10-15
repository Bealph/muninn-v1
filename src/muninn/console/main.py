"""Point d'entrée de la console de démonstration (ADR-09 : processus séparé de l'API).

La console ne parle qu'à l'API, jamais directement au LLM.
"""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

import httpx
from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from muninn import __version__
from muninn.core.config import get_settings

app = FastAPI(title="Muninn console", version=__version__)
gabarits = Jinja2Templates(directory=Path(__file__).parent / "templates")


def date_lisible(valeur: str) -> str:
    """Date lisible : « 15/10/2026 à 14:12 UTC » pour un instant, « 01/10/2026 » pour une date."""
    try:
        instant = datetime.fromisoformat(valeur)
    except (TypeError, ValueError):
        return str(valeur)
    if len(valeur) <= 10:
        return f"{instant:%d/%m/%Y}"
    return f"{instant.astimezone(UTC):%d/%m/%Y à %H:%M} UTC"


gabarits.env.filters["date_lisible"] = date_lisible


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
            "page": "accueil",
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


METIERS = ("plomberie", "chauffage", "electricite", "serrurerie", "autre")
LIBELLES = {
    "trouve": "Réponse tirée des données",
    "hors_corpus": "Refus : hors des données",
    "hors_perimetre": "Refus : hors du périmètre",
    "incoherent": "Nom et code postal incohérents",
}
TRANCHES = {
    "NN": "non employeur",
    "00": "0 salarié",
    "employer": "employeur",
    "empty": "non renseignée",
}
FORMES = {"ei": "entrepreneur individuel", "sarl": "SARL", "sas": "SAS", "other": "autre"}


def _page_referentiels(request: Request, **contexte: Any) -> HTMLResponse:
    valeurs: dict[str, Any] = {
        "page": "referentiels",
        "metiers": METIERS,
        "libelles": LIBELLES,
        "tranches": TRANCHES,
        "formes": FORMES,
        "nom": "",
        "code_postal": "",
        "mot": "",
        "metier": "plomberie",
        "metier_marche": "plomberie",
        "resultat": None,
        "rappel": None,
        "nationaux": None,
        "erreur": None,
    }
    return gabarits.TemplateResponse(request, "referentiels.html", valeurs | contexte)


def _interroger(appel: Callable[[], httpx.Response]) -> tuple[dict[str, Any] | None, str | None]:
    """Appelle l'API ; rend sa réponse, ou un message d'erreur lisible."""
    try:
        reponse = appel()
        donnees: dict[str, Any] = reponse.json()
    except (httpx.HTTPError, ValueError):
        return None, "L'API est injoignable."
    if reponse.status_code == 200:
        return donnees, None
    detail = donnees.get("detail", f"Erreur {reponse.status_code}.")
    if isinstance(detail, list):  # erreur de validation : premier message, en clair
        message = str(detail[0].get("msg", "valeur invalide")).removeprefix("Value error, ")
        detail = "Entrée refusée : " + message
    return None, str(detail)


@app.get("/referentiels", response_class=HTMLResponse)
def referentiels(request: Request) -> HTMLResponse:
    """Écran des référentiels (D-57) : questions aux données, sources citées, refus motivés."""
    return _page_referentiels(request)


@app.post("/referentiels/commune", response_class=HTMLResponse)
def referentiels_commune(
    request: Request,
    client: ClientAPI,
    nom: Annotated[str, Form(max_length=120)] = "",
    code_postal: Annotated[str, Form(max_length=5)] = "",
) -> HTMLResponse:
    corps = {k: v.strip() for k, v in (("nom", nom), ("code_postal", code_postal)) if v.strip()}
    resultat, erreur = _interroger(lambda: client.post("/v1/referentiels/communes", json=corps))
    rappel = " ; ".join(
        f"{libelle} « {valeur} »"
        for libelle, valeur in (("commune", nom.strip()), ("code postal", code_postal.strip()))
        if valeur
    )
    return _page_referentiels(
        request,
        nom=nom,
        code_postal=code_postal,
        resultat=resultat,
        erreur=erreur,
        rappel=rappel or "aucune valeur",
    )


@app.post("/referentiels/terme", response_class=HTMLResponse)
def referentiels_terme(
    request: Request,
    client: ClientAPI,
    mot: Annotated[str, Form(min_length=1, max_length=80)],
    metier: Annotated[str, Form(max_length=40)] = "plomberie",
) -> HTMLResponse:
    corps = {"mot": mot, "metier": metier}
    resultat, erreur = _interroger(lambda: client.post("/v1/referentiels/termes", json=corps))
    return _page_referentiels(
        request,
        mot=mot,
        metier=metier,
        resultat=resultat,
        erreur=erreur,
        rappel=f"mot « {mot} », métier {metier}",
    )


@app.get("/referentiels/marche", response_class=HTMLResponse)
def referentiels_marche(
    request: Request, client: ClientAPI, metier: Annotated[str, Query(max_length=40)]
) -> HTMLResponse:
    resultat, erreur = _interroger(
        lambda: client.get(f"/v1/referentiels/marche/{quote(metier, safe='')}")
    )
    nationaux = (
        [c for c in resultat["comptages"] if c["department_code"] == "FR"] if resultat else None
    )
    return _page_referentiels(
        request,
        metier_marche=metier,
        resultat=resultat,
        nationaux=nationaux,
        erreur=erreur,
        rappel=f"marché, métier {metier}",
    )
