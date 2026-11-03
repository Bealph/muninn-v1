"""Correction et validation d'un dossier par l'artisan (sprint 5, étape 2 ; V-09, CA-5, D-86).

Route de démonstration `POST /v1/demo/runs/{draft_id}/review` (contrat d'API, § 4.9). Écart au
contrat, propre à la démonstration (P-03, D-86) : la requête porte aussi les nouvelles valeurs,
pour que le serveur rejoue le contrôle de la commune et du code postal ; dans le produit, les
valeurs restent sur l'appareil de l'artisan.

Ce que fait le serveur, en une requête :
1. il applique les corrections à une liste fermée de champs ;
2. il rejoue le contrôle de la commune et du code postal avec les référentiels (D-69) ;
3. il enregistre l'état « validé », la date et une ligne par champ corrigé, sans sa valeur ;
4. il rend le dossier à jour, dans sa réponse seulement.
Les valeurs corrigées ne sont jamais enregistrées : le formulaire est public, on peut y taper de
vraies données personnelles (D-82). Le dossier gardé conserve ses valeurs synthétiques d'origine.
Aucune valeur corrigée n'est journalisée : seuls l'identifiant, la décision, les noms des champs
et les statuts des contrôles.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import Engine, text

from muninn.extraction.contrat import (
    Adresse,
    Client,
    CodePostal,
    Controles,
    Demande,
    DossierDraft,
    Telephone,
    TexteCourt,
    Urgence,
    numero_plausible,
)
from muninn.extraction.evaluateur import (
    Enveloppe,
    ProvenanceChamp,
    _cle_humaine,
    correspondre,
)
from muninn.extraction.outils import Referentiels
from muninn.extraction.regles import calculer_champs_manquants, verifier_regles

journal = logging.getLogger(__name__)

ChampCorrigeable = Literal[
    "client.nom",
    "client.prenom",
    "client.telephone",
    "client.adresse.rue",
    "client.adresse.code_postal",
    "client.adresse.commune",
    "demande.objet_court",
    "demande.urgence",
]
CORRIGE = ProvenanceChamp(origine="corrige", auteur="artisan")


class DemandeRevue(BaseModel):
    """Corps de la revue : décision, champs corrigés et, en démonstration, leurs valeurs."""

    model_config = ConfigDict(extra="forbid")
    decision: Literal["validated", "validated_with_corrections"]
    corrected_fields: list[ChampCorrigeable] = Field(default_factory=list, max_length=8)
    values: dict[ChampCorrigeable, Annotated[str, Field(max_length=120)] | None] = Field(
        default_factory=dict
    )

    @model_validator(mode="after")
    def _coherence(self) -> Self:
        if len(set(self.corrected_fields)) != len(self.corrected_fields):
            raise ValueError("un champ corrigé est cité deux fois")
        if self.decision == "validated" and (self.corrected_fields or self.values):
            raise ValueError("une validation sans correction ne porte aucun champ")
        if self.decision == "validated_with_corrections":
            if not self.corrected_fields:
                raise ValueError("une validation avec corrections cite au moins un champ")
            if set(self.values) != set(self.corrected_fields):
                raise ValueError("chaque champ corrigé a sa valeur, et seulement lui")
        return self


class DossierInconnu(Exception):
    """Aucun dossier enregistré sous cet identifiant (jamais enregistré, ou purgé)."""


class DejaValide(Exception):
    """Le dossier a déjà été validé."""


class CorrectionInvalide(Exception):
    """Une valeur corrigée ne respecte pas le contrat ; `champ` dit lequel, jamais la valeur."""

    def __init__(self, champ: str) -> None:
        super().__init__(champ)
        self.champ = champ


@dataclass
class Revue:
    brouillon: DossierDraft
    enveloppe: Enveloppe
    valide_le: datetime
    champs: list[str]


def _texte(valeur: str | None) -> TexteCourt:
    propre = (valeur or "").strip() or None
    return TexteCourt(value=propre, confidence=1.0 if propre else 0)


def _telephone(valeur: str | None) -> Telephone:
    """Numéro corrigé : séparateurs retirés, numéro français à 10 chiffres mis au format +33 ;
    un texte qui n'est pas un numéro est refusé, jamais vidé sans le dire."""
    propre = re.sub(r"[\s.\-()]", "", valeur or "")
    if not propre:
        return Telephone(value=None, confidence=0, origin=None)
    if re.fullmatch(r"0[1-9][0-9]{8}", propre):
        propre = "+33" + propre[1:]
    if not numero_plausible(propre):
        raise ValueError("numéro invalide")
    return Telephone(value=propre, confidence=1.0, origin="spoken")


def _code_postal(valeur: str | None) -> CodePostal:
    propre = re.sub(r"\s", "", valeur or "")
    if propre and not re.fullmatch(r"[0-9]{5}", propre):
        raise ValueError("cinq chiffres attendus")
    return CodePostal(value=propre or None, confidence=1.0 if propre else 0)


def appliquer(b: DossierDraft, valeurs: dict[str, str | None]) -> tuple[Client, Demande]:
    """Le client et la demande corrigés ; lève `CorrectionInvalide` sur une valeur hors contrat."""
    client, demande = b.client, b.demande
    adresse = client.adresse
    for champ, valeur in valeurs.items():
        try:
            if champ == "client.nom":
                client = client.model_copy(update={"nom": _texte(valeur)})
            elif champ == "client.prenom":
                client = client.model_copy(update={"prenom": _texte(valeur)})
            elif champ == "client.telephone":
                client = client.model_copy(update={"telephone": _telephone(valeur)})
            elif champ == "client.adresse.rue":
                adresse = adresse.model_copy(update={"rue": _texte(valeur)})
            elif champ == "client.adresse.code_postal":
                adresse = adresse.model_copy(update={"code_postal": _code_postal(valeur)})
            elif champ == "client.adresse.commune":
                adresse = adresse.model_copy(update={"commune": _texte(valeur)})
            elif champ == "demande.objet_court":
                demande = demande.model_copy(update={"objet_court": _texte(valeur)})
            elif champ == "demande.urgence":
                if valeur not in Urgence.__args__:  # type: ignore[attr-defined]
                    raise ValueError("urgence hors liste")
                demande = demande.model_copy(update={"urgence": valeur})
        except (ValueError, ValidationError) as erreur:
            raise CorrectionInvalide(champ) from erreur
    return client.model_copy(
        update={"adresse": Adresse.model_validate(adresse.model_dump())}
    ), demande


LIRE = text("SELECT brouillon, enveloppe, etat FROM app.dossiers WHERE draft_id = :id FOR UPDATE")
# Seuls l'état et la date changent : le dossier gardé conserve ses valeurs synthétiques d'origine.
VALIDER = text("UPDATE app.dossiers SET etat = 'valide', valide_le = :le WHERE draft_id = :id")
CORRIGER = text(
    "INSERT INTO app.corrections (draft_id, champ, corrige_le) VALUES (:id, :champ, :le)"
)


def reviser(
    m: Engine, draft_id: uuid.UUID, demande: DemandeRevue, referentiels: Referentiels
) -> Revue:
    """Applique la revue ; lève `DossierInconnu`, `DejaValide` ou `CorrectionInvalide`."""
    maintenant = datetime.now(UTC)
    with m.begin() as conn:
        ligne = conn.execute(LIRE, {"id": str(draft_id)}).fetchone()
        if ligne is None:
            raise DossierInconnu()
        if ligne.etat == "valide":
            raise DejaValide()
        b = DossierDraft.model_validate(ligne.brouillon)
        e = Enveloppe.model_validate(ligne.enveloppe)
        valeurs = {str(k): v for k, v in demande.values.items()}
        client, dem = appliquer(b, valeurs)

        # Le serveur rejoue toujours le contrôle de l'adresse, corrigée ou non (CA-5).
        prov = dict(e.provenance)
        prov_commune = (
            CORRIGE
            if "client.adresse.commune" in valeurs
            else prov.get(
                "client.adresse.commune", ProvenanceChamp(origine="absent", auteur="aucun")
            )
        )
        prov_code = (
            CORRIGE
            if "client.adresse.code_postal" in valeurs
            else prov.get(
                "client.adresse.code_postal", ProvenanceChamp(origine="absent", auteur="aucun")
            )
        )
        c = correspondre(
            referentiels, client.adresse.commune, client.adresse.code_postal,
            prov_commune, prov_code, choix_agent=False,
        )  # fmt: skip
        client = client.model_copy(update={"adresse": Adresse(
            rue=client.adresse.rue, code_postal=c.code_postal, commune=c.commune
        )})  # fmt: skip
        for champ in valeurs:
            prov[champ] = CORRIGE
        prov["client.adresse.commune"] = c.provenance_commune
        prov["client.adresse.code_postal"] = c.provenance_code_postal

        controles = b.checks.model_dump(by_alias=True)
        controles["client.adresse.commune"] = c.controle_commune.model_dump(by_alias=True)
        controles["client.adresse.code_postal"] = c.controle_code_postal.model_dump(by_alias=True)
        try:
            nouveau = DossierDraft.model_validate(
                b.model_dump(by_alias=True)
                | {
                    "client": client.model_dump(by_alias=True),
                    "demande": dem.model_dump(by_alias=True),
                    "checks": Controles.model_validate(controles).model_dump(by_alias=True),
                    "cle_humaine": _cle_humaine(client, dem) if b.cle_humaine is not None else None,
                    "champs_manquants": calculer_champs_manquants(client, dem),
                }
            )
        except ValidationError as erreur:
            raise CorrectionInvalide(str(erreur.errors()[0]["loc"][0])) from erreur
        if verifier_regles(nouveau):
            raise CorrectionInvalide("dossier")
        enveloppe = e.model_copy(update={
            "provenance": prov, "departement": c.departement, "candidates": c.candidates,
            "a_verifier": False,
        })  # fmt: skip
        conn.execute(VALIDER, {"id": str(draft_id), "le": maintenant})
        for champ in demande.corrected_fields:
            conn.execute(CORRIGER, {"id": str(draft_id), "champ": champ, "le": maintenant})
    journal.info(
        "revue.fin draft_id=%s decision=%s champs=%s commune=%s code_postal=%s",
        draft_id, demande.decision, ",".join(demande.corrected_fields) or "aucun",
        c.controle_commune.status, c.controle_code_postal.status,
    )  # fmt: skip
    return Revue(nouveau, enveloppe, maintenant, list(demande.corrected_fields))
