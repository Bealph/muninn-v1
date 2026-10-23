"""L'évaluateur du serveur : il construit le brouillon, par des règles écrites (A-3, D-37, D-69).

Il reçoit la sortie de l'agent et fixe seul tout ce qui fait foi :
- la correspondance de la commune et du code postal avec les référentiels, dans tous les cas
  (D-69) : une seule commune donne son code postal et son département ; plusieurs : la valeur
  entendue est gardée, les candidates sont jointes, le dossier est « à vérifier » ; jamais de choix
  automatique entre homonymes ;
- les contrôles (`verified`, `mismatch`, `not_checked`), la provenance, les confiances ajustées ;
- la règle contre l'invention : une commune ou un code postal ni entendu, ni rendu par un outil,
  est retiré avant la correspondance ;
- la règle « gaz » (liste fermée de l'annexe A) et la règle « santé » (liste fermée, R7) ;
- les champs manquants, la clé humaine, `needs_review`, les dates de destruction.

Ce qu'il ajoute autour du brouillon va dans l'enveloppe (D-67) : jamais une valeur du client,
seulement des chemins, des énumérations et des données publiques des référentiels. Rien de la
transcription n'est journalisé (R3, R4).
"""

import logging
import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict

from muninn.extraction.agent import ResultatAgent, extraire
from muninn.extraction.contrat import (
    Action,
    Adresse,
    Client,
    CodePostal,
    ControleCodePostal,
    ControleCommune,
    Controles,
    ControleTelephone,
    Demande,
    Destruction,
    DossierDraft,
    Metier,
    Provenance,
    SortieLLM,
    Telephone,
    TexteCourt,
    TexteLong,
    VersionReferentiel,
)
from muninn.extraction.entree import controler, normaliser, paroles_appelant
from muninn.extraction.indices import departements_cites
from muninn.extraction.outils import MOTIF_NOM_COMPOSE, Referentiels
from muninn.extraction.paquet import Paquet
from muninn.extraction.regles import calculer_champs_manquants, champs_a_verifier, plafonner
from muninn.extraction.sortie import appliquer
from muninn.llm.fournisseur import FournisseurLLM
from muninn.observabilite import tracer
from muninn.telemetrie import etape

journal = logging.getLogger(__name__)

# Annexe A du dossier V1 : listes fermées, comparées après normalisation.
EXPRESSIONS_GAZ = ("odeur de gaz", "sent le gaz", "fuite de gaz", "odeur d oeuf pourri")
# Règle « urgence dite » (D-80) : mots qui disent l'urgence, et mots qui l'annulent ou la mettent
# en doute quand ils la précèdent (négation, condition, interrogation, atténuation).
MOTS_URGENT = frozenset({"urgent", "urgente", "urgents", "urgentes", "urgemment"})
BLOQUANTS_URGENCE = frozenset(
    {
        "pas",
        "non",
        "rien",
        "aucun",
        "aucune",
        "jamais",
        "sans",
        "plus",
        "peu",
        "si",
        "que",
        "pourquoi",
    }
)
TERMES_SANTE = (
    "diabet",
    "cardiaque",
    "asthm",
    "enceinte",
    "handicap",
    "medicament",
    "malad",
    "hopital",
)
ACTION_GAZ = Action(
    type="autre", libelle="Orienter vers Urgence Sécurité Gaz (0 800 47 33 33) ou le 112"
)
CONFIANCE_DEDUITE = 0.9
# Champs clés du dossier (vérification d'exactitude de la phase 1, VE).
CHAMPS_CLES = frozenset(
    {
        "client.nom",
        "client.telephone",
        "client.adresse.commune",
        "client.adresse.code_postal",
        "demande.objet_court",
    }
)

Origine = Literal["entendu", "deduit", "absent", "corrige"]
Auteur = Literal["transcription", "agent", "serveur", "aucun", "artisan"]
Motif = Literal[
    "extraction_incomplete",
    "brouillon_de_secours",
    "commune_ambigue",
    "code_postal_ambigu",
    "incoherent",
    "commune_inconnue",
    "non_controle",
    "invention_retiree",
    "detournement_suspect",
    "champ_incertain",
    "choix_sans_indice",
    "qualification_indeterminee",
    "fuite_retiree",
]
GardeFou = Literal["gaz", "sante", "invention", "detournement", "fuite", "hors_role"]
RaisonNonControle = Literal["no_value", "service_unavailable", "timeout", "not_applicable"]


class CandidateCommune(BaseModel):
    """Une commune candidate : données publiques du COG et de La Poste (D-67, condition 1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    code_insee: str
    nom: str
    departement: str
    codes_postaux: list[str]


class ProvenanceChamp(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origine: Origine
    auteur: Auteur


ABSENT = ProvenanceChamp(origine="absent", auteur="aucun")


class Enveloppe(BaseModel):
    """Écrite par le serveur à côté du brouillon (D-67) : ni stockée, ni journalisée."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    provenance: dict[str, ProvenanceChamp]
    departement: str | None
    candidates: list[CandidateCommune]
    a_verifier: bool
    motifs: list[Motif]
    garde_fous: list[GardeFou]


@dataclass
class Extraction:
    """Le brouillon et son enveloppe, plus la trace de l'agent pour les métriques (sans contenu)."""

    brouillon: DossierDraft
    enveloppe: Enveloppe
    agent: ResultatAgent | None


MESSAGE_REFUS_CONTENU = (
    "La demande n'a pas pu être traitée : son contenu a été bloqué par le filtre de modération."
)


class ContenuRefuse(Exception):
    """Le filtre de contenu a bloqué l'extraction : refus poli à texte fixe, aucun brouillon
    (D-63, D-70). Le texte ne reprend jamais un fragment de l'entrée."""

    def __init__(self, message: str = MESSAGE_REFUS_CONTENU) -> None:
        super().__init__(MESSAGE_REFUS_CONTENU)


class EntreeRefusee(Exception):
    """Entrée inexploitable (vide, trop longue) : refus motivé à texte fixe, aucun brouillon."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# --- Comparaison des textes (normalisation commune avec les garde-fous d'entrée) ----------------


def present(valeur: str, transcription_normalisee: str) -> bool:
    """La valeur figure-t-elle dans la transcription, après normalisation (mots entiers) ?"""
    v = normaliser(valeur)
    return bool(v) and f" {v} " in f" {transcription_normalisee} "


def present_code_postal(code: str, transcription: str) -> bool:
    """Un code postal dit en chiffres groupés (« 93 100 ») compte comme entendu."""
    chiffres = re.sub(r"(?<=\d)[ .](?=\d)", "", transcription)
    return re.search(rf"(?<!\d){re.escape(code)}(?!\d)", chiffres) is not None


def chiffres(texte: str) -> str:
    return re.sub(r"\D", "", texte)


def retirer_identite_inventee(
    sortie: SortieLLM, texte: str, transcription: str, numero_presente: str | None
) -> tuple[SortieLLM, bool]:
    """Règle contre l'invention (D-37) étendue au nom, au prénom, à la rue et au téléphone dit :
    une valeur absente de la transcription est retirée (fuite d'une autre donnée, ou invention)."""
    client = sortie.client
    mises_a_jour: dict[str, Any] = {}
    # L'identité du client vient de ce que dit l'appelant : dans un dialogue, une valeur qui n'est
    # que dans les répliques de l'agent (le nom de l'artisan dans « Karim vous rappellera ») est
    # retirée.
    paroles = normaliser(paroles_appelant(transcription))
    for champ in ("nom", "prenom"):
        valeur = getattr(client, champ).value
        if valeur is not None and not present(valeur, paroles):
            mises_a_jour[champ] = _vide()
    rue = client.adresse.rue.value
    if rue is not None and not present(rue, paroles):
        mises_a_jour["adresse"] = client.adresse.model_copy(update={"rue": _vide()})
    tel = client.telephone
    if tel.value is not None:
        national = "0" + tel.value[3:] if tel.value.startswith("+33") else tel.value
        dit = national in chiffres(transcription) or tel.value[1:] in chiffres(transcription)
        if not (dit or (tel.origin == "caller_id" and tel.value == numero_presente)):
            mises_a_jour["telephone"] = Telephone(value=None, confidence=0, origin=None)
    if not mises_a_jour:
        return sortie, False
    return sortie.model_copy(update={"client": client.model_copy(update=mises_a_jour)}), True


# --- Règles « gaz » et « santé » ---------------------------------------------------------------


def detecter_gaz(transcription_normalisee: str) -> bool:
    return any(f" {e} " in f" {transcription_normalisee} " for e in EXPRESSIONS_GAZ)


def urgence_dite(paroles_normalisees: str) -> bool:
    """« Urgent » dit en clair par l'appelant (D-80) : un mot de `MOTS_URGENT` sans négation,
    condition ni question dans les quatre mots qui le précèdent (« ce n'est pas urgent », « je ne
    sais pas si c'est urgent », « est-ce que c'est urgent »). Dans le doute, la règle ne dit rien
    et la valeur du modèle reste."""
    mots = paroles_normalisees.split()
    for i, mot in enumerate(mots):
        avant = mots[max(0, i - 4) : i]
        question = any(avant[j : j + 2] == ["est", "ce"] for j in range(len(avant) - 1))
        if mot in MOTS_URGENT and not (BLOQUANTS_URGENCE & set(avant) or question):
            return True
    return False


def contient_sante(texte: str | None) -> bool:
    return texte is not None and any(t in normaliser(texte) for t in TERMES_SANTE)


def retirer_sante(sortie: SortieLLM) -> tuple[SortieLLM, bool]:
    """Règle « santé » (R7) : tout champ qui contient un terme de la liste fermée est vidé."""
    donnees = sortie.model_dump()
    retire = False

    def visiter(noeud: Any) -> None:
        nonlocal retire
        if isinstance(noeud, dict):
            valeur = noeud.get("value")
            if "confidence" in noeud and isinstance(valeur, str) and contient_sante(valeur):
                noeud["value"], noeud["confidence"] = None, 0
                if "origin" in noeud:
                    noeud["origin"] = None
                retire = True
            for enfant in noeud.values():
                visiter(enfant)
        elif isinstance(noeud, list):
            for enfant in noeud:
                visiter(enfant)

    visiter(donnees)
    actions = [a for a in donnees["actions"] if not contient_sante(a["libelle"])]
    retire |= len(actions) != len(donnees["actions"])
    donnees["actions"] = actions
    if contient_sante(donnees["cle_humaine"]):
        donnees["cle_humaine"], retire = None, True
    return SortieLLM.model_validate(donnees), retire


# --- Correspondance avec les référentiels (D-69) -----------------------------------------------


@dataclass
class Correspondance:
    commune: TexteCourt
    code_postal: CodePostal
    controle_commune: ControleCommune
    controle_code_postal: ControleCodePostal
    provenance_commune: ProvenanceChamp
    provenance_code_postal: ProvenanceChamp
    departement: str | None = None
    candidates: list[CandidateCommune] = field(default_factory=list)
    motifs: list[Motif] = field(default_factory=list)


def commune_non_controlee(raison: RaisonNonControle) -> ControleCommune:
    return ControleCommune(
        status="not_checked",
        reason=raison,
        referential=None,
        insee_code=None,
        match=None,
        heard_value=None,
    )


def code_non_controle(raison: RaisonNonControle) -> ControleCodePostal:
    return ControleCodePostal(status="not_checked", reason=raison, referential=None)


def _version(reponse: dict[str, Any], source_id: Literal["SRC-06", "SRC-07"]) -> VersionReferentiel:
    for source in reponse.get("sources") or []:
        if isinstance(source, dict) and source.get("source_id") == source_id:
            return VersionReferentiel(
                dataset="communes" if source_id == "SRC-07" else "postal_codes",
                source_id=source_id,
                source_date=str(source.get("date_source")),
                channel="production",
            )
    raise ValueError(f"source {source_id} absente de la réponse")


def _match(
    via: str, entendu: str | None, nom_officiel: str
) -> Literal["exact", "normalized", "delegated"]:
    if via == "code postal" or entendu is None:
        return "exact"
    if via != "nom officiel":
        return "delegated"
    return "exact" if entendu == nom_officiel else "normalized"


def correspondre(
    referentiels: Referentiels,
    commune: TexteCourt,
    code_postal: CodePostal,
    provenance_commune: ProvenanceChamp,
    provenance_code_postal: ProvenanceChamp,
    choix_agent: bool,
    transcription_normalisee: str = "",
) -> Correspondance:
    """Rejoue le contrôle et complète la commune et le code postal par les référentiels (D-69)."""
    nom, code = commune.value, code_postal.value
    resultat = Correspondance(
        commune,
        code_postal,
        commune_non_controlee("no_value"),
        code_non_controle("no_value"),
        provenance_commune,
        provenance_code_postal,
    )
    if nom is None and code is None:
        return resultat
    malforme = code is not None and len(code) != 5
    corps = {k: v for k, v in (("nom", nom), ("code_postal", None if malforme else code)) if v}
    try:
        if not corps:
            raise ValueError("rien à chercher")
        reponse = referentiels.communes(corps)
        principal = MOTIF_NOM_COMPOSE.match(nom or "")
        if reponse.get("statut") == "hors_corpus" and principal:
            # Nom usuel non officiel (« Clichy-la-Garenne ») : le serveur cherche le nom principal,
            # même si l'agent ne l'a pas fait. Une commune : elle est retenue ; plusieurs : jointes
            # au dossier, jamais choisies (D-69, D-77).
            secours = referentiels.communes(corps | {"nom": principal.group(1)})
            if secours.get("candidates"):
                reponse = secours | {
                    "candidates": [
                        c | {"via": "nom principal"}
                        for c in secours["candidates"]
                        if isinstance(c, dict)
                    ]
                }
        ref_communes, ref_codes = _version(reponse, "SRC-07"), _version(reponse, "SRC-06")
    except Exception as erreur:  # noqa: BLE001 (toute panne : contrôle « non contrôlé », D-29)
        if not isinstance(erreur, httpx.HTTPError | ValueError | KeyError | TypeError):
            journal.warning("evaluateur.referentiels_erreur type=%s", type(erreur).__name__)
        raison: RaisonNonControle = (
            "timeout" if isinstance(erreur, httpx.TimeoutException) else "service_unavailable"
        )
        resultat.motifs.append("non_controle")
        if nom is not None:
            resultat.controle_commune = commune_non_controlee(raison)
        if code is not None:
            resultat.controle_code_postal = code_non_controle(raison)
        return _plafonner(resultat)

    statut = str(reponse.get("statut"))
    lignes = [c for c in reponse.get("candidates") or [] if isinstance(c, dict)]
    candidates = [
        CandidateCommune(
            code_insee=str(c["code_insee"]),
            nom=str(c["nom"]),
            departement=str(c["departement"]),
            codes_postaux=[str(cp) for cp in c.get("codes_postaux") or []],
        )
        for c in lignes
    ]
    vias = {str(c["code_insee"]): str(c.get("via") or "") for c in lignes}

    indice_serveur = False
    if statut == "trouve" and len(candidates) > 1 and code is None and nom is not None:
        # D-78 : un département cité en clair (« en Seine-et-Marne », « le 9-3 ») départage les
        # homonymes ; seulement si une seule candidate est dans un département cité.
        retenues = [
            c for c in candidates if c.departement in departements_cites(transcription_normalisee)
        ]
        if len(retenues) == 1:
            candidates, indice_serveur = retenues, True

    if malforme:
        resultat.controle_code_postal = ControleCodePostal(
            status="mismatch", reason="malformed", referential=ref_codes
        )
        resultat.motifs.append("incoherent")

    if statut == "hors_corpus" or not candidates:
        if nom is not None:
            resultat.controle_commune = ControleCommune(
                status="mismatch", reason="unknown_commune", referential=ref_communes,
                insee_code=None, match=None, heard_value=nom,
            )  # fmt: skip
            resultat.motifs.append("commune_inconnue")
        if code is not None and not malforme:
            resultat.controle_code_postal = ControleCodePostal(
                status="mismatch", reason="unknown_postal_code", referential=ref_codes
            )
            resultat.motifs.append("incoherent")
    elif statut == "incoherent":
        # Nom et code donnés, aucune commune ne les accorde : rien n'est corrigé en silence.
        resultat.controle_commune = ControleCommune(
            status="mismatch", reason="inconsistent_pair", referential=ref_communes,
            insee_code=None, match=None, heard_value=nom,
        )  # fmt: skip
        resultat.controle_code_postal = ControleCodePostal(
            status="mismatch", reason="inconsistent_pair", referential=ref_codes
        )
        resultat.candidates = candidates
        resultat.motifs.append("incoherent")
    elif len(candidates) == 1:
        choisie = candidates[0]
        resultat.departement = choisie.departement
        resultat.commune = TexteCourt(
            value=choisie.nom,
            confidence=commune.confidence if nom is not None else CONFIANCE_DEDUITE,
        )
        resultat.controle_commune = ControleCommune(
            status="verified",
            reason=None,
            referential=ref_communes,
            insee_code=choisie.code_insee,
            match=_match(vias.get(choisie.code_insee, ""), nom, choisie.nom),
            heard_value=nom,
        )
        if nom is None:
            resultat.provenance_commune = ProvenanceChamp(origine="deduit", auteur="serveur")
        elif choix_agent:
            # L'agent a choisi parmi des homonymes grâce à un indice (« le 9-3 ») : déduit.
            resultat.provenance_commune = ProvenanceChamp(origine="deduit", auteur="agent")
        elif indice_serveur:
            resultat.provenance_commune = ProvenanceChamp(origine="deduit", auteur="serveur")
        if code is None:
            if len(choisie.codes_postaux) == 1:
                resultat.code_postal = CodePostal(
                    value=choisie.codes_postaux[0], confidence=CONFIANCE_DEDUITE
                )
                resultat.controle_code_postal = ControleCodePostal(
                    status="verified", reason=None, referential=ref_codes
                )
                resultat.provenance_code_postal = ProvenanceChamp(
                    origine="deduit", auteur="serveur"
                )
            else:
                resultat.candidates = candidates
                resultat.motifs.append("code_postal_ambigu")
        elif not malforme:
            resultat.controle_code_postal = ControleCodePostal(
                status="verified", reason=None, referential=ref_codes
            )
    else:
        # Plusieurs communes : jamais de choix automatique (D-69). La valeur entendue est gardée.
        resultat.candidates = candidates
        resultat.motifs.append("commune_ambigue" if nom is not None else "code_postal_ambigu")
        if nom is not None:
            resultat.controle_commune = commune_non_controlee("not_applicable")
        if code is not None and not malforme:
            resultat.controle_code_postal = ControleCodePostal(
                status="verified", reason=None, referential=ref_codes
            )
    return _plafonner(resultat)


def _plafonner(resultat: Correspondance) -> Correspondance:
    """Règle 2 : un champ incohérent ou non contrôlé reste « à vérifier »."""
    resultat.commune = resultat.commune.model_copy(
        update={
            "confidence": plafonner(resultat.commune.confidence, resultat.controle_commune.status)
        }
    )
    resultat.code_postal = resultat.code_postal.model_copy(
        update={
            "confidence": plafonner(
                resultat.code_postal.confidence, resultat.controle_code_postal.status
            )
        }
    )
    return resultat


# --- Construction du brouillon ------------------------------------------------------------------


def _provenance(valeur: str | None, entendue: bool, rendue_par_outil: bool) -> ProvenanceChamp:
    if valeur is None:
        return ABSENT
    if entendue:
        return ProvenanceChamp(origine="entendu", auteur="transcription")
    return ProvenanceChamp(origine="deduit", auteur="agent" if rendue_par_outil else "aucun")


def _cle_humaine(client: Client, demande: Demande) -> str | None:
    """Règle 10 : « Nom, Commune, objet court », recalculée par le serveur."""
    morceaux = [client.nom.value, client.adresse.commune.value, demande.objet_court.value]
    if any(m is None for m in morceaux):
        return None
    cle = ", ".join(m for m in morceaux if m)
    return cle if 5 <= len(cle) <= 160 else None


def _vide() -> TexteCourt:
    return TexteCourt(value=None, confidence=0)


def _telephone_presente(numero_presente: str | None) -> Telephone:
    if numero_presente and re.fullmatch(r"\+[1-9][0-9]{7,14}", numero_presente):
        return Telephone(value=numero_presente, confidence=CONFIANCE_DEDUITE, origin="caller_id")
    return Telephone(value=None, confidence=0, origin=None)


def _brouillon_vide(metier: Metier, numero_presente: str | None) -> SortieLLM:
    """Brouillon partiel ou de secours (D-29) : le numéro présenté, un rappel, à vérifier."""
    return SortieLLM(
        client=Client(
            nom=_vide(),
            prenom=_vide(),
            telephone=_telephone_presente(numero_presente),
            adresse=Adresse(
                rue=_vide(), code_postal=CodePostal(value=None, confidence=0), commune=_vide()
            ),
        ),
        demande=Demande(
            objet_court=_vide(),
            description=TexteLong(value=None, confidence=0),
            metier=metier,
            urgence="non_precise",
            disponibilites_client=[],
        ),
        cle_humaine=None,
        actions=[Action(type="rappeler", libelle="Rappeler le client : demande non extraite")],
        champs_manquants=[],
    )


def evaluer(
    resultat: ResultatAgent,
    transcription: str,
    paquet: Paquet,
    referentiels: Referentiels,
    metier: Metier,
    numero_presente: str | None = None,
    input_mode: Literal["text", "simulated"] = "simulated",
    maintenant: Callable[[], datetime] = lambda: datetime.now(UTC),
    motifs_entree: tuple[str, ...] = (),
) -> tuple[DossierDraft, Enveloppe]:
    """Construit le brouillon et l'enveloppe à partir de la sortie de l'agent."""
    if resultat.statut == "content_refused":
        raise ContenuRefuse()
    texte = normaliser(transcription)
    garde_fous: list[GardeFou] = []
    motifs: list[Motif] = []

    sortie = resultat.sortie
    if sortie is None:
        sortie = _brouillon_vide(metier, numero_presente)
        motifs.append(
            "brouillon_de_secours"
            if resultat.statut == "fallback_no_llm"
            else "extraction_incomplete"
        )
    else:
        sortie, retire = retirer_sante(sortie)
        if retire:
            garde_fous.append("sante")
        # Garde-fous de sortie (étape 7) : fuite (témoin, secret) et hors rôle (lien, balisage).
        assainie, declenches = appliquer(
            sortie.model_dump(), SortieLLM.model_validate, ("cle_humaine", "indice_commune")
        )
        garde_fous += sorted(declenches)
        if "fuite" in declenches:
            motifs.append("fuite_retiree")
        if assainie is None:
            journal.warning("evaluateur.sortie_invalide_apres_assainissement")
            assainie = _brouillon_vide(metier, numero_presente)
            motifs.append("extraction_incomplete")
        sortie = assainie
        sortie, inventes = retirer_identite_inventee(sortie, texte, transcription, numero_presente)
        if inventes:
            garde_fous.append("invention")
        if sortie.client.telephone.value is None and numero_presente:
            client = sortie.client.model_copy(
                update={"telephone": _telephone_presente(numero_presente)}
            )
            sortie = sortie.model_copy(update={"client": client})

    # Règle contre l'invention (D-37), avant la correspondance avec les référentiels (D-69).
    adresse = sortie.client.adresse
    rendues = resultat.communes_rendues
    commune, code_postal = adresse.commune, adresse.code_postal
    commune_entendue = commune.value is not None and present(commune.value, texte)
    code_entendu = code_postal.value is not None and present_code_postal(
        code_postal.value, transcription
    )
    commune_outil = commune.value is not None and any(
        normaliser(c.nom) == normaliser(commune.value) for c in rendues
    )
    code_outil = code_postal.value is not None and any(
        code_postal.value in c.codes_postaux for c in rendues
    )
    if commune.value is not None and not commune_entendue and not commune_outil:
        commune, commune_outil = _vide(), False
        garde_fous.append("invention")
    if code_postal.value is not None and not code_entendu and not code_outil:
        code_postal, code_outil = CodePostal(value=None, confidence=0), False
        garde_fous.append("invention")
    if "invention" in garde_fous:
        motifs.append("invention_retiree")
    homonymes_vus = {
        c.code_insee
        for c in rendues
        if commune.value is not None and normaliser(c.nom) == normaliser(commune.value)
    }
    indice = sortie.indice_commune
    choix_agent = len(homonymes_vus) > 1 and code_postal.value is not None and not code_entendu
    if choix_agent and (indice is None or not present(indice, texte)):
        # Règle 4 de la politique, appliquée par le serveur : sans indice vérifiable dans la
        # transcription, le choix de l'agent entre homonymes est refusé (D-69).
        code_postal, code_outil, choix_agent = CodePostal(value=None, confidence=0), False, False
        motifs.append("choix_sans_indice")
    correspondance = correspondre(
        referentiels,
        commune,
        code_postal,
        _provenance(commune.value, commune_entendue, commune_outil),
        _provenance(code_postal.value, code_entendu, code_outil),
        choix_agent,
        texte,
    )
    motifs += correspondance.motifs

    client = sortie.client.model_copy(
        update={
            "adresse": Adresse(
                rue=adresse.rue,
                code_postal=correspondance.code_postal,
                commune=correspondance.commune,
            )
        }
    )
    demande = sortie.demande
    actions = list(sortie.actions)
    call_outcome: Literal["completed", "safety_redirect"] = "completed"
    urgence_par_le_serveur = demande.urgence in ("normal", "non_precise") and urgence_dite(
        normaliser(paroles_appelant(transcription))
    )
    if urgence_par_le_serveur:
        # Règle « urgence dite » (D-80) : l'urgence dite en clair par l'appelant n'est jamais
        # abaissée par le modèle ; la règle ne l'abaisse pas non plus, et « gaz » reste prioritaire.
        demande = demande.model_copy(update={"urgence": "urgent"})
    if detecter_gaz(texte):
        # Règle « gaz » (US-09, CA-3) : urgence de sécurité, aucun rendez-vous, orientation en tête.
        demande = demande.model_copy(update={"urgence": "securite", "rdv_propose": None})
        actions = [ACTION_GAZ] + [a for a in actions if a != ACTION_GAZ]
        garde_fous.append("gaz")
        call_outcome = "safety_redirect"
    if resultat.detournement_detecte or motifs_entree:
        # Annotation du filtre (D-65) ou motif d'injection connu (D-63) : signalé, jamais bloquant.
        garde_fous.append("detournement")
        motifs.append("detournement_suspect")

    statut: Literal["complete", "partial_after_retry", "fallback_no_llm"] = (
        resultat.statut
        if resultat.statut in ("complete", "partial_after_retry")
        else "fallback_no_llm"
    )
    llm = statut != "fallback_no_llm"
    tentatives = {"complete": max(1, resultat.tentatives), "partial_after_retry": 2}.get(statut, 0)
    telephone = client.telephone
    brouillon = DossierDraft(
        draft_id=uuid.uuid4(),
        created_at=maintenant(),
        source="missed_call",
        call_outcome=call_outcome,
        provenance=Provenance(
            input_mode=input_mode,
            prompt_version=paquet.prompt_version if llm else None,
            model_id=paquet.model_id if llm else None,
            lexicon=None,
            extraction_status=statut,
            validation_attempts=tentatives,
        ),
        destruction=Destruction(transcript_destroyed_at=maintenant()),
        client=client,
        demande=demande,
        cle_humaine=_cle_humaine(client, demande) if llm else None,
        actions=actions[:10],
        checks=Controles.model_validate(
            {
                "client.telephone": ControleTelephone(
                    status="not_checked",
                    reason="no_value" if telephone.value is None else "not_applicable",
                ),
                "client.adresse.code_postal": correspondance.controle_code_postal,
                "client.adresse.commune": correspondance.controle_commune,
            }
        ),
        needs_review=statut != "complete",
        champs_manquants=calculer_champs_manquants(client, demande),  # type: ignore[arg-type]
    )
    # Le dossier n'est « à vérifier » que pour un vrai doute : un champ clé présent mais incertain
    # (un champ absent reste signalé champ par champ, par sa confiance nulle et la liste des
    # champs manquants).
    if set(champs_a_verifier(brouillon)) & CHAMPS_CLES - set(brouillon.champs_manquants):
        motifs.append("champ_incertain")
    adresse_finale = brouillon.client.adresse
    enveloppe = Enveloppe(
        provenance={
            "client.adresse.commune": (
                correspondance.provenance_commune if adresse_finale.commune.value else ABSENT
            ),
            "client.adresse.code_postal": (
                correspondance.provenance_code_postal
                if adresse_finale.code_postal.value
                else ABSENT
            ),
        }
        | (
            {"demande.urgence": ProvenanceChamp(origine="entendu", auteur="serveur")}
            if urgence_par_le_serveur and brouillon.demande.urgence == "urgent"
            else {}
        ),
        departement=correspondance.departement,
        candidates=correspondance.candidates,
        a_verifier=brouillon.needs_review or bool(motifs),
        motifs=list(dict.fromkeys(motifs)),
        garde_fous=list(dict.fromkeys(garde_fous)),
    )
    return brouillon, enveloppe


@tracer("extraction", "span", lambda x: {
    "statut": x.brouillon.provenance.extraction_status, "a_verifier": x.enveloppe.a_verifier,
    "motifs": ",".join(x.enveloppe.motifs) or "aucun",
    "garde_fous": ",".join(x.enveloppe.garde_fous) or "aucun",
    "commune": x.brouillon.checks.commune.status,
    "code_postal": x.brouillon.checks.code_postal.status,
})  # fmt: skip
def extraire_dossier(
    transcription: str,
    paquet: Paquet,
    fournisseur: FournisseurLLM,
    referentiels: Referentiels,
    metier: Metier,
    date_reference: str,
    numero_presente: str | None = None,
    input_mode: Literal["text", "simulated"] = "simulated",
    request_id: str = "",
) -> Extraction:
    """Agent puis évaluateur. Aucune copie de la transcription n'est gardée ; sa date de
    destruction est posée par l'évaluateur (contrat, règle 7). Journal d'audit sans contenu."""
    debut = time.perf_counter()
    controle = None
    try:
        controle = controler(transcription)
        if controle.refus is not None:
            raise EntreeRefusee(controle.refus, controle.message_refus or "")
        with etape("agent") as c:
            resultat = extraire(
                controle.texte,
                paquet,
                fournisseur,
                referentiels,
                date_reference,
                metier,
                numero_presente,
            )
            c.update(
                statut=resultat.statut, tentatives=resultat.tentatives,
                outils=len(resultat.appels_outils), borne=resultat.borne_atteinte,
                jetons=resultat.jetons_entree + resultat.jetons_sortie,
                cout_micro_eur=resultat.cout_micro_eur,
            )  # fmt: skip
        with etape("controles_serveur") as c:
            brouillon, enveloppe = evaluer(
                resultat,
                controle.texte,
                paquet,
                referentiels,
                metier,
                numero_presente,
                input_mode,
                motifs_entree=tuple(controle.motifs),
            )
            c.update(
                a_verifier=enveloppe.a_verifier,
                garde_fous=",".join(enveloppe.garde_fous) or "aucun",
                motifs=",".join(enveloppe.motifs) or "aucun",
            )  # fmt: skip
        motifs_entree = controle.motifs
    except (EntreeRefusee, ContenuRefuse) as refus:
        code = refus.code if isinstance(refus, EntreeRefusee) else "content_refused"
        journal.warning("extraction.refus request_id=%s code=%s", request_id, code)
        raise
    finally:
        del transcription, controle  # plus aucune référence locale au texte reçu (R3)
    controles = brouillon.checks
    journal.info(
        "extraction.fin request_id=%s draft_id=%s statut=%s a_verifier=%s motifs=%s garde_fous=%s "
        "motifs_entree=%s commune=%s code_postal=%s urgence=%s urgence_serveur=%s candidates=%s "
        "outils=%s jetons=%s cout_micro_eur=%s duree_ms=%s",
        request_id,
        brouillon.draft_id,
        brouillon.provenance.extraction_status,
        enveloppe.a_verifier,
        ",".join(enveloppe.motifs) or "aucun",
        ",".join(enveloppe.garde_fous) or "aucun",
        ",".join(motifs_entree) or "aucun",
        controles.commune.status,
        controles.code_postal.status,
        brouillon.demande.urgence,
        "demande.urgence" in enveloppe.provenance,
        len(enveloppe.candidates),
        len(resultat.appels_outils),
        resultat.jetons_entree + resultat.jetons_sortie,
        resultat.cout_micro_eur,
        round((time.perf_counter() - debut) * 1000),
    )
    return Extraction(brouillon=brouillon, enveloppe=enveloppe, agent=resultat)
