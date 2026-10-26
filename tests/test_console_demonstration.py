"""Écran « Démonstration » de la console (sprint 5, étape 6 ; D-50, D-74, D-88, CA-8).

L'API est simulée par un transport httpx : chaque test choisit sa réponse et garde les requêtes
reçues, pour vérifier ce que la console relaie (corps, type, paramètres) et ce qu'elle refuse
sans appeler l'API. Les réponses d'essai sont validées par les modèles du contrat : elles ont la
forme exacte de celles de l'API (`ReponseDemo`, `ReponseSynthese`, `TranscriptionAppel`).
"""

import base64
import json
import tempfile
from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest
import starlette.formparsers
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient

from muninn.api.agent import ReponseDemo
from muninn.console.main import app as console
from muninn.console.main import get_client_api
from muninn.voix.contrat import AUDIO_OCTETS_MAX, ReponseSynthese, TranscriptionAppel

SCENARIOS = ("SC-Q4", "SC-04", "SC-Q1", "SC-10")
# Faux extraits « MP3 » : la console et l'écran ne décodent jamais l'audio, ils le relaient.
EXTRAITS = (b"ID3\x04agent-1", b"ID3\x04appelant-1")
REFERENTIEL = {"source_id": "SRC-06", "source_date": "2026-01-01", "channel": "production"}

# --- Réponses d'essai, à la forme du contrat ---------------------------------------------------


def synthese(scenario_id: str = "SC-Q4") -> dict[str, Any]:
    """Réponse de `POST /v1/demo/voice/synthesis` : deux tours courts, un par locuteur."""
    tours = [
        {"speaker": "agent", "text": "Bonjour, ici Muninn.",
         "audio_base64": base64.b64encode(EXTRAITS[0]).decode()},
        {"speaker": "caller", "text": "Mon chauffe-eau fuit.",
         "audio_base64": base64.b64encode(EXTRAITS[1]).decode()},
    ]  # fmt: skip
    return ReponseSynthese.model_validate({
        "scenario_id": scenario_id,
        "voices": {"agent": "fr-FR-DeniseNeural", "caller": "fr-FR-HenriNeural"},
        "turns": tours,
    }).model_dump(mode="json")  # fmt: skip


def _etapes(principale: str, details: dict[str, Any]) -> list[dict[str, Any]]:
    """Étapes au format de l'API : la transcription en tête, puis le traitement réel."""
    return [
        {"nom": "appel", "debut_ms": 0, "duree_ms": 6800, "statut": "ok", "niveau": 0,
         "details": {"route": "demo", "issue": "dossier"}},
        {"nom": "transcription", "debut_ms": 0, "duree_ms": 2400, "statut": "ok", "niveau": 1,
         "details": {"audio_octets": sum(len(e) for e in EXTRAITS), "tours": 2}},
        {"nom": "controle_entree", "debut_ms": 2400, "duree_ms": 12, "statut": "ok", "niveau": 1,
         "details": {"motifs": "aucun"}},
        {"nom": "qualification", "debut_ms": 2412, "duree_ms": 900, "statut": "ok", "niveau": 1,
         "details": {"categorie": "demande_service", "securite": False, "jetons": 812,
                     "cout_micro_eur": 1000}},
        {"nom": principale, "debut_ms": 3312, "duree_ms": 3300, "statut": "ok", "niveau": 1,
         "details": {"statut": "complete", "tentatives": 1, "outils": 1, "borne": False,
                     "jetons": 4810, "cout_micro_eur": 4500}},
        {"nom": "outil", "debut_ms": 4000, "duree_ms": 123, "statut": "ok", "niveau": 2,
         "details": {"outil": "chercher_communes", "resultat": "ok"}},
        {"nom": "controles_serveur", "debut_ms": 6612, "duree_ms": 150, "statut": "ok",
         "niveau": 1, "details": details},
    ]  # fmt: skip


def _brouillon() -> dict[str, Any]:
    """Un dossier complet (SC-10) : commune entendue, trois homonymes, rien n'est choisi."""
    return {
        "draft_id": "0cf51407-1028-48b7-9f3b-694f09e8beba",
        "created_at": "2026-10-26T10:24:41Z", "source": "missed_call",
        "call_outcome": "completed",
        "provenance": {"input_mode": "simulated", "prompt_version": "extraction-2026.10.3",
                       "model_id": "gpt-5.4-mini-2026-03-17", "lexicon": None,
                       "extraction_status": "complete", "validation_attempts": 1},
        "destruction": {"transcript_destroyed_at": "2026-10-26T10:24:41Z"},
        "client": {
            "nom": {"value": None, "confidence": 0.0},
            "prenom": {"value": None, "confidence": 0.0},
            "telephone": {"value": None, "confidence": 0.0, "origin": None},
            "adresse": {"rue": {"value": None, "confidence": 0.0},
                        "code_postal": {"value": None, "confidence": 0.0},
                        "commune": {"value": "Montreuil", "confidence": 0.9}},
        },
        "demande": {"objet_court": {"value": "Radiateur qui ne chauffe plus", "confidence": 0.9},
                    "description": {"value": None, "confidence": 0.0},
                    "metier": "chauffage", "urgence": "non_precise",
                    "disponibilites_client": []},
        "cle_humaine": None,
        "actions": [{"type": "rappeler", "libelle": "Rappeler le client pour choisir la commune"}],
        "checks": {
            "client.telephone": {"status": "not_checked", "reason": "no_value"},
            "client.adresse.code_postal": {"status": "not_checked", "reason": "no_value",
                                           "referential": None},
            "client.adresse.commune": {"status": "not_checked", "reason": "not_applicable",
                                       "referential": None, "insee_code": None, "match": None,
                                       "heard_value": None},
        },
        "needs_review": False,
        "champs_manquants": ["client.nom", "client.telephone"],
    }  # fmt: skip


def _transcription() -> dict[str, Any]:
    return TranscriptionAppel.model_validate({
        "turns": [{"speaker": "agent", "text": "Bonjour, ici Muninn."},
                  {"speaker": "caller", "text": "Mon chauffe-eau fuit."}],
        "audio_bytes": sum(len(e) for e in EXTRAITS), "transcription_ms": 2400,
        "matches_scenario": True,
    }).model_dump(mode="json")  # fmt: skip


def _valider(corps: dict[str, Any]) -> dict[str, Any]:
    """La réponse a la forme exacte de `ReponseDemo` (plus la transcription, contrat § 2)."""
    transcription = corps.pop("transcription")
    corps = ReponseDemo.model_validate(corps).model_dump(mode="json", by_alias=True)
    return corps | {"transcription": transcription}


def _base(scenario_id: str, issue: str) -> dict[str, Any]:
    return {
        "request_id": "6b31ae46-c3da-4769-8d8e-c7535713b3c4", "scenario_id": scenario_id,
        "simulated_model": False, "issue": issue, "draft": None, "envelope": None,
        "message": None, "trace": None, "tool_calls": [], "tool_limit_reached": False,
        "guardrails": [], "run": None, "expected": None,
        "conformity": {"compliant": True, "gaps": []}, "latency_ms": 6800,
        "transcription": _transcription(),
    }  # fmt: skip


def reponse_dossier() -> dict[str, Any]:
    """SC-10 : dossier « à vérifier », commune ambiguë, trois candidates."""
    candidates = [
        {"code_insee": insee, "nom": "Montreuil", "departement": dep, "codes_postaux": [cp]}
        for insee, dep, cp in (("28267", "28", "28500"), ("85148", "85", "85200"),
                               ("93048", "93", "93100"))
    ]  # fmt: skip
    corps = _base("SC-10", "dossier") | {
        "qualification": {"categorie": "demande_service", "categorie_modele": "demande_service",
                          "confiance": 0.99, "regle": None, "securite": False,
                          "cost_micro_eur": 1000},
        "draft": _brouillon(),
        "envelope": {"provenance": {"client.adresse.commune": {"origine": "entendu",
                                                               "auteur": "transcription"},
                                    "client.adresse.code_postal": {"origine": "absent",
                                                                   "auteur": "aucun"}},
                     "departement": None, "candidates": candidates, "a_verifier": True,
                     "motifs": ["commune_ambigue"], "garde_fous": []},
        "steps": _etapes("agent", {"a_verifier": True, "garde_fous": "aucun",
                                   "motifs": "commune_ambigue"}),
    }  # fmt: skip
    return _valider(corps)


def reponse_gaz() -> dict[str, Any]:
    """SC-04 : urgence de sécurité, orientation en tête des actions, adresse vérifiée."""
    corps = reponse_dossier()
    corps["scenario_id"] = "SC-04"
    d = corps["draft"]
    d["demande"] |= {"urgence": "securite", "metier": "plomberie",
                     "objet_court": {"value": "Odeur de gaz", "confidence": 0.95}}  # fmt: skip
    d["client"]["adresse"] = {
        "rue": {"value": "8 rue Hoche", "confidence": 0.9},
        "code_postal": {"value": "93100", "confidence": 0.9},
        "commune": {"value": "Montreuil", "confidence": 0.95},
    }
    referentiel_cp = REFERENTIEL | {"dataset": "postal_codes", "source_id": "SRC-07"}
    d["checks"]["client.adresse.code_postal"] = {"status": "verified", "reason": None,
                                                 "referential": referentiel_cp}  # fmt: skip
    d["checks"]["client.adresse.commune"] = {"status": "verified", "reason": None,
                                             "referential": REFERENTIEL | {"dataset": "communes"},
                                             "insee_code": "93048", "match": "exact",
                                             "heard_value": "Montreuil"}  # fmt: skip
    d["actions"] = [{"type": "autre", "libelle": "Orienter : 0 800 47 33 33 ou 112"},
                    {"type": "rappeler", "libelle": "Rappeler le client"}]  # fmt: skip
    entendu = {"origine": "entendu", "auteur": "transcription"}
    corps["envelope"] |= {
        "candidates": [], "motifs": [], "a_verifier": False, "garde_fous": ["gaz"],
        "provenance": {"client.adresse.code_postal": entendu, "client.adresse.commune": entendu},
    }  # fmt: skip
    corps["guardrails"] = ["gaz"]
    corps["steps"] = _etapes("agent", {"a_verifier": False, "garde_fous": "gaz", "motifs": "aucun"})
    return _valider(corps)


def reponse_message() -> dict[str, Any]:
    """SC-Q1 : un fournisseur, un message pour Karim, pas de dossier."""
    corps = _base("SC-Q1", "message") | {
        "qualification": {"categorie": "fournisseur", "categorie_modele": "fournisseur",
                          "confiance": 0.99, "regle": None, "securite": False,
                          "cost_micro_eur": 1100},
        "message": {"categorie": "fournisseur", "nom_appelant": "Julie Lambert",
                    "societe": "Sanitaires Dupuis", "numero_rappel": "+33699000011",
                    "numero_dicte": None,
                    "message": "Livraison du ballon jeudi matin entre 8 h et 10 h au dépôt.",
                    "rappel_souhaite": True, "securite": False,
                    "recu_le": "2026-10-26T10:24:41Z", "prompt_version": "message-2026.10.1"},
    }  # fmt: skip
    etapes = [s for s in _etapes("message", {}) if s["nom"] not in ("outil", "controles_serveur")]
    etapes[-1]["details"] = {"garde_fous": "aucun"}  # l'étape « message » du qualificateur
    corps["steps"] = etapes
    return _valider(corps)


# --- API simulée -------------------------------------------------------------------------------


class ApiSimulee:
    """Transport httpx : rend la réponse choisie par le test et garde chaque requête reçue."""

    def __init__(self) -> None:
        self.demandes: list[httpx.Request] = []
        self.repondre: Callable[[httpx.Request], httpx.Response] = lambda r: httpx.Response(
            200, json={}
        )

    def __call__(self, requete: httpx.Request) -> httpx.Response:
        self.demandes.append(requete)
        return self.repondre(requete)


@pytest.fixture
def api() -> Iterator[ApiSimulee]:
    simulee = ApiSimulee()
    client = httpx.Client(transport=httpx.MockTransport(simulee), base_url="http://api")
    console.dependency_overrides[get_client_api] = lambda: client
    yield simulee
    console.dependency_overrides.pop(get_client_api, None)


@pytest.fixture
def ecran() -> TestClient:
    return TestClient(console)


def _appel(ecran: TestClient, audio: Any, type_: str = "audio/mpeg", sc: str = "SC-Q4") -> Any:
    return ecran.post(
        f"/demonstration/appel?scenario_id={sc}", content=audio, headers={"Content-Type": type_}
    )


# --- La page -----------------------------------------------------------------------------------


def test_page_liste_les_quatre_scenarios_et_le_lien(api: ApiSimulee, ecran: TestClient) -> None:
    page = ecran.get("/demonstration")
    assert page.status_code == 200
    html = page.text
    for sc in SCENARIOS:
        assert f'value="{sc}"' in html, sc
    assert html.count('type="radio" name="scenario"') == 4
    assert '<a href="/demonstration" aria-current="page">Démonstration</a>' in html
    assert 'href="/agent"' in html  # l'écran « Agent » reste
    for libelle in ("Lancer l'appel", "Arrêter", "Sonnerie de 15 s", "> Son<", "Animation"):
        assert libelle in html, libelle
    assert 'role="alert"' in html and 'aria-live="polite"' in html
    # Aucune ressource externe (police, bibliothèque, image) ; la page n'appelle pas l'API.
    assert "http://" not in html and "https://" not in html
    assert api.demandes == []


def test_lien_de_navigation_sur_les_autres_ecrans(ecran: TestClient) -> None:
    html = ecran.get("/referentiels").text
    assert '<a href="/demonstration" >Démonstration</a>' in html


def test_reponses_d_essai_conformes_au_contrat() -> None:
    """Les réponses d'essai passent par les modèles de l'API : leur forme ne peut pas dériver."""
    assert reponse_dossier()["envelope"]["candidates"][2]["code_insee"] == "93048"
    assert reponse_gaz()["draft"]["demande"]["urgence"] == "securite"
    assert reponse_message()["message"]["categorie"] == "fournisseur"
    assert [t["speaker"] for t in synthese()["turns"]] == ["agent", "caller"]


# --- Relais de la synthèse ---------------------------------------------------------------------


def test_relais_synthese(api: ApiSimulee, ecran: TestClient) -> None:
    attendu = synthese("SC-04")
    api.repondre = lambda r: httpx.Response(200, json=attendu)
    reponse = ecran.post("/demonstration/synthese", json={"scenario_id": "SC-04"})
    assert reponse.status_code == 200 and reponse.json() == attendu
    (demande,) = api.demandes
    assert demande.method == "POST" and demande.url.path == "/v1/demo/voice/synthesis"
    assert json.loads(demande.content) == {"scenario_id": "SC-04"}


@pytest.mark.parametrize(
    ("statut", "code"),
    [(404, "scenario_not_found"), (429, "rate_limited"), (503, "voice_unavailable")],
)
def test_relais_synthese_rend_l_erreur_de_l_api(
    api: ApiSimulee, ecran: TestClient, statut: int, code: str
) -> None:
    corps = {"code": code, "message": "Message de l'API.", "request_id": "r-1"}
    entetes = {"Retry-After": "30"} if statut == 429 else {}
    api.repondre = lambda r: httpx.Response(statut, json=corps, headers=entetes)
    reponse = ecran.post("/demonstration/synthese", json={"scenario_id": "SC-Q4"})
    assert reponse.status_code == statut and reponse.json() == corps
    if statut == 429:
        assert reponse.headers["Retry-After"] == "30"


def test_synthese_invalide_refusee_sans_appeler_l_api(api: ApiSimulee, ecran: TestClient) -> None:
    assert ecran.post("/demonstration/synthese", json={"scenario_id": "X" * 41}).status_code == 422
    assert ecran.post("/demonstration/synthese", json={}).status_code == 422
    assert api.demandes == []


# --- Relais de l'appel -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("statut", "corps"),
    [
        pytest.param(200, None, id="dossier"),
        pytest.param(404, {"code": "scenario_not_found", "message": "Scénario inconnu."}, id="404"),
        pytest.param(503, {"code": "voice_unavailable", "message": "Voix indisponible."}, id="503"),
    ],
)
def test_relais_appel_corps_brut_type_et_scenario(
    api: ApiSimulee, ecran: TestClient, statut: int, corps: dict[str, Any] | None
) -> None:
    rendu = corps or reponse_dossier()
    api.repondre = lambda r: httpx.Response(statut, json=rendu)
    audio = b"".join(EXTRAITS) + bytes(range(256)) * 40
    reponse = _appel(ecran, audio, sc="SC-10")
    assert reponse.status_code == statut and reponse.json() == rendu
    (demande,) = api.demandes
    assert demande.method == "POST" and demande.url.path == "/v1/demo/voice/call"
    assert demande.url.params["scenario_id"] == "SC-10"
    assert demande.headers["content-type"] == "audio/mpeg"
    assert demande.content == audio  # octet pour octet


def test_audio_a_la_limite_accepte(api: ApiSimulee, ecran: TestClient) -> None:
    api.repondre = lambda r: httpx.Response(200, json=reponse_message())
    assert _appel(ecran, b"\0" * AUDIO_OCTETS_MAX).status_code == 200
    assert len(api.demandes[0].content) == AUDIO_OCTETS_MAX


def test_audio_trop_grand_refuse_sans_appeler_l_api(api: ApiSimulee, ecran: TestClient) -> None:
    reponse = _appel(ecran, b"\0" * (AUDIO_OCTETS_MAX + 1))
    assert reponse.status_code == 413 and reponse.json()["code"] == "audio_too_large"
    # Sans longueur annoncée (envoi par morceaux) : la lecture s'arrête dès la limite dépassée.
    morceaux = iter([b"\0" * AUDIO_OCTETS_MAX, b"\0"])
    reponse = _appel(ecran, morceaux)
    assert reponse.status_code == 413 and reponse.json()["code"] == "audio_too_large"
    assert api.demandes == []


@pytest.mark.parametrize("type_", ["audio/wav", "application/octet-stream", "multipart/form-data"])
def test_autre_type_refuse_sans_appeler_l_api(
    api: ApiSimulee, ecran: TestClient, type_: str
) -> None:
    reponse = _appel(ecran, b"ID3", type_)
    assert reponse.status_code == 415 and reponse.json()["code"] == "unsupported_media_type"
    assert api.demandes == []


def test_scenario_invalide_refuse_sans_appeler_l_api(api: ApiSimulee, ecran: TestClient) -> None:
    assert _appel(ecran, b"ID3", sc="SC-Q4%3Cscript%3E").status_code == 422
    assert ecran.post("/demonstration/appel", content=b"ID3",
                      headers={"Content-Type": "audio/mpeg"}).status_code == 422  # fmt: skip
    assert api.demandes == []


def test_parcours_contre_l_api_reelle(client_console: TestClient) -> None:
    """La console contre la vraie API (faux fournisseurs, sans réseau) : synthèse, extraits mis
    bout à bout comme le fait l'écran, puis appel ; l'API entend les tours joués et met la
    transcription en tête des étapes."""
    voix = client_console.post("/demonstration/synthese", json={"scenario_id": "SC-04"})
    assert voix.status_code == 200
    tours = voix.json()["turns"]
    enregistrement = b"".join(base64.b64decode(t["audio_base64"]) for t in tours)
    reponse = _appel(client_console, enregistrement, sc="SC-04")
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    entendus = corps["transcription"]["turns"]
    assert [(t["speaker"], t["text"]) for t in entendus] == [
        (t["speaker"], t["text"]) for t in tours
    ]
    assert corps["transcription"]["audio_bytes"] == len(enregistrement)
    principales = [s["nom"] for s in corps["steps"] if s["niveau"] == 1]
    assert principales[0] == "transcription"
    assert corps["issue"] in ("dossier", "message", "trace")
    # Le modèle simulé n'a pas de dialogue : l'API refuse, la console rend son refus.
    refus = _appel(client_console, enregistrement, sc="P4-perimetre")
    assert refus.status_code == 404 and refus.json()["code"] == "scenario_not_found"


def test_api_injoignable_erreur_lisible(api: ApiSimulee, ecran: TestClient) -> None:
    def panne(requete: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refus de connexion", request=requete)

    api.repondre = panne
    for reponse in (
        _appel(ecran, b"ID3"),
        ecran.post("/demonstration/synthese", json={"scenario_id": "SC-Q4"}),
    ):
        assert reponse.status_code == 502
        assert reponse.json() == {"code": "api_unreachable", "message": "L'API est injoignable."}


# --- L'audio ne touche pas le disque (D-50) ----------------------------------------------------


def _pieger_fichiers(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Toute création de fichier temporaire lève et laisse une trace ; y compris celle de
    Starlette pour un `UploadFile`, qui importe `SpooledTemporaryFile` directement. La trace
    compte, car FastAPI transforme l'exception levée pendant la lecture d'un formulaire en 400."""
    tentatives: list[str] = []

    def piege(nom: str) -> Callable[..., None]:
        def lever(*args: object, **kwargs: object) -> None:
            tentatives.append(nom)
            raise AssertionError(f"fichier temporaire créé ({nom})")

        return lever

    for nom in ("SpooledTemporaryFile", "TemporaryFile", "NamedTemporaryFile", "mkstemp"):
        monkeypatch.setattr(tempfile, nom, piege(nom))
    monkeypatch.setattr(starlette.formparsers, "SpooledTemporaryFile", piege("UploadFile"))
    return tentatives


def test_piege_detecte_un_upload_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Témoin : le piège attrape bien la lecture d'un `UploadFile`, ce que le relais évite."""
    temoin = FastAPI()

    @temoin.post("/fichier")
    async def fichier(audio: UploadFile) -> dict[str, int]:
        return {"octets": len(await audio.read())}

    client = TestClient(temoin)
    assert client.post("/fichier", files={"audio": ("a.mp3", b"ID3")}).json() == {"octets": 3}
    tentatives = _pieger_fichiers(monkeypatch)
    assert client.post("/fichier", files={"audio": ("a.mp3", b"ID3")}).status_code == 400
    assert tentatives == ["UploadFile"]


def test_audio_relaye_sans_fichier_temporaire(
    api: ApiSimulee, ecran: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    api.repondre = lambda r: httpx.Response(200, json=reponse_dossier())
    audio = b"\xff\xfb" * (600 * 1024)  # 1,2 Mo : un `UploadFile` aurait débordé sur disque
    tentatives = _pieger_fichiers(monkeypatch)
    reponse = _appel(ecran, audio)
    assert reponse.status_code == 200
    assert api.demandes[0].content == audio
    assert tentatives == []
