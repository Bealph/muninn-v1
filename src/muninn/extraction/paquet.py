"""Paquet d'extraction versionné et son empreinte (chaîne LLMOps de la phase 2, § 2 et § 5.2).

Le paquet réunit ce qui fixe le comportement de l'agent : consigne système, gabarit du bloc de
données, schéma de sortie, définitions des outils et paramètres. Il est lu dans
`src/muninn/extraction/paquet_fichiers/` et ne change qu'avec une nouvelle `prompt_version`.

L'empreinte est un SHA-256 sur une liste fermée de chemins : le paquet, le code de l'extraction
et des outils (D-37), la qualification des appels (V-11), l'adaptateur du fournisseur et le
fichier de verrouillage des dépendances. L'évaluation en CI ne tourne que si elle change (D-64).
Le harnais et le jeu d'évaluation y sont depuis l'étape 9 du sprint 4.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DOSSIER_PAQUET = Path(__file__).parent / "paquet_fichiers"
BALISE_OUVRANTE = "<transcription>"
BALISE_FERMANTE = "</transcription>"
_BALISES = re.compile(r"</?\s*transcription\s*>", re.IGNORECASE)

# Liste fermée, relative à la racine du dépôt. Un motif qui ne trouve aucun fichier est une
# erreur : un chemin renommé ne doit pas sortir de l'empreinte en silence.
MOTIFS_EMPREINTE: tuple[str, ...] = (
    "src/muninn/extraction/*.py",
    "src/muninn/extraction/departements.json",
    "src/muninn/extraction/paquet_fichiers/*",
    "src/muninn/llm/*.py",
    "src/muninn/observabilite.py",
    "src/muninn/qualification/*.py",
    "src/muninn/qualification/paquet_fichiers/*",
    "src/muninn/evaluation/*.py",
    "src/muninn/demo/*",
    "eval/v08/*.json",
    "eval/qualification/scenarios.json",
    "uv.lock",
)


@dataclass(frozen=True)
class Paquet:
    """Contenu du paquet d'extraction, lu une fois par processus."""

    consigne: str
    gabarit: str
    schema_sortie: dict[str, Any]
    outils: list[dict[str, Any]]
    parametres: dict[str, Any]

    @property
    def prompt_version(self) -> str:
        return str(self.parametres["prompt_version"])

    @property
    def model_id(self) -> str:
        """Identifiant daté du modèle, porté par chaque brouillon (`provenance.model_id`)."""
        return f"{self.parametres['modele']}-{self.parametres['modele_version']}"

    @property
    def noms_outils(self) -> frozenset[str]:
        return frozenset(o["function"]["name"] for o in self.outils)

    def message_utilisateur(
        self, transcription: str, date_reference: str, metier: str, numero_presente: str | None
    ) -> str:
        """Bloc de données délimité (M-04) : la transcription ne peut pas fermer la balise."""
        return self.gabarit.format(
            date_reference=date_reference,
            metier=metier,
            numero_presente=numero_presente or "masqué",
            transcription=neutraliser_balises(transcription),
        )


def neutraliser_balises(texte: str) -> str:
    """Retire de la transcription toute balise qui imiterait la fin du bloc de données."""
    precedent = None
    while precedent != texte:  # « </trans</transcription>cription> » ne reforme pas la balise
        precedent, texte = texte, _BALISES.sub("", texte)
    return texte


@lru_cache
def charger_paquet(dossier: Path = DOSSIER_PAQUET) -> Paquet:
    def lire(nom: str) -> str:
        return (dossier / nom).read_text(encoding="utf-8")

    return Paquet(
        consigne=lire("consigne.md").strip(),
        gabarit=lire("gabarit.txt"),
        schema_sortie=json.loads(lire("schema_sortie.json")),
        outils=json.loads(lire("outils.json")),
        parametres=json.loads(lire("parametres.json")),
    )


def fichiers_empreinte(racine: Path) -> list[Path]:
    """Fichiers couverts par l'empreinte, triés ; erreur si un motif ne trouve rien."""
    fichiers: set[Path] = set()
    for motif in MOTIFS_EMPREINTE:
        trouves = [f for f in racine.glob(motif) if f.is_file() and "__pycache__" not in f.parts]
        if not trouves:
            raise FileNotFoundError(f"motif d'empreinte sans fichier : {motif}")
        fichiers.update(trouves)
    return sorted(fichiers, key=lambda f: f.relative_to(racine).as_posix())


def calculer_empreinte(racine: Path) -> str:
    """SHA-256 des chemins et des contenus ; fins de ligne normalisées (Windows et Linux)."""
    somme = hashlib.sha256()
    for fichier in fichiers_empreinte(racine):
        somme.update(fichier.relative_to(racine).as_posix().encode("utf-8") + b"\0")
        somme.update(fichier.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return somme.hexdigest()
