#!/usr/bin/env bash
# Sprint 5, étape 5 : alerte Azure Monitor AL-04 et son groupe d'actions par courriel (D-40, D-83).
#
#   1. modèle ARM construit par `infra/azure/alertes/construire.py` (requête `alertes/al04.kql`,
#      testée sur `log-muninn` et sur des journaux fabriqués aux seuils exacts le 26 octobre 2026) ;
#   2. validation par Azure, puis aperçu de ce qui sera créé ou modifié (`what-if`) ;
#   3. déploiement incrémental sous un nom fixe : une relance met à jour les mêmes ressources ;
#   4. avec --tester : un courriel d'essai envoyé par le groupe d'actions.
#
# Coût (API des prix de Microsoft, 26 octobre 2026, France Central) : règle sur les journaux
# évaluée toutes les 15 minutes, 0,44 € par mois ; courriels, 0 € sur la tranche de 1 000.
# L'adresse n'est jamais écrite dans le dépôt : elle est lue dans COURRIEL_ALERTE.
# Prérequis : az connecté, python 3, COURRIEL_ALERTE définie. Relançable.
# Usage : COURRIEL_ALERTE=... bash infra/azure/11-alertes.sh [--valider | --tester]

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"
: "${COURRIEL_ALERTE:?Définir COURRIEL_ALERTE (adresse qui reçoit les alertes) avant de lancer le script.}"

modele=$(mktemp --suffix=.json)
trap 'rm -f "$modele"' EXIT
python "$(dirname "$0")/alertes/construire.py" > "$modele"
# Sous Git Bash, az (Python Windows) ne lit pas un chemin /tmp : chemin Windows si cygpath existe.
fichier=$(cygpath -w "$modele" 2>/dev/null || echo "$modele")
parametres=(espace="$JOURNAUX" region="$REGION" courriel="$COURRIEL_ALERTE")

echo "1/3 Validation du modèle"
az_tenace deployment group validate -g "$GROUPE" --template-file "$fichier" \
  --parameters "${parametres[@]}" --only-show-errors -o none
echo "   modèle valide ; ce qui sera créé ou modifié :"
az_tenace deployment group what-if -g "$GROUPE" --template-file "$fichier" \
  --parameters "${parametres[@]}" --only-show-errors --no-pretty-print \
  --query "changes[?changeType!='Ignore'].[changeType, resourceId]" -o tsv |
  sed -E 's#/subscriptions/[^/]+#/subscriptions/…#'
if [ "${1:-}" = "--valider" ]; then exit 0; fi

echo "2/3 Déploiement du groupe d'actions et de la règle AL-04"
az_tenace deployment group create -g "$GROUPE" -n alertes-muninn --template-file "$fichier" \
  --parameters "${parametres[@]}" --only-show-errors -o none
# `az resource show` plutôt que `az monitor scheduled-query`, qui demande une extension.
az_tenace resource show -g "$GROUPE" -n al04-muninn-modele \
  --resource-type Microsoft.Insights/scheduledQueryRules \
  --query "{regle:name, active:properties.enabled, frequence:properties.evaluationFrequency, fenetre:properties.windowSize}" \
  -o table

echo "3/3 Contrôle"
if [ "${1:-}" = "--tester" ]; then
  # Juste après l'ajout d'une adresse, l'essai est refusé (« There are no valid receivers in the
  # request ») tant qu'Azure n'a pas envoyé le courriel « You've been added to an Azure Monitor
  # action group » : constaté le 26 octobre 2026, l'essai a réussi une fois ce courriel reçu.
  if ! az_tenace monitor action-group test-notifications create -g "$GROUPE" \
    --action-group ag-muninn -a email exploitant "$COURRIEL_ALERTE" usecommonalertschema \
    --alert-type logalertv2 --only-show-errors -o none; then
    echo "   essai refusé : attendre le courriel « You've been added… » d'Azure, puis relancer" >&2
    echo "   bash infra/azure/11-alertes.sh --tester" >&2
    exit 1
  fi
  echo "   courriel d'essai envoyé : vérifier la boîte de réception (et les indésirables)"
else
  echo "   relancer avec --tester pour envoyer un courriel d'essai"
fi
