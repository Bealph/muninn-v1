#!/usr/bin/env bash
# Retour arrière en une opération (sprint 2, étape 8) : ramène 100 % du trafic de l'API et de la
# console d'un environnement sur une révision antérieure, déjà présente. Aucune image n'est
# reconstruite, aucune révision n'est créée : seul le trafic bascule.
#
# Usage : bash infra/azure/retour-arriere.sh <preproduction|production> [sha]
#   sans sha : révision créée juste avant celle qui reçoit le trafic ;
#   avec sha : révision la plus récente qui porte l'image de ce commit.
# Lancé par le workflow manuel « retour-arriere » ou par le porteur.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

env="${1:?environnement : preproduction ou production}"
sha_cible="${2:-}"
case "$env" in preproduction | production) ;; *) echo "Environnement inconnu : $env" >&2; exit 2 ;; esac

contient() { [[ "$1" == *"$2"* ]]; }

# Rend « révision<TAB>sha » de la cible pour une application.
cible() {
  local app="$1" en_service
  en_service=$(az containerapp revision list -g "$GROUPE" -n "$app" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
  # Révisions triées par date de création, une par ligne : « nom<TAB>sha ».
  az containerapp revision list -g "$GROUPE" -n "$app" --all \
    --query "sort_by(@, &properties.createdTime)[].[name, properties.template.containers[0].image]" -o tsv |
    awk -F'\t' -v courante="$en_service" -v visee="$sha_cible" '
      { n = split($2, morceaux, ":"); ligne = $1 "\t" morceaux[n] }
      visee != "" { if (morceaux[n] == visee) trouvee = ligne; next }
      $1 == courante { if (prec != "") print prec; exit }
      { prec = ligne }
      END { if (visee != "" && trouvee != "") print trouvee }'
}

debut=$(date +%s)
declare -A revisions shas
for app in "$(app_api "$env")" "$(app_console "$env")"; do
  rev="" sha=""
  read -r rev sha < <(cible "$app") || true
  if [ -z "$rev" ]; then
    echo "Aucune révision antérieure à servir pour $app" >&2
    exit 1
  fi
  revisions[$app]="$rev"
  shas[$app]="$sha"
done
api=$(app_api "$env")
console=$(app_console "$env")
if [ "${shas[$api]}" != "${shas[$console]}" ]; then
  echo "L'API (${shas[$api]}) et la console (${shas[$console]}) ne visent pas le même commit" >&2
  exit 1
fi
sha="${shas[$api]}"
echo "Retour arrière en $env vers $sha"

for app in "$api" "$console"; do
  rev="${revisions[$app]}"
  # Une révision désactivée ne peut pas recevoir de trafic : la réactiver d'abord.
  if [ "$(az containerapp revision show -g "$GROUPE" -n "$app" --revision "$rev" \
    --query properties.active -o tsv)" != "true" ]; then
    az containerapp revision activate -g "$GROUPE" -n "$app" --revision "$rev" \
      --only-show-errors -o none
  fi
  az containerapp ingress traffic set -g "$GROUPE" -n "$app" --revision-weight "$rev=100" \
    --only-show-errors -o none
  echo "   $app : 100 % sur $rev"
done
bascule=$(date +%s)

# Contrôle : l'adresse publique de l'API sert le commit visé (démarrage à froid possible).
url="https://$(az containerapp show -g "$GROUPE" -n "$api" --query properties.configuration.ingress.fqdn -o tsv)"
for _ in $(seq 1 36); do
  if contient "$(curl -fsS -m 20 "$url/version" 2>/dev/null || true)" "\"git_sha\":\"$sha\""; then
    fin=$(date +%s)
    echo "Retour arrière vérifié : $url sert $sha"
    echo "Durée : bascule du trafic $((bascule - debut)) s, jusqu'au service vérifié $((fin - debut)) s"
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
      {
        echo "### Retour arrière en $env"
        echo "- Commit servi : \`$sha\`"
        echo "- API : \`${revisions[$api]}\` ; console : \`${revisions[$console]}\`"
        echo "- Durée : bascule $((bascule - debut)) s, service vérifié $((fin - debut)) s"
      } >>"$GITHUB_STEP_SUMMARY"
    fi
    exit 0
  fi
  sleep 5
done
echo "L'adresse publique ne sert pas $sha après bascule" >&2
exit 1
