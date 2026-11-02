"""Vigie (C20) : choisit les issues « Incident » à ouvrir à partir des alertes Azure Monitor.

Entrées : la réponse de l'API Alerts Management (`az rest`, version 2019-03-01), et les issues
déjà ouvertes par la vigie (`gh issue list --json number,body`). Sortie : la liste JSON des issues
à créer, `[{"titre": ..., "corps": ...}]`. Une alerte n'ouvre qu'une issue, jamais deux : son
identifiant est écrit dans l'issue, et une alerte déjà connue est ignorée, même si l'issue est
fermée. Seules les alertes déclenchées (`Fired`) ouvrent une issue.

Bibliothèque standard seulement : le script tourne tel quel sur le runner de GitHub Actions.
Usage : `python3 vigie.py alertes.json issues.json`.
"""

import json
import sys
from pathlib import Path
from typing import Any

MARQUEUR = "<!-- alerte-azure: {} -->"
GRAVITES = {
    "Sev0": "critique",
    "Sev1": "erreur",
    "Sev2": "avertissement",
    "Sev3": "information",
    "Sev4": "verbeux",
}


def nom_regle(identifiant: str) -> str:
    """Dernier segment de l'identifiant de la règle : al04-muninn-modele."""
    return identifiant.rstrip("/").rsplit("/", 1)[-1] or "règle inconnue"


def corps(alerte: dict[str, Any]) -> str:
    e = alerte.get("properties", {}).get("essentials", {})
    gravite = e.get("severity", "inconnue")
    debut = e.get("startDateTime", "inconnue")
    lignes = [
        MARQUEUR.format(alerte["id"]),
        "Issue ouverte automatiquement par la vigie (workflow `vigie`) à partir d'une alerte "
        "Azure Monitor. À compléter au format des fiches INC, puis à fermer avec la PR du "
        "correctif.",
        "",
        "| Champ | Valeur |",
        "| --- | --- |",
        f"| Règle | {nom_regle(e.get('alertRule', ''))} |",
        f"| Déclenchée le (UTC) | {debut} |",
        f"| Gravité | {gravite} ({GRAVITES.get(gravite, 'non précisée')}) |",
        f"| Ressource visée | {nom_regle(e.get('targetResource', ''))} |",
        f"| État de l'alerte | {e.get('alertState', 'inconnu')} |",
        "| Détection | Automatique : règle Azure Monitor, puis workflow `vigie` |",
        "",
        "## Symptôme",
        "",
        "## Diagnostic",
        "",
        "## Cause racine",
        "",
        "## Correctif",
        "",
        "## Test de non-régression",
        "",
    ]
    return "\n".join(lignes)


def a_ouvrir(reponse: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Les issues à créer : une par alerte déclenchée dont aucune issue ne porte l'identifiant."""
    connues = "\n".join(i.get("body") or "" for i in issues)
    nouvelles = []
    for alerte in reponse.get("value", []):
        e = alerte.get("properties", {}).get("essentials", {})
        if e.get("monitorCondition") != "Fired" or not alerte.get("id"):
            continue
        if MARQUEUR.format(alerte["id"]) in connues:
            continue
        nouvelles.append(alerte)
    nouvelles.sort(key=lambda a: a["properties"]["essentials"].get("startDateTime", ""))
    return [
        {
            "titre": "Incident · {} · {}".format(
                nom_regle(a["properties"]["essentials"].get("alertRule", "")),
                a["properties"]["essentials"].get("startDateTime", "date inconnue"),
            ),
            "corps": corps(a),
        }
        for a in nouvelles
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage : vigie.py alertes.json issues.json", file=sys.stderr)
        return 2
    reponse = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    issues = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    # UTF-8 quel que soit l'encodage de la console (Windows) : le workflow lit la sortie avec jq.
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    print(json.dumps(a_ouvrir(reponse, issues), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
