#!/usr/bin/env bash
# Sprint 5, étape 3 : traces vers Application Insights (D-40, D-87).
#
#   1. extension Azure CLI « application-insights », si elle manque ;
#   2. composant Application Insights `appi-muninn`, en France Central, lié à l'espace de
#      journaux `log-muninn` (plafond de 0,5 Go par jour, 30 jours), étiqueté `projet=muninn` pour
#      entrer dans le budget ; créé s'il n'existe pas ;
#   3. pour l'API de chaque environnement (les deux par défaut, ou ceux passés en arguments) :
#      secret `appinsights-connection-string` et variable APPLICATIONINSIGHTS_CONNECTION_STRING ;
#      comme deployer.sh, la nouvelle révision ne reçoit le trafic qu'après un contrôle ;
#   4. contrôle : un appel de démonstration ; ses traces arrivent dans Application Insights en
#      quelques minutes (délai d'ingestion).
# Un seul composant pour les deux environnements : chaque trace porte `deployment.environment.name`.
#
# Coût (vérifié le 23 octobre 2026, API officielle des prix de Microsoft) : l'ingestion d'un
# composant lié à un espace est facturée par l'espace, 5 Go gratuits par mois puis 2,43 € par Go ;
# le plafond de 0,5 Go par jour de l'espace s'applique aussi à ces données.
# La chaîne de connexion n'est jamais affichée ni écrite sur disque.
# Prérequis : az connecté. Relançable.
# Usage : bash infra/azure/09-observabilite.sh [preproduction] [production]

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

COMPOSANT="appi-muninn"
if [ "$#" -gt 0 ]; then environnements=("$@"); else environnements=("${ENVIRONNEMENTS_APP[@]}"); fi

attendre() {
  for _ in $(seq 1 36); do
    # Réponse jetée par bash, pas par curl : le curl de Windows refuse « -o /dev/null ».
    if curl -fsS -m 20 "$1" >/dev/null; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}

echo "1/4 Extension « application-insights » d'Azure CLI"
az extension show --name application-insights --only-show-errors -o none 2>/dev/null \
  || az extension add --name application-insights --yes --only-show-errors

echo "2/4 Composant $COMPOSANT lié à l'espace $JOURNAUX"
espace=$(az monitor log-analytics workspace show -g "$GROUPE" -n "$JOURNAUX" --query id -o tsv)
if ! az monitor app-insights component show -g "$GROUPE" --app "$COMPOSANT" --only-show-errors -o none 2>/dev/null; then
  az_tenace monitor app-insights component create -g "$GROUPE" --app "$COMPOSANT" \
    --location "$REGION" --kind web --application-type web --workspace "$espace" \
    --tags "$ETIQUETTE" --only-show-errors -o none
fi
lie=$(az monitor app-insights component show -g "$GROUPE" --app "$COMPOSANT" \
  --query workspaceResourceId -o tsv)
if [ "${lie,,}" != "${espace,,}" ]; then
  echo "Le composant $COMPOSANT n'est pas lié à $JOURNAUX : arrêt." >&2
  exit 1
fi
connexion=$(az monitor app-insights component show -g "$GROUPE" --app "$COMPOSANT" \
  --query connectionString -o tsv)

for env in "${environnements[@]}"; do
  api=$(app_api "$env")
  echo "3/4 API $api : chaîne de connexion et révision contrôlée"
  precedente=$(az_tenace containerapp revision list -g "$GROUPE" -n "$api" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
  az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
    --revision-weight "$precedente=100" --only-show-errors -o none
  az_tenace containerapp secret set -g "$GROUPE" -n "$api" --only-show-errors -o none \
    --secrets "appinsights-connection-string=$connexion"
  nouvelle=$(az_tenace containerapp update -g "$GROUPE" -n "$api" --only-show-errors \
    --set-env-vars APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:appinsights-connection-string \
    --query properties.latestRevisionName -o tsv)
  fqdn=$(az_tenace containerapp revision show -g "$GROUPE" -n "$api" --revision "$nouvelle" \
    --query properties.fqdn -o tsv)
  if ! attendre "https://$fqdn/health"; then
    echo "Contrôle échoué : le trafic reste sur $precedente" >&2
    exit 1
  fi
  az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
    --revision-weight "$nouvelle=100" --only-show-errors -o none
  echo "   trafic : 100 % sur $nouvelle (précédente conservée : $precedente)"

  echo "4/4 Contrôle : un appel de démonstration (SC-01)"
  public=$(az_tenace containerapp show -g "$GROUPE" -n "$api" \
    --query properties.configuration.ingress.fqdn -o tsv)
  curl -fsS -m 90 -X POST "https://$public/v1/demo/runs" -H "Content-Type: application/json" \
    -d '{"mode":"scenario","scenario_id":"SC-01"}' >/dev/null
  echo "   appel traité ; ses traces arrivent dans $COMPOSANT en quelques minutes."
done
unset connexion
