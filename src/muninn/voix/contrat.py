"""Contrat de la voix simulée (sprint 5, étape 6 ; D-50, D-74, D-88, V-12, CA-8).

Ce module est le contrat partagé entre l'API, la console et les tests : modèles des deux routes,
interface du fournisseur de voix, découpage d'un dialogue en tours, limites. Il ne fait aucun
appel réseau.

Parcours d'un appel joué (écran « Démonstration ») :
1. la console demande la synthèse d'un scénario : `POST /v1/demo/voice/synthesis` rend un extrait
   audio par tour de parole (Muninn par une voix, l'appelant par une autre) ;
2. la console joue la sonnerie, puis les extraits, bulle par bulle ;
3. à la fin de l'appel joué, la console renvoie l'enregistrement de l'appel (les extraits mis bout
   à bout) : `POST /v1/demo/voice/call?scenario_id=…`, audio brut en corps de requête ;
4. l'API transcrit l'audio (transcription rapide, séparation des locuteurs), recompose la
   transcription en tours « Agent : … / Appelant : … », puis la traite comme `POST /v1/demo/runs`
   (qualification, extraction, contrôles, enregistrement) ; elle rend le résultat, ses étapes avec
   leurs durées (la transcription en tête) et la transcription obtenue.
CA-8 (avenant D-74) se mesure de la fin de l'appel joué (étape 3) à la réponse : 45 s au plus.

Règles :
- l'audio n'est jamais écrit sur disque (D-50, TC-10) : corps de requête lu en mémoire, jamais
  `UploadFile` (qui déborde sur un fichier temporaire au-delà de 1 Mo) ; aucun journal ne porte
  d'audio ni de texte de l'appel (OB-1) ;
- seuls les scénarios du jeu synthétique sont joués : aucune donnée réelle ;
- authentification Entra sans clé (identité managée), comme le modèle de langage.
"""

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field

# Voix neuronales vérifiées sur la ressource Foundry (West Europe) le 26 octobre 2026.
VOIX_AGENT = "fr-FR-DeniseNeural"
VOIX_APPELANT = "fr-FR-HenriNeural"
# Format des extraits : MP3, lu par tout navigateur et accepté par la transcription rapide.
FORMAT_SYNTHESE = "audio-24khz-48kbitrate-mono-mp3"
TYPE_AUDIO: Literal["audio/mpeg"] = "audio/mpeg"

TOURS_MAX = 40  # le plus long dialogue du jeu en compte 17
CARACTERES_MAX_PAR_TOUR = 600
# Environ 4 min 20 s à 48 kbit/s, pour des appels de 1 à 2 min (0,4 à 0,7 Mo). La transcription
# est facturée à la durée : un débit plus bas loge plus de minutes dans la même taille (26 min à
# 8 kbit/s) ; ce reste est borné par la limite de débit des appels (revue de sécurité, étape 6).
AUDIO_OCTETS_MAX = 1536 * 1024
# Lecture du corps bornée dans le temps et en nombre d'appels simultanés : un envoi au
# goutte-à-goutte ne retient pas indéfiniment la mémoire de l'API.
LECTURE_AUDIO_S = 20.0
APPELS_VOIX_SIMULTANES = 4

Locuteur = Literal["agent", "caller"]


@dataclass(frozen=True)
class Tour:
    """Un tour de parole : qui parle, et ce qu'il dit."""

    locuteur: Locuteur
    texte: str


class ErreurVoix(Exception):
    """Le service de voix est injoignable, a refusé, ou a rendu une réponse inexploitable."""


class FournisseurVoix(Protocol):
    """Synthèse et transcription. Implémentations : Azure AI Speech, et un faux pour les tests."""

    def synthetiser(self, tour: Tour) -> bytes:
        """L'audio MP3 d'un tour, avec la voix de son locuteur. Lève `ErreurVoix`."""
        ...

    def transcrire(self, audio: bytes) -> list[Tour]:
        """Les tours entendus dans l'audio MP3, dans l'ordre ; le premier locuteur entendu est
        Muninn (« agent ») : c'est lui qui décroche et parle le premier. Lève `ErreurVoix`."""
        ...


_LIGNE = re.compile(r"^(Agent|Appelant)\s*:\s*(.+)$")
_ETIQUETTES: dict[str, Locuteur] = {"Agent": "agent", "Appelant": "caller"}
_NOMS: dict[Locuteur, str] = {"agent": "Agent", "caller": "Appelant"}


def decouper(transcription: str) -> list[Tour]:
    """Les tours d'un dialogue écrit « Agent : … » / « Appelant : … », une ligne par tour.

    Une ligne qui ne commence pas par une étiquette prolonge le tour précédent. Lève `ValueError`
    si le dialogue n'a aucun tour, dépasse `TOURS_MAX`, ou si un tour dépasse
    `CARACTERES_MAX_PAR_TOUR`.
    """
    tours: list[Tour] = []
    for brute in transcription.splitlines():
        ligne = brute.strip()
        if not ligne:
            continue
        m = _LIGNE.match(ligne)
        if m:
            tours.append(Tour(_ETIQUETTES[m.group(1)], m.group(2).strip()))
        elif tours:
            precedent = tours[-1]
            tours[-1] = Tour(precedent.locuteur, f"{precedent.texte} {ligne}")
    if not tours or len(tours) > TOURS_MAX:
        raise ValueError("dialogue vide ou trop long")
    if any(len(t.texte) > CARACTERES_MAX_PAR_TOUR for t in tours):
        raise ValueError("tour trop long")
    return tours


def une_ligne(texte: str) -> str:
    """Le texte d'un tour sur une seule ligne : un saut de ligne fabriquerait un faux tour."""
    return " ".join(texte.split())


def recomposer(tours: list[Tour]) -> str:
    """La transcription au format du jeu de scénarios, pour la qualification et l'extraction.

    Chaque tour est ramené à une ligne : un texte entendu « …\nAgent : … » ne crée pas de tour
    attribué à Muninn (revue de sécurité de l'étape 6).
    """
    return "\n".join(f"{_NOMS[t.locuteur]} : {une_ligne(t.texte)}" for t in tours)


# --- Modèles des routes (JSON) ---


class TourSynthetise(BaseModel):
    """Un tour de la synthèse : le texte affiché dans la bulle et son audio."""

    speaker: Locuteur
    text: str
    audio_base64: str = Field(description="MP3, voix du locuteur")


class ReponseSynthese(BaseModel):
    """`POST /v1/demo/voice/synthesis` : les tours du scénario, prêts à être joués."""

    scenario_id: str
    voices: dict[Locuteur, str]
    audio_type: Literal["audio/mpeg"] = TYPE_AUDIO
    turns: list[TourSynthetise]


class DemandeSynthese(BaseModel):
    scenario_id: str = Field(max_length=40)


class TourEntendu(BaseModel):
    """Un tour tel que la transcription l'a entendu."""

    speaker: Locuteur
    text: str


class TranscriptionAppel(BaseModel):
    """Ce que Muninn a entendu : rendu avec le résultat de `POST /v1/demo/voice/call`."""

    turns: list[TourEntendu]
    audio_bytes: int
    transcription_ms: int
    # Vrai si l'entendu reprend le dialogue du scénario, et rien d'autre (`voix.fidelite`) :
    # sinon le contenu n'est ni stocké ni corrigeable, comme un texte libre (P-03).
    matches_scenario: bool
