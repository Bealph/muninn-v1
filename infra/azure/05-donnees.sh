#!/usr/bin/env bash
# Sprint 3, étape 10 : les données en production (D-56, D-58).
#
# Pour chaque environnement (les deux par défaut, ou ceux passés en arguments) :
#   1. extension pg_trgm autorisée sur le serveur (paramètre dynamique, sans redémarrage) ;
#   2. tâche Container Apps des données, créée ou mise à jour : même image que l'API servie,
#      1 vCPU, 2 Gio, planifiée le 3 de chaque mois (Sirene est publié chaque mois), et
#      lançable à la demande par le workflow « donnees » ; commande `muninn-donnees`
#      (migrations, rôles, ingestion avec le seul rôle d'écriture) ;
#   3. droit de l'identité de déploiement sur la tâche (mettre son image à jour, la lancer) ;
#   4. une exécution de la tâche, suivie jusqu'à son terme ;
#   5. l'API basculée sur le rôle de lecture `<base>_api`, puis redémarrée ;
#   6. contrôle : le jeu de questions de démonstration rejoué contre l'API publique.
#
# Coût : un premier chargement dure environ 6 min à 1 vCPU et 2 Gio (environ 360
# vCPU-secondes), une exécution mensuelle sans nouveauté environ 80 s ;
# la franchise mensuelle de Container Apps est de 180 000 vCPU-secondes par abonnement.
# Mots de passe des rôles : tirés au hasard au premier passage, gardés dans les secrets de la
# tâche, réutilisés ensuite (un rejeu ne coupe pas l'API). Rien n'est écrit sur disque.
#
# Prérequis : POSTGRES_MOT_DE_PASSE (celui de 01-socle.sh) ; az connecté ; uv. Relançable.
# Usage : bash infra/azure/05-donnees.sh [preproduction] [production]

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
: "${POSTGRES_MOT_DE_PASSE:?Définir POSTGRES_MOT_DE_PASSE avant de lancer le script.}"
cd "$(git rev-parse --show-toplevel)"

existe() { "$@" --only-show-errors >/dev/null 2>&1; }
attribuer() { # principal, rôle, portée
  if [ -z "$(az role assignment list --assignee "$1" --role "$2" --scope "$3" --query '[0].id' -o tsv)" ]; then
    az role assignment create --assignee-object-id "$1" --assignee-principal-type ServicePrincipal \
      --role "$2" --scope "$3" --only-show-errors -o none
  fi
}
secret_tache() { # tâche, nom du secret : valeur, ou vide
  az containerapp job secret list -g "$GROUPE" -n "$1" --show-values \
    --query "[?name=='$2'].value | [0]" -o tsv --only-show-errors 2>/dev/null || true
}

if [ "$#" -gt 0 ]; then environnements=("$@"); else environnements=("${ENVIRONNEMENTS_APP[@]}"); fi
# Planification mensuelle, en UTC : deux jours après la publication du stock Sirene ; la
# préproduction une heure avant la production, pour ne pas charger le serveur en même temps.
planification() { if [ "$1" = production ]; then echo "0 4 3 * *"; else echo "0 3 3 * *"; fi; }
execution_id=$(az identity show -g "$GROUPE" -n "$IDENTITE_EXECUTION" --query id -o tsv)
deploiement_principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_DEPLOIEMENT" --query principalId -o tsv)
hote="$POSTGRES.postgres.database.azure.com"

echo "1/6 Extension pg_trgm autorisée sur $POSTGRES"
actuelle=$(az postgres flexible-server parameter show -g "$GROUPE" -s "$POSTGRES" \
  --name azure.extensions --query value -o tsv --only-show-errors)
if [[ ",${actuelle,,}," != *",pg_trgm,"* ]]; then
  az postgres flexible-server parameter set -g "$GROUPE" -s "$POSTGRES" --name azure.extensions \
    --value "${actuelle:+$actuelle,}pg_trgm" --only-show-errors -o none
fi

for env in "${environnements[@]}"; do
  api=$(app_api "$env"); base=$(base_de_donnees "$env"); tache=$(tache_donnees "$env")
  image=$(az containerapp show -g "$GROUPE" -n "$api" \
    --query "properties.template.containers[0].image" -o tsv --only-show-errors)
  sha="${image##*:}"
  echo "== $env : base $base, tâche $tache, image $sha"

  mdp_api=$(secret_tache "$tache" mdp-api)
  mdp_ingestion=$(secret_tache "$tache" mdp-ingestion)
  [ -n "$mdp_api" ] || mdp_api=$(openssl rand -hex 24)
  [ -n "$mdp_ingestion" ] || mdp_ingestion=$(openssl rand -hex 24)
  url_admin="postgresql://$POSTGRES_ADMIN:$POSTGRES_MOT_DE_PASSE@$hote:5432/$base?sslmode=require"
  secrets=("database-url=$url_admin" "mdp-api=$mdp_api" "mdp-ingestion=$mdp_ingestion")

  echo "2/6 Tâche $tache"
  # Le type de déclenchement ne se change pas par « job update » : une tâche encore manuelle
  # est supprimée puis recréée planifiée. Ses mots de passe ont été relus ci-dessus.
  declenchement=$(az containerapp job show -g "$GROUPE" -n "$tache" \
    --query properties.configuration.triggerType -o tsv --only-show-errors 2>/dev/null || true)
  if [ "$declenchement" = "Manual" ]; then
    echo "   tâche manuelle : recréée planifiée"
    az containerapp job delete -g "$GROUPE" -n "$tache" --yes --only-show-errors -o none
  fi
  if ! existe az containerapp job show -g "$GROUPE" -n "$tache"; then
    az containerapp job create -g "$GROUPE" -n "$tache" --environment "$ENVIRONNEMENT_CA" \
      --trigger-type Schedule --cron-expression "$(planification "$env")" \
      --replica-timeout 1800 --replica-retry-limit 0 \
      --replica-completion-count 1 --parallelism 1 \
      --image "$image" --cpu 1 --memory 2Gi \
      --registry-server "$REGISTRE.azurecr.io" --registry-identity "$execution_id" \
      --mi-user-assigned "$execution_id" --secrets "${secrets[@]}" \
      --env-vars ENVIRONMENT="$env" GIT_SHA="$sha" DATABASE_URL=secretref:database-url \
        MUNINN_MDP_API=secretref:mdp-api MUNINN_MDP_INGESTION=secretref:mdp-ingestion \
      --command muninn-donnees --tags "$ETIQUETTE" --only-show-errors -o none
  else
    az containerapp job secret set -g "$GROUPE" -n "$tache" --secrets "${secrets[@]}" \
      --only-show-errors -o none
    az containerapp job update -g "$GROUPE" -n "$tache" --image "$image" \
      --set-env-vars GIT_SHA="$sha" --only-show-errors -o none
  fi
  unset url_admin secrets

  echo "3/6 Droit de l'identité de déploiement sur la tâche"
  attribuer "$deploiement_principal" "$ROLE_CONTAINER_APPS_JOBS_CONTRIBUTOR" \
    "$(az containerapp job show -g "$GROUPE" -n "$tache" --query id -o tsv)"

  echo "4/6 Exécution de la tâche (environ 6 min)"
  execution=$(az containerapp job start -g "$GROUPE" -n "$tache" --query name -o tsv --only-show-errors)
  for _ in $(seq 1 120); do
    etat=$(az containerapp job execution show -g "$GROUPE" -n "$tache" \
      --job-execution-name "$execution" --query properties.status -o tsv --only-show-errors)
    case "$etat" in Succeeded | Failed | Stopped | Degraded) break ;; esac
    sleep 15
  done
  echo "   exécution $execution : $etat"
  if [ "$etat" != "Succeeded" ]; then
    echo "Échec. Journal : az containerapp job logs show -g $GROUPE -n $tache --execution $execution --container $tache" >&2
    exit 1
  fi

  echo "5/6 API $api : rôle de lecture ${base}_api"
  az containerapp secret set -g "$GROUPE" -n "$api" --only-show-errors -o none \
    --secrets "database-url=postgresql://${base}_api:$mdp_api@$hote:5432/$base?sslmode=require"
  unset mdp_api mdp_ingestion
  revision=$(az containerapp revision list -g "$GROUPE" -n "$api" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv --only-show-errors)
  az containerapp revision restart -g "$GROUPE" -n "$api" --revision "$revision" \
    --only-show-errors -o none

  echo "6/6 Jeu de questions de démonstration"
  fqdn=$(az containerapp show -g "$GROUPE" -n "$api" \
    --query properties.configuration.ingress.fqdn -o tsv --only-show-errors)
  # Redirection du shell plutôt que « -o /dev/null » : le curl de Windows, appelé depuis Git Bash,
  # ne sait pas écrire dans /dev/null (erreur 23 constatée le 16 octobre 2026).
  for _ in $(seq 1 24); do curl -fsS -m 20 "https://$fqdn/health" > /dev/null && break; sleep 5; done
  uv run muninn-questions "https://$fqdn"
done
echo "Données en place. Rejouer ensuite : gh workflow run donnees -f environnement=<env>"
