"""Point d'entrée de l'API Muninn."""

import logging
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from muninn import __version__
from muninn.api import erreurs
from muninn.api.agent import routeur as routeur_agent
from muninn.api.dependances import get_fournisseur, get_limiteur
from muninn.api.limites import LimiteurDebit
from muninn.core.config import get_settings
from muninn.llm.fournisseur import ErreurFournisseur, FournisseurLLM
from muninn.referentiels.routes import routeur as routeur_referentiels

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
journal = logging.getLogger(__name__)

app = FastAPI(title="Muninn API", version=__version__)
app.include_router(routeur_referentiels)
app.include_router(routeur_agent)
erreurs.installer(app)

__all__ = ["app", "get_fournisseur", "get_limiteur"]


class QuestionLLM(BaseModel):
    """Question envoyée au LLM. La longueur est bornée : la route est publique en démonstration."""

    question: str = Field(min_length=1, max_length=500)
    modele: Literal["A", "B"] = "A"


class ReponseAPI(BaseModel):
    """Réponse rendue au client : le texte et de quoi savoir qui a répondu."""

    reponse: str
    modele: str
    fournisseur: str
    duree_ms: int


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que le processus répond."""
    settings = get_settings()
    return {"status": "ok", "environment": settings.environment}


@app.get("/version")
def version() -> dict[str, str]:
    """Version et SHA livrés : ils prouvent quelle image tourne (rollback, étape 8)."""
    settings = get_settings()
    return {
        "version": __version__,
        "git_sha": settings.git_sha,
        "environment": settings.environment,
    }


@app.post("/llm/essai")
def essai_llm(
    corps: QuestionLLM,
    fournisseur: Annotated[FournisseurLLM, Depends(get_fournisseur)],
    limiteur: Annotated[LimiteurDebit, Depends(get_limiteur)],
) -> ReponseAPI:
    """Envoie une question au modèle A ou B et rend sa réponse (squelette du sprint 2)."""
    settings = get_settings()
    modele = settings.azure_ai_model_a if corps.modele == "A" else settings.azure_ai_model_b
    if not modele:
        raise HTTPException(status_code=422, detail="Le modèle B n'est pas configuré.")
    attente = limiteur.reserver()
    if attente is not None:
        journal.warning("llm.limite_atteinte attente_s=%s", attente)
        raise HTTPException(
            status_code=429,
            detail=f"Trop de demandes au modèle : réessayer dans {attente} s.",
            headers={"Retry-After": str(attente)},
        )
    try:
        r = fournisseur.repondre(corps.question, modele)
    except ErreurFournisseur as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ReponseAPI(
        reponse=r.texte, modele=r.modele, fournisseur=r.fournisseur, duree_ms=r.duree_ms
    )
