"""Traces du parcours principal et étapes d'un appel (sprint 5, étape 3 ; D-40, D-87).

Un même mécanisme, `etape(nom, **attributs)`, sert à deux choses :
1. une trace OpenTelemetry vers Application Insights, si `APPLICATIONINSIGHTS_CONNECTION_STRING`
   est définie (export direct, D-87) ; sinon rien n'est envoyé et aucune erreur n'est levée ;
2. la liste chronologique des étapes de l'appel en cours, avec leurs durées, que l'API rend à
   l'écran « Démonstration » (`collecte()`).

Aucun contenu dans un signal (OB-1) : les attributs passent par une liste blanche (OB-2) ; une
valeur texte n'est gardée que si c'est un code court (`[a-z0-9_.-]`, 40 caractères au plus).
Le fournisseur de traces est propre au module, jamais enregistré comme fournisseur global :
Langfuse garde le sien (V-13).
"""

import atexit
import logging
import os
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode, Tracer

journal = logging.getLogger(__name__)

ATTRIBUTS_AUTORISES = frozenset({
    "muninn.request_id", "muninn.route", "muninn.scenario_id", "muninn.issue", "muninn.categorie",
    "muninn.regle", "muninn.statut", "muninn.outil", "muninn.resultat", "muninn.a_verifier",
    "muninn.garde_fous", "muninn.motifs", "muninn.tentatives", "muninn.outils", "muninn.borne",
    "muninn.jetons", "muninn.cout_micro_eur", "muninn.securite", "muninn.code_refus",
})  # fmt: skip
MOTIF_CODE = re.compile(r"[a-z0-9_.,\-]{1,80}")


@dataclass
class Etape:
    """Une étape de l'appel : nom, début et durée en millisecondes, statut ; sans contenu."""

    nom: str
    debut_ms: int
    duree_ms: int
    statut: str = "ok"
    niveau: int = 0
    details: dict[str, str | int | float | bool] = field(default_factory=dict)


_collecte: ContextVar[tuple[float, list[Etape]] | None] = ContextVar("collecte", default=None)
_niveau: ContextVar[int] = ContextVar("niveau", default=0)


def filtrer(attributs: dict[str, object]) -> dict[str, str | int | float | bool]:
    """Les seuls attributs autorisés, et pour un texte, un code court seulement."""
    gardes: dict[str, str | int | float | bool] = {}
    for cle, valeur in attributs.items():
        nom = cle if cle.startswith("muninn.") else f"muninn.{cle}"
        if nom not in ATTRIBUTS_AUTORISES or valeur is None:
            continue
        if isinstance(valeur, bool | int | float):
            gardes[nom] = valeur
        elif isinstance(valeur, str) and MOTIF_CODE.fullmatch(valeur.lower()):
            gardes[nom] = valeur
    return gardes


@lru_cache
def traceur() -> Tracer | None:
    """Le traceur vers Application Insights, ou rien sans chaîne de connexion."""
    connexion = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connexion:
        return None
    from azure.monitor.opentelemetry.exporter import (  # noqa: PLC0415 : chargé seulement si utile
        ApplicationInsightsSampler,
        AzureMonitorTraceExporter,
    )

    ressource = Resource.create({
        "service.name": "muninn-api",
        "service.version": os.environ.get("GIT_SHA", "local"),
        "deployment.environment.name": os.environ.get("ENVIRONMENT", "local"),
    })  # fmt: skip
    # L'exportateur exige l'échantillonneur d'Application Insights (page du paquet) ;
    # tout est gardé.
    fournisseur = TracerProvider(resource=ressource, sampler=ApplicationInsightsSampler(1.0))
    fournisseur.add_span_processor(
        BatchSpanProcessor(AzureMonitorTraceExporter(connection_string=connexion))
    )
    atexit.register(fournisseur.shutdown)
    return fournisseur.get_tracer("muninn")


@contextmanager
def collecte() -> Iterator[list[Etape]]:
    """Active la liste des étapes pour l'appel en cours, et la rend."""
    etapes: list[Etape] = []
    jeton = _collecte.set((time.perf_counter(), etapes))
    try:
        yield etapes
    finally:
        _collecte.reset(jeton)


@contextmanager
def etape(nom: str, **attributs: object) -> Iterator[dict[str, object]]:
    """Une étape mesurée ; le bloc peut compléter ses attributs par le dictionnaire rendu."""
    complements: dict[str, object] = {}
    debut = time.perf_counter()
    niveau = _niveau.get()
    jeton_niveau = _niveau.set(niveau + 1)
    t = traceur()
    span_ctx = t.start_as_current_span(nom) if t is not None else None
    span = span_ctx.__enter__() if span_ctx is not None else None
    statut = "ok"
    try:
        yield complements
    except Exception:
        statut = "erreur"
        raise
    finally:
        _niveau.reset(jeton_niveau)
        gardes = filtrer(attributs | complements)
        statut = str(complements.get("statut_etape", statut))
        if span is not None and span_ctx is not None:
            try:
                span.set_attributes(gardes)
                if statut == "erreur":
                    span.set_status(Status(StatusCode.ERROR))
                span_ctx.__exit__(None, None, None)
            except Exception as erreur:  # noqa: BLE001 : une trace ne fait jamais échouer un appel
                journal.warning("telemetrie.echec erreur=%s", type(erreur).__name__)
        actif = _collecte.get()
        if actif is not None:
            origine, etapes = actif
            etapes.append(Etape(
                nom=nom, debut_ms=round((debut - origine) * 1000),
                duree_ms=round((time.perf_counter() - debut) * 1000), statut=statut,
                niveau=niveau, details={k.removeprefix("muninn."): v for k, v in gardes.items()},
            ))  # fmt: skip
