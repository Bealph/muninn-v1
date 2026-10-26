"""Voix simulée (sprint 5, étape 6 ; D-50) : découpage, faux fournisseur, fournisseur Azure.

Aucun appel réseau : le fournisseur Azure parle à un `httpx.MockTransport`.
"""

import json
import logging
from collections.abc import Callable

import httpx
import pytest

from muninn.core.config import Settings
from muninn.demo import PERIMETRE, charger_scenarios
from muninn.voix.azure import DEFINITION, FournisseurVoixAzure, ssml, tours_entendus
from muninn.voix.contrat import (
    FORMAT_SYNTHESE,
    VOIX_AGENT,
    VOIX_APPELANT,
    ErreurVoix,
    FournisseurVoix,
    Tour,
    decouper,
    recomposer,
)
from muninn.voix.faux import PREFIXE, FauxFournisseurVoix
from muninn.voix.fournisseur import construire_fournisseur_voix

SCENARIOS = sorted(i for i in charger_scenarios() if i != PERIMETRE)
RESSOURCE = "/subscriptions/0000/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/x"
SOUS_DOMAINE = "https://muninn-essai.cognitiveservices.azure.com/"
TEXTE_APPEL = "Martin habite 3 rue <des> Lilas & fils, l'artisan"


def reunis(tours: list[Tour]) -> list[Tour]:
    """Les tours tels que la transcription les entend : un locuteur à la suite, un seul tour."""
    vus: list[Tour] = []
    for t in tours:
        if vus and vus[-1].locuteur == t.locuteur:
            vus[-1] = Tour(t.locuteur, f"{vus[-1].texte} {t.texte}")
        else:
            vus.append(t)
    return vus


# --- Découpage et recomposition ----------------------------------------------------------------


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_decoupage_et_recomposition_du_jeu(scenario_id: str) -> None:
    transcription = charger_scenarios()[scenario_id].transcription
    tours = decouper(transcription)
    assert tours[0].locuteur == "agent"  # Muninn décroche et parle le premier
    lignes = [ligne.strip() for ligne in transcription.splitlines() if ligne.strip()]
    assert recomposer(tours).splitlines() == lignes
    assert decouper(recomposer(tours)) == tours


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_faux_aller_retour_sur_la_concatenation(scenario_id: str) -> None:
    """La console renvoie les extraits mis bout à bout : le faux les relit tous, dans l'ordre."""
    voix: FournisseurVoix = FauxFournisseurVoix()
    tours = decouper(charger_scenarios()[scenario_id].transcription)
    audio = b"".join(voix.synthetiser(t) for t in tours)
    assert voix.transcrire(audio) == reunis(tours)


def test_faux_reunit_un_meme_locuteur_et_refuse_l_illisible() -> None:
    voix = FauxFournisseurVoix()
    tours = [Tour("agent", "Bonjour."), Tour("caller", "Allô,"), Tour("caller", "une fuite.")]
    audio = b"".join(voix.synthetiser(t) for t in tours)
    assert voix.transcrire(audio) == [Tour("agent", "Bonjour."), Tour("caller", "Allô, une fuite.")]
    for illisible in (b"", b"ID3 du vrai mp3", PREFIXE + b"{pas du json", b"x" + audio):
        with pytest.raises(ErreurVoix):
            voix.transcrire(illisible)


# --- Choix du fournisseur ----------------------------------------------------------------------


def test_le_faux_est_le_defaut() -> None:
    faux = construire_fournisseur_voix(Settings(environment="local"))
    assert isinstance(faux, FauxFournisseurVoix)


@pytest.mark.parametrize("environnement", ["preproduction", "production"])
def test_le_faux_est_refuse_hors_du_local(environnement: str) -> None:
    # Une API déployée sans réglage de voix ne doit pas accepter du texte déguisé en audio.
    with pytest.raises(ValueError, match="VOIX_FOURNISSEUR"):
        construire_fournisseur_voix(Settings(environment=environnement))


@pytest.mark.parametrize(
    ("reglages", "manque"),
    [
        ({"speech_resource_id": RESSOURCE}, "SPEECH_ENDPOINT"),
        ({"speech_endpoint": SOUS_DOMAINE}, "SPEECH_RESOURCE_ID"),
    ],
)
def test_azure_exige_point_d_acces_et_ressource(reglages: dict[str, str], manque: str) -> None:
    with pytest.raises(ValueError, match=manque):
        construire_fournisseur_voix(Settings(voix_fournisseur="azure", **reglages))  # type: ignore[arg-type]


# --- Fournisseur Azure, sans réseau --------------------------------------------------------------


def azure(gerer: Callable[[httpx.Request], httpx.Response]) -> FournisseurVoixAzure:
    client = httpx.Client(transport=httpx.MockTransport(gerer))
    return FournisseurVoixAzure("westeurope", SOUS_DOMAINE, RESSOURCE, lambda: "jeton-1", client)


def test_synthese_url_entetes_et_ssml_echappe(caplog: pytest.LogCaptureFixture) -> None:
    vues: list[httpx.Request] = []

    def gerer(requete: httpx.Request) -> httpx.Response:
        vues.append(requete)
        return httpx.Response(200, content=b"ID3-mp3")

    with caplog.at_level(logging.DEBUG):
        audio = azure(gerer).synthetiser(Tour("caller", TEXTE_APPEL))
    assert audio == b"ID3-mp3"
    r = vues[0]
    assert str(r.url) == "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
    assert r.headers["Authorization"] == f"Bearer aad#{RESSOURCE}#jeton-1"
    assert r.headers["Content-Type"] == "application/ssml+xml"
    assert r.headers["X-Microsoft-OutputFormat"] == FORMAT_SYNTHESE
    assert r.headers["User-Agent"] == "muninn"
    corps = r.content.decode("utf-8")
    assert corps == ssml(Tour("caller", TEXTE_APPEL))
    assert f"<voice name='{VOIX_APPELANT}'>" in corps and "xml:lang='fr-FR'" in corps
    assert "rue &lt;des&gt; Lilas &amp; fils, l&apos;artisan" in corps
    assert "<des>" not in corps
    assert VOIX_AGENT in ssml(Tour("agent", "Bonjour."))
    assert TEXTE_APPEL not in caplog.text and "Lilas" not in caplog.text
    assert "voix.synthese statut=200 octets=7" in caplog.text


def test_transcription_requete_fusion_et_premier_locuteur(caplog: pytest.LogCaptureFixture) -> None:
    vues: list[httpx.Request] = []
    phrases = [
        # Désordonnées : le tri se fait sur le début de chaque phrase.
        {"speaker": 2, "text": "Bonjour, une fuite", "offsetMilliseconds": 3000},
        {"speaker": 1, "text": "Bonjour, ici Muninn.", "offsetMilliseconds": 0},
        {"speaker": 1, "text": "Que puis-je noter ?", "offsetMilliseconds": 1500},
        {"speaker": 2, "text": "sous l'évier.", "offsetMilliseconds": 4200},
        {"speaker": 1, "text": " ", "offsetMilliseconds": 5000},
        {"speaker": 1, "text": "C'est noté.", "offsetMilliseconds": 6000},
    ]

    def gerer(requete: httpx.Request) -> httpx.Response:
        vues.append(requete)
        return httpx.Response(200, json={"durationMilliseconds": 7000, "phrases": phrases})

    with caplog.at_level(logging.DEBUG):
        tours = azure(gerer).transcrire(b"ID3-audio-mp3")
    assert tours == [
        Tour("agent", "Bonjour, ici Muninn. Que puis-je noter ?"),
        Tour("caller", "Bonjour, une fuite sous l'évier."),
        Tour("agent", "C'est noté."),
    ]
    r = vues[0]
    assert str(r.url) == (
        "https://muninn-essai.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe"
        "?api-version=2025-10-15"
    )
    assert r.headers["Authorization"] == "Bearer jeton-1"  # jeton nu, sans « aad# »
    assert r.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    corps = r.content
    assert b'name="audio"; filename="appel.mp3"' in corps and b"ID3-audio-mp3" in corps
    assert b'name="definition"' in corps and DEFINITION.encode() in corps
    assert json.loads(DEFINITION) == {
        "locales": ["fr-FR"], "diarization": {"enabled": True, "maxSpeakers": 2}
    }  # fmt: skip
    for passage in ("Muninn", "fuite", "évier", "noté"):
        assert passage not in caplog.text
    assert "voix.transcription statut=200 octets=13" in caplog.text and "tours=3" in caplog.text


def test_le_premier_locuteur_entendu_est_l_agent_quel_que_soit_son_numero() -> None:
    tours = tours_entendus([
        {"speaker": 2, "text": "Bonjour.", "offsetMilliseconds": 0},
        {"speaker": 1, "text": "Allô.", "offsetMilliseconds": 900},
    ])  # fmt: skip
    assert [t.locuteur for t in tours] == ["agent", "caller"]
    assert tours_entendus([]) == []


@pytest.mark.parametrize(
    "reponse",
    [
        httpx.Response(401, json={"error": "nope"}),
        httpx.Response(404),
        httpx.Response(500, text="Martin habite rue des Lilas"),
        httpx.Response(200, text="pas du json"),
        httpx.Response(200, json={"autre": []}),
        httpx.Response(200, json={"phrases": "texte"}),
        httpx.Response(200, json={"phrases": [{"speaker": 1}]}),
    ],
)
def test_transcription_en_erreur(reponse: httpx.Response, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG), pytest.raises(ErreurVoix):
        azure(lambda _: reponse).transcrire(b"ID3")
    assert "Lilas" not in caplog.text and "voix.echec operation=transcription" in caplog.text


@pytest.mark.parametrize(
    "reponse", [httpx.Response(403), httpx.Response(429), httpx.Response(200, content=b"")]
)
def test_synthese_en_erreur(reponse: httpx.Response) -> None:
    with pytest.raises(ErreurVoix):
        azure(lambda _: reponse).synthetiser(Tour("agent", "Bonjour."))


@pytest.mark.parametrize("exception", [httpx.ConnectError("refus"), httpx.ReadTimeout("lent")])
def test_panne_reseau(exception: Exception, caplog: pytest.LogCaptureFixture) -> None:
    def gerer(requete: httpx.Request) -> httpx.Response:
        raise exception

    voix = azure(gerer)
    with caplog.at_level(logging.WARNING), pytest.raises(ErreurVoix):
        voix.synthetiser(Tour("agent", TEXTE_APPEL))
    with pytest.raises(ErreurVoix):
        voix.transcrire(b"ID3")
    assert "Lilas" not in caplog.text


def test_jeton_indisponible() -> None:
    def sans_jeton() -> str:
        raise RuntimeError("az login requis")

    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    voix = FournisseurVoixAzure("westeurope", SOUS_DOMAINE, RESSOURCE, sans_jeton, client)
    with pytest.raises(ErreurVoix):
        voix.synthetiser(Tour("agent", "Bonjour."))


def test_region_invalide_refusee() -> None:
    with pytest.raises(ValueError, match="SPEECH_REGION"):
        FournisseurVoixAzure("evil.com/x", SOUS_DOMAINE, RESSOURCE, lambda: "j")


def test_delais_bornes() -> None:
    delais: list[dict[str, float | None]] = []

    def gerer(requete: httpx.Request) -> httpx.Response:
        delais.append(requete.extensions["timeout"])
        return httpx.Response(200, content=b"ID3")

    voix = azure(gerer)
    voix.synthetiser(Tour("agent", "Bonjour."))
    with pytest.raises(ErreurVoix):  # la réponse n'est pas un JSON de transcription
        voix.transcrire(b"ID3")
    assert delais[0] == {"connect": 5.0, "read": 30.0, "write": 30.0, "pool": 30.0}
    assert delais[1] == {"connect": 5.0, "read": 30.0, "write": 30.0, "pool": 30.0}
