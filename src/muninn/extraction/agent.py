"""L'agent d'extraction : une boucle bornée, écrite dans le projet, sans framework (D-37, A-1).

Le modèle lit la transcription et décide lui-même quand appeler ses deux outils. Le code fixe
tout le reste :
- six appels d'outils au plus ; au-delà, l'appel n'est pas exécuté et le modèle doit conclure
  sans outil ;
- un délai par appel au modèle et par appel d'outil ;
- une relance unique quand la sortie ne respecte pas le schéma, puis un brouillon partiel
  (contrat, règle 6 : `partial_after_retry`) ;
- un modèle indisponible donne un brouillon de secours (D-29 : `fallback_no_llm`) ;
- un refus du filtre de contenu est rapporté comme tel (garde-fou, D-65) : jamais confondu avec
  une panne.

L'agent ne fixe ni statut de contrôle ni provenance : c'est l'évaluateur du serveur (étape 4) qui
le fait, à partir de `ResultatAgent`. Rien de la transcription n'est journalisé (R3, R4).
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Literal

from pydantic import ValidationError

from muninn.extraction.contrat import SortieLLM
from muninn.extraction.outils import CommuneRendue, Referentiels, ResultatOutil, executer_outil
from muninn.extraction.paquet import Paquet
from muninn.llm.fournisseur import (
    DelaiDepasse,
    ErreurFournisseur,
    FournisseurLLM,
    RefusContenu,
    ReponseChat,
    RequeteChat,
    message_outil,
)

journal = logging.getLogger(__name__)

Statut = Literal["complete", "partial_after_retry", "fallback_no_llm", "content_refused"]
BORNE_ATTEINTE = json.dumps({"erreur": "borne d'appels atteinte : conclus sans outil"})
RELANCE = (
    "Ta réponse ne respecte pas le schéma demandé. Champs en cause : {champs}. "
    "Rends uniquement le JSON conforme au schéma, sans texte autour."
)


@dataclass
class ResultatAgent:
    """Ce que l'agent remet à l'évaluateur du serveur : la sortie et sa trace, sans contenu."""

    statut: Statut
    sortie: SortieLLM | None
    tentatives: int
    appels_outils: list[ResultatOutil] = field(default_factory=list)
    borne_atteinte: bool = False
    detournement_detecte: bool = False
    jetons_entree: int = 0
    jetons_sortie: int = 0
    cout_micro_eur: int = 0
    duree_ms: int = 0
    etapes: int = 0

    @property
    def communes_rendues(self) -> list[CommuneRendue]:
        return [c for r in self.appels_outils for c in r.communes]

    @property
    def termes_rendus(self) -> list[str]:
        return [r.terme for r in self.appels_outils if r.terme]


def normaliser_sortie(donnees: object) -> object:
    """Corrections bénignes avant validation : une valeur nulle a une confiance de 0 et, pour le
    téléphone, une origine nulle (contrat, règle 1). Ne crée, ne modifie ni ne supprime jamais une
    valeur : tout le reste du contrat est validé strictement (M-05)."""

    def corriger(noeud: object) -> None:
        if isinstance(noeud, dict):
            if "value" in noeud and "confidence" in noeud and noeud["value"] is None:
                noeud["confidence"] = 0
                if "origin" in noeud:
                    noeud["origin"] = None
            for valeur in noeud.values():
                corriger(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                corriger(valeur)

    corriger(donnees)
    return donnees


def _champs_en_erreur(erreur: ValidationError | ValueError) -> str:
    """Chemins des champs fautifs, jamais leur valeur (contrat d'API, format d'erreur)."""
    if isinstance(erreur, ValidationError):
        chemins = sorted({".".join(str(p) for p in e["loc"]) or "racine" for e in erreur.errors()})
        return ", ".join(chemins[:10])
    return "JSON illisible"


def extraire(
    transcription: str,
    paquet: Paquet,
    fournisseur: FournisseurLLM,
    referentiels: Referentiels,
    date_reference: str,
    metier: str,
    numero_presente: str | None = None,
) -> ResultatAgent:
    """Fait tourner l'agent sur une transcription ; ne lève pas d'exception du fournisseur."""
    parametres = paquet.parametres
    max_outils = int(parametres["max_appels_outils"])
    relances = int(parametres["relances_validation"])
    resultat = ResultatAgent(statut="fallback_no_llm", sortie=None, tentatives=0)
    messages: list[dict[str, object]] = [
        {"role": "system", "content": paquet.consigne},
        {
            "role": "user",
            "content": paquet.message_utilisateur(
                transcription, date_reference, metier, numero_presente
            ),
        },
    ]
    debut = time.perf_counter()

    def etape(avec_outils: bool) -> ReponseChat:
        reponse = fournisseur.completer(
            RequeteChat(
                modele=str(parametres["modele"]),
                messages=list(messages),
                outils=paquet.outils if avec_outils else None,
                schema_sortie=paquet.schema_sortie,
                max_jetons_sortie=int(parametres["max_jetons_sortie"]),
                delai_s=float(parametres["delai_llm_s"]),
            )
        )
        resultat.etapes += 1
        resultat.jetons_entree += reponse.jetons_entree
        resultat.jetons_sortie += reponse.jetons_sortie
        resultat.cout_micro_eur += reponse.cout_micro_eur
        resultat.detournement_detecte |= reponse.detournement_detecte
        return reponse

    try:
        avec_outils = True
        # Borne de sécurité sur la boucle : six outils, une conclusion forcée, une relance.
        for _ in range(max_outils + relances + 2):
            reponse = etape(avec_outils)
            if reponse.appels_outils:
                messages.append(reponse.message_assistant())
                for appel in reponse.appels_outils:
                    if len(resultat.appels_outils) >= max_outils:
                        resultat.borne_atteinte = True
                        messages.append(
                            message_outil(
                                appel,
                                BORNE_ATTEINTE,
                            )
                        )
                        continue
                    sortie_outil = executer_outil(referentiels, appel.nom, appel.arguments)
                    resultat.appels_outils.append(sortie_outil)
                    messages.append(message_outil(appel, sortie_outil.contenu))
                avec_outils = not resultat.borne_atteinte
                continue

            resultat.tentatives += 1
            try:
                if reponse.refus_modele is not None:
                    raise ValueError("refus du modèle")
                resultat.sortie = SortieLLM.model_validate(
                    normaliser_sortie(json.loads(reponse.contenu or ""))
                )
                resultat.statut = "complete"
                break
            except (ValidationError, ValueError) as erreur:
                journal.warning("agent.sortie_hors_schema tentative=%s", resultat.tentatives)
                if resultat.tentatives > relances:
                    resultat.statut = "partial_after_retry"
                    break
                messages.append({"role": "assistant", "content": reponse.contenu or ""})
                messages.append(
                    {"role": "user", "content": RELANCE.format(champs=_champs_en_erreur(erreur))}
                )
                avec_outils = False
        else:
            resultat.statut = "partial_after_retry"
    except RefusContenu:
        resultat.statut = "content_refused"
    except (DelaiDepasse, ErreurFournisseur):
        resultat.statut = "fallback_no_llm"

    resultat.duree_ms = round((time.perf_counter() - debut) * 1000)
    journal.info(
        "agent.fin statut=%s tentatives=%s etapes=%s outils=%s borne=%s detournement=%s "
        "jetons_entree=%s jetons_sortie=%s cout_micro_eur=%s duree_ms=%s",
        resultat.statut,
        resultat.tentatives,
        resultat.etapes,
        ",".join(r.nom for r in resultat.appels_outils) or "aucun",
        resultat.borne_atteinte,
        resultat.detournement_detecte,
        resultat.jetons_entree,
        resultat.jetons_sortie,
        resultat.cout_micro_eur,
        resultat.duree_ms,
    )
    return resultat
