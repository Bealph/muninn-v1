"""Traces du parcours principal et étapes d'un appel (sprint 5, étape 3 ; D-40, D-87).

Un même mécanisme, `etape(nom, **attributs)`, sert à deux choses :
1. une trace OpenTelemetry vers Application Insights, si `APPLICATIONINSIGHTS_CONNECTION_STRING`
   est définie (export direct, D-87) ; sinon rien n'est envoyé et aucune erreur n'est levée ;
2. la liste chronologique des étapes de l'appel en cours, avec leurs durées, que l'API rend à
   l'écran « Démonstration » (`collecte()`).

Aucun contenu dans un signal (OB-1) : les attributs passent par une liste blanche (OB-2) ; une
valeur texte n'est gardée que si c'est un code court (`[a-z0-9_.,-]`, 80 caractères au plus).
Le fournisseur de traces est propre au module, jamais enregistré comme fournisseur global :
Langfuse garde le sien (V-13). Le contexte global non plus n'est pas partagé : la parenté des
étapes suit sa propre variable de contexte (voir `_ouvrir`).
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

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, Status, StatusCode, Tracer

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
_span: ContextVar[Span | None] = ContextVar("span", default=None)


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


def ressource() -> Resource:
    """Identité du service dans les traces.

    Application Insights ne reprend pas `deployment.environment.name` : son rôle (`cloud_RoleName`)
    vaut `service.namespace` + « . » + `service.name` (exportateur, `_utils._get_cloud_role`).
    L'environnement est donc posé en espace de noms : `production.muninn-api`, par exemple ;
    c'est ce qui sépare la préproduction de la production dans le composant partagé.
    """
    environnement = os.environ.get("ENVIRONMENT", "local")
    return Resource.create({
        "service.name": "muninn-api",
        "service.namespace": environnement,
        "service.version": os.environ.get("GIT_SHA", "local"),
        "deployment.environment.name": environnement,
    })  # fmt: skip


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

    # L'exportateur exige l'échantillonneur d'Application Insights (page du paquet) ;
    # tout est gardé.
    fournisseur = TracerProvider(resource=ressource(), sampler=ApplicationInsightsSampler(1.0))
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


def _ouvrir(t: Tracer, nom: str, debut_ns: int) -> Span | None:
    """Ouvre le span d'une étape, enfant de l'étape en cours ou racine.

    Le contexte OpenTelemetry global n'est ni lu ni modifié : Langfuse y place ses observations,
    et une étape qui s'y rattacherait aurait pour parent un span absent d'Application Insights
    (arbre cassé), tandis que les observations de Langfuse deviendraient filles des étapes (V-13).
    """
    try:
        parent = _span.get()
        vide = otel_context.Context()
        ctx = otel_trace.set_span_in_context(parent, vide) if parent is not None else vide
        return t.start_span(nom, context=ctx, start_time=debut_ns)
    except Exception as erreur:  # noqa: BLE001 : une trace ne fait jamais échouer un appel
        journal.warning("telemetrie.echec erreur=%s", type(erreur).__name__)
        return None


@contextmanager
def etape(nom: str, **attributs: object) -> Iterator[dict[str, object]]:
    """Une étape mesurée ; le bloc peut compléter ses attributs par le dictionnaire rendu."""
    complements: dict[str, object] = {}
    debut = time.perf_counter()
    debut_ns = time.time_ns()
    niveau = _niveau.get()
    jeton_niveau = _niveau.set(niveau + 1)
    t = traceur()
    span = _ouvrir(t, nom, debut_ns) if t is not None else None
    jeton_span = _span.set(span) if span is not None else None
    statut = "ok"
    try:
        yield complements
    except Exception:
        statut = "erreur"
        raise
    finally:
        _niveau.reset(jeton_niveau)
        if jeton_span is not None:
            _span.reset(jeton_span)
        gardes = filtrer(attributs | complements)
        statut = str(complements.get("statut_etape", statut))
        if span is not None:
            try:
                span.set_attributes(gardes)
                if statut == "erreur":
                    span.set_status(Status(StatusCode.ERROR))
                span.end()
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
