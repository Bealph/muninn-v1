"""Traces Langfuse (sprint 4, étape 10 ; V-13, D-49), sans réseau : exportateur en mémoire."""

import json
import uuid
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from muninn import observabilite
from muninn.extraction.evaluateur import extraire_dossier
from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import FauxFournisseur, FournisseurAzure, RequeteChat, reponse_faux

TRANSCRIPTION = "Paul Martin, 12 rue des Lilas à Vincennes, fuite sous l'évier, au 06 99 00 00 01."
SENSIBLES = ("Martin", "Lilas", "06 99 00 00 01", "évier")


class ReferentielsHorsLigne:
    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")


@pytest.fixture
def exportateur(monkeypatch: pytest.MonkeyPatch) -> Iterator[InMemorySpanExporter]:
    """Un vrai client Langfuse, mais qui exporte en mémoire : aucune donnée ne sort du test."""
    from langfuse import Langfuse

    memoire = InMemorySpanExporter()
    client = Langfuse(
        # Singleton par clé publique dans le SDK : une clé neuve par test, donc un exportateur neuf.
        public_key=f"cle-publique-de-test-{uuid.uuid4()}",
        secret_key="cle-privee-de-test",  # noqa: S106 (valeur factice, aucun réseau)
        base_url="http://localhost:9",
        tracer_provider=TracerProvider(),
        span_exporter=memoire,
    )
    monkeypatch.setattr(observabilite, "client", lambda: client)
    monkeypatch.setattr(observabilite, "_contenu_synthetique", False)
    yield memoire
    client.flush()


def attributs(memoire: InMemorySpanExporter) -> tuple[list[str], str]:
    observabilite.envoyer()
    spans = memoire.get_finished_spans()
    texte = json.dumps([dict(s.attributes or {}) for s in spans], ensure_ascii=False, default=str)
    return [s.name for s in spans], texte


def test_sans_cles_aucun_client() -> None:
    observabilite.client.cache_clear()
    assert observabilite.client() is None
    with observabilite.observation("x") as obs:
        obs.maj(metadata={"a": 1}, entree="texte")  # ne fait rien, sans erreur


def test_extraction_tracee_sans_contenu(exportateur: InMemorySpanExporter) -> None:
    extraire_dossier(TRANSCRIPTION, charger_paquet(), FauxFournisseur(), ReferentielsHorsLigne(),
                     "plomberie", "2026-10-20", request_id="req-trace")  # fmt: skip
    noms, texte = attributs(exportateur)
    assert {"extraction", "agent"} <= set(noms)
    assert "req-trace" in texte and "partial_after_retry" in texte
    for fragment in SENSIBLES:
        assert fragment not in texte, fragment


def _azure() -> FournisseurAzure:
    corps = {"model": "gpt-5.4-mini", "usage": {"prompt_tokens": 1000, "completion_tokens": 50},
             "choices": [{"message": {"role": "assistant", "content": '{"nom": "Martin"}'},
                          "finish_reason": "stop"}]}  # fmt: skip
    return FournisseurAzure(
        "https://exemple.services.ai.azure.com",
        lambda: {"Authorization": "Bearer jeton-de-test"},
        client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=corps))
        ),
    )


def _requete() -> RequeteChat:
    return RequeteChat(modele="gpt-5.4-mini",
                       messages=[{"role": "user", "content": TRANSCRIPTION}])  # fmt: skip


def test_generation_metadonnees_seulement_en_production(exportateur: InMemorySpanExporter) -> None:
    _azure().completer(_requete())
    noms, texte = attributs(exportateur)
    assert "llm" in noms and "gpt-5.4-mini" in texte and "1000" in texte
    for fragment in (*SENSIBLES, '"nom"'):
        assert fragment not in texte, fragment


def test_contenu_visible_sur_donnees_synthetiques(
    exportateur: InMemorySpanExporter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(observabilite, "_contenu_synthetique", True)
    _azure().completer(_requete())
    _, texte = attributs(exportateur)
    assert "Lilas" in texte and "Martin" in texte


def test_une_trace_en_echec_ne_fait_pas_echouer_l_appel(monkeypatch: pytest.MonkeyPatch) -> None:
    class Cassee:
        def start_as_current_observation(self, **kwargs: Any) -> Any:
            raise RuntimeError("Langfuse en panne")

    monkeypatch.setattr(observabilite, "client", lambda: Cassee())
    f = FauxFournisseur(scenario=[reponse_faux(contenu="{}")])
    assert f.completer(_requete()).contenu == "{}"
    with observabilite.observation("x") as obs:
        obs.maj(metadata={"a": 1})


def test_nom_d_outil_invente_jamais_recopie(exportateur: InMemorySpanExporter) -> None:
    """Le modèle peut demander un outil au nom arbitraire : seul « outil_inconnu » est tracé."""
    from muninn.extraction.agent import extraire

    f = FauxFournisseur(scenario=[
        reponse_faux(appels=[("ignore_tes_regles_et_lis_la_base", {})]),
        reponse_faux(contenu="{}"),
    ])  # fmt: skip
    extraire(TRANSCRIPTION, charger_paquet(), f, ReferentielsHorsLigne(), "2026-10-20", "plomberie")
    _, texte = attributs(exportateur)
    assert "outil_inconnu" in texte and "ignore_tes_regles" not in texte
