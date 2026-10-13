"""Accès au LLM derrière une interface de fournisseur (R8, D-32).

Deux fournisseurs : un faux, sans réseau, pour les tests et la CI ; un fournisseur Azure AI
Foundry, qui parle le format OpenAI v1 (`/openai/v1/chat/completions`) pour les deux modèles
retenus (D-44, D-45). Les journaux ne contiennent jamais le texte échangé (R4).
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import httpx

from muninn.core.config import Settings

journal = logging.getLogger(__name__)

PORTEE_COGNITIVE_SERVICES = "https://cognitiveservices.azure.com/.default"
CONSIGNE_SYSTEME = (
    "Tu es Muninn, le secrétariat automatique d'un artisan. "
    "Réponds en français, en une ou deux phrases."
)


@dataclass(frozen=True)
class ReponseLLM:
    """Réponse du LLM, avec ce qu'il faut pour la tracer sans exposer le contenu."""

    texte: str
    modele: str
    fournisseur: str
    duree_ms: int


class ErreurFournisseur(Exception):
    """Le fournisseur n'a pas pu répondre ; le message ne contient aucune donnée échangée."""


class FournisseurLLM(Protocol):
    """Contrat commun à tous les fournisseurs."""

    nom: str

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        """Envoie la question au modèle et rend sa réponse."""
        ...


class FauxFournisseur:
    """Répond sans réseau, de façon déterministe : pour les tests, la CI et le local hors ligne."""

    nom = "faux"

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        return ReponseLLM(
            texte=f"Réponse simulée ({len(question)} caractères reçus).",
            modele=modele,
            fournisseur=self.nom,
            duree_ms=0,
        )


class FournisseurAzure:
    """Azure AI Foundry, déploiement en zone de données UE (R5), API au format OpenAI v1."""

    nom = "azure"

    def __init__(
        self,
        endpoint: str,
        entetes_auth: Callable[[], dict[str, str]],
        client: httpx.Client | None = None,
        max_jetons: int = 300,
    ) -> None:
        self._url = endpoint.rstrip("/") + "/openai/v1/chat/completions"
        self._entetes_auth = entetes_auth
        self._client = client or httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0))
        self._max_jetons = max_jetons

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        corps = {
            "model": modele,
            "messages": [
                {"role": "system", "content": CONSIGNE_SYSTEME},
                {"role": "user", "content": question},
            ],
            "max_completion_tokens": self._max_jetons,
        }
        debut = time.perf_counter()
        try:
            reponse = self._client.post(self._url, json=corps, headers=self._entetes_auth())
        except httpx.HTTPError as exc:
            journal.warning("llm.echec modele=%s cause=%s", modele, type(exc).__name__)
            raise ErreurFournisseur("Le service du modèle est injoignable.") from exc
        duree_ms = round((time.perf_counter() - debut) * 1000)
        if reponse.status_code != 200:
            journal.warning(
                "llm.echec modele=%s statut=%s duree_ms=%s", modele, reponse.status_code, duree_ms
            )
            raise ErreurFournisseur(f"Le service du modèle a répondu {reponse.status_code}.")
        try:
            donnees = reponse.json()
            texte = str(donnees["choices"][0]["message"]["content"] or "")
            modele_servi = str(donnees.get("model", modele))
            usage = donnees.get("usage", {})
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            journal.warning("llm.echec modele=%s cause=reponse_illisible", modele)
            raise ErreurFournisseur("La réponse du modèle est illisible.") from exc
        journal.info(
            "llm.appel modele=%s duree_ms=%s jetons_entree=%s jetons_sortie=%s",
            modele_servi,
            duree_ms,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return ReponseLLM(texte=texte, modele=modele_servi, fournisseur=self.nom, duree_ms=duree_ms)


def _entetes_entra() -> Callable[[], dict[str, str]]:
    """Authentification sans secret : identité managée en Azure, az login en local."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    jeton = get_bearer_token_provider(
        DefaultAzureCredential(exclude_interactive_browser_credential=True),
        PORTEE_COGNITIVE_SERVICES,
    )
    return lambda: {"Authorization": f"Bearer {jeton()}"}


def construire_fournisseur(reglages: Settings) -> FournisseurLLM:
    """Choisit le fournisseur selon la configuration."""
    if reglages.llm_fournisseur == "faux":
        return FauxFournisseur()
    if not reglages.azure_ai_endpoint:
        raise ValueError("AZURE_AI_ENDPOINT est requis quand LLM_FOURNISSEUR=azure.")
    cle = reglages.azure_ai_api_key
    if cle is not None and cle.get_secret_value():
        valeur = cle.get_secret_value()
        entetes: Callable[[], dict[str, str]] = lambda: {"api-key": valeur}  # noqa: E731
    else:
        entetes = _entetes_entra()
    return FournisseurAzure(reglages.azure_ai_endpoint, entetes)
