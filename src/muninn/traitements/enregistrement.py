"""Enregistrement de chaque appel traité (sprint 5, étape 1 ; D-82, D-85).

Une ligne par appel dans `app.traitements` : ses mesures, sans contenu (catégorie, statut, motifs,
garde-fous, outils, jetons, coût, durée). Le brouillon et son enveloppe (`app.dossiers`), ou le
message (`app.messages`), seulement pour un scénario du jeu synthétique (D-82) : un texte libre
peut contenir de vraies données personnelles, il n'en laisse que la ligne de mesures. Jamais la
transcription, jamais l'audio.

Règles :
- sans `DATABASE_URL_TRAITEMENTS`, rien n'est enregistré ; l'appel est traité quand même ;
- une panne de la base ne fait jamais échouer un appel : un avertissement sans contenu est
  journalisé (`traitements.echec`) ;
- conservation de 30 jours (D-82) : les traitements plus anciens sont purgés au plus une fois par
  heure par processus, et par la commande `muninn-purge`.
"""

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import timedelta
from functools import lru_cache
from typing import Literal

from sqlalchemy import Engine, text

from muninn.core.config import get_settings
from muninn.db.connexion import creer_moteur
from muninn.extraction.evaluateur import Extraction
from muninn.qualification.qualificateur import Traitement

journal = logging.getLogger(__name__)

CONSERVATION = timedelta(days=30)
PURGE_TOUTES_LES_S = 3600

Route = Literal["demo", "extraction"]


@dataclass
class Enregistrement:
    """Ce qui est gardé d'un appel ; rien de ce que l'appelant a dit, hors du dossier lui-même."""

    request_id: str
    route: Route
    duree_ms: int
    scenario_id: str | None = None
    modele_simule: bool = False
    # Vrai seulement pour un scénario du jeu synthétique : lui seul laisse son contenu en base.
    contenu_synthetique: bool = False
    code_refus: str | None = None
    traitement: Traitement | None = None
    extraction: Extraction | None = None
    garde_fous_message: list[str] = field(default_factory=list)


@lru_cache
def moteur() -> Engine | None:
    """Moteur du rôle des traitements, ou rien si `DATABASE_URL_TRAITEMENTS` manque."""
    url = get_settings().database_url_traitements
    if url is None:
        return None
    return creer_moteur(url.get_secret_value())


_derniere_purge = 0.0


def ligne(e: Enregistrement) -> dict[str, object]:
    """Les mesures de l'appel, prêtes pour `app.traitements`."""
    t, x = e.traitement, e.extraction or (e.traitement.extraction if e.traitement else None)
    q = t.qualification if t else None
    agent = x.agent if x else None
    issue = (
        "refus"
        if e.code_refus
        else "trace"
        if t and t.trace
        else "message"
        if t and t.message
        else "dossier"
    )
    garde_fous = sorted({str(g) for g in (x.enveloppe.garde_fous if x else [])}
                        | set(e.garde_fous_message))  # fmt: skip
    return {
        "request_id": e.request_id,
        "route": e.route,
        "scenario_id": e.scenario_id,
        "modele_simule": e.modele_simule,
        "issue": issue,
        "code_refus": e.code_refus,
        "categorie": q.categorie if q else None,
        "regle": q.regle if q else None,
        "securite": bool(q and q.securite),
        "statut": x.brouillon.provenance.extraction_status if x else None,
        "a_verifier": x.enveloppe.a_verifier if x else None,
        "motifs": [str(m) for m in x.enveloppe.motifs] if x else [],
        "garde_fous": garde_fous,
        "outils": len(agent.appels_outils) if agent else 0,
        "borne": bool(agent and agent.borne_atteinte),
        "tentatives": agent.tentatives if agent else None,
        "urgence": x.brouillon.demande.urgence if x else None,
        "urgence_serveur": bool(x and "demande.urgence" in x.enveloppe.provenance),
        "commune_statut": x.brouillon.checks.commune.status if x else None,
        "code_postal_statut": x.brouillon.checks.code_postal.status if x else None,
        "jetons": (q.jetons_entree + q.jetons_sortie if q else 0)
        + (agent.jetons_entree + agent.jetons_sortie if agent else 0),
        "cout_micro_eur": (q.cout_micro_eur if q else 0) + (agent.cout_micro_eur if agent else 0),
        "duree_ms": e.duree_ms,
        "duree_extraction_ms": x.duree_ms if x else None,
    }


INSERER_TRAITEMENT = text(
    "INSERT INTO app.traitements (request_id, route, scenario_id, modele_simule, issue,"
    " code_refus, categorie, regle, securite, statut, a_verifier, motifs, garde_fous, outils,"
    " borne, tentatives, urgence, urgence_serveur, commune_statut, code_postal_statut, jetons,"
    " cout_micro_eur, duree_ms, duree_extraction_ms)"
    " VALUES (:request_id, :route, :scenario_id, :modele_simule, :issue,"
    " :code_refus, :categorie, :regle, :securite, :statut, :a_verifier, :motifs, :garde_fous,"
    " :outils, :borne, :tentatives, :urgence, :urgence_serveur, :commune_statut,"
    " :code_postal_statut, :jetons, :cout_micro_eur, :duree_ms, :duree_extraction_ms)"
)
INSERER_DOSSIER = text(
    "INSERT INTO app.dossiers (draft_id, request_id, brouillon, enveloppe)"
    " VALUES (:draft_id, :request_id, CAST(:brouillon AS jsonb), CAST(:enveloppe AS jsonb))"
)
INSERER_MESSAGE = text(
    "INSERT INTO app.messages (message_id, request_id, message)"
    " VALUES (:message_id, :request_id, CAST(:message AS jsonb))"
)
PURGER = text("DELETE FROM app.traitements WHERE recu_le < now() - make_interval(days => :jours)")


def enregistrer(e: Enregistrement) -> bool:
    """Enregistre l'appel ; rend vrai si c'est fait. Ne lève jamais d'exception."""
    m = moteur()
    if m is None:
        return False
    x = e.extraction or (e.traitement.extraction if e.traitement else None)
    message = e.traitement.message if e.traitement else None
    try:
        with m.begin() as conn:
            conn.execute(INSERER_TRAITEMENT, ligne(e))
            if e.contenu_synthetique and x is not None and not e.code_refus:
                conn.execute(INSERER_DOSSIER, {
                    "draft_id": str(x.brouillon.draft_id), "request_id": e.request_id,
                    "brouillon": x.brouillon.model_dump_json(by_alias=True),
                    "enveloppe": x.enveloppe.model_dump_json(),
                })  # fmt: skip
            elif e.contenu_synthetique and message is not None:
                conn.execute(INSERER_MESSAGE, {
                    "message_id": str(message.message_id), "request_id": e.request_id,
                    "message": message.model_dump_json(),
                })  # fmt: skip
        purger_si_besoin(m)
        return True
    except Exception as erreur:  # noqa: BLE001 : jamais d'échec de l'appel à cause de la base
        journal.warning(
            "traitements.echec request_id=%s erreur=%s", e.request_id, type(erreur).__name__
        )
        return False


def purger(m: Engine, conservation: timedelta = CONSERVATION) -> int:
    """Supprime les traitements plus anciens que la durée de conservation ; rend leur nombre."""
    with m.begin() as conn:
        resultat = conn.execute(PURGER, {"jours": conservation.days})
    return int(resultat.rowcount or 0)


def purger_si_besoin(m: Engine) -> None:
    global _derniere_purge
    if time.monotonic() - _derniere_purge < PURGE_TOUTES_LES_S:
        return
    _derniere_purge = time.monotonic()
    supprimes = purger(m)
    if supprimes:
        journal.info("traitements.purge supprimes=%s", supprimes)


def main() -> int:
    """Commande `muninn-purge` : purge à la demande ; rend le nombre de traitements supprimés."""
    m = moteur()
    if m is None:
        print("DATABASE_URL_TRAITEMENTS n'est pas définie", file=sys.stderr)
        return 2
    print(json.dumps({"supprimes": purger(m), "conservation_jours": CONSERVATION.days}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
