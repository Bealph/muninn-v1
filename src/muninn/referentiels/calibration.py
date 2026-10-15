"""Calibration du seuil du lexique (protocole : docs/v1/sprints/sprint-3/calibration-seuil.md).

Usage : `python -m muninn.referentiels.calibration` (base de `DATABASE_URL`). Mesure le dernier
lexique de plomberie, publié ou candidat, sur le jeu étiqueté versionné, et rend le tableau des
erreurs par seuil et le seuil retenu par la règle fixée avant la mesure.
"""

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from muninn.referentiels import depot

JEU = Path(__file__).parent / "calibration_lexique.csv"
SEUILS = [round(0.30 + 0.05 * i, 2) for i in range(14)]  # 0,30 à 0,95


@dataclass(frozen=True)
class Mesure:
    mot: str
    attendu: str | None
    nature: str
    terme: str | None
    similarite: float


def wilson(succes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalle de Wilson à 95 % d'une proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = succes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    marge = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - marge), min(1.0, centre + marge))


def mesurer(conn: depot.Connexion, lexique_id: int) -> list[Mesure]:
    mesures = []
    with JEU.open(encoding="utf-8", newline="") as fichier:
        for ligne in csv.DictReader(fichier):
            meilleur = depot.terme_le_plus_proche(conn, lexique_id, ligne["mot"])
            mesures.append(
                Mesure(
                    ligne["mot"],
                    ligne["attendu"] or None,
                    ligne["nature"],
                    meilleur["term"] if meilleur else None,
                    round(float(meilleur["similarite"]), 3) if meilleur else 0.0,
                )
            )
    return mesures


def erreurs(mesures: list[Mesure], seuil: float) -> tuple[int, int, int]:
    """Fausses acceptations, faux refus, positifs correctement acceptés, au seuil donné."""
    fausses_acceptations = faux_refus = justes = 0
    for m in mesures:
        accepte = m.similarite >= seuil
        if m.attendu is None:
            fausses_acceptations += accepte
        elif not accepte:
            faux_refus += 1
        elif m.terme == m.attendu:
            justes += 1
        else:
            fausses_acceptations += 1
    return fausses_acceptations, faux_refus, justes


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    with depot.connecter() as conn:
        ligne = conn.execute(
            "SELECT id, version, report->>'empreinte' AS empreinte FROM ref.trade_lexicons"
            " WHERE trade = 'plomberie' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if ligne is None:
            print("Aucun lexique de plomberie en base.")
            return 1
        mesures = mesurer(conn, ligne["id"])
    positifs = sum(1 for m in mesures if m.attendu is not None)
    negatifs = len(mesures) - positifs
    print(f"Lexique {ligne['version']}, empreinte {ligne['empreinte']}")
    print(f"Jeu : {positifs} positifs, {negatifs} négatifs\n")
    print("| Mot | Nature | Attendu | Terme le plus proche | Similarité |")
    print("| --- | --- | --- | --- | --- |")
    for m in mesures:
        print(f"| {m.mot} | {m.nature} | {m.attendu or 'refus'} | {m.terme} | {m.similarite} |")
    print("\n| Seuil | Fausses acceptations | Faux refus | Positifs justes |")
    print("| --- | --- | --- | --- |")
    retenu = None
    for seuil in SEUILS:
        fa, fr, justes = erreurs(mesures, seuil)
        print(f"| {seuil:.2f} | {fa} | {fr} | {justes} sur {positifs} |")
        if retenu is None and fa == 0:
            retenu = seuil
    if retenu is None:
        print("\nAucun seuil sans fausse acceptation.")
        return 1
    fa, fr, justes = erreurs(mesures, retenu)
    bas, haut = wilson(justes, positifs)
    _, haut_fa = wilson(0, negatifs)
    print(f"\nSeuil retenu (règle : le plus bas sans fausse acceptation) : {retenu:.2f}")
    print(f"Rappel : {justes}/{positifs}, IC 95 % de Wilson [{bas:.2f} ; {haut:.2f}]")
    print(f"Fausse acceptation des négatifs : 0/{negatifs}, borne haute à 95 % {haut_fa:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
