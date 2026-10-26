"""Fournisseur de voix Azure AI Speech, par HTTP (httpx), sans le SDK Speech (D-50).

Deux appels, vérifiés en réel sur la ressource du projet le 26 octobre 2026 :
- synthèse : point d'accès régional `https://<région>.tts.speech.microsoft.com/cognitiveservices/v1`
  (l'exemple de Microsoft sur le sous-domaine de la ressource répond 404), jeton
  « aad#<identifiant ARM de la ressource>#<jeton Entra> », corps SSML, une voix par tour ;
- transcription rapide : `<sous-domaine>/speechtotext/transcriptions:transcribe`, jeton Entra nu,
  formulaire multipart (`audio`, `definition`), séparation des locuteurs (deux au plus).

L'audio reste en mémoire. Les journaux ne portent que des codes et des nombres (statut HTTP,
octets, durée, nombre de tours) : jamais de texte, jamais d'audio (OB-1).
"""

import json
import logging
import re
import time
from collections.abc import Callable
from typing import Any
from xml.sax.saxutils import escape

import httpx

from muninn.llm.fournisseur import PORTEE_COGNITIVE_SERVICES
from muninn.voix.contrat import (
    FORMAT_SYNTHESE,
    TYPE_AUDIO,
    VOIX_AGENT,
    VOIX_APPELANT,
    ErreurVoix,
    Locuteur,
    Tour,
    une_ligne,
)

journal = logging.getLogger(__name__)

VERSION_TRANSCRIPTION = "2025-10-15"
DELAI_CONNEXION_S = 5.0
DELAI_SYNTHESE_S = 30.0
DELAI_TRANSCRIPTION_S = 30.0  # sous le budget de CA-8 (45 s, D-74), modèle compris
LOCALE = "fr-FR"
VOIX: dict[Locuteur, str] = {"agent": VOIX_AGENT, "caller": VOIX_APPELANT}
# Définition de la transcription rapide : français, deux locuteurs séparés.
DEFINITION = json.dumps(
    {"locales": [LOCALE], "diarization": {"enabled": True, "maxSpeakers": 2}},
    separators=(",", ":"),
)
_REGION = re.compile(r"[a-z0-9]{2,40}")


def ssml(tour: Tour) -> str:
    """Le corps SSML d'un tour : la voix de son locuteur, le texte échappé pour XML."""
    texte = escape(tour.texte, {"'": "&apos;", '"': "&quot;"})
    return (
        f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{LOCALE}'>"
        f"<voice name='{VOIX[tour.locuteur]}'>{texte}</voice></speak>"
    )


def tours_entendus(phrases: list[dict[str, Any]]) -> list[Tour]:
    """Les tours d'une transcription séparée par locuteur.

    Les phrases sont prises dans l'ordre de leur début ; le premier locuteur entendu est Muninn
    (« agent »), tout autre est l'appelant ; les phrases consécutives d'un même locuteur forment
    un seul tour. Lève `KeyError`, `TypeError` ou `ValueError` sur une phrase mal formée.
    """
    tours: list[Tour] = []
    premier: object = None
    for phrase in sorted(phrases, key=lambda p: int(p.get("offsetMilliseconds") or 0)):
        texte = une_ligne(str(phrase["text"]))
        if not texte:
            continue
        locuteur_brut = phrase.get("speaker")
        if not tours:  # la première phrase entendue fixe le locuteur de Muninn
            premier = locuteur_brut
        locuteur: Locuteur = "agent" if locuteur_brut == premier else "caller"
        if tours and tours[-1].locuteur == locuteur:
            tours[-1] = Tour(locuteur, f"{tours[-1].texte} {texte}")
        else:
            tours.append(Tour(locuteur, texte))
    return tours


class FournisseurVoixAzure:
    """Synthèse et transcription par Azure AI Speech, authentification Entra sans clé.

    `jeton` rend un jeton Entra de portée Cognitive Services ; il est appelé à chaque requête
    (le fournisseur de jetons d'`azure.identity` le garde en cache et le renouvelle).
    """

    nom = "azure"

    def __init__(
        self,
        region: str,
        endpoint: str,
        resource_id: str,
        jeton: Callable[[], str],
        client: httpx.Client | None = None,
    ) -> None:
        if not _REGION.fullmatch(region):
            raise ValueError("SPEECH_REGION doit être un nom de région Azure, par ex. westeurope.")
        self._url_synthese = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self._url_transcription = (
            f"{endpoint.rstrip('/')}/speechtotext/transcriptions:transcribe"
            f"?api-version={VERSION_TRANSCRIPTION}"
        )
        self._resource_id = resource_id
        self._jeton = jeton
        self._client = client or httpx.Client()

    def _jeton_entra(self, operation: str) -> str:
        try:
            return self._jeton()
        except Exception as exc:  # noqa: BLE001 : toute panne d'authentification rend la voix indisponible
            journal.warning("voix.echec operation=%s cause=%s", operation, type(exc).__name__)
            raise ErreurVoix("Authentification au service de voix impossible.") from exc

    def _envoyer(
        self, operation: str, delai_s: float, **requete: Any
    ) -> tuple[httpx.Response, int]:
        """Envoie la requête ; rend la réponse 200 et sa durée. Lève `ErreurVoix` sinon."""
        debut = time.perf_counter()
        try:
            reponse = self._client.post(
                timeout=httpx.Timeout(delai_s, connect=DELAI_CONNEXION_S), **requete
            )
        except httpx.TimeoutException as exc:
            journal.warning("voix.echec operation=%s cause=delai_depasse", operation)
            raise ErreurVoix("Le service de voix n'a pas répondu dans le délai.") from exc
        except httpx.HTTPError as exc:
            journal.warning("voix.echec operation=%s cause=%s", operation, type(exc).__name__)
            raise ErreurVoix("Le service de voix est injoignable.") from exc
        duree_ms = round((time.perf_counter() - debut) * 1000)
        if reponse.status_code != 200:
            journal.warning(
                "voix.echec operation=%s statut=%s duree_ms=%s",
                operation, reponse.status_code, duree_ms,
            )  # fmt: skip
            raise ErreurVoix(f"Le service de voix a répondu {reponse.status_code}.")
        return reponse, duree_ms

    def synthetiser(self, tour: Tour) -> bytes:
        """L'audio MP3 d'un tour, avec la voix de son locuteur."""
        jeton = self._jeton_entra("synthese")
        reponse, duree_ms = self._envoyer(
            "synthese",
            DELAI_SYNTHESE_S,
            url=self._url_synthese,
            content=ssml(tour).encode("utf-8"),
            headers={
                "Authorization": f"Bearer aad#{self._resource_id}#{jeton}",
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": FORMAT_SYNTHESE,
                "User-Agent": "muninn",
            },
        )
        audio = reponse.content
        if not audio:
            journal.warning("voix.echec operation=synthese cause=reponse_vide")
            raise ErreurVoix("Le service de voix a rendu un audio vide.")
        journal.info(
            "voix.synthese statut=%s octets=%s duree_ms=%s", reponse.status_code, len(audio),
            duree_ms,
        )  # fmt: skip
        return audio

    def transcrire(self, audio: bytes) -> list[Tour]:
        """Les tours entendus dans l'audio MP3, dans l'ordre ; le premier locuteur est l'agent."""
        jeton = self._jeton_entra("transcription")
        reponse, duree_ms = self._envoyer(
            "transcription",
            DELAI_TRANSCRIPTION_S,
            url=self._url_transcription,
            headers={"Authorization": f"Bearer {jeton}", "User-Agent": "muninn"},
            files={"audio": ("appel.mp3", audio, TYPE_AUDIO)},
            data={"definition": DEFINITION},
        )
        try:
            phrases = reponse.json()["phrases"]
            if not isinstance(phrases, list):
                raise TypeError("phrases")
            tours = tours_entendus(phrases)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            journal.warning("voix.echec operation=transcription cause=reponse_illisible")
            raise ErreurVoix("La transcription est illisible.") from exc
        journal.info(
            "voix.transcription statut=%s octets=%s duree_ms=%s phrases=%s tours=%s",
            reponse.status_code, len(audio), duree_ms, len(phrases), len(tours),
        )  # fmt: skip
        return tours


def jeton_entra() -> Callable[[], str]:
    """Jeton Entra sans secret : identité managée en Azure, az login en local."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    return get_bearer_token_provider(
        DefaultAzureCredential(exclude_interactive_browser_credential=True),
        PORTEE_COGNITIVE_SERVICES,
    )
