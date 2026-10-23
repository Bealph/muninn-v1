"""Routes de l'agent : extraction d'un texte et parcours de démonstration (étape 8, D-62).

- `POST /v1/extract/text` : extraction seule (contrat d'API, § 4.8) ; brouillon, enveloppe
  (D-67) et mesures de l'exécution.
- `POST /v1/demo/runs` : parcours complet de l'écran « Agent » (contrat, § 4.9, adapté à la V1) :
  qualification, puis dossier, message ou trace sans contenu ; appels d'outils et garde-fous.
  Brouillon en clair sur données synthétiques (écart P-03, D-07) ; rien n'est stocké.

Écarts V1, dits : pas de jeton de service (points publics de démonstration, bornés par la limite
de débit, comme les référentiels, D-57) ; pas de webhook simulé ni de `field_diffs` (V-09,
sprint 5).
Les outils de l'agent appellent l'API des référentiels de la même application, par HTTP, avec le
délai du paquet (`delai_outil_s`) : l'agent n'a accès à aucune base (D-18).
"""

import logging
import os
import time
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError

from muninn.api.dependances import get_fournisseur, get_limiteur
from muninn.api.erreurs import DetailErreur, Erreur, ErreurAPI, identifiant
from muninn.api.limites import LimiteurDebit
from muninn.demo import PERIMETRE, charger_scenarios, fournisseur_perimetre
from muninn.demo.verification import verifier
from muninn.extraction.agent import ResultatAgent
from muninn.extraction.contrat import MOTIF_TELEPHONE, DossierDraft, Metier
from muninn.extraction.entree import LONGUEUR_MAX
from muninn.extraction.evaluateur import (
    ContenuRefuse,
    EntreeRefusee,
    Enveloppe,
    Extraction,
    extraire_dossier,
)
from muninn.extraction.outils import ClientReferentiels, Referentiels
from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import FournisseurLLM
from muninn.qualification.contrat import Categorie, MessageRecu, RegleServeur, TraceSansContenu
from muninn.qualification.qualificateur import charger_paquet_qualification, traiter_appel
from muninn.telemetrie import Etape, collecte, etape
from muninn.traitements.enregistrement import Enregistrement, enregistrer, moteur
from muninn.traitements.metriques import FENETRES_HEURES, Metriques, calculer
from muninn.traitements.revue import (
    CorrectionInvalide,
    DejaValide,
    DemandeRevue,
    DossierInconnu,
    reviser,
)

routeur = APIRouter(tags=["agent"])
NumeroE164 = Annotated[str, Field(pattern=MOTIF_TELEPHONE.pattern)]
ERREURS = {
    422: {"model": Erreur, "description": "Requête invalide, contenu refusé ou inexploitable"},
    429: {"model": Erreur, "description": "Limite de débit atteinte"},
}


# --- Dépendances (remplacées dans les tests) ---------------------------------------------------


@lru_cache
def get_referentiels() -> Referentiels:
    """L'API des référentiels de la même application, par HTTP (D-18)."""
    url = os.environ.get("REFERENTIELS_URL") or f"http://127.0.0.1:{os.environ.get('PORT', '8000')}"
    delai = float(charger_paquet().parametres["delai_outil_s"])
    return ClientReferentiels(url, delai_s=delai)


def reserver(limiteur: Annotated[LimiteurDebit, Depends(get_limiteur)]) -> None:
    """Chaque exécution appelle le modèle plusieurs fois : une réservation par exécution."""
    attente = limiteur.reserver()
    if attente is not None:
        raise ErreurAPI(429, "rate_limited", retry_after_s=attente)


# --- Contrats des réponses -------------------------------------------------------------------


class Mesures(BaseModel):
    """`RunMetrics` du contrat (§ 4.8), sans contenu."""

    status: str
    validation_attempts: int
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_micro_eur: int
    reference_check: Literal["ok", "flagged", "unchecked", "not_applicable"]
    fields_to_review_count: int


class ReponseExtraction(BaseModel):
    draft: DossierDraft
    envelope: Enveloppe
    run: Mesures


class DemandeExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=LONGUEUR_MAX)
    trade: Metier = "plomberie"
    caller_number: NumeroE164 | None = None
    input_mode: Literal["text", "simulated"] = "text"
    reference_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class AppelOutilVu(BaseModel):
    """Un appel d'outil vu à l'écran : nom, statut, durée, données publiques rendues."""

    nom: str
    statut: str
    duree_ms: int
    communes: list[str]
    terme: str | None


class QualificationVue(BaseModel):
    categorie: Categorie
    categorie_modele: Categorie | None
    confiance: float
    regle: RegleServeur | None
    securite: bool
    cost_micro_eur: int


class DemandeDemo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["scenario", "transcript"]
    scenario_id: str | None = Field(default=None, max_length=40)
    transcript: str | None = Field(default=None, max_length=LONGUEUR_MAX)
    trade: Metier = "plomberie"
    caller_number: NumeroE164 | None = None


class Conformite(BaseModel):
    """Verdict du scénario par les vérifications des essais (`muninn.demo.verification`)."""

    compliant: bool
    gaps: list[str]


class EtapeVue(BaseModel):
    """Une étape de l'appel, dans l'ordre, avec sa durée ; codes et nombres seulement."""

    nom: str
    debut_ms: int
    duree_ms: int
    statut: str
    niveau: int
    details: dict[str, str | int | float | bool]


def etapes_vues(etapes: list[Etape]) -> list[EtapeVue]:
    return [EtapeVue(**vars(e)) for e in sorted(etapes, key=lambda e: (e.debut_ms, e.niveau))]


class ReponseDemo(BaseModel):
    """`DemoRunResponse` adapté à la V1 : la qualification et l'issue en plus ; pas de
    `field_diffs` (V-09) ; `expected` rappelle l'attendu du scénario, pour comparaison à l'œil."""

    request_id: str
    scenario_id: str | None
    simulated_model: bool
    issue: Literal["dossier", "message", "trace"]
    qualification: QualificationVue | None
    draft: DossierDraft | None
    envelope: Enveloppe | None
    message: MessageRecu | None
    trace: TraceSansContenu | None
    tool_calls: list[AppelOutilVu]
    tool_limit_reached: bool
    guardrails: list[str]
    run: Mesures | None
    expected: dict[str, object] | None
    conformity: Conformite | None
    latency_ms: int
    # Le dossier est enregistré : il peut être corrigé et validé (V-09, CA-5).
    review_available: bool = False
    # Étapes de l'appel, dans l'ordre, avec leurs durées mesurées (écran « Démonstration »).
    steps: list[EtapeVue] = Field(default_factory=list)
    plaintext_draft_notice: Literal["P-03"] = "P-03"


class ReponseRevue(BaseModel):
    """Le dossier validé, contrôles rejoués par le serveur (V-09, CA-5, D-86)."""

    draft: DossierDraft
    envelope: Enveloppe
    state: Literal["validated"] = "validated"
    reviewed_at: datetime
    corrected_fields: list[str]
    plaintext_draft_notice: Literal["P-03"] = "P-03"


# --- Mise en forme -----------------------------------------------------------------------------


def mesures(x: Extraction, latence_ms: int) -> Mesures:
    agent: ResultatAgent | None = x.agent
    controles = x.brouillon.checks
    statuts = {controles.commune.status, controles.code_postal.status}
    return Mesures(
        status=x.brouillon.provenance.extraction_status,
        validation_attempts=x.brouillon.provenance.validation_attempts,
        latency_ms=latence_ms,
        input_tokens=agent.jetons_entree if agent else 0,
        output_tokens=agent.jetons_sortie if agent else 0,
        cost_micro_eur=agent.cout_micro_eur if agent else 0,
        reference_check=(
            "flagged"
            if "mismatch" in statuts
            else "unchecked"
            if "not_checked" in statuts
            else "ok"
        ),
        fields_to_review_count=len(x.brouillon.champs_manquants),
    )


def appels_vus(x: Extraction | None) -> list[AppelOutilVu]:
    if x is None or x.agent is None:
        return []
    return [
        AppelOutilVu(
            nom=a.nom,
            statut=a.statut,
            duree_ms=a.duree_ms,
            communes=[
                f"{c.nom} ({c.departement}, {', '.join(c.codes_postaux)})" for c in a.communes
            ],
            terme=a.terme,
        )
        for a in x.agent.appels_outils
    ]


def aujourd_hui() -> str:
    return datetime.now(UTC).date().isoformat()


# --- Routes ------------------------------------------------------------------------------------


class ScenarioVu(BaseModel):
    id: str
    groupe: Literal["annexe_a", "qualification", "perimetre"]
    libelle: str


class ListeScenarios(BaseModel):
    scenarios: list[ScenarioVu]


@routeur.get("/v1/demo/scenarios", response_model=ListeScenarios)
def lister_scenarios() -> ListeScenarios:
    """Scénarios de l'écran « Agent » : identifiant, groupe et libellé, sans la transcription."""
    return ListeScenarios(
        scenarios=[
            ScenarioVu(id=s.id, groupe=s.groupe, libelle=s.libelle)  # type: ignore[arg-type]
            for s in charger_scenarios().values()
        ]
    )


@routeur.post(
    "/v1/extract/text",
    response_model=ReponseExtraction,
    responses=ERREURS,  # type: ignore[arg-type]
    dependencies=[Depends(reserver)],
)
def extraire_texte(
    corps: DemandeExtraction,
    request: Request,
    fournisseur: Annotated[FournisseurLLM, Depends(get_fournisseur)],
    referentiels: Annotated[Referentiels, Depends(get_referentiels)],
) -> ReponseExtraction:
    """Extraction d'un brouillon de dossier depuis un texte (sans qualification)."""
    debut = time.perf_counter()

    def refuser(code: str) -> None:
        duree = round((time.perf_counter() - debut) * 1000)
        enregistrer(Enregistrement(identifiant(request), "extraction", duree, code_refus=code))

    try:
        x = extraire_dossier(
            corps.text, charger_paquet(), fournisseur, referentiels, corps.trade,
            corps.reference_date or aujourd_hui(), corps.caller_number, corps.input_mode,
            request_id=identifiant(request),
        )  # fmt: skip
    except ContenuRefuse as refus:
        refuser("content_refused")
        raise ErreurAPI(422, "content_refused") from refus
    except EntreeRefusee as refus:
        if refus.code == "entree_vide":
            refuser("content_unprocessable")
            raise ErreurAPI(422, "content_unprocessable") from refus
        refuser("too_long")
        detail = DetailErreur(field="body.text", issue="too_long")
        raise ErreurAPI(422, "validation_failed", [detail]) from refus
    latence = round((time.perf_counter() - debut) * 1000)
    enregistrer(Enregistrement(identifiant(request), "extraction", latence, extraction=x))
    return ReponseExtraction(draft=x.brouillon, envelope=x.enveloppe, run=mesures(x, latence))


@routeur.post(
    "/v1/demo/runs",
    response_model=ReponseDemo,
    responses={**ERREURS, 404: {"model": Erreur, "description": "Scénario inconnu"}},  # type: ignore[dict-item]
    dependencies=[Depends(reserver)],
)
def executer_demo(
    corps: DemandeDemo,
    request: Request,
    fournisseur: Annotated[FournisseurLLM, Depends(get_fournisseur)],
    referentiels: Annotated[Referentiels, Depends(get_referentiels)],
) -> ReponseDemo:
    """Parcours de l'écran « Agent » : un scénario du jeu synthétique, ou une transcription."""
    debut = time.perf_counter()
    scenario = None
    if corps.mode == "scenario":
        scenario = charger_scenarios().get(corps.scenario_id or "")
        if scenario is None:
            detail = DetailErreur(field="body.scenario_id", issue="not_allowed")
            raise ErreurAPI(404, "scenario_not_found", [detail])
        texte, metier, numero = scenario.transcription, scenario.metier, scenario.numero_presente
        if scenario.id == PERIMETRE:
            fournisseur = fournisseur_perimetre()
    else:
        if not corps.transcript:
            detail = DetailErreur(field="body.transcript", issue="required")
            raise ErreurAPI(422, "validation_failed", [detail])
        texte, metier, numero = corps.transcript, corps.trade, corps.caller_number
    try:
        with collecte() as etapes, etape(
            "appel", route="demo", request_id=identifiant(request),
            scenario_id=scenario.id if scenario else None,
        ) as racine:  # fmt: skip
            t = traiter_appel(
                texte, charger_paquet_qualification(), charger_paquet(), fournisseur, referentiels,
                metier, aujourd_hui(), numero, request_id=identifiant(request),  # type: ignore[arg-type]
            )  # fmt: skip
            racine["issue"] = "trace" if t.trace else "message" if t.message else "dossier"
    except (ContenuRefuse, EntreeRefusee) as refus:
        code = "content_refused" if isinstance(refus, ContenuRefuse) else "too_long"
        enregistrer(Enregistrement(
            identifiant(request), "demo", round((time.perf_counter() - debut) * 1000),
            scenario_id=scenario.id if scenario else None,
            modele_simule=bool(scenario and scenario.modele_simule), code_refus=code,
        ))  # fmt: skip
        if isinstance(refus, ContenuRefuse):
            raise ErreurAPI(422, "content_refused") from refus
        detail = DetailErreur(field="body.transcript", issue="too_long")
        raise ErreurAPI(422, "validation_failed", [detail]) from refus
    del texte
    latence = round((time.perf_counter() - debut) * 1000)
    stocke = enregistrer(Enregistrement(
        identifiant(request), "demo", latence,
        scenario_id=scenario.id if scenario else None,
        modele_simule=bool(scenario and scenario.modele_simule),
        contenu_synthetique=scenario is not None,
        traitement=t, garde_fous_message=sorted(str(g) for g in t.garde_fous),
    ))  # fmt: skip
    q, x = t.qualification, t.extraction
    ecarts = verifier(scenario.groupe, scenario.id, scenario.attendu, t) if scenario else []
    gardes: list[str] = sorted(
        {str(g) for g in (x.enveloppe.garde_fous if x else [])} | t.garde_fous
    )
    return ReponseDemo(
        request_id=identifiant(request),
        scenario_id=scenario.id if scenario else None,
        simulated_model=bool(scenario and scenario.modele_simule),
        issue="trace" if t.trace else "message" if t.message else "dossier",
        qualification=QualificationVue(
            categorie=q.categorie,
            categorie_modele=q.categorie_modele,
            confiance=q.confiance,
            regle=q.regle,
            securite=q.securite,
            cost_micro_eur=q.cout_micro_eur,
        )
        if q
        else None,  # fmt: skip
        draft=x.brouillon if x else None,
        envelope=x.enveloppe if x else None,
        message=t.message,
        trace=t.trace,
        tool_calls=appels_vus(x),
        tool_limit_reached=bool(x and x.agent and x.agent.borne_atteinte),
        guardrails=gardes,
        run=mesures(x, latence) if x else None,
        expected=scenario.attendu if scenario else None,
        conformity=Conformite(compliant=not ecarts, gaps=ecarts) if scenario else None,
        latency_ms=latence,
        review_available=bool(stocke and scenario and x),
        steps=etapes_vues(etapes),
    )


@routeur.post(
    "/v1/demo/runs/{draft_id}/review",
    response_model=ReponseRevue,
    responses={
        **ERREURS,  # type: ignore[dict-item]
        404: {"model": Erreur, "description": "Dossier inconnu, ou purgé"},
        409: {"model": Erreur, "description": "Dossier déjà validé"},
        503: {"model": Erreur, "description": "Enregistrement des traitements indisponible"},
    },
    dependencies=[Depends(reserver)],
)
def reviser_demo(
    draft_id: uuid.UUID,
    corps: DemandeRevue,
    referentiels: Annotated[Referentiels, Depends(get_referentiels)],
) -> ReponseRevue:
    """Correction et validation d'un dossier de démonstration par l'artisan (contrat, § 4.9)."""
    m = moteur()
    if m is None:
        raise ErreurAPI(503, "service_unavailable")
    try:
        r = reviser(m, draft_id, corps, referentiels)
    except DossierInconnu as erreur:
        raise ErreurAPI(404, "draft_not_found") from erreur
    except DejaValide as erreur:
        raise ErreurAPI(409, "conflict") from erreur
    except CorrectionInvalide as erreur:
        detail = DetailErreur(field=f"body.values.{erreur.champ}", issue="invalid_format")
        raise ErreurAPI(422, "validation_failed", [detail]) from erreur
    except SQLAlchemyError as erreur:
        logging.getLogger(__name__).warning(
            "revue.echec draft_id=%s erreur=%s", draft_id, type(erreur).__name__
        )
        raise ErreurAPI(503, "service_unavailable") from erreur
    return ReponseRevue(
        draft=r.brouillon, envelope=r.enveloppe, reviewed_at=r.valide_le,
        corrected_fields=r.champs,
    )  # fmt: skip


# Les métriques d'une fenêtre sont gardées 15 s : un rafraîchissement répété de l'écran « Qualité »
# ne peut pas charger la base (la route est publique, comme la démonstration).
CACHE_METRIQUES_S = 15.0
_cache_metriques: dict[int, tuple[float, Metriques]] = {}


@routeur.get(
    "/v1/demo/quality",
    response_model=Metriques,
    responses={
        503: {"model": Erreur, "description": "Enregistrement des traitements indisponible"}
    },
)
def qualite(heures: int = 24) -> Metriques:
    """Santé du service tirée de la base (V-10, TB-6) : sans contenu, modèle simulé exclu."""
    if heures not in FENETRES_HEURES:
        detail = DetailErreur(field="query.heures", issue="not_allowed")
        raise ErreurAPI(422, "validation_failed", [detail])
    m = moteur()
    if m is None:
        raise ErreurAPI(503, "service_unavailable")
    garde = _cache_metriques.get(heures)
    if garde and time.monotonic() - garde[0] < CACHE_METRIQUES_S:
        return garde[1]
    try:
        resultat = calculer(m, heures)
    except SQLAlchemyError as erreur:
        logging.getLogger(__name__).warning("qualite.echec erreur=%s", type(erreur).__name__)
        raise ErreurAPI(503, "service_unavailable") from erreur
    _cache_metriques[heures] = (time.monotonic(), resultat)
    return resultat
