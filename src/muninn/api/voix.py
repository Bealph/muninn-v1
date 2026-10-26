"""Routes de la voix simulée (sprint 5, étape 6 ; D-50, D-74, D-88, V-12, CA-8).

- `POST /v1/demo/voice/synthesis` : un extrait MP3 par tour d'un scénario du jeu synthétique ;
- `POST /v1/demo/voice/call?scenario_id=…` : l'enregistrement de l'appel joué (corps brut
  `audio/mpeg`), transcrit puis traité exactement comme `POST /v1/demo/runs` en mode scénario.

Contrat : `docs/v1/sprints/sprint-5/contrat-voix.md` et `muninn.voix.contrat`.
L'audio n'est jamais écrit sur disque (TC-10) : le corps est lu par morceaux, en mémoire, et borné
à `AUDIO_OCTETS_MAX` ; jamais `UploadFile` ni formulaire. Aucun texte ni audio dans les journaux
ni dans les traces : la transcription n'y laisse que des nombres (octets, tours, durée).
"""

import asyncio
import base64
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.concurrency import run_in_threadpool

from muninn.api.agent import ERREURS, ReponseDemo, get_referentiels, reserver, traiter_demo
from muninn.api.dependances import get_fournisseur, get_fournisseur_voix, get_limiteur
from muninn.api.erreurs import DetailErreur, Erreur, ErreurAPI
from muninn.api.limites import LimiteurDebit
from muninn.demo import PERIMETRE, Scenario, charger_scenarios
from muninn.extraction.outils import Referentiels
from muninn.llm.fournisseur import FournisseurLLM
from muninn.telemetrie import etape
from muninn.voix.contrat import (
    APPELS_VOIX_SIMULTANES,
    AUDIO_OCTETS_MAX,
    LECTURE_AUDIO_S,
    TYPE_AUDIO,
    VOIX_AGENT,
    VOIX_APPELANT,
    DemandeSynthese,
    ErreurVoix,
    FournisseurVoix,
    ReponseSynthese,
    Tour,
    TourEntendu,
    TourSynthetise,
    TranscriptionAppel,
    decouper,
    recomposer,
)
from muninn.voix.fidelite import conforme_au_dialogue

journal = logging.getLogger(__name__)
routeur = APIRouter(tags=["voix"])

# Extraits synthétisés en parallèle : le dialogue le plus long du jeu compte 17 tours.
SYNTHESES_SIMULTANEES = 4
# Synthèses gardées en mémoire par scénario, jamais sur disque : la sortie ne dépend que du
# dialogue, synthétique, et la rejouer coûterait une réservation et jusqu'à 17 synthèses payantes
# (revue de sécurité de l'étape 6). Quelques Mo pour tout le jeu ; vidée au redémarrage.
syntheses: dict[str, ReponseSynthese] = {}
# Appels joués traités en même temps, lecture du corps comprise ; au-delà, refus immédiat.
appels_en_cours = asyncio.Semaphore(APPELS_VOIX_SIMULTANES)


@dataclass
class Entendu:
    """Ce que la transcription a rendu, gardé pour la réponse ; jamais journalisé."""

    tours: list[Tour] = field(default_factory=list)
    ms: int = 0
    conforme: bool = False


class ReponseAppel(ReponseDemo):
    """`POST /v1/demo/voice/call` : le résultat de `/v1/demo/runs`, et ce que Muninn a entendu."""

    transcription: TranscriptionAppel


def scenario_parle(scenario_id: str, champ: str) -> Scenario:
    """Le scénario du jeu synthétique, s'il a un dialogue ; le modèle simulé n'en a pas (404)."""
    scenario = charger_scenarios().get(scenario_id)
    if scenario is None or scenario.id == PERIMETRE:
        raise ErreurAPI(404, "scenario_not_found", [DetailErreur(field=champ, issue="not_allowed")])
    return scenario


@routeur.post(
    "/v1/demo/voice/synthesis",
    response_model=ReponseSynthese,
    responses={
        **ERREURS,  # type: ignore[dict-item]
        404: {"model": Erreur, "description": "Scénario inconnu, ou sans dialogue"},
        503: {"model": Erreur, "description": "Service de voix indisponible"},
    },
)
def synthetiser(
    corps: DemandeSynthese,
    voix: Annotated[FournisseurVoix, Depends(get_fournisseur_voix)],
    limiteur: Annotated[LimiteurDebit, Depends(get_limiteur)],
) -> ReponseSynthese:
    """Un extrait MP3 par tour du scénario, Muninn et l'appelant chacun avec sa voix."""
    scenario = scenario_parle(corps.scenario_id, "body.scenario_id")
    if scenario.id in syntheses:  # déjà synthétisé : rien n'est consommé
        return syntheses[scenario.id]
    try:
        tours = decouper(scenario.transcription)
    except ValueError as erreur:
        detail = DetailErreur(field="body.scenario_id", issue="not_allowed")
        raise ErreurAPI(404, "scenario_not_found", [detail]) from erreur
    # La limite de débit après les contrôles : une demande refusée ne consomme rien.
    reserver(limiteur)
    debut = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=SYNTHESES_SIMULTANEES) as groupe:
            audios = list(groupe.map(voix.synthetiser, tours))
    except ErreurVoix as erreur:
        raise ErreurAPI(503, "voice_unavailable") from erreur
    journal.info(
        "voix.synthese_scenario tours=%s octets=%s duree_ms=%s", len(tours),
        sum(len(a) for a in audios), round((time.perf_counter() - debut) * 1000),
    )  # fmt: skip
    reponse = ReponseSynthese(
        scenario_id=scenario.id,
        voices={"agent": VOIX_AGENT, "caller": VOIX_APPELANT},
        turns=[
            TourSynthetise(
                speaker=t.locuteur, text=t.texte, audio_base64=base64.b64encode(a).decode("ascii")
            )
            for t, a in zip(tours, audios, strict=True)
        ],
    )
    syntheses[scenario.id] = reponse
    return reponse


async def lire_audio(request: Request) -> bytes:
    """Le corps de la requête, en mémoire, borné à `AUDIO_OCTETS_MAX` ; jamais sur disque.

    Un `Content-Length` trop grand est refusé avant toute lecture ; sans lui (envoi par morceaux),
    la lecture s'arrête dès que la borne est franchie. Un corps qui n'est pas reçu en
    `LECTURE_AUDIO_S` secondes est refusé (408) : un envoi au goutte-à-goutte ne retient pas la
    mémoire de l'API.
    """
    longueur = request.headers.get("content-length")
    if longueur is not None:
        try:
            annoncee = int(longueur)
        except ValueError:
            annoncee = -1
        if annoncee < 0:
            detail = DetailErreur(field="header.content-length", issue="bad_format")
            raise ErreurAPI(422, "validation_failed", [detail])
        if annoncee > AUDIO_OCTETS_MAX:
            raise ErreurAPI(413, "audio_too_large")
    morceaux: list[bytes] = []
    recus = 0
    try:
        async with asyncio.timeout(LECTURE_AUDIO_S):
            async for morceau in request.stream():
                morceaux.append(morceau)
                recus += len(morceau)
                if recus > AUDIO_OCTETS_MAX:
                    raise ErreurAPI(413, "audio_too_large")
    except TimeoutError as erreur:
        raise ErreurAPI(408, "request_timeout") from erreur
    if not recus:
        raise ErreurAPI(422, "validation_failed", [DetailErreur(field="body", issue="required")])
    return b"".join(morceaux)


@routeur.post(
    "/v1/demo/voice/call",
    response_model=ReponseAppel,
    responses={
        **ERREURS,  # type: ignore[dict-item]
        404: {"model": Erreur, "description": "Scénario inconnu, ou sans dialogue"},
        408: {"model": Erreur, "description": "Enregistrement non reçu à temps"},
        413: {"model": Erreur, "description": "Enregistrement trop volumineux"},
        415: {"model": Erreur, "description": "Type de contenu autre que audio/mpeg"},
        503: {"model": Erreur, "description": "Service de voix indisponible"},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {TYPE_AUDIO: {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def traiter_appel_joue(
    request: Request,
    scenario_id: Annotated[str, Query(max_length=40)],
    voix: Annotated[FournisseurVoix, Depends(get_fournisseur_voix)],
    fournisseur: Annotated[FournisseurLLM, Depends(get_fournisseur)],
    referentiels: Annotated[Referentiels, Depends(get_referentiels)],
    limiteur: Annotated[LimiteurDebit, Depends(get_limiteur)],
) -> ReponseAppel:
    """L'appel joué : transcription, puis le traitement de `/v1/demo/runs` en mode scénario."""
    debut = time.perf_counter()
    type_contenu = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if type_contenu != TYPE_AUDIO:
        raise ErreurAPI(415, "unsupported_media_type")
    scenario = scenario_parle(scenario_id, "query.scenario_id")
    if appels_en_cours.locked():  # jamais d'attente : la file serait elle-même une charge
        raise ErreurAPI(429, "rate_limited", retry_after_s=5)
    async with appels_en_cours:
        return await jouer_appel(
            request, scenario, debut, voix, fournisseur, referentiels, limiteur
        )


async def jouer_appel(
    request: Request,
    scenario: Scenario,
    debut: float,
    voix: FournisseurVoix,
    fournisseur: FournisseurLLM,
    referentiels: Referentiels,
    limiteur: LimiteurDebit,
) -> ReponseAppel:
    """Lecture, réservation, transcription et traitement d'un appel admis."""
    audio = await lire_audio(request)
    reserver(limiteur)
    entendu = Entendu()

    def transcrire() -> str:
        with etape("transcription", audio_octets=len(audio)) as c:
            debut_transcription = time.perf_counter()
            entendu.tours = voix.transcrire(audio)
            entendu.ms = round((time.perf_counter() - debut_transcription) * 1000)
            c["tours"] = len(entendu.tours)
        return recomposer(entendu.tours)

    def fidele() -> bool:
        entendu.conforme = conforme_au_dialogue(entendu.tours, decouper(scenario.transcription))
        return entendu.conforme

    def traiter() -> ReponseDemo:
        return traiter_demo(
            request, scenario, transcrire, scenario.metier, scenario.numero_presente,
            fournisseur, referentiels, debut, route="voix", champ_texte="body",
            synthetique=fidele,
        )  # fmt: skip

    try:
        # Transcription et modèle sont des appels bloquants : hors de la boucle d'événements.
        reponse = await run_in_threadpool(traiter)
    except ErreurVoix as erreur:
        raise ErreurAPI(503, "voice_unavailable") from erreur
    return ReponseAppel(
        **dict(reponse),
        transcription=TranscriptionAppel(
            turns=[TourEntendu(speaker=t.locuteur, text=t.texte) for t in entendu.tours],
            audio_bytes=len(audio),
            transcription_ms=entendu.ms,
            matches_scenario=entendu.conforme,
        ),
    )
