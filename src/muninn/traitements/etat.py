"""État du service sur la dernière heure, en mots, et historique des alertes (sprint 5, étapes 4
et 5 ; D-83, TB-6).

Trois règles, calculées par l'application sur une fenêtre glissante d'une heure :
- AL-01 : part des dossiers « à vérifier » au-dessus de 20 %, sur 20 dossiers au moins (SLO-09) ;
- AL-04 : brouillons de secours (modèle injoignable) au-dessus de 5 %, sur 20 dossiers au moins ;
- AL-16 : durée d'un traitement, 95e centile au-dessus de 20 s, sur 20 traitements au moins.
  La durée mesurée est celle du traitement entier (qualification comprise), plus longue que celle
  de la seule extraction visée par SLO-05 : la règle se déclenche donc plus tôt, jamais plus tard.

Sous le volume minimal, une règle ne conclut pas : « pas assez d'appels pour juger ». Un taux sur
trois appels ne dit rien, et une alerte qui s'allume au premier dossier ambigu serait ignorée.

L'historique rejoue les mêmes règles toutes les 5 minutes sur les 24 dernières heures, à partir de
la base : rien n'est stocké en plus, et l'écran montre quand une alerte a commencé et fini.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import Engine, text

from muninn.traitements.metriques import Metriques

MINIMUM = 20
PAS_HISTORIQUE = timedelta(minutes=5)

Niveau = Literal["ok", "alerte", "insuffisant"]


class Regle(BaseModel):
    """Une règle d'alerte et son verdict, en mots compréhensibles sans explication orale."""

    code: str
    surveille: str
    court: str
    seuil: str
    valeur: str
    niveau: Niveau
    explication: str
    volume: int
    unite_volume: str


class Episode(BaseModel):
    """Une alerte de l'historique : la règle, quand elle a commencé et fini, sa pire valeur."""

    code: str
    court: str
    debut: datetime
    fin: datetime
    en_cours: bool
    pire: str


class EtatService(BaseModel):
    niveau: Niveau
    titre: str
    phrase: str
    fenetre_heures: int
    regles: list[Regle]
    juge_jusqu_a: datetime | None = None
    historique: list[Episode] = []


@dataclass(frozen=True)
class Mesure:
    """Ce qu'il faut pour juger les trois règles sur une fenêtre."""

    dossiers: int
    a_verifier: int
    secours: int
    traitements: int
    p95_ms: int | None


def _pourcent(x: float | None) -> str:
    return "aucune mesure" if x is None else f"{x * 100:.0f} %".replace(".", ",")


def _secondes(ms: int | None) -> str:
    return "aucune mesure" if ms is None else f"{ms / 1000:.1f} s".replace(".", ",")


def _niveau(volume: int, valeur: float | None, seuil: float) -> Niveau:
    if volume < MINIMUM or valeur is None:
        return "insuffisant"
    return "alerte" if valeur > seuil else "ok"


def regles(x: Mesure) -> list[Regle]:
    """Les trois règles de D-83 jugées sur une mesure."""
    part = x.a_verifier / x.dossiers if x.dossiers else None
    secours = x.secours / x.dossiers if x.dossiers else None
    return [
        Regle(
            code="AL-01", surveille="Dossiers à vérifier par l'artisan",
            court="dossiers à vérifier",
            seuil=f"au plus 20 %, sur {MINIMUM} dossiers au moins",
            valeur=f"{_pourcent(part)} ({x.a_verifier} sur {x.dossiers})",
            niveau=_niveau(x.dossiers, part, 0.20),
            explication="Muninn signale plus de doutes que prévu : appels peu clairs, "
            "communes de même nom, ou IA moins fiable.",
            volume=x.dossiers, unite_volume="dossiers",
        ),
        Regle(
            code="AL-04", surveille="Brouillons de secours (l'IA n'a pas répondu)",
            court="brouillons de secours",
            seuil=f"au plus 5 %, sur {MINIMUM} dossiers au moins",
            valeur=f"{_pourcent(secours)} ({x.secours} sur {x.dossiers})",
            niveau=_niveau(x.dossiers, secours, 0.05),
            explication="L'IA ne répond plus : les dossiers sont préparés sans elle, et "
            "moins complets.",
            volume=x.dossiers, unite_volume="dossiers",
        ),
        Regle(
            code="AL-16",
            surveille="Temps pour préparer un dossier (95 appels sur 100 plus rapides)",
            court="temps de préparation",
            seuil=f"au plus 20 s, sur {MINIMUM} traitements au moins",
            valeur=_secondes(x.p95_ms),
            niveau=_niveau(x.traitements, None if x.p95_ms is None else x.p95_ms / 1000, 20),
            explication="L'artisan attend son dossier plus de 20 s dans plus d'un cas sur "
            "vingt.",
            volume=x.traitements, unite_volume="traitements",
        ),
    ]  # fmt: skip


def evaluer(
    m: Metriques, juge_jusqu_a: datetime | None = None, historique: list[Episode] | None = None
) -> EtatService:
    """Le verdict des trois règles sur les métriques `m` (fenêtre d'une heure attendue)."""
    rs = regles(Mesure(m.dossiers, m.a_verifier, m.secours, m.total - m.refus, m.latence_p95_ms))

    def etat(niveau: Niveau, titre: str, phrase: str) -> EtatService:
        return EtatService(
            niveau=niveau, titre=titre, phrase=phrase, fenetre_heures=m.fenetre_heures,
            regles=rs, historique=historique or [],
            juge_jusqu_a=None if niveau == "insuffisant" else juge_jusqu_a,
        )  # fmt: skip

    alertes = [r for r in rs if r.niveau == "alerte"]
    if alertes:
        noms = ", ".join(f"{r.court} ({r.code})" for r in alertes)
        return etat(
            "alerte", "Alerte",
            f"Seuil dépassé sur la dernière heure : {noms}. Prévenir l'exploitant de Muninn : "
            "il suit la procédure prévue pour cette alerte.",
        )  # fmt: skip
    non_jugees = [r for r in rs if r.niveau == "insuffisant"]
    if len(non_jugees) == len(rs):
        return etat(
            "insuffisant", "Pas assez d'appels pour juger",
            f"{m.dossiers} dossier{'s' if m.dossiers > 1 else ''} sur la dernière heure, il en "
            f"faut {MINIMUM} pour juger. Les chiffres ci-dessous restent exacts.",
        )  # fmt: skip
    phrase = "Aucun seuil dépassé sur la dernière heure."
    if non_jugees:
        phrase += " Non jugé faute d'appels : " + ", ".join(r.court for r in non_jugees) + "."
    return etat("ok", "Aucun seuil dépassé", phrase)


# Instant où la fenêtre d'une heure retombera sous 20 dossiers, si aucun appel n'arrive : une heure
# après le 20e dossier le plus récent. Vide s'il y a moins de 20 dossiers.
JUGE_JUSQU_A = text("""
SELECT recu_le + interval '1 hour' AS limite
FROM app.traitements
WHERE issue = 'dossier' AND NOT modele_simule AND recu_le > now() - interval '1 hour'
ORDER BY recu_le DESC OFFSET :rang LIMIT 1
""")

# Les trois règles rejouées toutes les 5 minutes sur la fenêtre d'une heure qui finit à cet instant.
HISTORIQUE = text("""
WITH points AS (
    SELECT generate_series(
        date_bin(interval '5 minutes', now() - interval '24 hours', timestamptz '2000-01-01'),
        now(), interval '5 minutes') AS t
    UNION SELECT now()
)
SELECT p.t,
       count(tr.*) FILTER (WHERE tr.issue = 'dossier')                       AS dossiers,
       count(tr.*) FILTER (WHERE tr.issue = 'dossier' AND tr.a_verifier)     AS a_verifier,
       count(tr.*) FILTER (WHERE tr.statut = 'fallback_no_llm')              AS secours,
       count(tr.*) FILTER (WHERE tr.issue <> 'refus')                        AS traitements,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY tr.duree_ms)
           FILTER (WHERE tr.issue <> 'refus')                                AS p95
FROM points p
LEFT JOIN app.traitements tr
       ON tr.recu_le > p.t - interval '1 hour' AND tr.recu_le <= p.t AND NOT tr.modele_simule
GROUP BY p.t ORDER BY p.t
""")


def juge_jusqu_a(m: Engine) -> datetime | None:
    with m.connect() as conn:
        limite: datetime | None = conn.execute(JUGE_JUSQU_A, {"rang": MINIMUM - 1}).scalar()
    return limite


def historique(m: Engine) -> list[Episode]:
    """Les alertes des 24 dernières heures : une ligne par règle et par épisode continu."""
    with m.connect() as conn:
        points = list(conn.execute(HISTORIQUE).mappings())
    episodes: list[Episode] = []
    ouverts: dict[str, tuple[Episode, float]] = {}
    for i, p in enumerate(points):
        p95 = None if p["p95"] is None else round(float(p["p95"]))
        mesure = Mesure(p["dossiers"], p["a_verifier"], p["secours"], p["traitements"], p95)
        dernier = i == len(points) - 1
        for r in regles(mesure):
            if r.niveau == "alerte":
                gravite = _gravite(r.code, mesure)
                if r.code in ouverts:
                    e, pire = ouverts[r.code]
                    e.fin, e.en_cours = p["t"], dernier
                    if gravite > pire:
                        e.pire, pire = r.valeur, gravite
                    ouverts[r.code] = (e, pire)
                else:
                    e = Episode(code=r.code, court=r.court, debut=p["t"], fin=p["t"],
                                en_cours=dernier, pire=r.valeur)  # fmt: skip
                    ouverts[r.code] = (e, gravite)
                    episodes.append(e)
            else:
                ouverts.pop(r.code, None)
    return sorted(episodes, key=lambda e: e.debut, reverse=True)


def _gravite(code: str, x: Mesure) -> float:
    if code == "AL-01":
        return x.a_verifier / x.dossiers
    if code == "AL-04":
        return x.secours / x.dossiers
    return float(x.p95_ms or 0)
