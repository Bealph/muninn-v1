"""État du service sur la dernière heure, en mots, et historique des alertes (sprint 5, étapes 4
et 5 ; D-83, TB-6).

Trois règles, calculées par l'application sur une fenêtre glissante d'une heure :
- AL-01 : part des dossiers « à vérifier » au-dessus de 20 %, sur 20 dossiers au moins (SLO-09) ;
- AL-04 : brouillons de secours (modèle injoignable) au-dessus de 5 %, sur 20 dossiers au moins ;
- AL-16 : durée de l'extraction, 95e centile au-dessus de 20 s, sur 20 extractions au moins
  (SLO-05). La durée enregistrée depuis la migration 0004 ; un traitement plus ancien, sans elle,
  n'est pas compté.

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
    unite_volume_singulier: str


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
    extractions: int
    p95_ms: int | None


def _pourcent(x: float | None) -> str:
    return "aucune mesure" if x is None else f"{x * 100:.0f} %".replace(".", ",")


def _secondes(ms: int | None) -> str:
    return "aucune mesure" if ms is None else f"{ms / 1000:.1f} s".replace(".", ",")


def _niveau(volume: int, valeur: float | None, seuil: float) -> Niveau:
    if volume < MINIMUM or valeur is None:
        return "insuffisant"
    return "alerte" if valeur > seuil else "ok"


def _compte(n: int, total: int, part: float | None) -> str:
    """« 25 % (5 sur 20) » ; sous le volume minimal, les seuls nombres : un pourcentage sur un
    dossier (« 100 % ») alarme sans rien dire."""
    nombre = f"{n} sur {total} dossier{'s' if total > 1 else ''}"
    return nombre if total < MINIMUM else f"{_pourcent(part)} ({n} sur {total})"


def regles(x: Mesure) -> list[Regle]:
    """Les trois règles de D-83 jugées sur une mesure."""
    part = x.a_verifier / x.dossiers if x.dossiers else None
    secours = x.secours / x.dossiers if x.dossiers else None
    return [
        Regle(
            code="AL-01", surveille="Dossiers à vérifier par l'artisan",
            court="dossiers à vérifier",
            seuil=f"au plus 20 %, sur {MINIMUM} dossiers au moins",
            valeur=_compte(x.a_verifier, x.dossiers, part),
            niveau=_niveau(x.dossiers, part, 0.20),
            explication="Muninn signale plus de doutes que prévu : appels peu clairs, "
            "communes de même nom, ou IA moins fiable.",
            volume=x.dossiers, unite_volume="dossiers", unite_volume_singulier="dossier",
        ),
        Regle(
            code="AL-04", surveille="Brouillons de secours (l'IA n'a pas répondu)",
            court="brouillons de secours",
            seuil=f"au plus 5 %, sur {MINIMUM} dossiers au moins",
            valeur=_compte(x.secours, x.dossiers, secours),
            niveau=_niveau(x.dossiers, secours, 0.05),
            explication="L'IA ne répond plus : les dossiers sont préparés sans elle, donc "
            "moins complets.",
            volume=x.dossiers, unite_volume="dossiers", unite_volume_singulier="dossier",
        ),
        Regle(
            code="AL-16",
            surveille="Temps de travail de l'IA sur un dossier (95 dossiers sur 100)",
            court="temps de travail de l'IA",
            seuil=f"au plus 20 s, sur {MINIMUM} dossiers au moins",
            valeur=_secondes(x.p95_ms),
            niveau=_niveau(x.extractions, None if x.p95_ms is None else x.p95_ms / 1000, 20),
            explication="L'IA met plus de 20 s à remplir un dossier, plus d'une fois sur "
            "vingt : l'artisan attend.",
            volume=x.extractions, unite_volume="dossiers mesurés",
            unite_volume_singulier="dossier mesuré",
        ),
    ]  # fmt: skip


def evaluer(
    m: Metriques, juge_jusqu_a: datetime | None = None, historique: list[Episode] | None = None
) -> EtatService:
    """Le verdict des trois règles sur les métriques `m` (fenêtre d'une heure attendue)."""
    rs = regles(Mesure(m.dossiers, m.a_verifier, m.secours, m.extractions, m.extraction_p95_ms))

    def etat(niveau: Niveau, titre: str, phrase: str) -> EtatService:
        return EtatService(
            niveau=niveau, titre=titre, phrase=phrase, fenetre_heures=m.fenetre_heures,
            regles=rs, historique=historique or [],
            juge_jusqu_a=None if niveau == "insuffisant" else juge_jusqu_a,
        )  # fmt: skip

    alertes = [r for r in rs if r.niveau == "alerte"]
    if alertes:
        noms = ", ".join(r.court for r in alertes)
        return etat(
            "alerte", "Alerte",
            f"Seuil dépassé sur les 60 dernières minutes : {noms}. Prévenir la personne qui "
            "gère Muninn : elle suit la procédure prévue pour cette alerte.",
        )  # fmt: skip
    non_jugees = [r for r in rs if r.niveau == "insuffisant"]
    if len(non_jugees) == len(rs):
        recu = f"{m.dossiers} dossier{'s' if m.dossiers > 1 else ''}"
        if not historique:
            return etat(
                "insuffisant", "Aucun problème détecté depuis 24 heures",
                f"Trop peu d'appels dans les 60 dernières minutes ({recu}, il en faut "
                f"{MINIMUM}) pour un contrôle complet. Rien à faire.",
            )  # fmt: skip
        return etat(
            "insuffisant", "Pas assez d'appels pour juger",
            f"{recu} dans les 60 dernières minutes, il en faut {MINIMUM} pour juger. Une "
            "alerte a eu lieu dans les 24 heures : voir plus bas.",
        )  # fmt: skip
    phrase = "Aucun seuil dépassé sur les 60 dernières minutes. Rien à faire."
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
       count(tr.duree_extraction_ms)                                         AS extractions,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY tr.duree_extraction_ms)  AS p95
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
        mesure = Mesure(p["dossiers"], p["a_verifier"], p["secours"], p["extractions"], p95)
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
