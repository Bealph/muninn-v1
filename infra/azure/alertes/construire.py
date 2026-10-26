"""Modèle ARM de l'alerte Azure Monitor AL-04 et de son groupe d'actions (sprint 5, étape 5 ;
D-40, D-83).

Usage : `python infra/azure/alertes/construire.py > modele.json` (bibliothèque standard seule).
Lu par `infra/azure/11-alertes.sh`, qui le valide puis le déploie (`az deployment group create`).

AL-01 et AL-16 sont calculées et affichées par l'application (écran « Qualité ») ; AL-04 est la
seule alerte notifiée par Azure Monitor (D-83) : elle sonne même quand personne ne regarde l'écran,
et c'est elle qu'une panne du fournisseur du modèle déclenche.

Choix, vérifiés le 26 octobre 2026 :
- versions d'API publiées par le fournisseur `Microsoft.Insights` (`az provider show`) : règle
  `scheduledQueryRules` 2023-12-01, groupe `actionGroups` 2023-01-01, région « Global » ;
- règle évaluée toutes les 15 minutes sur une fenêtre d'une heure : 0,44 € par mois en France
  Central (API des prix de Microsoft, « Alerts System Log Monitored at 15 Minute Frequency ») ;
  courriels : 0 € sur la tranche de 1 000 ;
- la requête calcule elle-même les taux et ne rend une ligne qu'au-delà du seuil : la règle
  alerte dès qu'une ligne est rendue (nombre de résultats supérieur à 0).
L'adresse du courriel n'est pas dans le dépôt : elle est passée au déploiement (paramètre).
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
GROUPE_ACTIONS = "ag-muninn"
REGLE = "al04-muninn-modele"
ESPACE = "[resourceId('Microsoft.OperationalInsights/workspaces', parameters('espace'))]"


def requete() -> str:
    """La requête d'AL-04, sans ses commentaires."""
    texte = (DOSSIER / "al04.kql").read_text(encoding="utf-8")
    lignes = [ligne for ligne in texte.splitlines() if not ligne.lstrip().startswith("//")]
    return "\n".join(lignes).strip()


def modele() -> dict[str, object]:
    groupe_id = f"[resourceId('Microsoft.Insights/actionGroups', '{GROUPE_ACTIONS}')]"
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "espace": {"type": "string"},
            "region": {"type": "string"},
            "courriel": {"type": "string"},
            "projet": {"type": "string", "defaultValue": "muninn"},
        },
        "resources": [
            {
                "type": "Microsoft.Insights/actionGroups",
                "apiVersion": "2023-01-01",
                "name": GROUPE_ACTIONS,
                "location": "Global",
                "tags": {"projet": "[parameters('projet')]"},
                "properties": {
                    "groupShortName": "muninn",
                    "enabled": True,
                    "emailReceivers": [{
                        "name": "exploitant",
                        "emailAddress": "[parameters('courriel')]",
                        "useCommonAlertSchema": True,
                    }],
                },
            },
            {
                "type": "Microsoft.Insights/scheduledQueryRules",
                "apiVersion": "2023-12-01",
                "name": REGLE,
                "location": "[parameters('region')]",
                "kind": "LogAlert",
                "tags": {"projet": "[parameters('projet')]"},
                "dependsOn": [groupe_id],
                "properties": {
                    "displayName": "Muninn AL-04 : erreurs du modèle et brouillons de secours",
                    "description": (
                        "Plus de 5 % de brouillons de secours sur 20 extractions au moins, ou plus "
                        "de 5 % d'échecs d'appel au modèle sur 20 appels au moins, sur une heure, "
                        "API de production (D-83). Action : docs/exploitation.md, AL-04."
                    ),
                    "severity": 2,
                    "enabled": True,
                    "evaluationFrequency": "PT15M",
                    "windowSize": "PT1H",
                    "scopes": [ESPACE],
                    "criteria": {"allOf": [{
                        "query": requete(),
                        "timeAggregation": "Count",
                        "operator": "GreaterThan",
                        "threshold": 0,
                        "failingPeriods": {
                            "numberOfEvaluationPeriods": 1,
                            "minFailingPeriodsToAlert": 1,
                        },
                    }]},
                    "autoMitigate": True,
                    "actions": {"actionGroups": [groupe_id]},
                },
            },
        ],
    }  # fmt: skip


if __name__ == "__main__":
    # ASCII pur (accents en \\uXXXX) : lisible par az quel que soit l'encodage de la console.
    json.dump(modele(), sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
