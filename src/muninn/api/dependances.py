"""Dépendances partagées des routes : fournisseur LLM et limite de débit, uniques par processus.

Les tests les remplacent par `app.dependency_overrides` (faux fournisseur, limite neuve).
"""

from functools import lru_cache

from muninn.api.limites import LimiteurDebit
from muninn.core.config import get_settings
from muninn.llm.fournisseur import FournisseurLLM, construire_fournisseur


@lru_cache
def get_fournisseur() -> FournisseurLLM:
    """Fournisseur LLM unique par processus ; remplacé par le faux dans les tests."""
    return construire_fournisseur(get_settings())


@lru_cache
def get_limiteur() -> LimiteurDebit:
    """Limite globale des appels au LLM, unique par processus."""
    settings = get_settings()
    return LimiteurDebit([(60, settings.llm_limite_minute), (86_400, settings.llm_limite_jour)])
