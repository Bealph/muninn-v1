#!/usr/bin/env bash
# Sprint 5, étape 4 : classeur Azure Monitor « Muninn, exploitation » (TB-1 à TB-3, D-87).
#
#   1. modèle ARM construit par `infra/azure/classeur/construire.py` (requêtes de
#      `classeur/requetes.kql`, chacune testée sur l'espace `log-muninn` le 23 octobre 2026) ;
#   2. validation du modèle par Azure (`az deployment group validate`) ;
#   3. déploiement incrémental sous un nom fixe : une relance met à jour le même classeur
#      (nom `guid(resourceGroup().id, ...)`), sans doublon ni historique qui grossit.
#
# Coût : la ressource classeur n'a pas de tarif documenté ; ses requêtes portent sur des tables au
# plan Analytics, dont les requêtes interactives ne sont pas facturées (Microsoft Learn,
# « Azure Monitor Logs cost calculations », vérifié le 23 octobre 2026).
# Prérequis : az connecté, python 3. Relançable.
# Usage : bash infra/azure/10-classeur.sh [--valider]   (--valider : rien n'est créé)

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

modele=$(mktemp --suffix=.json)
trap 'rm -f "$modele"' EXIT
python "$(dirname "$0")/classeur/construire.py" > "$modele"
# Sous Git Bash, az (Python Windows) ne lit pas un chemin /tmp : chemin Windows si cygpath existe.
fichier=$(cygpath -w "$modele" 2>/dev/null || echo "$modele")

echo "1/2 Validation du modèle"
az_tenace deployment group validate -g "$GROUPE" --template-file "$fichier" \
  --parameters espace="$JOURNAUX" region="$REGION" --only-show-errors -o none
echo "   modèle valide"
if [ "${1:-}" = "--valider" ]; then exit 0; fi

echo "2/2 Déploiement du classeur"
id=$(az_tenace deployment group create -g "$GROUPE" -n classeur-muninn \
  --template-file "$fichier" --parameters espace="$JOURNAUX" region="$REGION" \
  --only-show-errors --query properties.outputs.classeur.value -o tsv)
echo "   classeur $id : portail Azure, Monitor, Classeurs, « Muninn, exploitation »"
