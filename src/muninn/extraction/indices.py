"""Indices de département dits en clair, reconnus par le serveur (D-78).

Le serveur départage des communes homonymes seulement si l'appelant cite explicitement un
département : par son nom (« en Seine-et-Marne », « dans le Var »), par son numéro (« dans le 77 »)
ou par son surnom chiffré (« le 9-3 »). Les indices libres (quartier, commune voisine) restent
l'affaire de l'agent. La liste des départements vient de l'API Géo (`departements.json`).
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from muninn.extraction.entree import normaliser

FICHIER = Path(__file__).parent / "departements.json"
AMORCES = r"(?:en|dans le|dans la|dans les|dans l|du|de la|de l|des)"


@lru_cache
def departements() -> dict[str, str]:
    """Nom normalisé vers code ; « 2a » et « 2b » en minuscules comme le texte normalisé."""
    donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
    return {normaliser(d["nom"]): d["code"] for d in donnees["departements"]}


def departements_cites(transcription_normalisee: str) -> set[str]:
    """Codes des départements cités explicitement dans la transcription (texte normalisé)."""
    texte = f" {transcription_normalisee} "
    codes = {
        code
        for nom, code in departements().items()
        if re.search(rf"\b{AMORCES} {re.escape(nom)}\b", texte)
    }
    codes_connus = {c.lower() for c in departements().values()}
    for nombre in re.findall(r"\b(?:dans le|le|du|en) (\d{2,3}|2a|2b)\b", texte):
        if nombre in codes_connus:
            codes.add(nombre.upper())
    for dizaine, unite in re.findall(r"\b(?:dans le|le|du) (\d) (\d)\b", texte):  # « le 9-3 »
        if dizaine + unite in codes_connus:
            codes.add(dizaine + unite)
    return codes
