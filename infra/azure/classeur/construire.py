"""Modèle ARM du classeur Azure Monitor de Muninn (sprint 5, étape 4 ; TB-1 à TB-3, D-87).

Usage : `python infra/azure/classeur/construire.py > modele.json` (bibliothèque standard seule).
Lu par `infra/azure/10-classeur.sh`, qui le déploie avec `az deployment group create`.

Le classeur est le pendant technique de l'écran « Qualité » : pour l'exploitant, il montre les
traces (durée de chaque étape, appels par heure), les anomalies des journaux, les événements des
révisions, et retrouve un appel par son identifiant. Portée : l'espace `log-muninn`, où
`appi-muninn` écrit ses traces (`AppDependencies`) à côté des journaux des applications.

Choix de format, d'après la documentation de Microsoft vérifiée le 23 octobre 2026 :
- ressource `Microsoft.Insights/workbooks`, API 2023-06-01 ; `kind` « shared », `category`
  « workbook », `version` « Notebook/1.0 » (schéma ARM) ;
- nom stable `guid(resourceGroup().id, ...)` : une relance met à jour le même classeur ;
- éléments limités à ceux des exemples officiels : texte (type 1), paramètres texte (type 9,
  paramètre de type 1), requêtes en tableau (type 3, `queryType` 0 sur un espace). Les valeurs
  non documentées (graphiques, plage de temps en paramètre, liens profonds) sont écartées.
"""

import json
import re
import sys
import uuid
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
ESPACE = "microsoft.operationalinsights/workspaces"
NOM = "[guid(resourceGroup().id, 'muninn-classeur-exploitation')]"
SOURCE = "[resourceId('Microsoft.OperationalInsights/workspaces', parameters('espace'))]"
# Identifiants des paramètres : fixes, pour qu'une relance produise le même contenu.
ID_ENVIRONNEMENT = str(uuid.uuid5(uuid.NAMESPACE_URL, "muninn/classeur/environnement"))
ID_REQUETE = str(uuid.uuid5(uuid.NAMESPACE_URL, "muninn/classeur/requete"))

SECTIONS = [
    ("etapes", "Durée de chaque étape d'un appel (24 heures)",
     "Une ligne par étape : nombre, échecs, médiane et 95e centile en millisecondes. "
     "AL-16 surveille l'agent et les contrôles du serveur (l'extraction)."),
    ("heures", "Appels par heure (24 heures)",
     "Volume, échecs et 95e centile de la durée d'un appel, heure par heure."),
    ("anomalies", "Avertissements et erreurs des journaux (24 heures)",
     "Lignes de niveau WARNING ou ERROR, traces de pile, échecs `.echec` de l'application."),
    ("revisions", "Événements des révisions (24 heures)",
     "Création, démarrage, arrêt, échec de sonde : ce qu'a fait Container Apps."),
    ("appel", "Les étapes d'un appel",
     "Renseigner l'identifiant affiché par l'écran « Qualité » (paramètre Requete)."),
    ("journaux_appel", "Les journaux du même appel",
     "Les lignes portent l'identifiant de l'appel, jamais son contenu."),
]  # fmt: skip


def requetes() -> dict[str, str]:
    """Les requêtes de `requetes.kql`, par nom de bloc, sans les commentaires."""
    texte = (DOSSIER / "requetes.kql").read_text(encoding="utf-8")
    morceaux = re.split(r"^// == (\w+)\n", texte, flags=re.MULTILINE)[1:]
    return {
        nom: "\n".join(ligne for ligne in corps.splitlines() if not ligne.startswith("//")).strip()
        for nom, corps in zip(morceaux[::2], morceaux[1::2], strict=True)
    }


def contenu() -> dict[str, object]:
    """Le contenu du classeur (`serializedData`), au format « Notebook/1.0 »."""
    q = requetes()
    items: list[dict[str, object]] = [
        {"type": 1, "name": "introduction", "content": {"json": (
            "# Muninn : exploitation\n"
            "Vue technique pour l'exploitant : traces, journaux et révisions des API. "
            "Paramètres : Environnement (production ou preproduction) ; Requete, l'identifiant "
            "d'un appel affiché par l'écran « Qualité ». "
            "L'état du service en mots est sur l'écran « Qualité » de la console ; ce classeur "
            "sert au diagnostic. Aucune donnée d'appel : des durées, des codes et des "
            "identifiants opaques (OB-1)."
        )}},
        {"type": 9, "name": "parametres", "content": {
            "version": "KqlParameterItem/1.0", "style": "above", "queryType": 0,
            "resourceType": ESPACE,
            "parameters": [
                {"id": ID_ENVIRONNEMENT, "version": "KqlParameterItem/1.0",
                 "name": "Environnement", "type": 1, "value": "production"},
                {"id": ID_REQUETE, "version": "KqlParameterItem/1.0", "name": "Requete",
                 "type": 1, "value": ""},
            ],
        }},
    ]  # fmt: skip
    for nom, titre, aide in SECTIONS:
        items.append({"type": 1, "name": f"titre - {nom}",
                      "content": {"json": f"## {titre}\n{aide}"}})  # fmt: skip
        items.append({"type": 3, "name": nom, "content": {
            "version": "KqlItem/1.0", "query": q[nom], "size": 0, "queryType": 0,
            "resourceType": ESPACE, "visualization": "table",
        }})  # fmt: skip
    return {"version": "Notebook/1.0", "items": items}


def modele() -> dict[str, object]:
    """Le modèle ARM : un classeur partagé, rattaché à l'espace `log-muninn`."""
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "espace": {"type": "string",
                       "metadata": {"description": "Nom de l'espace de journaux"}},
            "region": {"type": "string", "metadata": {"description": "Région Azure"}},
            "projet": {"type": "string", "defaultValue": "muninn"},
        },
        "resources": [{
            "type": "Microsoft.Insights/workbooks",
            "apiVersion": "2023-06-01",
            "name": NOM,
            "location": "[parameters('region')]",
            "kind": "shared",
            "tags": {"projet": "[parameters('projet')]"},
            "properties": {
                "displayName": "Muninn, exploitation",
                "category": "workbook",
                "version": "Notebook/1.0",
                "sourceId": SOURCE,
                "serializedData": json.dumps(contenu(), ensure_ascii=False),
            },
        }],
        "outputs": {"classeur": {"type": "string", "value": NOM}},
    }  # fmt: skip


if __name__ == "__main__":
    # ASCII pur (accents en \uXXXX) : lisible par az quel que soit l'encodage de la console.
    json.dump(modele(), sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
