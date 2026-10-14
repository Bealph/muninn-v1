#!/usr/bin/env bash
# Étape 5, partie 4 : budget mensuel de Muninn (D-34), avec alertes par courriel.
# Le groupe de ressources héberge d'autres projets : le budget ne compte que les ressources
# étiquetées projet=muninn. La ressource Foundry des modèles reçoit aussi l'étiquette.
#
# Prérequis : `az login` ; variable COURRIEL_ALERTE définie dans le shell (adresse jamais
# écrite dans le dépôt). API : Microsoft.Consumption/budgets, version 2026-06-01.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
: "${COURRIEL_ALERTE:?Définir COURRIEL_ALERTE avant de lancer le script.}"

echo "Étiquette $ETIQUETTE sur la ressource Foundry $FOUNDRY"
az tag update --resource-id "$(az cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --query id -o tsv)" \
  --operation merge --tags "$ETIQUETTE" --only-show-errors -o none

abonnement=$(az account show --query id -o tsv)
debut="$(date -u +%Y-%m)-01T00:00:00Z"
corps=$(cat <<EOF
{
  "properties": {
    "category": "Cost",
    "amount": $BUDGET_MENSUEL_EUR,
    "timeGrain": "Monthly",
    "timePeriod": { "startDate": "$debut" },
    "filter": { "tags": { "name": "${ETIQUETTE%%=*}", "operator": "In", "values": ["${ETIQUETTE#*=}"] } },
    "notifications": {
      "reel-50": { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 50,
                   "thresholdType": "Actual", "contactEmails": ["$COURRIEL_ALERTE"], "locale": "fr-fr" },
      "reel-80": { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 80,
                   "thresholdType": "Actual", "contactEmails": ["$COURRIEL_ALERTE"], "locale": "fr-fr" },
      "reel-100": { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 100,
                    "thresholdType": "Actual", "contactEmails": ["$COURRIEL_ALERTE"], "locale": "fr-fr" },
      "prevu-100": { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 100,
                     "thresholdType": "Forecasted", "contactEmails": ["$COURRIEL_ALERTE"], "locale": "fr-fr" }
    }
  }
}
EOF
)
echo "Budget budget-muninn : $BUDGET_MENSUEL_EUR par mois, alertes à 50, 80 et 100 % (réel) et 100 % (prévu)"
az rest --method put \
  --url "https://management.azure.com/subscriptions/$abonnement/resourceGroups/$GROUPE/providers/Microsoft.Consumption/budgets/budget-muninn?api-version=2026-06-01" \
  --body "$corps" --query "{nom:name,montant:properties.amount,filtre:properties.filter}" -o json
