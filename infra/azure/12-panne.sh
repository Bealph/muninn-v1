#!/usr/bin/env bash
# Sprint 5, étape 8 : panne type simulée, pour l'exercice d'exploitation (D-79, CA-6 partie 2).
#
# La panne : le point d'accès du modèle (AZURE_AI_ENDPOINT) est mal configuré sur une nouvelle
# révision de l'API, qui reçoit le trafic. Chaque appel au modèle échoue (`llm.echec`) : la
# qualification passe en « modèle indisponible », l'extraction donne un brouillon de secours,
# « à vérifier ». Aucun appel n'est perdu, aucune donnée n'est touchée (trafic synthétique).
# Symptômes : écran « Qualité » (brouillons de secours), classeur (anomalies), et AL-04 par
# courriel si au moins 20 appels passent dans l'heure (`rafale.py --profil nominal`).
#
#   --provoquer : nouvelle révision avec le mauvais point d'accès, et bascule du trafic ;
#   --reparer   : remet le bon point d'accès (FOUNDRY_ENDPOINT de parametres.sh) sur une nouvelle
#                 révision, la contrôle (santé et appel réel au modèle), puis y bascule.
#
# Le retour arrière (`gh workflow run retour-arriere -f environnement=...`) rend le service tout
# de suite, mais ne bascule que le trafic : le modèle de l'application garde le mauvais point
# d'accès, et la livraison suivante en hériterait (son contrôle `/llm/essai` la bloquerait, sans
# dommage). Après le retour arrière, lancer donc --reparer.
# Prérequis : az connecté. Usage : bash infra/azure/12-panne.sh <preproduction|production> <--provoquer|--reparer>

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

env="${1:?Environnement : preproduction ou production}"
action="${2:?Action : --provoquer ou --reparer}"
api=$(app_api "$env")
PANNE="https://panne-simulee.invalid"

case "$action" in
  --provoquer) valeur="$PANNE" ;;
  --reparer) valeur="$FOUNDRY_ENDPOINT" ;;
  *) echo "Action inconnue : $action" >&2; exit 2 ;;
esac

attendre() {
  for _ in $(seq 1 36); do
    if curl -fsS -m 20 "$1" >/dev/null; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}

precedente=$(az_tenace containerapp revision list -g "$GROUPE" -n "$api" \
  --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
echo "1/3 $api : révision en service $precedente ; AZURE_AI_ENDPOINT ← $valeur"
az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
  --revision-weight "$precedente=100" --only-show-errors -o none
az_tenace containerapp update -g "$GROUPE" -n "$api" --only-show-errors -o none \
  --set-env-vars AZURE_AI_ENDPOINT="$valeur"
# Nom relu sur l'application, jamais pris dans la réponse de `update` (INC-07).
nouvelle=$(nouvelle_revision "$api" "$precedente" \
  "properties.template.containers[0].env[?name=='AZURE_AI_ENDPOINT'].value | [0] == '$valeur'")
fqdn=$(az_tenace containerapp revision show -g "$GROUPE" -n "$api" --revision "$nouvelle" \
  --query properties.fqdn -o tsv)

echo "2/3 Contrôle de la révision $nouvelle"
attendre "https://$fqdn/health"
if [ "$action" = "--reparer" ]; then
  # Appel réel au modèle : la réparation n'est mise en service que si le modèle répond.
  if ! curl -fsS -m 90 -X POST "https://$fqdn/llm/essai" -H "Content-Type: application/json" \
    -d '{"question":"Reponds juste : ok","modele":"A"}' | grep -q '"fournisseur":"azure"'; then
    echo "Le modèle ne répond pas sur $nouvelle : le trafic reste sur $precedente" >&2
    exit 1
  fi
fi

echo "3/3 Bascule du trafic"
az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
  --revision-weight "$nouvelle=100" --only-show-errors -o none
echo "   trafic : 100 % sur $nouvelle (précédente conservée : $precedente)"
if [ "$action" = "--provoquer" ]; then
  echo "   panne en place : suivre docs/exploitation.md, section 4"
else
  echo "   service réparé ; vérifier un appel SC-01 depuis la console (écran « Agent »)"
fi
