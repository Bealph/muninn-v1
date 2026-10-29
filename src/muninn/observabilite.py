"""Traces Langfuse des appels au modèle et de l'agent (V-13, D-49 ; sprint 4, étape 10).

- **Sans clés** (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`), aucun client n'est créé : les
  fonctions ci-dessous ne font rien, sans erreur. C'est le cas des tests et de la CI ordinaire.
- **En production, métadonnées seulement** : modèle, jetons, coût, durées, statuts, codes des
  garde-fous et des motifs. Le texte de l'appel, les valeurs du dossier et les messages au modèle ne
  sont jamais envoyés (R3, R4). Le contenu n'est visible que pour l'évaluation, sur données
  synthétiques (R9), quand le harnais l'autorise explicitement (`autoriser_contenu_synthetique`).
- **Traceur isolé** : un `TracerProvider` propre à Langfuse, jamais enregistré comme fournisseur
  global d'OpenTelemetry, pour ne pas capter ni perturber d'autres instrumentations.

SDK `langfuse` 4.15.6, épinglé (D-49). Région UE : https://cloud.langfuse.com.
"""

import functools
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, ParamSpec, TypeVar

from opentelemetry import trace as otel
from opentelemetry.sdk.trace import TracerProvider

from muninn.core.config import get_settings
from muninn.telemetrie import ressource

journal = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")
_contenu_synthetique = False


@lru_cache
def client() -> Any | None:
    """Le client Langfuse, ou None sans clés (aucune trace, aucune erreur)."""
    s = get_settings()
    publique = s.langfuse_public_key.get_secret_value() if s.langfuse_public_key else ""
    privee = s.langfuse_secret_key.get_secret_value() if s.langfuse_secret_key else ""
    if _contenu_synthetique and s.langfuse_eval_public_key and s.langfuse_eval_secret_key:
        # Évaluation : toujours le projet « muninn-evaluation », jamais celui de production.
        publique = s.langfuse_eval_public_key.get_secret_value()
        privee = s.langfuse_eval_secret_key.get_secret_value()
    if not (publique and privee):  # absente ou vide (secret GitHub non défini) : rien
        return None
    from langfuse import Langfuse  # import tardif : sans clés, le SDK n'est jamais chargé

    return Langfuse(
        public_key=publique,
        secret_key=privee,
        base_url=s.langfuse_base_url,
        environment=s.environment,
        release=s.git_sha,
        # Isolé : jamais le fournisseur global. La ressource est celle d'Application Insights :
        # sans elle, Langfuse affiche `service.name = unknown_service` sur chaque observation.
        tracer_provider=TracerProvider(resource=ressource()),
    )


def autoriser_contenu_synthetique() -> None:
    """Le harnais d'évaluation, sur données synthétiques seulement, rend le contenu visible."""
    global _contenu_synthetique
    _contenu_synthetique = True
    vider = getattr(client, "cache_clear", None)
    if vider is not None:  # le client suivant vise le projet d'évaluation s'il est configuré
        vider()


def contenu_visible() -> bool:
    return _contenu_synthetique


class Observation:
    """Une observation Langfuse ; sans client, chaque méthode ne fait rien."""

    def __init__(self, brute: Any = None) -> None:
        self._brute = brute

    def maj(
        self,
        *,
        metadata: dict[str, Any] | None = None,
        entree: Any = None,
        sortie: Any = None,
        **autres: Any,
    ) -> None:
        """Met à jour l'observation ; entrée et sortie sur données synthétiques seulement."""
        if self._brute is None:
            return
        champs = {k: v for k, v in autres.items() if v is not None}
        if metadata:
            champs["metadata"] = metadata
        if contenu_visible():
            if entree is not None:
                champs["input"] = entree
            if sortie is not None:
                champs["output"] = sortie
        try:
            self._brute.update(**champs)
        except Exception as erreur:  # noqa: BLE001 (une trace ne fait jamais échouer un appel)
            journal.warning("langfuse.echec type=%s", type(erreur).__name__)


def _dans_une_trace() -> bool:
    return otel.get_current_span().get_span_context().is_valid


@contextmanager
def observation(
    nom: str,
    as_type: str = "span",
    *,
    request_id: str = "",
    metadata: dict[str, Any] | None = None,
    model: str | None = None,
) -> Iterator[Observation]:
    """Ouvre une observation ; à la racine, elle nomme la trace et porte le `request_id`."""
    c = client()
    if c is None:
        yield Observation()
        return
    try:
        from langfuse import propagate_attributes

        racine = not _dans_une_trace()
        attributs = (
            propagate_attributes(
                trace_name=nom,
                metadata={"request_id": request_id} if request_id else None,
                tags=[get_settings().environment],
            )
            if racine
            else None
        )
        ouverture = c.start_as_current_observation(
            name=nom, as_type=as_type, metadata=metadata, model=model
        )
    except Exception as erreur:  # noqa: BLE001
        journal.warning("langfuse.echec type=%s", type(erreur).__name__)
        yield Observation()
        return
    if attributs is not None:
        with attributs, ouverture as brute:
            yield Observation(brute)
    else:
        with ouverture as brute:
            yield Observation(brute)


def tracer(
    nom: str | Callable[..., str],
    as_type: str = "span",
    metadata: Callable[[Any], dict[str, Any]] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Décorateur typé : trace l'appel de la fonction, garde sa signature (vérifiée par mypy).

    `nom` peut dépendre des arguments ; `metadata` reçoit le résultat et rend des métadonnées sans
    contenu. Un `request_id` passé en mot-clé est porté par la trace racine.
    """

    def decorer(fonction: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fonction)
        def enveloppe(*args: P.args, **kwargs: P.kwargs) -> R:
            libelle = nom(*args, **kwargs) if callable(nom) else nom
            with observation(libelle, as_type, request_id=str(kwargs.get("request_id", ""))) as obs:
                resultat = fonction(*args, **kwargs)
                if metadata is not None:
                    obs.maj(metadata=metadata(resultat))
                return resultat

        return enveloppe

    return decorer


def envoyer() -> None:
    """Envoie les traces en attente (fin d'un script ; l'API envoie au fil de l'eau)."""
    c = client()
    if c is not None:
        c.flush()
