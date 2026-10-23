"""État du service sur la dernière heure, en mots (sprint 5, étapes 4 et 5 ; D-83, TB-6).

Trois règles, calculées par l'application sur les métriques de la dernière heure :
- AL-01 : part des dossiers « à vérifier » au-dessus de 20 %, sur 20 dossiers au moins (SLO-09) ;
- AL-04 : brouillons de secours (modèle injoignable) au-dessus de 5 %, sur 20 dossiers au moins ;
- AL-16 : durée d'un traitement, 95e centile au-dessus de 20 s, sur 20 traitements au moins.
  La durée mesurée est celle du traitement entier (qualification comprise), plus longue que celle
  de la seule extraction visée par SLO-05 : la règle se déclenche donc plus tôt, jamais plus tard.

Sous le volume minimal, une règle ne conclut pas : « pas assez d'appels pour juger ». Un taux sur
trois appels ne dit rien, et une alerte qui s'allume au premier dossier ambigu serait ignorée.
"""

from typing import Literal

from pydantic import BaseModel

from muninn.traitements.metriques import Metriques

MINIMUM = 20

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


class EtatService(BaseModel):
    niveau: Niveau
    titre: str
    phrase: str
    fenetre_heures: int
    regles: list[Regle]


def _pourcent(x: float | None) -> str:
    return "aucune mesure" if x is None else f"{x * 100:.0f} %".replace(".", ",")


def _secondes(ms: int | None) -> str:
    return "aucune mesure" if ms is None else f"{ms / 1000:.1f} s".replace(".", ",")


def evaluer(m: Metriques) -> EtatService:
    """Le verdict des trois règles sur les métriques `m` (fenêtre d'une heure attendue)."""
    secours = m.secours / m.dossiers if m.dossiers else None
    traitements = m.total - m.refus
    regles = [
        Regle(
            code="AL-01", surveille="Dossiers à vérifier par l'artisan",
            court="dossiers à vérifier",
            seuil=f"au plus 20 %, sur {MINIMUM} dossiers au moins",
            valeur=f"{_pourcent(m.part_a_verifier)} ({m.a_verifier} sur {m.dossiers})",
            niveau=_niveau(m.dossiers, m.part_a_verifier, 0.20),
            explication="Muninn signale plus de doutes que prévu : appels peu clairs, "
            "communes de même nom, ou IA moins fiable.",
        ),
        Regle(
            code="AL-04", surveille="Brouillons de secours (l'IA n'a pas répondu)",
            court="brouillons de secours",
            seuil=f"au plus 5 %, sur {MINIMUM} dossiers au moins",
            valeur=f"{_pourcent(secours)} ({m.secours} sur {m.dossiers})",
            niveau=_niveau(m.dossiers, secours, 0.05),
            explication="L'IA ne répond plus : les dossiers sont préparés sans elle, et "
            "moins complets.",
        ),
        Regle(
            code="AL-16",
            surveille="Temps pour préparer un dossier (95 appels sur 100 plus rapides)",
            court="temps de préparation",
            seuil=f"au plus 20 s, sur {MINIMUM} traitements au moins",
            valeur=_secondes(m.latence_p95_ms),
            niveau=_niveau(
                traitements, None if m.latence_p95_ms is None else m.latence_p95_ms / 1000, 20
            ),
            explication="L'artisan attend son dossier plus de 20 s dans plus d'un cas sur "
            "vingt.",
        ),
    ]  # fmt: skip
    alertes = [r for r in regles if r.niveau == "alerte"]
    if alertes:
        noms = ", ".join(f"{r.court} ({r.code})" for r in alertes)
        return EtatService(
            niveau="alerte", titre="Alerte", fenetre_heures=m.fenetre_heures, regles=regles,
            phrase=f"Seuil dépassé sur la dernière heure : {noms}. Prévenir l'exploitant de "
            "Muninn : il suit la procédure prévue pour cette alerte.",
        )  # fmt: skip
    non_jugees = [r for r in regles if r.niveau == "insuffisant"]
    if len(non_jugees) == len(regles):
        return EtatService(
            niveau="insuffisant", titre="Pas assez d'appels pour juger",
            fenetre_heures=m.fenetre_heures, regles=regles,
            phrase=f"Moins de {MINIMUM} dossiers sur la dernière heure : trop peu pour juger. "
            "Les chiffres ci-dessous restent exacts.",
        )  # fmt: skip
    phrase = "Aucun seuil dépassé sur la dernière heure."
    if non_jugees:
        phrase += " Non jugé faute d'appels : " + ", ".join(r.court for r in non_jugees) + "."
    return EtatService(
        niveau="ok", titre="Aucun seuil dépassé", fenetre_heures=m.fenetre_heures,
        regles=regles, phrase=phrase,
    )  # fmt: skip


def _niveau(volume: int, valeur: float | None, seuil: float) -> Niveau:
    if volume < MINIMUM or valeur is None:
        return "insuffisant"
    return "alerte" if valeur > seuil else "ok"
