#!/usr/bin/env bash
# Étape 0 de la reconstruction : ressource Azure AI Foundry et déploiements des modèles A et B
# (D-44 à D-46), en « Zone de données standard » UE (R5). Créés à l'origine par le porteur dans
# le portail ; ce script les recrée à l'identique s'ils manquent, sans toucher à l'existant.
#
# Prérequis : `az login`. Relançable.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

abonnement=$(az account show --query id -o tsv)
FOUNDRY_REGION="westeurope"
API="2025-06-01"

echo "Ressource Foundry $FOUNDRY ($FOUNDRY_REGION, AIServices, S0)"
if ! az cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --only-show-errors -o none 2>/dev/null; then
  az cognitiveservices account create -g "$GROUPE" -n "$FOUNDRY" -l "$FOUNDRY_REGION" \
    --kind AIServices --sku S0 --custom-domain "$FOUNDRY" --allow-project-management true \
    --tags "$ETIQUETTE" --yes --only-show-errors -o none
fi

# Déploiement par l'API REST : la CLI ne règle ni la mise à niveau automatique ni la politique
# de filtrage du contenu. Arguments : nom, format, version, capacité (milliers de jetons par
# minute), option de mise à niveau.
corps_deploiement() { # format, nom, version, capacité, option de mise à niveau, politique
  echo "{
    \"sku\": {\"name\": \"DataZoneStandard\", \"capacity\": $4},
    \"properties\": {
      \"model\": {\"format\": \"$1\", \"name\": \"$2\", \"version\": \"$3\"},
      \"versionUpgradeOption\": \"$5\",
      \"raiPolicyName\": \"$6\"
    }
  }"
}

deployer_modele() {
  local url="https://management.azure.com/subscriptions/$abonnement/resourceGroups/$GROUPE/providers/Microsoft.CognitiveServices/accounts/$FOUNDRY/deployments/$1?api-version=$API"
  local actuel version capacite politique
  actuel=$(az rest --method get --url "$url" --query properties.versionUpgradeOption -o tsv \
    --only-show-errors 2>/dev/null || true)
  if [ -z "$actuel" ]; then
    echo "Déploiement $1 : création"
    az rest --method put --url "$url" --only-show-errors -o none \
      --body "$(corps_deploiement "$2" "$1" "$3" "$4" "$5" "Microsoft.DefaultV2")"
  elif [ "$actuel" != "$5" ]; then
    # Seule l'option de mise à niveau change : version, capacité et politique sont reprises de
    # l'existant.
    echo "Déploiement $1 : mise à niveau automatique $actuel -> $5"
    version=$(az rest --method get --url "$url" --query properties.model.version -o tsv)
    capacite=$(az rest --method get --url "$url" --query sku.capacity -o tsv)
    politique=$(az rest --method get --url "$url" --query properties.raiPolicyName -o tsv)
    az rest --method put --url "$url" --only-show-errors -o none \
      --body "$(corps_deploiement "$2" "$1" "$version" "$capacite" "$5" "$politique")"
  else
    echo "Déploiement $1 : déjà conforme"
  fi
}

# Mise à niveau automatique désactivée pour les deux modèles : les résultats du banc d'essai T-06
# restent reproductibles (décision du porteur du 14 octobre 2026).
deployer_modele "$MODELE_A" "OpenAI" "2026-03-17" 50 "NoAutoUpgrade"
deployer_modele "$MODELE_B" "Mistral AI" "1" 20 "NoAutoUpgrade"
