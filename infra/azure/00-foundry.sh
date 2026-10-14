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
deployer_modele() {
  local url="https://management.azure.com/subscriptions/$abonnement/resourceGroups/$GROUPE/providers/Microsoft.CognitiveServices/accounts/$FOUNDRY/deployments/$1?api-version=$API"
  if az rest --method get --url "$url" --only-show-errors -o none 2>/dev/null; then
    echo "Déploiement $1 : déjà présent, laissé tel quel"
    return
  fi
  echo "Déploiement $1 : création"
  az rest --method put --url "$url" --only-show-errors -o none --body "{
    \"sku\": {\"name\": \"DataZoneStandard\", \"capacity\": $4},
    \"properties\": {
      \"model\": {\"format\": \"$2\", \"name\": \"$1\", \"version\": \"$3\"},
      \"versionUpgradeOption\": \"$5\",
      \"raiPolicyName\": \"Microsoft.DefaultV2\"
    }
  }"
}

deployer_modele "$MODELE_A" "OpenAI" "2026-03-17" 50 "NoAutoUpgrade"
# Réglage actuel du déploiement B, relevé le 14 octobre 2026. NoAutoUpgrade serait préférable
# pour la reproductibilité du banc d'essai (voir le README) ; à décider par le porteur.
deployer_modele "$MODELE_B" "Mistral AI" "1" 20 "OnceNewDefaultVersionAvailable"
