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
- une série par heure, pour les tendances.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Engine, text

FENETRES_HEURES = (1, 24, 24 * 7, 24 * 30)

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
    percentile_cont(0.5) WITHIN GROUP (ORDER BY duree_ms)
        FILTER (WHERE issue <> 'refus')                              AS latence_p50,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY duree_ms)
        FILTER (WHERE issue <> 'refus')                              AS latence_p95,
    coalesce(avg(cout_micro_eur) FILTER (WHERE issue <> 'refus'), 0) AS cout_moyen,
    coalesce(sum(cout_micro_eur), 0)                                 AS cout_total,
    min(recu_le)                                                     AS premier,
    max(recu_le)                                                     AS dernier
FROM t
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
    bornes: int
    a_verifier: int
    part_a_verifier: float | None
    securite: int
    latence_p50_ms: int | None
    latence_p95_ms: int | None
    cout_moyen_eur: float
    cout_total_eur: float
    dossiers_valides: int
    champs_corriges: int
    corrections_par_champ: list[Compte]
    garde_fous: list[Compte]
    premier: datetime | None
    dernier: datetime | None
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
        bornes=s["bornes"], a_verifier=s["a_verifier"],
        part_a_verifier=_part(s["a_verifier"], s["dossiers"]), securite=s["securite"],
        latence_p50_ms=_entier(s["latence_p50"]), latence_p95_ms=_entier(s["latence_p95"]),
        cout_moyen_eur=round(float(s["cout_moyen"]) / 1e6, 6),
        cout_total_eur=round(float(s["cout_total"]) / 1e6, 6),
        dossiers_valides=v["valides"], champs_corriges=int(v["champs_corriges"]),
        corrections_par_champ=corrections, garde_fous=gardes,
        premier=s["premier"], dernier=s["dernier"], serie=serie,
    )  # fmt: skip
