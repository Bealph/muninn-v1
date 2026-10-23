"""Traces du parcours principal et étapes d'un appel (sprint 5, étape 3 ; D-40, D-87).

Les traces sont captées par un exportateur en mémoire : aucun envoi vers Azure.
"""

import logging
import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from muninn import telemetrie

CODE = re.compile(r"[A-Za-z0-9_.,\-]{1,80}")


@pytest.fixture
def traces(monkeypatch: pytest.MonkeyPatch) -> Iterator[InMemorySpanExporter]:
    exportateur = InMemorySpanExporter()
    fournisseur = TracerProvider()
    fournisseur.add_span_processor(SimpleSpanProcessor(exportateur))
    monkeypatch.setattr(telemetrie, "traceur", lambda: fournisseur.get_tracer("essai"))
    yield exportateur
    fournisseur.shutdown()


def test_sans_chaine_de_connexion_aucun_traceur(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    telemetrie.traceur.cache_clear()
    assert telemetrie.traceur() is None


def test_liste_blanche_des_attributs() -> None:
    gardes = telemetrie.filtrer({
        "categorie": "demande_service", "outils": 2, "a_verifier": True,
        "nom_client": "Martin", "statut": "Paul Martin, Montreuil", "motifs": "x" * 200,
    })  # fmt: skip
    assert gardes == {
        "muninn.categorie": "demande_service", "muninn.outils": 2, "muninn.a_verifier": True
    }  # fmt: skip


def test_la_demo_rend_les_etapes_dans_l_ordre(client_api: TestClient) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    assert r.status_code == 200, r.text
    etapes = r.json()["steps"]
    noms = [e["nom"] for e in etapes]
    assert noms[0] == "appel"
    for attendu in ("controle_entree", "qualification", "agent", "controles_serveur"):
        assert attendu in noms
    assert noms.index("controle_entree") < noms.index("qualification") < noms.index("agent")
    assert noms.index("agent") < noms.index("controles_serveur")
    debuts = [e["debut_ms"] for e in etapes]
    assert debuts == sorted(debuts) and all(e["duree_ms"] >= 0 for e in etapes)
    racine = etapes[0]
    assert racine["niveau"] == 0 and racine["details"]["issue"] == "dossier"
    assert all(e["niveau"] >= 1 for e in etapes[1:])


def test_les_traces_ne_portent_aucun_contenu(
    client_api: TestClient, traces: InMemorySpanExporter
) -> None:
    r = client_api.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-01"})
    assert r.status_code == 200
    spans = traces.get_finished_spans()
    noms = {s.name for s in spans}
    assert {"appel", "controle_entree", "qualification", "agent", "controles_serveur"} <= noms
    racine = next(s for s in spans if s.name == "appel")
    assert all(s.context.trace_id == racine.context.trace_id for s in spans)
    # Arbre complet : chaque étape a pour parent une étape exportée, la racine n'en a pas.
    ids = {s.context.span_id for s in spans}
    assert racine.parent is None
    assert all(s.parent is not None and s.parent.span_id in ids for s in spans if s is not racine)
    # Un attribut texte est un code sans espace : il ne peut pas reprendre un passage de l'appel.
    for s in spans:
        for cle, valeur in (s.attributes or {}).items():
            assert cle in telemetrie.ATTRIBUTS_AUTORISES, cle
            if isinstance(valeur, str):
                assert CODE.fullmatch(valeur), (cle, valeur)


def test_l_environnement_separe_les_traces(monkeypatch: pytest.MonkeyPatch) -> None:
    # Application Insights forme le rôle avec l'espace de noms et le nom du service.
    monkeypatch.setenv("ENVIRONMENT", "production")
    attributs = telemetrie.ressource().attributes
    assert (attributs["service.namespace"], attributs["service.name"]) == (
        "production", "muninn-api"
    )  # fmt: skip


def test_les_etapes_ignorent_le_contexte_global(traces: InMemorySpanExporter) -> None:
    # Langfuse place ses observations dans le contexte global (V-13) : une étape ne s'y rattache
    # pas, et une observation de Langfuse ne devient pas fille d'une étape.
    exportateur = InMemorySpanExporter()
    autre = TracerProvider()
    autre.add_span_processor(SimpleSpanProcessor(exportateur))
    langfuse = autre.get_tracer("langfuse")
    with telemetrie.etape("appel"), langfuse.start_as_current_span("observation"):
        with telemetrie.etape("agent"), langfuse.start_as_current_span("generation"):
            with telemetrie.etape("outil"):
                pass
    nos = {s.name: s for s in traces.get_finished_spans()}
    leurs = {s.name: s for s in exportateur.get_finished_spans()}
    assert nos["appel"].parent is None
    assert nos["agent"].parent is not None and nos["outil"].parent is not None
    assert nos["agent"].parent.span_id == nos["appel"].context.span_id
    assert nos["outil"].parent.span_id == nos["agent"].context.span_id
    assert leurs["observation"].parent is None
    assert leurs["generation"].parent is not None
    assert leurs["generation"].parent.span_id == leurs["observation"].context.span_id


def test_exportateur_relie_a_notre_fournisseur_et_journal_http_muet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Chaîne de connexion factice : rien n'est envoyé pendant le test (aucun span n'est créé).
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000;"
        "IngestionEndpoint=https://exemple.invalid/",
    )
    monkeypatch.setenv("APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL", "true")
    telemetrie.traceur.cache_clear()
    try:
        t = telemetrie.traceur()
        assert t is not None
        processeur = t.span_processor._span_processors[0]  # type: ignore[attr-defined]
        lie = processeur.span_exporter._tracer_provider
        # Sans ce lien, l'exportateur cherche le fournisseur global et journalise une erreur.
        assert isinstance(lie, TracerProvider)
        assert lie._active_span_processor is t.span_processor  # type: ignore[attr-defined]
        journal_http = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
        assert journal_http.getEffectiveLevel() >= logging.WARNING
    finally:
        telemetrie.traceur.cache_clear()
