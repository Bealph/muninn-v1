"""Contrats de la qualification : sortie du LLM, message reçu, trace sans contenu (§5).

Le `DossierDraft` 1.1 n'est pas modifié : un message n'est pas un dossier.
"""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from muninn.extraction.contrat import MOTIF_TELEPHONE, Confiance

Categorie = Literal["demande_service", "indetermine", "fournisseur", "personnel", "autre"]
CategorieMessage = Literal["fournisseur", "personnel", "autre"]
CATEGORIES_MESSAGE: frozenset[str] = frozenset({"fournisseur", "personnel", "autre"})
RegleServeur = Literal[
    "seuil", "retrogradation", "detournement", "modele_indisponible", "sortie_invalide"
]
NumeroE164 = Annotated[str, Field(pattern=MOTIF_TELEPHONE.pattern)]
LONGUEUR_MESSAGE = 500


class SortieQualification(BaseModel):
    """Sortie du LLM, au schéma fermé (`paquet_fichiers/schema_sortie.json`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    categorie: Categorie
    confiance: Confiance
    nom_appelant: str | None
    societe: str | None
    numero_dicte: str | None
    message: str | None
    rappel_souhaite: bool


class MessageRecu(BaseModel):
    """Message pour l'artisan : qui, comment rappeler, quoi (§5.2). Aucune autre extraction."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    message_id: UUID = Field(default_factory=uuid4)
    categorie: CategorieMessage
    nom_appelant: str | None
    societe: str | None
    numero_rappel: NumeroE164 | None  # numéro présenté par le réseau
    numero_dicte: NumeroE164 | None  # un numéro dicté différent, noté à part (provenance « dit »)
    message: Annotated[str, Field(max_length=LONGUEUR_MESSAGE)]
    rappel_souhaite: bool
    securite: bool
    recu_le: datetime
    prompt_version: str


class TraceSansContenu(BaseModel):
    """Appel sans contenu exploitable (§5.4) : numéro, heure et motif, rien d'autre."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    numero_presente: NumeroE164 | None
    recu_le: datetime
    motif: Literal["sans_contenu"]
