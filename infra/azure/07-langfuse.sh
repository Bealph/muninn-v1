#!/usr/bin/env bash
# Sprint 4, étape 10 : clés Langfuse Cloud UE (V-13, D-49) pour l'API et pour l'évaluation en CI.
#
# Deux projets Langfuse distincts : « muninn » (traces de production) et « muninn-evaluation »
# (CI). Le job d'évaluation exécute le code d'une PR : il ne reçoit jamais les clés de production.
#
# Prérequis : `az login`, `gh auth login` ; dans le shell (par exemple : set -a; source .env;
# set +a), LANGFUSE_PUBLIC_KEY et LANGFUSE_SECRET_KEY (projet de production), et
# LANGFUSE_EVAL_PUBLIC_KEY et LANGFUSE_EVAL_SECRET_KEY (projet d'évaluation). Les clés ne sont
# jamais affichées ni écrites sur disque par ce script.
#
#   1. secrets langfuse-public-key et langfuse-secret-key de l'API de chaque environnement,
#      variables LANGFUSE_* qui y renvoient, région UE (une nouvelle révision démarre) ;
#   2. secrets LANGFUSE_PUBLIC_KEY et LANGFUSE_SECRET_KEY de l'environnement GitHub « evaluation »,
#      avec les clés du projet d'évaluation.
#
# Aucun coût : palier gratuit Hobby (50 000 unités par mois).

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"
: "${LANGFUSE_PUBLIC_KEY:?Définir LANGFUSE_PUBLIC_KEY (sans l'afficher) avant de lancer le script.}"
: "${LANGFUSE_SECRET_KEY:?Définir LANGFUSE_SECRET_KEY (sans l'afficher) avant de lancer le script.}"
: "${LANGFUSE_EVAL_PUBLIC_KEY:?Définir LANGFUSE_EVAL_PUBLIC_KEY (projet d'évaluation).}"
: "${LANGFUSE_EVAL_SECRET_KEY:?Définir LANGFUSE_EVAL_SECRET_KEY (projet d'évaluation).}"
if [ "$LANGFUSE_EVAL_PUBLIC_KEY" = "$LANGFUSE_PUBLIC_KEY" ]; then
  echo "Les clés d'évaluation doivent venir d'un autre projet que celles de production." >&2
  exit 1
fi
URL_LANGFUSE="https://cloud.langfuse.com"

attendre() {
  for _ in $(seq 1 36); do
    # Réponse jetée par bash, pas par curl : le curl de Windows refuse « -o /dev/null ».
    if curl -fsS -m 20 "$1" >/dev/null; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}
revision_en_service() {
  az containerapp revision list -g "$GROUPE" -n "$1" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv
}

# Révisions multiples (comme deployer.sh) : la nouvelle révision ne reçoit le trafic qu'après un
# contrôle à son adresse propre ; la précédente reste disponible pour un retour arrière.
for env in "${ENVIRONNEMENTS_APP[@]}"; do
  api=$(app_api "$env")
  precedente=$(revision_en_service "$api")
  echo "API $api : secrets et variables Langfuse (révision en service : $precedente)"
  az containerapp ingress traffic set -g "$GROUPE" -n "$api" \
    --revision-weight "$precedente=100" --only-show-errors -o none
  az containerapp secret set -g "$GROUPE" -n "$api" --only-show-errors -o none \
    --secrets "langfuse-public-key=$LANGFUSE_PUBLIC_KEY" "langfuse-secret-key=$LANGFUSE_SECRET_KEY"
  az containerapp update -g "$GROUPE" -n "$api" --only-show-errors -o none \
    --set-env-vars LANGFUSE_PUBLIC_KEY=secretref:langfuse-public-key \
      LANGFUSE_SECRET_KEY=secretref:langfuse-secret-key LANGFUSE_BASE_URL="$URL_LANGFUSE"
  # Nom relu sur l'application, jamais pris dans la réponse de `update` (INC-07).
  nouvelle=$(nouvelle_revision "$api" "$precedente" \
    "length(properties.template.containers[0].env[?name=='LANGFUSE_BASE_URL']) > \`0\`")
  fqdn=$(az containerapp revision show -g "$GROUPE" -n "$api" --revision "$nouvelle" \
    --query properties.fqdn -o tsv)
  if ! attendre "https://$fqdn/health"; then
    echo "Contrôle échoué : le trafic reste sur $precedente" >&2
    exit 1
  fi
  az containerapp ingress traffic set -g "$GROUPE" -n "$api" \
    --revision-weight "$nouvelle=100" --only-show-errors -o none
  echo "   trafic : 100 % sur $nouvelle (précédente conservée : $precedente)"
done

echo "GitHub : secrets de l'environnement « evaluation » (projet muninn-evaluation)"
printf '%s' "$LANGFUSE_EVAL_PUBLIC_KEY" | gh secret set LANGFUSE_PUBLIC_KEY --env evaluation --repo Bealph/Muninn
printf '%s' "$LANGFUSE_EVAL_SECRET_KEY" | gh secret set LANGFUSE_SECRET_KEY --env evaluation --repo Bealph/Muninn

echo
echo "Contrôle (noms seulement, jamais les valeurs) :"
for env in "${ENVIRONNEMENTS_APP[@]}"; do
  az containerapp show -g "$GROUPE" -n "$(app_api "$env")" \
    --query "properties.template.containers[0].env[?starts_with(name, 'LANGFUSE')].name" -o tsv
done
gh secret list --env evaluation --repo Bealph/Muninn
