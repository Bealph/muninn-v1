#!/usr/bin/env bash
# Réglages du dépôt GitHub dont dépend la chaîne (sprint 2, étapes 4 et 6) : protection de main,
# environnements de livraison, variables d'identité Azure. Relançable : chaque appel fixe l'état
# voulu, à l'identique s'il est déjà en place.
#
# Prérequis : `gh auth login` avec les droits d'administration du dépôt ; `az login` (pour lire
# l'identifiant de l'identité de déploiement). Lancer après infra/azure/03-applications.sh.

set -euo pipefail
source "$(dirname "$0")/../azure/parametres.sh"
DEPOT="$DEPOT_GITHUB"

echo "Variables d'identité Azure (ce ne sont pas des secrets)"
gh variable set AZURE_CLIENT_ID -R "$DEPOT" \
  --body "$(az identity show -g "$GROUPE" -n "$IDENTITE_DEPLOIEMENT" --query clientId -o tsv)"
gh variable set AZURE_TENANT_ID -R "$DEPOT" --body "$(az account show --query tenantId -o tsv)"
gh variable set AZURE_SUBSCRIPTION_ID -R "$DEPOT" --body "$(az account show --query id -o tsv)"

echo "Environnements de livraison, réservés aux branches protégées"
for env in "${ENVIRONNEMENTS_APP[@]}"; do
  gh api -X PUT "repos/$DEPOT/environments/$env" --silent --input - <<'EOF'
{"deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}}
EOF
done

echo "Protection de main : verdict requis, administrateurs compris"
# 15368 : identifiant de l'application GitHub Actions, qui publie le contrôle verdict.
gh api -X PUT "repos/$DEPOT/branches/main/protection" --silent --input - <<'EOF'
{
  "required_status_checks": {"strict": true, "checks": [{"context": "verdict", "app_id": 15368}]},
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "Contrôle"
gh api "repos/$DEPOT/branches/main/protection" \
  --jq '"main : verdict requis = \([.required_status_checks.checks[].context] | join(",")), administrateurs inclus = \(.enforce_admins.enabled)"'
gh variable list -R "$DEPOT"
