"""Métriques tirées de la base (sprint 5, étape 3 ; V-10, TB-6, D-83).

Calculées à la demande sur `app.traitements` et `app.corrections`, sur une fenêtre glissante. Elles
ne portent aucun contenu : des nombres, des codes et des noms de champs. Les traitements du modèle
simulé (scénario `P4-perimetre`) sont exclus : ils ne disent rien du service réel.

Signaux (D-83 ; phase 2, `03-observabilite.md`) :
- volume, issues, taux de refus ;
- taux d'erreur de la composante : brouillons de secours (modèle injoignable) et relances ;
- latence (médiane et 95e centile) et coût ;
- part « à vérifier » parmi les dossiers (AL-01) ;
- garde-fous déclenchés, borne d'outils, corrections par champ, dossiers validés ;
- part des dossiers dont la commune ou le code postal n'a pas pu être contrôlé (« non contrôlé ») :
  commune ambiguë que le serveur refuse de trancher (D-69), ou référentiels injoignables (SLO-10) ;
- le dernier appel (identifiant opaque, scénario, issue, durée), pour retrouver sa trace (TB-6) ;
- une série par heure, pour les tendances.
"""

import calendar
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Engine, text

FENETRES_HEURES = (1, 24, 24 * 7, 24 * 30)
BUDGET_MENSUEL_EUR = 60.0  # SLO-16 : budget Azure du projet, hébergement compris

SYNTHESE = text("""
WITH t AS (
    SELECT * FROM app.traitements
    WHERE recu_le >= now() - make_interval(hours => :heures) AND NOT modele_simule
)
SELECT
    count(*)                                                         AS total,
    count(*) FILTER (WHERE issue = 'dossier')                        AS dossiers,
    count(*) FILTER (WHERE issue = 'message')                        AS messages,
    count(*) FILTER (WHERE issue = 'trace')                          AS traces,
    count(*) FILTER (WHERE issue = 'refus')                          AS refus,
    count(*) FILTER (WHERE statut = 'fallback_no_llm')               AS secours,
    count(*) FILTER (WHERE statut = 'partial_after_retry')           AS relances,
    count(*) FILTER (WHERE borne)                                    AS bornes,
    count(*) FILTER (WHERE issue = 'dossier' AND a_verifier)         AS a_verifier,
    count(*) FILTER (WHERE urgence = 'securite')                     AS securite,
    count(*) FILTER (WHERE issue = 'dossier' AND 'not_checked' IN (commune_statut,
                                                                  code_postal_statut))
                                                                     AS non_controle,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY duree_ms)
        FILTER (WHERE issue <> 'refus')                              AS latence_p50,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY duree_ms)
        FILTER (WHERE issue <> 'refus')                              AS latence_p95,
    count(duree_extraction_ms)                                       AS extractions,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY duree_extraction_ms)  AS extraction_p50,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY duree_extraction_ms) AS extraction_p95,
    coalesce(avg(cout_micro_eur) FILTER (WHERE issue <> 'refus'), 0) AS cout_moyen,
    coalesce(sum(cout_micro_eur), 0)                                 AS cout_total,
    min(recu_le)                                                     AS premier,
    max(recu_le)                                                     AS dernier
FROM t
""")

DERNIER = text("""
SELECT request_id, scenario_id, issue, duree_ms, recu_le
FROM app.traitements
WHERE recu_le >= now() - make_interval(hours => :heures) AND NOT modele_simule
ORDER BY recu_le DESC LIMIT 1
""")

GARDE_FOUS = text("""
SELECT g AS nom, count(*) AS nombre
FROM app.traitements, unnest(garde_fous) AS g
WHERE recu_le >= now() - make_interval(hours => :heures) AND NOT modele_simule
GROUP BY g ORDER BY nombre DESC, nom
""")

CORRECTIONS = text("""
SELECT c.champ AS nom, count(*) AS nombre
FROM app.corrections c
WHERE c.corrige_le >= now() - make_interval(hours => :heures)
GROUP BY c.champ ORDER BY nombre DESC, nom
""")

VALIDES = text("""
SELECT count(*) AS valides,
       coalesce(sum((SELECT count(*) FROM app.corrections c WHERE c.draft_id = d.draft_id)), 0)
           AS champs_corriges
FROM app.dossiers d
WHERE d.etat = 'valide' AND d.valide_le >= now() - make_interval(hours => :heures)
""")

SERIE = text("""
SELECT date_trunc('hour', recu_le) AS heure,
       count(*) AS total,
       count(*) FILTER (WHERE issue = 'dossier') AS dossiers,
       count(*) FILTER (WHERE issue = 'dossier' AND a_verifier) AS a_verifier,
       count(*) FILTER (WHERE issue = 'refus') AS refus,
       count(*) FILTER (WHERE statut = 'fallback_no_llm') AS secours,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY duree_ms)
           FILTER (WHERE issue <> 'refus') AS latence_p95
FROM app.traitements
WHERE recu_le >= now() - make_interval(hours => :heures) AND NOT modele_simule
GROUP BY 1 ORDER BY 1
""")


class Compte(BaseModel):
    nom: str
    nombre: int


class Point(BaseModel):
    heure: datetime
    total: int
    dossiers: int
    a_verifier: int
    refus: int
    secours: int
    latence_p95_ms: int | None


class DernierAppel(BaseModel):
    """Le dernier appel de la fenêtre : de quoi retrouver sa trace, sans rien de son contenu."""

    request_id: str
    scenario_id: str | None
    issue: str
    duree_ms: int
    recu_le: datetime


class Metriques(BaseModel):
    """Santé du service sur la fenêtre ; aucune donnée de l'appel."""

    fenetre_heures: int
    total: int
    dossiers: int
    messages: int
    traces: int
    refus: int
    taux_refus: float | None
    secours: int
    relances: int
    taux_erreur: float | None
    part_secours: float | None
    bornes: int
    a_verifier: int
    part_a_verifier: float | None
    securite: int
    non_controle: int
    part_non_controle: float | None
    latence_p50_ms: int | None
    latence_p95_ms: int | None
    extractions: int
    extraction_p50_ms: int | None
    extraction_p95_ms: int | None
    cout_moyen_eur: float
    cout_total_eur: float
    dossiers_valides: int
    champs_corriges: int
    corrections_par_champ: list[Compte]
    garde_fous: list[Compte]
    premier: datetime | None
    dernier: datetime | None
    dernier_appel: DernierAppel | None
    serie: list[Point]


def _part(numerateur: int, denominateur: int) -> float | None:
    return round(numerateur / denominateur, 4) if denominateur else None


def _entier(valeur: Any) -> int | None:
    return None if valeur is None else round(float(valeur))


def calculer(m: Engine, heures: int) -> Metriques:
    """Les métriques des `heures` dernières heures."""
    p = {"heures": heures}
    with m.connect() as conn:
        s = conn.execute(SYNTHESE, p).mappings().one()
        gardes = [Compte(**r) for r in conn.execute(GARDE_FOUS, p).mappings()]
        corrections = [Compte(**r) for r in conn.execute(CORRECTIONS, p).mappings()]
        v = conn.execute(VALIDES, p).mappings().one()
        d = conn.execute(DERNIER, p).mappings().one_or_none()
        serie = [
            Point(
                heure=r["heure"], total=r["total"], dossiers=r["dossiers"],
                a_verifier=r["a_verifier"], refus=r["refus"], secours=r["secours"],
                latence_p95_ms=_entier(r["latence_p95"]),
            )
            for r in conn.execute(SERIE, p).mappings()
        ]  # fmt: skip
    return Metriques(
        fenetre_heures=heures,
        total=s["total"], dossiers=s["dossiers"], messages=s["messages"], traces=s["traces"],
        refus=s["refus"], taux_refus=_part(s["refus"], s["total"]),
        secours=s["secours"], relances=s["relances"],
        taux_erreur=_part(s["secours"] + s["relances"], s["dossiers"]),
        part_secours=_part(s["secours"], s["dossiers"]),
        bornes=s["bornes"], a_verifier=s["a_verifier"],
        part_a_verifier=_part(s["a_verifier"], s["dossiers"]), securite=s["securite"],
        non_controle=s["non_controle"], part_non_controle=_part(s["non_controle"], s["dossiers"]),
        latence_p50_ms=_entier(s["latence_p50"]), latence_p95_ms=_entier(s["latence_p95"]),
        extractions=s["extractions"], extraction_p50_ms=_entier(s["extraction_p50"]),
        extraction_p95_ms=_entier(s["extraction_p95"]),
        cout_moyen_eur=round(float(s["cout_moyen"]) / 1e6, 6),
        cout_total_eur=round(float(s["cout_total"]) / 1e6, 6),
        dossiers_valides=v["valides"], champs_corriges=int(v["champs_corriges"]),
        corrections_par_champ=corrections, garde_fous=gardes,
        premier=s["premier"], dernier=s["dernier"],
        dernier_appel=DernierAppel(**d) if d else None, serie=serie,
    )  # fmt: skip


COUT_DU_MOIS = text("""
SELECT coalesce(sum(cout_micro_eur), 0) AS total, min(recu_le) AS premier
FROM app.traitements
WHERE recu_le >= date_trunc('month', now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
""")


class CoutMois(BaseModel):
    """Coût de l'IA pour les appels traités depuis le début du mois, et sa projection.

    Le budget de 60 € (SLO-16) couvre tout le projet Azure, hébergement compris : la part affichée
    n'est que celle de l'IA du service, sans les campagnes d'évaluation de la CI.
    """

    mois: str
    depuis: datetime | None
    total_eur: float
    projection_eur: float
    budget_eur: float
    part_budget: float


def cout_du_mois(m: Engine, maintenant: datetime | None = None) -> CoutMois:
    """Coût du mois en cours, projeté au même rythme jusqu'à la fin du mois.

    Le rythme se mesure depuis le premier traitement du mois, pas depuis le 1er : un service
    ouvert en cours de mois serait sinon projeté trop bas. Il faut une heure de mesure au moins.
    """
    t = maintenant or datetime.now(UTC)
    with m.connect() as conn:
        ligne = conn.execute(COUT_DU_MOIS).mappings().one()
    total = float(ligne["total"] or 0) / 1e6
    premier: datetime | None = ligne["premier"]
    debut_mois = t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mois = debut_mois + timedelta(days=calendar.monthrange(t.year, t.month)[1])
    depuis = max(debut_mois, premier) if premier else debut_mois
    mesure_s = (t - depuis).total_seconds()
    restant_s = (fin_mois - t).total_seconds()
    projection = total + total * restant_s / mesure_s if mesure_s >= 3600 else total
    return CoutMois(
        mois=f"{t:%m/%Y}", depuis=premier, total_eur=round(total, 4),
        projection_eur=round(projection, 2),
        budget_eur=BUDGET_MENSUEL_EUR, part_budget=round(projection / BUDGET_MENSUEL_EUR, 4),
    )  # fmt: skip
