#!/usr/bin/env bash
# Livraison d'une image dans un environnement (sprint 2, étape 6), utilisée par la CI sur fusion
# dans main. Pour chaque application (API, puis console) :
#   1. le trafic est figé sur la révision en service ;
#   2. une nouvelle révision est créée avec l'image, sans trafic ;
#   3. elle est contrôlée à sa propre adresse ;
#   4. le trafic bascule vers elle ; la révision précédente reste active (retour arrière, étape 8).
# Si un contrôle échoue, le trafic reste sur la révision précédente et le script s'arrête en erreur.
#
# Usage : bash infra/azure/deployer.sh <preproduction|production> <sha>
# Prérequis : az connecté avec une identité qui a les droits de déploiement ; image
# <registre>/muninn:<sha> déjà poussée.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

env="${1:?environnement : preproduction ou production}"
sha="${2:?SHA du commit à livrer}"
case "$env" in preproduction | production) ;; *) echo "Environnement inconnu : $env" >&2; exit 2 ;; esac
image="$REGISTRE.azurecr.io/muninn:$sha"

# Attend qu'une adresse réponde 200 (démarrage à froid possible : zéro réplique au repos).
attendre() {
  for _ in $(seq 1 36); do
    if curl -fsS -m 20 -o /dev/null "$1"; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}

# Teste qu'un texte en contient un autre (sans tube : pas de faux échec sous pipefail).
contient() { [[ "$1" == *"$2"* ]]; }

revision_en_service() {
  az containerapp revision list -g "$GROUPE" -n "$1" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv
}

image_de() { # application, révision
  az containerapp revision show -g "$GROUPE" -n "$1" --revision "$2" \
    --query "properties.template.containers[0].image" -o tsv
}

livrer() { # application, fonction de contrôle
  local app="$1" controler="$2" precedente nouvelle fqdn
  precedente=$(revision_en_service "$app")
  echo "== $app : révision en service $precedente"
  # 0. Image déjà en service (même commit livré deux fois, INC-03) : rien à livrer, ce n'est pas
  #    une erreur. Les contrôles finaux par l'adresse publique s'exécutent quand même.
  if [ "$(image_de "$app" "$precedente")" = "$image" ]; then
    echo "   $image déjà en service : rien à livrer"
    return 0
  fi
  # 1. Trafic figé sur la révision nommée : la nouvelle ne reçoit rien avant d'être contrôlée.
  az containerapp ingress traffic set -g "$GROUPE" -n "$app" \
    --revision-weight "$precedente=100" --only-show-errors -o none

  # 2. Nouvelle révision.
  nouvelle=$(az containerapp update -g "$GROUPE" -n "$app" --image "$image" \
    --set-env-vars GIT_SHA="$sha" --only-show-errors \
    --query properties.latestRevisionName -o tsv)
  if [ "$nouvelle" = "$precedente" ]; then
    echo "Aucune nouvelle révision créée pour $app" >&2
    return 1
  fi
  fqdn=$(az containerapp revision show -g "$GROUPE" -n "$app" --revision "$nouvelle" \
    --query properties.fqdn -o tsv)
  echo "   nouvelle révision $nouvelle"

  # 3. Contrôle à l'adresse de la révision.
  if ! "$controler" "https://$fqdn"; then
    echo "Contrôle échoué : le trafic reste sur $precedente" >&2
    return 1
  fi

  # 4. Bascule.
  az containerapp ingress traffic set -g "$GROUPE" -n "$app" \
    --revision-weight "$nouvelle=100" --only-show-errors -o none
  echo "   trafic : 100 % sur $nouvelle (précédente conservée : $precedente)"
}

controler_api() {
  attendre "$1/health" || return 1
  contient "$(curl -fsS -m 20 "$1/version")" "\"git_sha\":\"$sha\"" ||
    { echo "SHA livré inattendu sur $1" >&2; return 1; }
  # Appel réel au modèle A : prouve l'identité, le rôle et le point d'accès.
  contient "$(curl -fsS -m 90 -X POST "$1/llm/essai" -H "Content-Type: application/json" \
    -d '{"question":"Reponds juste : ok","modele":"A"}')" '"fournisseur":"azure"' ||
    { echo "Appel au modèle en échec sur $1" >&2; return 1; }
}

controler_console() {
  attendre "$1/health" || return 1
  contient "$(curl -fsS -m 30 "$1/")" "($sha)" ||
    { echo "La console n'affiche pas la version livrée sur $1" >&2; return 1; }
}

livrer "$(app_api "$env")" controler_api
livrer "$(app_console "$env")" controler_console

# Contrôle final par l'adresse publique de chaque application.
for app in "$(app_api "$env")" "$(app_console "$env")"; do
  url="https://$(az containerapp show -g "$GROUPE" -n "$app" --query properties.configuration.ingress.fqdn -o tsv)"
  attendre "$url/health"
done
api_url="https://$(az containerapp show -g "$GROUPE" -n "$(app_api "$env")" --query properties.configuration.ingress.fqdn -o tsv)"
contient "$(curl -fsS -m 20 "$api_url/version")" "\"git_sha\":\"$sha\"" ||
  { echo "L'adresse publique ne sert pas $sha" >&2; exit 1; }
console_url="https://$(az containerapp show -g "$GROUPE" -n "$(app_console "$env")" --query properties.configuration.ingress.fqdn -o tsv)"
echo "Livré en $env : $sha"
if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "url=$console_url" >>"$GITHUB_OUTPUT"; fi
