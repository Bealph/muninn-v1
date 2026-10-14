#!/usr/bin/env bash
# Étape 5, partie 3 : applications Container Apps (API et console, en préproduction et en
# production), droits de l'identité de déploiement et confiance OIDC avec GitHub Actions.
#
# Prérequis : 01-socle.sh et 02-image-initiale.sh lancés depuis le même commit ; variable
# POSTGRES_MOT_DE_PASSE définie (la même qu'à l'étape 1). Relançable.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
: "${POSTGRES_MOT_DE_PASSE:?Définir POSTGRES_MOT_DE_PASSE avant de lancer le script.}"
cd "$(git rev-parse --show-toplevel)"

existe() { "$@" --only-show-errors >/dev/null 2>&1; }

sha=$(git rev-parse HEAD)
image="$REGISTRE.azurecr.io/muninn:$sha"
az acr manifest show-metadata "$image" --only-show-errors -o none ||
  { echo "Image absente du registre : lancer 02-image-initiale.sh." >&2; exit 1; }

execution_id=$(az identity show -g "$GROUPE" -n "$IDENTITE_EXECUTION" --query id -o tsv)
execution_client=$(az identity show -g "$GROUPE" -n "$IDENTITE_EXECUTION" --query clientId -o tsv)
deploiement_principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_DEPLOIEMENT" --query principalId -o tsv)
environnement_id=$(az containerapp env show -g "$GROUPE" -n "$ENVIRONNEMENT_CA" --query id -o tsv)
hote_postgres="$POSTGRES.postgres.database.azure.com"

attribuer() { # principal, rôle, portée
  if [ -z "$(az role assignment list --assignee "$1" --role "$2" --scope "$3" --query '[0].id' -o tsv)" ]; then
    az role assignment create --assignee-object-id "$1" --assignee-principal-type ServicePrincipal \
      --role "$2" --scope "$3" --only-show-errors -o none
  fi
}

# Réglages communs : une réplique au plus (coût et abus bornés), zéro au repos ;
# révisions multiples pour le retour arrière par le trafic (étape 8).
commun=(--environment "$ENVIRONNEMENT_CA" --image "$image"
  --registry-server "$REGISTRE.azurecr.io" --registry-identity "$execution_id"
  --user-assigned "$execution_id" --ingress external --target-port 8000
  --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi --revisions-mode multiple
  --tags "$ETIQUETTE" --only-show-errors -o none)

for env in "${ENVIRONNEMENTS_APP[@]}"; do
  api=$(app_api "$env"); console=$(app_console "$env"); base=$(base_de_donnees "$env")

  echo "Application $api"
  if ! existe az containerapp show -g "$GROUPE" -n "$api"; then
    url_base="postgresql://$POSTGRES_ADMIN:$POSTGRES_MOT_DE_PASSE@$hote_postgres:5432/$base?sslmode=require"
    az containerapp create -g "$GROUPE" -n "$api" "${commun[@]}" \
      --secrets "database-url=$url_base" \
      --env-vars ENVIRONMENT="$env" GIT_SHA="$sha" DATABASE_URL=secretref:database-url \
        LLM_FOURNISSEUR=azure AZURE_AI_ENDPOINT="$FOUNDRY_ENDPOINT" \
        AZURE_AI_MODEL_A="$MODELE_A" AZURE_AI_MODEL_B="$MODELE_B" \
        AZURE_CLIENT_ID="$execution_client"
    unset url_base
  fi

  echo "Application $console"
  if ! existe az containerapp show -g "$GROUPE" -n "$console"; then
    az containerapp create -g "$GROUPE" -n "$console" "${commun[@]}" \
      --env-vars MUNINN_PROCESSUS=console ENVIRONMENT="$env" GIT_SHA="$sha" \
        API_BASE_URL="http://$api"
  fi

  for app in "$api" "$console"; do
    attribuer "$deploiement_principal" "$ROLE_CONTAINER_APPS_CONTRIBUTOR" \
      "$(az containerapp show -g "$GROUPE" -n "$app" --query id -o tsv)"
  done

  echo "Confiance OIDC : GitHub Actions, environnement $env"
  existe az identity federated-credential show -g "$GROUPE" --identity-name "$IDENTITE_DEPLOIEMENT" \
    -n "github-$env" ||
    az identity federated-credential create -g "$GROUPE" --identity-name "$IDENTITE_DEPLOIEMENT" \
      -n "github-$env" --issuer "https://token.actions.githubusercontent.com" \
      --subject "repo:$DEPOT_GITHUB:environment:$env" --audiences "api://AzureADTokenExchange" \
      --only-show-errors -o none
done
# Le déploiement met à jour des applications rattachées à l'environnement : lecture et
# rattachement nécessaires sur l'environnement lui-même.
attribuer "$deploiement_principal" "$ROLE_CONTAINER_APPS_CONTRIBUTOR" "$environnement_id"

echo
echo "Adresses :"
for env in "${ENVIRONNEMENTS_APP[@]}"; do
  for app in "$(app_api "$env")" "$(app_console "$env")"; do
    echo "  $app : https://$(az containerapp show -g "$GROUPE" -n "$app" \
      --query properties.configuration.ingress.fqdn -o tsv)"
  done
done
echo "Identifiants à déclarer dans GitHub (variables, pas des secrets) :"
echo "  AZURE_CLIENT_ID=$(az identity show -g "$GROUPE" -n "$IDENTITE_DEPLOIEMENT" --query clientId -o tsv)"
echo "  AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)"
echo "  AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)"
