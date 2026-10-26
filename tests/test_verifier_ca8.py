"""Script de preuve de CA-8 (sprint 5, étape 6) : fonctions pures et parcours, sans réseau.

L'API est simulée par `httpx.MockTransport`, d'après le contrat de la voix
(`src/muninn/voix/contrat.py`) seulement : ces tests ne dépendent pas du code des routes.
"""

import base64
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest

from muninn.voix.contrat import (
    ReponseSynthese,
    TourEntendu,
    TourSynthetise,
    TranscriptionAppel,
)

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "eval" / "production" / "verifier_ca8.py"


def charger() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verifier_ca8", SCRIPT)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V = charger()

DIALOGUE = [
    ("agent", "Bonjour, je suis une intelligence artificielle. Quel est le souci ?"),
    ("caller", "Une fuite sous l'évier, 12 rue des Lilas à Montreuil, 93100."),
    ("agent", "Votre numéro ?"),
    ("caller", "Le 06 99 00 00 01."),
]
EXTRAITS = [b"\xff\xfb\x90\x00tour1", b"\xff\xfb\x90\x00tour2", b"\xff\xfb3", b"\xff\xfb4"]


def synthese() -> dict[str, Any]:
    return ReponseSynthese(
        scenario_id="SC-01",
        voices={"agent": "fr-FR-DeniseNeural", "caller": "fr-FR-HenriNeural"},
        turns=[
            TourSynthetise(speaker=s, text=t, audio_base64=base64.b64encode(a).decode())  # type: ignore[arg-type]
            for (s, t), a in zip(DIALOGUE, EXTRAITS, strict=True)
        ],
    ).model_dump()


def reponse_appel(
    entendus: list[tuple[str, str]] | None = None,
    etapes: list[str] | None = None,
    issue: str = "dossier",
    conforme: bool = True,
    fidele: bool = True,
) -> dict[str, Any]:
    entendus = DIALOGUE if entendus is None else entendus
    noms = ["appel", "transcription", "qualification", "agent"] if etapes is None else etapes
    return {
        "request_id": "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0",
        "scenario_id": "SC-01",
        "issue": issue,
        "conformity": {"compliant": conforme, "gaps": [] if conforme else ["commune montreuil"]},
        "latency_ms": 6100,
        "steps": [
            {
                "nom": n,
                "debut_ms": 0,
                "duree_ms": 2100 if n == "transcription" else 1000,
                "statut": "ok",
                "niveau": 0 if n == "appel" else 1,
                "details": {"cout_micro_eur": 1500} if n == "agent" else {},
            }
            for n in noms
        ],
        "transcription": TranscriptionAppel(
            turns=[TourEntendu(speaker=s, text=t) for s, t in entendus],  # type: ignore[arg-type]
            audio_bytes=sum(len(a) for a in EXTRAITS),
            transcription_ms=2100,
            matches_scenario=fidele,
        ).model_dump(),
    }


class Horloge:
    """Horloge simulée : chaque lecture avance d'un pas ; `dormir` avance du temps demandé."""

    def __init__(self, pas: float = 0.0) -> None:
        self.t, self.pas = 0.0, pas
        self.sommeils: list[float] = []

    def __call__(self) -> float:
        self.t += self.pas
        return self.t

    def dormir(self, s: float) -> None:
        self.sommeils.append(s)
        self.t += s


def client(
    appel: dict[str, Any] | None = None,
    statut_synthese: int = 200,
    statut_appel: int = 200,
    vus: list[httpx.Request] | None = None,
) -> httpx.Client:
    def repondre(requete: httpx.Request) -> httpx.Response:
        if vus is not None:
            vus.append(requete)
        if requete.url.path == "/v1/demo/voice/synthesis":
            if statut_synthese != 200:
                return httpx.Response(statut_synthese, json={"code": "voice_unavailable"})
            return httpx.Response(200, json=synthese())
        if requete.url.path == "/v1/demo/voice/call":
            if statut_appel != 200:
                return httpx.Response(statut_appel, json={"code": "audio_too_large"})
            return httpx.Response(200, json=reponse_appel() if appel is None else appel)
        return httpx.Response(404)

    return httpx.Client(base_url="https://api.exemple", transport=httpx.MockTransport(repondre))


def test_mots_sans_accents_ni_ponctuation_nombres_regroupes() -> None:
    assert V.mots("L'évier fuit, à Montreuil !") == ["l", "evier", "fuit", "a", "montreuil"]
    assert V.mots("Le 06 99 00 00 01.") == V.mots("le 0699000001")
    assert V.mots("12 rue, 93100") == ["12", "rue", "93100"]


def test_taux_mots() -> None:
    assert V.taux_mots(["Une fuite sous l'évier"], ["une fuite sous l evier"]) == 1.0
    assert V.taux_mots(["un deux trois quatre"], ["un deux"]) == 0.5
    # Les répétitions comptent : un mot dit deux fois, entendu une fois, compte à moitié.
    assert V.taux_mots(["oui oui"], ["oui"]) == 0.5
    assert V.taux_mots([], ["oui"]) == 0.0


def test_assembler_met_les_extraits_bout_a_bout() -> None:
    assert V.assembler(synthese()["turns"]) == b"".join(EXTRAITS)


def test_cadence_un_appel_toutes_les_7_s() -> None:
    h = Horloge()
    cadence = V.Cadence(7.0, horloge=h, dormir=h.dormir)
    cadence.attendre()  # premier appel : aucune attente
    h.t += 2.5  # la requête a duré 2,5 s
    cadence.attendre()
    h.t += 9.0  # plus longue que l'espacement : aucune attente
    cadence.attendre()
    assert h.sommeils == [pytest.approx(4.5)]


def test_parcours_conforme_et_requetes_du_contrat() -> None:
    vus: list[httpx.Request] = []
    h = Horloge(pas=6.2)  # l'appel dure 6,2 s côté client
    cadence = V.Cadence(0.0, horloge=lambda: 0.0, dormir=lambda s: None)
    ligne = V.jouer(client(vus=vus), "SC-01", "dossier", cadence, horloge=h)
    assert ligne["conforme"], ligne["ecarts"]
    assert ligne["duree_appel_ms"] == 6200
    assert ligne["etape_en_tete"] == "transcription"
    assert ligne["transcription_ms"] == 2100
    assert ligne["taux_mots"] == 1.0
    assert (ligne["tours_dits"], ligne["tours_entendus"]) == (4, 4)
    assert ligne["cout_modele_micro_eur"] == 1500
    synth, appel = vus
    assert json.loads(synth.content) == {"scenario_id": "SC-01"}
    assert appel.url.params["scenario_id"] == "SC-01"
    assert appel.headers["content-type"] == "audio/mpeg"
    assert appel.content == b"".join(EXTRAITS)


def test_ligne_sans_contenu() -> None:
    cadence = V.Cadence(0.0, horloge=lambda: 0.0, dormir=lambda s: None)
    ligne = V.jouer(client(), "SC-01", "dossier", cadence, horloge=Horloge(pas=1.0))
    contenu = json.dumps(V.preuve([ligne], 1, "https://api.exemple", {}), ensure_ascii=False)
    for mot in ("Lilas", "évier", "0699000001", "06 99", base64.b64encode(EXTRAITS[0]).decode()):
        assert mot not in contenu


@pytest.mark.parametrize(
    ("appel", "duree_s", "attendu"),
    [
        (reponse_appel(), 45.5, "durée 45500 ms au-delà de 45000"),
        (reponse_appel(issue="message"), 5, "issue message au lieu de dossier"),
        (reponse_appel(conforme=False), 5, "non conforme à l'attendu du scénario"),
        (
            reponse_appel(etapes=["appel", "qualification", "transcription"]),
            5,
            "première étape qualification au lieu de transcription",
        ),
        (
            reponse_appel(
                entendus=[(("caller" if s == "agent" else "agent"), t) for s, t in DIALOGUE]
            ),
            5,
            "locuteurs entendus différents des locuteurs dits",
        ),
        (
            reponse_appel(entendus=[(s, "euh") for s, _ in DIALOGUE]),
            5,
            "mots retrouvés 0.00 sous 0.85",
        ),
        (
            reponse_appel(fidele=False),
            5,
            "transcription jugée non fidèle au scénario par l'API",
        ),
    ],
)
def test_ecarts(appel: dict[str, Any], duree_s: float, attendu: str) -> None:
    cadence = V.Cadence(0.0, horloge=lambda: 0.0, dormir=lambda s: None)
    ligne = V.jouer(client(appel=appel), "SC-01", "dossier", cadence, horloge=Horloge(duree_s))
    assert not ligne["conforme"]
    assert ligne["ecarts"] == [attendu]


def test_tour_perdu_est_un_ecart() -> None:
    cadence = V.Cadence(0.0, horloge=lambda: 0.0, dormir=lambda s: None)
    appel = reponse_appel(entendus=DIALOGUE[:3])
    ligne = V.jouer(client(appel=appel), "SC-01", "dossier", cadence, horloge=Horloge(1.0))
    assert ligne["tours_entendus"] == 3
    assert "locuteurs entendus différents des locuteurs dits" in ligne["ecarts"]


def test_voix_indisponible_et_audio_refuse() -> None:
    cadence = V.Cadence(0.0, horloge=lambda: 0.0, dormir=lambda s: None)
    ligne = V.jouer(client(statut_synthese=503), "SC-01", "dossier", cadence)
    assert ligne == {
        "scenario_id": "SC-01",
        "conforme": False,
        "ecarts": ["synthèse HTTP 503 voice_unavailable"],
    }
    ligne = V.jouer(client(statut_appel=413), "SC-01", "dossier", cadence, horloge=Horloge(1.0))
    assert ligne["ecarts"] == ["appel HTTP 413 audio_too_large"]
    assert not ligne["conforme"]


def test_bilan_et_cout() -> None:
    lignes: list[dict[str, Any]] = [
        {"conforme": True, "caracteres_synthetises": 1_000_000, "audio_s": 3600.0},
        {"conforme": False},
        {"conforme": True, "cout_modele_micro_eur": 5000},
        {"conforme": True},
    ]
    assert V.bilan(lignes, 3) == {"ca8": "2/3", "demonstration": "1/1"}
    assert V.cout_eur(lignes) == {
        "synthese": 13.2,
        "transcription": 0.32,
        "modele": 0.005,
        "total": 13.525,
    }


def test_estimation_avant_les_appels() -> None:
    # 1 141 caractères (SC-Q4, le plus long dialogue) : environ 0,015 € de synthèse.
    dialogue = "Agent : " + "a" * 541 + "\nAppelant : " + "b" * 600
    assert V.estimation_eur([dialogue]) == pytest.approx(
        1141 * 13.20 / 1e6 + 1141 / 15 * 0.32 / 3600
    )


def test_scenarios_du_plan_existent_et_ont_un_dialogue() -> None:
    from muninn.demo import charger_scenarios

    scenarios = charger_scenarios()
    for s in [V.SCENARIO_CA8, *V.DEMONSTRATION]:
        assert s in scenarios
        assert not scenarios[s].modele_simule
    assert scenarios["SC-Q1"].attendu["issue"] == "message"
