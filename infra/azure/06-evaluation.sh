#!/usr/bin/env bash
# Sprint 4, étape 9 : accès de la CI au modèle pour l'évaluation de l'agent (V-08, D-64).
#
# Crée, ou met en conformité :
#   1. l'identité managée id-muninn-evaluation, distincte de celle du déploiement : le job
#      d'évaluation exécute le code d'une PR non encore relue, il ne doit pouvoir que lire le modèle ;
#   2. son seul rôle : Foundry User sur la ressource Foundry (inférence par Entra ID) ;
#   3. la confiance OIDC avec l'environnement GitHub « evaluation » (sujet immuable du dépôt).
#
# Aucun secret. Coût : nul (les appels au modèle sont facturés à l'usage, plafond D-64).
# Après le script : créer l'environnement GitHub « evaluation » et y déclarer la variable
# AZURE_CLIENT_ID affichée en fin de script (une variable, pas un secret).

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

echo "1/3 Identité $IDENTITE_EVALUATION"
if ! az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" --only-show-errors -o none 2>/dev/null; then
  az identity create -g "$GROUPE" -n "$IDENTITE_EVALUATION" -l "$REGION" --tags "$ETIQUETTE" \
    --only-show-errors -o none
fi
principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" --query principalId -o tsv)
client=$(az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" --query clientId -o tsv)

echo "2/3 Rôle Foundry User sur $FOUNDRY, et rien d'autre"
foundry_id=$(az cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --query id -o tsv)
# Lecture par la portée, sans passer par l'annuaire : une identité tout juste créée n'y est
# visible qu'après quelques dizaines de secondes (réplication d'Entra ID).
roles_de() {
  az role assignment list --scope "$foundry_id" \
    --query "[?principalId=='$principal'].roleDefinitionId" -o tsv
}
if ! roles_de | grep -q "$ROLE_FOUNDRY_USER"; then
  for essai in 1 2 3 4 5 6; do
    if az role assignment create --assignee-object-id "$principal" \
      --assignee-principal-type ServicePrincipal --role "$ROLE_FOUNDRY_USER" \
      --scope "$foundry_id" --only-show-errors -o none; then
      break
    fi
    if [ "$essai" = 6 ]; then
      echo "Rôle non attribué : relancer le script dans une minute."
      exit 1
    fi
    echo "Identité pas encore répliquée dans Entra ID : nouvel essai dans 20 s ($essai/6)"
    sleep 20
  done
fi

echo "3/3 Confiance OIDC avec l'environnement GitHub « evaluation »"
nom="github-evaluation"
sujet="$SUJET_OIDC_PREFIXE:environment:evaluation"
actuel=$(az identity federated-credential show -g "$GROUPE" --identity-name "$IDENTITE_EVALUATION" \
  -n "$nom" --query subject -o tsv 2>/dev/null || true)
if [ -z "$actuel" ]; then
  az identity federated-credential create -g "$GROUPE" --identity-name "$IDENTITE_EVALUATION" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
elif [ "$actuel" != "$sujet" ]; then
  az identity federated-credential update -g "$GROUPE" --identity-name "$IDENTITE_EVALUATION" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
fi

echo
echo "Rôles de l'identité sur toutes les portées (attendu : Foundry User seul) :"
az role assignment list --all --query "[?principalId=='$principal'].roleDefinitionName" -o tsv
echo "Variable à déclarer dans l'environnement GitHub « evaluation » :"
echo "  AZURE_CLIENT_ID=$client"
