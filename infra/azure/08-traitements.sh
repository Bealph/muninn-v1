#!/usr/bin/env bash
# Sprint 5, étape 1 : enregistrement des traitements (D-82, D-85).
#
# À lancer une fois, après la livraison du code de l'étape 1 (migration 0003 et rôle
# `<base>_traitements`). Pour chaque environnement (les deux par défaut, ou ceux passés en
# arguments) :
#   1. mot de passe du rôle `<base>_traitements` : relu dans les secrets de la tâche des données,
#      sinon tiré au hasard ; jamais affiché, jamais écrit sur disque ;
#   2. tâche des données : image de l'API servie, secret `mdp-traitements` et variable
#      MUNINN_MDP_TRAITEMENTS ;
#   3. une exécution de la tâche (environ 2 min sans nouvelle donnée) : migrations, dont le schéma
#      `app` ; rôles, dont `<base>_traitements` ; ingestion, qui ne crée aucune version ;
#   4. API : secret `database-url-traitements` et variable DATABASE_URL_TRAITEMENTS ; comme
#      deployer.sh, la nouvelle révision ne reçoit le trafic qu'après un contrôle à son adresse ;
#   5. contrôle : un appel de démonstration ; vérifier ensuite l'enregistrement avec
#      `bash infra/azure/consulter-base.sh <env> --traitements`.
#
# Coût : une exécution de la tâche, dans la franchise de Container Apps ; un appel au modèle.
# Prérequis : az connecté. Relançable : un second passage garde le même mot de passe.
# Usage : bash infra/azure/08-traitements.sh [preproduction] [production]

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

if [ "$#" -gt 0 ]; then environnements=("$@"); else environnements=("${ENVIRONNEMENTS_APP[@]}"); fi
hote="$POSTGRES.postgres.database.azure.com"

secret_tache() { # tâche, nom du secret : valeur, ou vide
  az containerapp job secret list -g "$GROUPE" -n "$1" --show-values \
    --query "[?name=='$2'].value | [0]" -o tsv --only-show-errors 2>/dev/null || true
}
attendre() {
  for _ in $(seq 1 36); do
    # Réponse jetée par bash, pas par curl : le curl de Windows refuse « -o /dev/null ».
    if curl -fsS -m 20 "$1" >/dev/null; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}

for env in "${environnements[@]}"; do
  api=$(app_api "$env"); base=$(base_de_donnees "$env"); tache=$(tache_donnees "$env")
  image=$(az_tenace containerapp show -g "$GROUPE" -n "$api" \
    --query "properties.template.containers[0].image" -o tsv --only-show-errors)
  echo "== $env : base $base, tâche $tache, image ${image##*:}"

  echo "1/5 Mot de passe du rôle ${base}_traitements"
  mdp=$(secret_tache "$tache" mdp-traitements)
  [ -n "$mdp" ] || mdp=$(openssl rand -hex 24)

  echo "2/5 Tâche $tache : image, secret et variable"
  az_tenace containerapp job secret set -g "$GROUPE" -n "$tache" \
    --secrets "mdp-traitements=$mdp" --only-show-errors -o none
  az_tenace containerapp job update -g "$GROUPE" -n "$tache" --image "$image" \
    --set-env-vars MUNINN_MDP_TRAITEMENTS=secretref:mdp-traitements GIT_SHA="${image##*:}" \
    --only-show-errors -o none

  echo "3/5 Exécution de la tâche (migrations, rôles, ingestion sans nouveauté)"
  execution=$(az_tenace containerapp job start -g "$GROUPE" -n "$tache" --query name -o tsv --only-show-errors)
  etat=""
  for _ in $(seq 1 120); do
    etat=$(az_tenace containerapp job execution show -g "$GROUPE" -n "$tache" \
      --job-execution-name "$execution" --query properties.status -o tsv --only-show-errors)
    case "$etat" in Succeeded | Failed | Stopped | Degraded) break ;; esac
    sleep 15
  done
  echo "   exécution $execution : $etat"
  if [ "$etat" != "Succeeded" ]; then
    echo "Échec. Journal : az containerapp job logs show -g $GROUPE -n $tache --execution $execution --container $tache" >&2
    exit 1
  fi

  echo "4/5 API $api : enregistrement des traitements"
  precedente=$(az_tenace containerapp revision list -g "$GROUPE" -n "$api" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
  az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
    --revision-weight "$precedente=100" --only-show-errors -o none
  az_tenace containerapp secret set -g "$GROUPE" -n "$api" --only-show-errors -o none \
    --secrets "database-url-traitements=postgresql://${base}_traitements:$mdp@$hote:5432/$base?sslmode=require"
  unset mdp
  nouvelle=$(az_tenace containerapp update -g "$GROUPE" -n "$api" --only-show-errors \
    --set-env-vars DATABASE_URL_TRAITEMENTS=secretref:database-url-traitements \
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

  echo "5/5 Contrôle : un appel de démonstration (SC-01)"
  public=$(az_tenace containerapp show -g "$GROUPE" -n "$api" \
    --query properties.configuration.ingress.fqdn -o tsv)
  curl -fsS -m 90 -X POST "https://$public/v1/demo/runs" -H "Content-Type: application/json" \
    -d '{"mode":"scenario","scenario_id":"SC-01"}' >/dev/null
  echo "   appel traité. Vérifier : bash infra/azure/consulter-base.sh $env --traitements"
done
