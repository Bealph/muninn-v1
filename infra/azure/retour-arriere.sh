#!/usr/bin/env bash
# Retour arrière en une opération (sprint 2, étape 8) : ramène 100 % du trafic de l'API et de la
# console d'un environnement sur une révision antérieure, déjà présente. Aucune image n'est
# reconstruite, aucune révision n'est créée : seul le trafic bascule.
#
# Usage : bash infra/azure/retour-arriere.sh <preproduction|production> [sha]
#   sans sha : pour l'API, la révision créée juste avant celle qui reçoit le trafic ;
#   avec sha : pour l'API, la plus récente qui porte ce commit, autre que celle en service ;
#   la console suit le commit visé, et ne bouge pas si elle le sert déjà.
# Une révision de configuration (même image, autre réglage : panne type, INC-07) se défait donc
# comme une livraison.
# Lancé par le workflow manuel « retour-arriere » ou par le porteur.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

env="${1:?environnement : preproduction ou production}"
sha_cible="${2:-}"
case "$env" in preproduction | production) ;; *) echo "Environnement inconnu : $env" >&2; exit 2 ;; esac

contient() { [[ "$1" == *"$2"* ]]; }

# Révisions d'une application triées par date de création, une par ligne : « nom<TAB>sha ».
revisions_de() {
  az containerapp revision list -g "$GROUPE" -n "$1" --all \
    --query "sort_by(@, &properties.createdTime)[].[name, properties.template.containers[0].image]" -o tsv |
    awk -F'\t' '{ n = split($2, m, ":"); print $1 "\t" m[n] }'
}

en_service_de() {
  az containerapp revision list -g "$GROUPE" -n "$1" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv
}

# Cible de l'API, « révision<TAB>sha ». Sans sha : la révision créée juste avant celle en service.
# Avec sha : la plus récente qui porte ce commit, autre que celle en service ; une révision de
# configuration (panne type, INC-07) porte la même image que la bonne : il faut revenir à la bonne,
# pas rester sur celle qui sert déjà ce commit.
cible_api() {
  awk -F'\t' -v courante="$2" -v visee="$sha_cible" '
    visee != "" { if ($2 == visee && $1 != courante) trouvee = $0; next }
    $1 == courante { if (prec != "") print prec; exit }
    { prec = $0 }
    END { if (visee != "" && trouvee != "") print trouvee }' <<<"$1"
}

# Cible de la console pour le commit visé : la révision en service si elle le sert déjà (une panne de
# configuration de l'API ne touche pas la console), sinon la plus récente qui le porte.
cible_console() {
  awk -F'\t' -v courante="$2" -v visee="$3" '
    $2 == visee { if ($1 == courante) deja = $0; trouvee = $0 }
    END { if (deja != "") print deja; else if (trouvee != "") print trouvee }' <<<"$1"
}

debut=$(date +%s)
declare -A revisions shas
api=$(app_api "$env")
console=$(app_console "$env")
read -r rev sha < <(cible_api "$(revisions_de "$api")" "$(en_service_de "$api")") || true
if [ -z "${rev:-}" ]; then
  echo "Aucune révision antérieure à servir pour $api" >&2
  exit 1
fi
revisions[$api]="$rev"
shas[$api]="$sha"
rev="" sha_console=""
read -r rev sha_console < <(cible_console "$(revisions_de "$console")" "$(en_service_de "$console")" "${shas[$api]}") || true
if [ -z "${rev:-}" ]; then
  echo "Aucune révision de $console ne porte le commit ${shas[$api]}" >&2
  exit 1
fi
revisions[$console]="$rev"
shas[$console]="$sha_console"
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
