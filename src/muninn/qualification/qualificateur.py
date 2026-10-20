"""Qualification d'un appel, puis dossier ou message (V-11 ; conception, qualification, §4 et §5).

1. Garde-fous d'entrée (D-63) : une entrée sans contenu donne une trace sans contenu (§5.4) ; dans
   un dialogue, seules les paroles de l'appelant comptent.
2. Classification par le LLM : une seule étape, schéma fermé, sans outil. Ce n'est pas un agent.
3. Règles du serveur, qui appliquent l'asymétrie des erreurs (§4.2) ; dans le doute, un dossier :
   - modèle indisponible, sortie hors schéma, ou qualification bloquée par le filtre de contenu
     (D-73) : `indetermine` ;
   - confiance sous le seuil (0,7, hypothèse [H]) : `indetermine` ;
   - `personnel` ou `autre` avec une expression de besoin de la liste figée : `indetermine` ;
   - `personnel` ou `autre` avec un motif d'injection connu : `indetermine` ;
   - `fournisseur` n'est jamais rétrogradé ;
   - règle « gaz » dans toutes les catégories (Q-07).
4. `demande_service` et `indetermine` : extraction du dossier (`indetermine` : « à vérifier ») ;
   `fournisseur`, `personnel` et `autre` : `MessageRecu`, sans autre extraction (Q-08).

Aucun contenu dans les journaux (R4) : catégories, confiance, règle, coût, durée.
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from muninn.extraction.contrat import MOTIF_TELEPHONE, Metier
from muninn.extraction.entree import LETTRES_MIN, controler, normaliser, paroles_appelant
from muninn.extraction.evaluateur import (
    ContenuRefuse,
    EntreeRefusee,
    Extraction,
    contient_sante,
    detecter_gaz,
    extraire_dossier,
)
from muninn.extraction.outils import Referentiels
from muninn.extraction.paquet import Paquet, charger_paquet
from muninn.extraction.sortie import GardeFouSortie, assainir
from muninn.llm.fournisseur import (
    DelaiDepasse,
    ErreurFournisseur,
    FournisseurLLM,
    RefusContenu,
    RequeteChat,
)
from muninn.qualification.contrat import (
    CATEGORIES_MESSAGE,
    LONGUEUR_MESSAGE,
    Categorie,
    MessageRecu,
    RegleServeur,
    SortieQualification,
    TraceSansContenu,
)

journal = logging.getLogger(__name__)

DOSSIER_PAQUET = Path(__file__).parent / "paquet_fichiers"
MESSAGE_SANTE = "Message non repris : il contenait une information de santé."
MESSAGE_RETIRE = "Message non repris : retiré par un garde-fou de sortie."


@lru_cache
def charger_paquet_qualification() -> Paquet:
    return charger_paquet(DOSSIER_PAQUET)


@lru_cache
def charger_expressions(
    chemin: Path = DOSSIER_PAQUET / "expressions_besoin.json",
) -> tuple[str, tuple[str, ...]]:
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    return str(donnees["version"]), tuple(str(e) for e in donnees["expressions"])


def contient_besoin(transcription_normalisee: str) -> bool:
    """Expression de besoin d'intervention, en mots entiers, après normalisation (§4.2)."""
    _, expressions = charger_expressions()
    texte = f" {transcription_normalisee} "
    return any(f" {e} " in texte for e in expressions)


def sans_contenu(transcription: str) -> bool:
    """Silence ou inaudible (§5.4) : l'annonce de l'agent ne compte pas comme contenu."""
    return sum(c.isalpha() for c in paroles_appelant(transcription)) < LETTRES_MIN


@dataclass
class Qualification:
    """Résultat de qualification (§5.1), plus la trace pour les métriques (sans contenu)."""

    categorie: Categorie
    confiance: float
    categorie_modele: Categorie | None = None
    regle: RegleServeur | None = None
    securite: bool = False
    sortie: SortieQualification | None = None
    jetons_entree: int = 0
    jetons_sortie: int = 0
    cout_micro_eur: int = 0
    duree_ms: int = 0
    detournement_annote: bool = False  # annotation du filtre d'Azure (D-65, D-75)


@dataclass
class Traitement:
    """Issue d'un appel : un dossier, un message, ou une trace sans contenu ; jamais deux."""

    qualification: Qualification | None
    extraction: Extraction | None = None
    message: MessageRecu | None = None
    trace: TraceSansContenu | None = None
    garde_fous: set[GardeFouSortie] = field(default_factory=set)  # du message (étape 7)


def qualifier(
    transcription: str,
    paquet: Paquet,
    fournisseur: FournisseurLLM,
    date_reference: str,
    metier: str,
    numero_presente: str | None = None,
    motifs_entree: tuple[str, ...] = (),
) -> Qualification:
    """Classe une transcription déjà contrôlée ; lève `ContenuRefuse` si le filtre la bloque."""
    parametres = paquet.parametres
    debut = time.perf_counter()
    q = Qualification(categorie="indetermine", confiance=0.0)
    try:
        reponse = fournisseur.completer(
            RequeteChat(
                modele=str(parametres["modele"]),
                messages=[
                    {"role": "system", "content": paquet.consigne},
                    {
                        "role": "user",
                        "content": paquet.message_utilisateur(
                            transcription, date_reference, metier, numero_presente
                        ),
                    },
                ],
                schema_sortie=paquet.schema_sortie,
                max_jetons_sortie=int(parametres["max_jetons_sortie"]),
                delai_s=float(parametres["delai_llm_s"]),
            )
        )
        q.jetons_entree, q.jetons_sortie = reponse.jetons_entree, reponse.jetons_sortie
        q.cout_micro_eur = reponse.cout_micro_eur
        q.detournement_annote = reponse.detournement_detecte
        if reponse.refus_modele is not None:
            raise ValueError("refus du modèle")
        q.sortie = SortieQualification.model_validate_json(reponse.contenu or "")
    except RefusContenu:
        # D-73 : un blocage du filtre sur la qualification ne refuse pas l'appel ; dans le doute,
        # un dossier « à vérifier ». Le refus poli ne vient que si l'extraction est bloquée aussi.
        q.regle = "filtre"
    except (DelaiDepasse, ErreurFournisseur):
        q.regle = "modele_indisponible"
    except (ValidationError, ValueError):
        q.regle = "sortie_invalide"

    normalisee = normaliser(transcription)
    if q.sortie is not None:
        q.categorie_modele = q.categorie = q.sortie.categorie
        q.confiance = q.sortie.confiance
        if q.confiance < float(parametres["seuil_confiance"]):
            q.categorie, q.regle = "indetermine", "seuil"
        elif q.categorie in ("personnel", "autre") and contient_besoin(normalisee):
            q.categorie, q.regle = "indetermine", "retrogradation"
        elif q.categorie in ("personnel", "autre") and (motifs_entree or q.detournement_annote):
            q.categorie, q.regle = "indetermine", "detournement"
    q.securite = detecter_gaz(normalisee)
    q.duree_ms = round((time.perf_counter() - debut) * 1000)
    return q


def numero_valide(numero: str | None) -> str | None:
    return numero if numero and MOTIF_TELEPHONE.match(numero) else None


def dit_dans(valeur: str | None, transcription_normalisee: str) -> str | None:
    """Garde une valeur seulement si elle a été dite (jamais déduite, §5.2)."""
    if not valeur or not normaliser(valeur):
        return None
    return valeur.strip() if f" {normaliser(valeur)} " in f" {transcription_normalisee} " else None


def construire_message(
    q: Qualification,
    transcription: str,
    paquet: Paquet,
    numero_presente: str | None,
    recu_le: datetime,
) -> tuple[MessageRecu, set[GardeFouSortie]]:
    """Message pour `fournisseur`, `personnel` et `autre` ; règles du serveur, pas du modèle.
    Garde-fous de sortie (étape 7) sur chaque texte : fuite, hors rôle."""
    sortie = q.sortie
    if sortie is None or q.categorie not in CATEGORIES_MESSAGE:
        raise ValueError("un message suppose une catégorie fournisseur, personnel ou autre")
    normalisee = normaliser(transcription)
    presente = numero_valide(numero_presente)
    dicte = sortie.numero_dicte
    if dicte is None or not MOTIF_TELEPHONE.match(dicte) or dicte == presente:
        dicte = None
    declenches: set[GardeFouSortie] = set()

    def propre(valeur: str | None) -> str | None:
        if valeur is None:
            return None
        resultat, g = assainir(valeur)
        declenches.update(g)
        return resultat

    texte = propre((sortie.message or "").strip())
    if texte is None and "fuite" in declenches:
        texte = MESSAGE_RETIRE
    texte = (texte or "")[:LONGUEUR_MESSAGE]
    if contient_sante(texte):
        texte = MESSAGE_SANTE
    message = MessageRecu(
        categorie=q.categorie,  # type: ignore[arg-type]  # vérifié ci-dessus
        nom_appelant=propre(dit_dans(sortie.nom_appelant, normalisee)),
        societe=(
            propre(dit_dans(sortie.societe, normalisee)) if q.categorie != "personnel" else None
        ),
        numero_rappel=presente,
        numero_dicte=dicte,
        message=texte,
        rappel_souhaite=sortie.rappel_souhaite,
        securite=q.securite,
        recu_le=recu_le,
        prompt_version=paquet.prompt_version,
    )
    return message, declenches


def traiter_appel(
    transcription: str,
    paquet_qualification: Paquet,
    paquet_extraction: Paquet,
    fournisseur: FournisseurLLM,
    referentiels: Referentiels,
    metier: Metier,
    date_reference: str,
    numero_presente: str | None = None,
    request_id: str = "",
    maintenant: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Traitement:
    """Qualifie l'appel, puis produit un dossier, un message ou une trace sans contenu."""
    controle = None
    try:
        controle = controler(transcription)
        if controle.refus == "entree_vide" or (
            controle.refus is None and sans_contenu(controle.texte)
        ):
            traitement = Traitement(
                qualification=None,
                trace=TraceSansContenu(
                    numero_presente=numero_valide(numero_presente),
                    recu_le=maintenant(),
                    motif="sans_contenu",
                ),
            )
        elif controle.refus is not None:
            raise EntreeRefusee(controle.refus, controle.message_refus or "")
        else:
            q = qualifier(
                controle.texte,
                paquet_qualification,
                fournisseur,
                date_reference,
                metier,
                numero_presente,
                tuple(controle.motifs),
            )
            traitement = Traitement(qualification=q)
            if q.categorie in CATEGORIES_MESSAGE:
                traitement.message, traitement.garde_fous = construire_message(
                    q, controle.texte, paquet_qualification, numero_presente, maintenant()
                )
            else:
                x = extraire_dossier(
                    controle.texte,
                    paquet_extraction,
                    fournisseur,
                    referentiels,
                    metier,
                    date_reference,
                    numero_presente,
                    request_id=request_id,
                )
                if q.categorie == "indetermine":
                    e = x.enveloppe
                    x.enveloppe = e.model_copy(
                        update={
                            "a_verifier": True,
                            "motifs": [*e.motifs, "qualification_indeterminee"],
                        }
                    )
                traitement.extraction = x
    except (EntreeRefusee, ContenuRefuse) as refus:
        code = refus.code if isinstance(refus, EntreeRefusee) else "content_refused"
        journal.warning("qualification.refus request_id=%s code=%s", request_id, code)
        raise
    finally:
        del transcription, controle  # plus aucune référence locale au texte reçu (R3)

    qual = traitement.qualification
    journal.info(
        "qualification.fin request_id=%s issue=%s categorie=%s categorie_modele=%s confiance=%s "
        "regle=%s securite=%s garde_fous=%s jetons=%s cout_micro_eur=%s duree_ms=%s",
        request_id,
        "trace" if traitement.trace else "message" if traitement.message else "dossier",
        qual.categorie if qual else "aucune",
        (qual.categorie_modele or "aucune") if qual else "aucune",
        round(qual.confiance, 2) if qual else 0,
        (qual.regle or "aucune") if qual else "aucune",
        qual.securite if qual else False,
        ",".join(sorted(traitement.garde_fous)) or "aucun",
        (qual.jetons_entree + qual.jetons_sortie) if qual else 0,
        qual.cout_micro_eur if qual else 0,
        qual.duree_ms if qual else 0,
    )
    return traitement
