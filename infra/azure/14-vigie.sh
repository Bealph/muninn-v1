#!/usr/bin/env bash
# C20 : détection automatique d'incident. Le workflow GitHub « vigie » lit les alertes Azure
# Monitor déclenchées sur le groupe de ressources et ouvre une issue « Incident » par alerte.
#
# Crée, ou met en conformité :
#   1. l'identité managée id-muninn-vigie, distincte des autres : elle ne fait que lire ;
#   2. son seul rôle : Monitoring Reader sur le groupe de ressources (lecture des alertes) ;
#   3. la confiance OIDC avec l'environnement GitHub « vigie » (sujet immuable du dépôt) ;
#   4. l'environnement GitHub « vigie », réservé aux branches protégées, et sa variable
#      AZURE_CLIENT_ID (une variable, pas un secret).
#
# Aucun secret. Coût : nul. Prérequis : `az login` (propriétaire du groupe de ressources) et
# `gh auth login` (administration du dépôt).

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

echo "1/4 Identité $IDENTITE_VIGIE"
if ! az identity show -g "$GROUPE" -n "$IDENTITE_VIGIE" --only-show-errors -o none 2>/dev/null; then
  az identity create -g "$GROUPE" -n "$IDENTITE_VIGIE" -l "$REGION" --tags "$ETIQUETTE" \
    --only-show-errors -o none
fi
principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_VIGIE" --query principalId -o tsv)
client=$(az identity show -g "$GROUPE" -n "$IDENTITE_VIGIE" --query clientId -o tsv)

echo "2/4 Rôle Monitoring Reader sur le groupe $GROUPE, et rien d'autre"
groupe_id=$(az group show -n "$GROUPE" --query id -o tsv)
# Lecture par la portée, sans passer par l'annuaire : une identité tout juste créée n'y est
# visible qu'après quelques dizaines de secondes (réplication d'Entra ID).
roles_de() {
  az role assignment list --scope "$groupe_id" \
    --query "[?principalId=='$principal'].roleDefinitionId" -o tsv
}
if ! roles_de | grep -q "$ROLE_MONITORING_READER"; then
  for essai in 1 2 3 4 5 6; do
    if az role assignment create --assignee-object-id "$principal" \
      --assignee-principal-type ServicePrincipal --role "$ROLE_MONITORING_READER" \
      --scope "$groupe_id" --only-show-errors -o none; then
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

echo "3/4 Confiance OIDC avec l'environnement GitHub « vigie »"
nom="github-vigie"
sujet="$SUJET_OIDC_PREFIXE:environment:vigie"
actuel=$(az identity federated-credential show -g "$GROUPE" --identity-name "$IDENTITE_VIGIE" \
  -n "$nom" --query subject -o tsv 2>/dev/null || true)
if [ -z "$actuel" ]; then
  az identity federated-credential create -g "$GROUPE" --identity-name "$IDENTITE_VIGIE" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
elif [ "$actuel" != "$sujet" ]; then
  az identity federated-credential update -g "$GROUPE" --identity-name "$IDENTITE_VIGIE" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
fi

echo "4/4 Environnement GitHub « vigie », réservé aux branches protégées"
gh api -X PUT "repos/$DEPOT_GITHUB/environments/vigie" --silent --input - <<'EOF'
{"deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}}
EOF
gh variable set AZURE_CLIENT_ID -R "$DEPOT_GITHUB" --env vigie --body "$client"

echo
echo "Rôles de l'identité sur toutes les portées (attendu : Monitoring Reader seul) :"
az role assignment list --all --query "[?principalId=='$principal'].roleDefinitionName" -o tsv
echo "Variable de l'environnement « vigie » :"
gh variable list -R "$DEPOT_GITHUB" --env vigie
