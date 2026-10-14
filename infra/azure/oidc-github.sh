#!/usr/bin/env bash
# Confiance OIDC entre GitHub Actions et l'identité de déploiement : une par environnement GitHub.
# Crée la confiance, ou corrige son sujet s'il diffère. Appelé par 03-applications.sh ; peut être
# lancé seul (aucun secret requis).
#
# Le dépôt utilise le sujet « immuable » de GitHub, qui contient les identifiants numériques du
# compte et du dépôt : un dépôt supprimé puis recréé sous le même nom n'hérite pas de la
# confiance. Préfixe lu par : gh api repos/Bealph/Muninn/actions/oidc/customization/sub

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

for env in "${ENVIRONNEMENTS_APP[@]}"; do
  nom="github-$env"
  sujet="$SUJET_OIDC_PREFIXE:environment:$env"
  actuel=$(az identity federated-credential show -g "$GROUPE" --identity-name "$IDENTITE_DEPLOIEMENT" \
    -n "$nom" --query subject -o tsv 2>/dev/null || true)
  if [ -z "$actuel" ]; then
    echo "Confiance OIDC $nom : création"
    az identity federated-credential create -g "$GROUPE" --identity-name "$IDENTITE_DEPLOIEMENT" \
      -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
      --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
  elif [ "$actuel" != "$sujet" ]; then
    echo "Confiance OIDC $nom : sujet corrigé ($actuel -> $sujet)"
    az identity federated-credential update -g "$GROUPE" --identity-name "$IDENTITE_DEPLOIEMENT" \
      -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
      --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
  else
    echo "Confiance OIDC $nom : déjà correcte"
  fi
done
