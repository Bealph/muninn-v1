"""Contrat `DossierDraft` 1.1, sous-ensemble de la V1 (contrat d'API de la phase 2, § 3).

Deux modèles, et la frontière entre eux est une mesure de sécurité (§ 3.2, M-04, M-05) :
- `SortieLLM` : ce que produit le modèle (contenu extrait et confiances brutes), rien d'autre ;
- `DossierDraft` : le brouillon complet, dont le serveur écrit seul les métadonnées, les
  contrôles, les statuts et les dates de destruction.

Les deux refusent tout champ inconnu (`extra="forbid"`). Le sous-ensemble de la V1 et ses écarts
au contrat de la phase 2 sont décrits dans `docs/v1/sprints/sprint-4/contrat-dossier.md`.
"""

import re
from datetime import datetime
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION_SCHEMA = "1.1"

Confiance = Annotated[float, Field(ge=0, le=1)]
Metier = Literal["plomberie", "chauffage", "electricite", "serrurerie", "autre"]
Urgence = Literal["securite", "urgent", "normal", "non_precise"]
TypeAction = Literal["rappeler", "envoyer_devis", "commander", "autre"]
StatutControle = Literal["verified", "mismatch", "not_checked"]
MotifNonControle = Literal["no_value", "service_unavailable", "timeout", "not_applicable"]

MOTIF_TELEPHONE = re.compile(r"^\+[1-9][0-9]{7,14}$")
# Numéro français : 10 chiffres en national, donc « +33 » suivi de 9 chiffres. Le motif E.164
# seul accepte « +336990000002 », un zéro répété par la transcription (benchmark C7, SC-02).
MOTIF_TELEPHONE_FRANCE = re.compile(r"^\+33[1-9][0-9]{8}$")
MOTIF_CODE_POSTAL = re.compile(r"^[0-9]{4,5}$")


def numero_plausible(numero: str) -> bool:
    """Numéro E.164 ; s'il est français, exactement 9 chiffres après « +33 »."""
    if not MOTIF_TELEPHONE.fullmatch(numero):
        return False
    return not numero.startswith("+33") or MOTIF_TELEPHONE_FRANCE.fullmatch(numero) is not None


# Liste fermée des chemins de champ (contrat § 3.4, `FieldPath`), sans les chemins `depense.*`
# ni `contact.*`, hors V1.
CHEMINS_CHAMPS: tuple[str, ...] = (
    "client.nom",
    "client.prenom",
    "client.telephone",
    "client.adresse.rue",
    "client.adresse.code_postal",
    "client.adresse.commune",
    "demande.objet_court",
    "demande.description",
    "demande.metier",
    "demande.urgence",
    "demande.disponibilites_client",
    "demande.rdv_propose",
    "cle_humaine",
    "actions",
)
CheminChamp = Literal[
    "client.nom",
    "client.prenom",
    "client.telephone",
    "client.adresse.rue",
    "client.adresse.code_postal",
    "client.adresse.commune",
    "demande.objet_court",
    "demande.description",
    "demande.metier",
    "demande.urgence",
    "demande.disponibilites_client",
    "demande.rdv_propose",
    "cle_humaine",
    "actions",
]


class Strict(BaseModel):
    """Base commune : aucun champ inconnu, valeurs figées après construction."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _confiance_nulle_si_vide(valeur: object, confiance: float) -> None:
    if valeur is None and confiance != 0:
        raise ValueError("une valeur nulle a une confiance de 0 (règle 1)")


class TexteCourt(Strict):
    value: Annotated[str, Field(min_length=1, max_length=120)] | None
    confidence: Confiance

    @model_validator(mode="after")
    def _regle_1(self) -> Self:
        _confiance_nulle_si_vide(self.value, self.confidence)
        return self


class TexteLong(Strict):
    value: Annotated[str, Field(min_length=1, max_length=2000)] | None
    confidence: Confiance

    @model_validator(mode="after")
    def _regle_1(self) -> Self:
        _confiance_nulle_si_vide(self.value, self.confidence)
        return self


class Telephone(Strict):
    value: Annotated[str, Field(pattern=MOTIF_TELEPHONE.pattern)] | None
    confidence: Confiance
    origin: Literal["caller_id", "spoken"] | None

    @model_validator(mode="after")
    def _origine(self) -> Self:
        _confiance_nulle_si_vide(self.value, self.confidence)
        if (self.value is None) != (self.origin is None):
            raise ValueError("l'origine est nulle si et seulement si le numéro l'est")
        return self


class CodePostal(Strict):
    value: Annotated[str, Field(pattern=MOTIF_CODE_POSTAL.pattern)] | None
    confidence: Confiance

    @model_validator(mode="after")
    def _regles(self) -> Self:
        _confiance_nulle_si_vide(self.value, self.confidence)
        if self.value is not None and len(self.value) == 4 and self.confidence >= 0.7:
            raise ValueError("un code postal à 4 chiffres a une confiance sous 0,7")
        return self


class Adresse(Strict):
    rue: TexteCourt
    code_postal: CodePostal
    commune: TexteCourt


class Client(Strict):
    nom: TexteCourt
    prenom: TexteCourt
    telephone: Telephone
    adresse: Adresse


class Demande(Strict):
    objet_court: TexteCourt
    description: TexteLong
    metier: Metier
    urgence: Urgence
    disponibilites_client: Annotated[list[TexteCourt], Field(max_length=5)]
    # Rendez-vous hors V1 (dossier V1, § 2.3) : le champ reste vide.
    rdv_propose: None = None


class Action(Strict):
    type: TypeAction
    libelle: Annotated[str, Field(min_length=1, max_length=140)]


class SortieLLM(Strict):
    """Ce que le modèle produit : le contenu extrait, sans aucun champ du serveur (§ 3.2)."""

    client: Client
    demande: Demande
    cle_humaine: Annotated[str, Field(min_length=5, max_length=160)] | None
    actions: Annotated[list[Action], Field(max_length=10)]
    champs_manquants: list[CheminChamp]
    # Mots de la transcription qui ont permis de choisir entre des communes homonymes (règle 4
    # de la politique) ; le serveur vérifie qu'ils y figurent (D-69). Absent du brouillon.
    indice_commune: Annotated[str, Field(min_length=1, max_length=120)] | None = None

    @model_validator(mode="after")
    def _sans_doublon(self) -> Self:
        if len(set(self.champs_manquants)) != len(self.champs_manquants):
            raise ValueError("champs_manquants contient un doublon")
        return self


class Lexique(Strict):
    trade: Metier
    version: Annotated[str, Field(pattern=r"^[0-9]{4}\.[0-9]{2}\.[0-9]+$")]


class Provenance(Strict):
    input_mode: Literal["text", "simulated"]
    prompt_version: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")] | None
    model_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,99}$")] | None
    lexicon: Lexique | None
    extraction_status: Literal["complete", "partial_after_retry", "fallback_no_llm"]
    validation_attempts: Annotated[int, Field(ge=0, le=2)]

    @model_validator(mode="after")
    def _coherence(self) -> Self:
        if self.extraction_status == "fallback_no_llm":
            if self.validation_attempts != 0 or self.prompt_version or self.model_id:
                raise ValueError("un brouillon de secours n'a ni tentative, ni prompt, ni modèle")
        else:
            if self.validation_attempts < 1 or not self.prompt_version or not self.model_id:
                raise ValueError("une extraction par le LLM porte ses versions et ses tentatives")
        if self.extraction_status == "partial_after_retry" and self.validation_attempts != 2:
            raise ValueError("un brouillon partiel suit deux tentatives")
        return self


class Destruction(Strict):
    # Entrée écrite ou simulée en V1 : jamais d'audio ni d'image côté serveur (règle 7).
    audio_destroyed_at: None = None
    transcript_destroyed_at: datetime
    image_destroyed_at: None = None


class VersionReferentiel(Strict):
    dataset: Literal["communes", "postal_codes"]
    source_id: Literal["SRC-06", "SRC-07"]
    source_date: str
    channel: Literal["production", "test"]


class ControleTelephone(Strict):
    """Contrôle du numéro hors V1 (dossier V1, § 2.3) : toujours « non contrôlé »."""

    status: Literal["not_checked"]
    reason: Literal["no_value", "not_applicable"]
    referential: None = None
    line_type: None = None
    sms_capable: None = None


class ControleCodePostal(Strict):
    status: StatutControle
    reason: (
        Literal["inconsistent_pair", "unknown_postal_code", "malformed"] | MotifNonControle | None
    )
    referential: VersionReferentiel | None

    @model_validator(mode="after")
    def _coherence(self) -> Self:
        _verifier_controle(self.status, self.reason, self.referential)
        if self.status == "mismatch" and self.reason not in (
            "inconsistent_pair",
            "unknown_postal_code",
            "malformed",
        ):
            raise ValueError("motif d'incohérence inconnu pour le code postal")
        return self


class ControleCommune(Strict):
    status: StatutControle
    reason: Literal["inconsistent_pair", "unknown_commune"] | MotifNonControle | None
    referential: VersionReferentiel | None
    insee_code: Annotated[str, Field(pattern=r"^[0-9][0-9AB][0-9]{3}$")] | None
    match: Literal["exact", "normalized", "fuzzy", "delegated"] | None
    heard_value: Annotated[str, Field(min_length=1, max_length=120)] | None

    @model_validator(mode="after")
    def _coherence(self) -> Self:
        _verifier_controle(self.status, self.reason, self.referential)
        if self.status == "verified" and (self.insee_code is None or self.match is None):
            raise ValueError("une commune vérifiée porte son code INSEE et son mode d'appariement")
        if self.status == "mismatch" and self.reason not in (
            "inconsistent_pair",
            "unknown_commune",
        ):
            raise ValueError("motif d'incohérence inconnu pour la commune")
        if self.status == "not_checked" and (
            self.insee_code is not None or self.match is not None or self.heard_value is not None
        ):
            raise ValueError("une commune non contrôlée n'a ni code, ni appariement, ni valeur")
        return self


def _verifier_controle(
    statut: str, motif: str | None, referentiel: VersionReferentiel | None
) -> None:
    if statut == "verified" and (motif is not None or referentiel is None):
        raise ValueError("un contrôle vérifié n'a pas de motif et cite son référentiel")
    if statut == "mismatch" and referentiel is None:
        raise ValueError("un contrôle incohérent cite son référentiel")
    if statut == "not_checked" and (
        motif not in ("no_value", "service_unavailable", "timeout", "not_applicable")
        or referentiel is not None
    ):
        raise ValueError("un contrôle non fait porte un motif de non-contrôle et aucun référentiel")


class Controles(Strict):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    telephone: ControleTelephone = Field(alias="client.telephone")
    code_postal: ControleCodePostal = Field(alias="client.adresse.code_postal")
    commune: ControleCommune = Field(alias="client.adresse.commune")


class DossierDraft(Strict):
    """Brouillon complet, contrat 1.1, sous-ensemble de la V1."""

    schema_version: Literal["1.1"] = "1.1"
    draft_id: UUID
    created_at: datetime
    source: Literal["missed_call"]
    call_outcome: Literal["completed", "caller_refused", "safety_redirect", "abandoned"]
    provenance: Provenance
    destruction: Destruction
    client: Client
    demande: Demande
    cle_humaine: Annotated[str, Field(min_length=5, max_length=160)] | None
    actions: Annotated[list[Action], Field(max_length=10)]
    # Dépense hors V1 : toujours nulle pour un appel manqué (règle 9).
    depense: None = None
    checks: Controles
    needs_review: bool
    champs_manquants: list[CheminChamp]

    @model_validator(mode="after")
    def _regle_6(self) -> Self:
        attendu = self.provenance.extraction_status != "complete"
        if self.needs_review != attendu:
            raise ValueError(
                "needs_review vaut vrai si et seulement si l'extraction n'est pas complète"
            )
        if len(set(self.champs_manquants)) != len(self.champs_manquants):
            raise ValueError("champs_manquants contient un doublon")
        return self

    def en_json(self) -> dict[str, Any]:
        """Forme publiée du contrat : chemins complets dans `checks`, dates ISO 8601."""
        return self.model_dump(mode="json", by_alias=True)
