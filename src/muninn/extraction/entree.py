"""Garde-fous d'entrée par règles (D-63, première couche), avant l'agent.

- **Refus motivé** d'une entrée inexploitable : vide, sans contenu (moins de 10 lettres), ou trop
  longue (8 000 caractères au plus, contrat d'API, `POST /v1/extractions/text`). Le refus a un texte
  fixe, jamais un fragment de l'entrée.
- **Nettoyage** des caractères de contrôle et invisibles (largeur nulle, sens d'écriture), qui
  servent à cacher une consigne ; les sauts de ligne et tabulations sont gardés.
- **Détection** des motifs d'injection connus (liste fermée et versionnée,
  `paquet_fichiers/motifs_injection.json`) : une détection marque le dossier « à vérifier » et est
  journalisée par l'identifiant du motif ; elle ne bloque jamais, pour ne pas refuser un client
  légitime. La transcription reste traitée comme une donnée, dans un bloc délimité (M-04).

Les deux autres couches : la modération par le filtre de contenu d'Azure, et le hors-périmètre par
la qualification des appels (étape 6).
"""

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from muninn.extraction.paquet import DOSSIER_PAQUET

journal = logging.getLogger(__name__)

LONGUEUR_MAX = 8000
LETTRES_MIN = 10
REFUS = {
    "entree_vide": "Aucun contenu exploitable : la demande ne peut pas être traitée.",
    "entree_trop_longue": "La transcription dépasse la longueur admise.",
}


@dataclass(frozen=True)
class Motif:
    id: str
    regex: re.Pattern[str]


@dataclass
class ControleEntree:
    """Résultat du contrôle : le texte nettoyé, un refus éventuel, les motifs détectés."""

    texte: str
    refus: str | None = None
    motifs: list[str] = field(default_factory=list)
    caracteres_retires: int = 0

    @property
    def message_refus(self) -> str | None:
        return REFUS.get(self.refus) if self.refus else None


@lru_cache
def charger_motifs(
    chemin: Path = DOSSIER_PAQUET / "motifs_injection.json",
) -> tuple[str, tuple[Motif, ...]]:
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    return str(donnees["version"]), tuple(
        Motif(id=str(m["id"]), regex=re.compile(str(m["regex"]))) for m in donnees["motifs"]
    )


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, ponctuation en espaces (même règle que l'évaluateur)."""
    texte = texte.lower().replace("œ", "oe").replace("æ", "ae")
    texte = "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texte).strip()


def nettoyer(texte: str) -> tuple[str, int]:
    """Retire les caractères de contrôle et de format (catégories Cc et Cf), sauf saut de ligne et
    tabulation ; rend le texte et le nombre de caractères retirés."""
    garde = [c for c in texte if c in "\n\t" or unicodedata.category(c) not in ("Cc", "Cf")]
    return "".join(garde), len(texte) - len(garde)


def controler(texte: str) -> ControleEntree:
    """Contrôle une transcription avant l'agent ; ne journalise jamais son contenu."""
    if len(texte) > LONGUEUR_MAX:
        resultat = ControleEntree(texte="", refus="entree_trop_longue")
    else:
        propre, retires = nettoyer(texte)
        if sum(c.isalpha() for c in propre) < LETTRES_MIN:
            resultat = ControleEntree(texte="", refus="entree_vide", caracteres_retires=retires)
        else:
            _, motifs = charger_motifs()
            normalise = normaliser(propre)
            detectes = [m.id for m in motifs if m.regex.search(normalise)]
            resultat = ControleEntree(texte=propre, motifs=detectes, caracteres_retires=retires)
    if resultat.refus or resultat.motifs or resultat.caracteres_retires:
        journal.warning(
            "entree.controle refus=%s motifs=%s caracteres_retires=%s",
            resultat.refus or "aucun",
            ",".join(resultat.motifs) or "aucun",
            resultat.caracteres_retires,
        )
    return resultat
