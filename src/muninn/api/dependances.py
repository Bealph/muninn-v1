"""Dépendances partagées des routes : fournisseur LLM, fournisseur de voix et limite de débit,
uniques par processus.

Les tests les remplacent par `app.dependency_overrides` (faux fournisseurs, limite neuve).
"""

from functools import lru_cache

from muninn.api.erreurs import ErreurAPI
from muninn.api.limites import LimiteurDebit
from muninn.core.config import get_settings
from muninn.llm.fournisseur import FournisseurLLM, construire_fournisseur
from muninn.voix.contrat import FournisseurVoix
from muninn.voix.fournisseur import construire_fournisseur_voix


@lru_cache
def get_fournisseur() -> FournisseurLLM:
    """Fournisseur LLM unique par processus ; remplacé par le faux dans les tests."""
    return construire_fournisseur(get_settings())


@lru_cache
def _fournisseur_voix() -> FournisseurVoix:
    return construire_fournisseur_voix(get_settings())


def get_fournisseur_voix() -> FournisseurVoix:
    """Fournisseur de voix unique par processus (D-50) ; remplacé par le faux dans les tests.

    Une configuration incomplète (voix « azure » sans point d'accès) rend une 503 au format du
    contrat, et non une erreur 500 brute.
    """
    try:
        return _fournisseur_voix()
    except ValueError as erreur:
        raise ErreurAPI(503, "voice_unavailable") from erreur


@lru_cache
def get_limiteur() -> LimiteurDebit:
    """Limite globale des appels au LLM, unique par processus."""
    settings = get_settings()
    return LimiteurDebit([(60, settings.llm_limite_minute), (86_400, settings.llm_limite_jour)])
