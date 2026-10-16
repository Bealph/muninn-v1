#!/usr/bin/env bash
# Rejoue le chargement des données d'un environnement, en une commande (sprint 3, critère P4) :
# lance la tâche des données (migrations, rôles, ingestion), la suit jusqu'à son terme, puis
# rejoue le jeu de questions de démonstration contre l'API publique.
# Utilisé par le workflow « donnees » ; lançable aussi depuis le poste. La tâche doit exister
# (05-donnees.sh). Une source inchangée ne crée aucune version : le rejeu est sans doublon.
#
# Usage : bash infra/azure/donnees.sh <preproduction|production>

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

env="${1:?environnement : preproduction ou production}"
case "$env" in preproduction | production) ;; *) echo "Environnement inconnu : $env" >&2; exit 2 ;; esac
tache=$(tache_donnees "$env"); api=$(app_api "$env")

debut=$(date +%s)
execution=$(az containerapp job start -g "$GROUPE" -n "$tache" --query name -o tsv --only-show-errors)
echo "Exécution $execution de $tache lancée"
etat=""
for _ in $(seq 1 120); do
  etat=$(az containerapp job execution show -g "$GROUPE" -n "$tache" \
    --job-execution-name "$execution" --query properties.status -o tsv --only-show-errors)
  case "$etat" in Succeeded | Failed | Stopped | Degraded) break ;; esac
  sleep 15
done
echo "Exécution $execution : $etat en $(( $(date +%s) - debut )) s"
if [ "$etat" != "Succeeded" ]; then
  echo "Journal : az containerapp job logs show -g $GROUPE -n $tache --execution $execution --container $tache" >&2
  exit 1
fi

fqdn=$(az containerapp show -g "$GROUPE" -n "$api" \
  --query properties.configuration.ingress.fqdn -o tsv --only-show-errors)
for _ in $(seq 1 24); do curl -fsS -m 20 -o /dev/null "https://$fqdn/health" && break; sleep 5; done
uv run muninn-questions "https://$fqdn"
