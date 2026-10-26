#!/usr/bin/env bash
# Sprint 5, étape 6 : voix simulée branchée sur Azure AI Speech (D-50, D-88, V-12, CA-8).
#
#   1. lecture (rien n'est modifié) de la ressource Foundry `FOUNDRY` de parametres.sh : région,
#      sous-domaine personnalisé, identifiant ARM. Le service Speech de cette ressource (kind
#      AIServices, West Europe) sert la synthèse et la transcription ; l'identité de l'API
#      (`id-muninn-execution`) y a déjà le rôle Foundry User : aucun rôle à créer ;
#   2. pour l'API de chaque environnement (les deux par défaut, ou ceux passés en arguments) :
#      VOIX_FOURNISSEUR=azure, SPEECH_REGION, SPEECH_ENDPOINT (sous-domaine de la ressource),
#      SPEECH_RESOURCE_ID ; comme deployer.sh, la nouvelle révision ne reçoit le trafic qu'après
#      un contrôle : santé, puis une synthèse réelle (SC-10) à son adresse propre ;
#   3. essai final sur l'adresse publique : `POST /v1/demo/voice/synthesis` (SC-10) rend 200.
# Ces réglages ne sont pas des secrets (authentification Entra sans clé, identité managée).
#
# Relançable : si la révision en service porte déjà les quatre valeurs, rien n'est changé ; seul
# l'essai final est rejoué. Une révision créée par un passage interrompu est retrouvée
# (`nouvelle_revision`). Prérequis : l'image en service contient les routes `/v1/demo/voice/*`
# (sans elles, le contrôle échoue et le trafic reste où il est).
#
# Coût (API officielle des prix de Microsoft, lue le 26 octobre 2026, West Europe) : synthèse
# neuronale 13,20 € par million de caractères ; transcription rapide 0,32 € par heure d'audio. Un
# dialogue du jeu fait au plus 1 141 caractères (SC-Q4), soit environ 0,015 € de synthèse ;
# l'essai de ce script (SC-10, 4 tours, moins de 200 caractères) coûte moins de 0,003 € par
# synthèse, deux fois par environnement au plus.
# Prérequis : az connecté. Usage : bash infra/azure/13-voix.sh [preproduction] [production]

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

# L'identifiant ARM commence par « /subscriptions/ » : sans MSYS_NO_PATHCONV (posé par
# parametres.sh), Git Bash le transformerait en chemin Windows dans les arguments de az.
if [ "${MSYS_NO_PATHCONV:-}" != "1" ]; then
  echo "MSYS_NO_PATHCONV=1 attendu (parametres.sh) : arrêt." >&2
  exit 1
fi
if [ "$#" -gt 0 ]; then environnements=("$@"); else environnements=("${ENVIRONNEMENTS_APP[@]}"); fi
ESSAI='{"scenario_id":"SC-10"}'

attendre() {
  for _ in $(seq 1 36); do
    # Réponse jetée par bash, pas par curl : le curl de Windows refuse « -o /dev/null ».
    if curl -fsS -m 20 "$1" >/dev/null; then return 0; fi
    sleep 5
  done
  echo "Pas de réponse de $1" >&2
  return 1
}

# Synthèse réelle d'un scénario court : 200 et au moins un extrait audio. La révision porte
# VOIX_FOURNISSEUR=azure (condition vérifiée) : un 200 vient donc d'Azure AI Speech, une panne du
# service rendrait 503 `voice_unavailable`.
synthese() {
  local reponse
  # Réponse gardée en variable : avec pipefail, `curl | grep -q` échouerait quand grep s'arrête
  # avant la fin d'une réponse longue (curl reçoit SIGPIPE).
  reponse=$(curl -fsS -m 90 -X POST "$1/v1/demo/voice/synthesis" \
    -H "Content-Type: application/json" -d "$ESSAI") || return 1
  grep -qE '"audio_base64": *"[A-Za-z0-9+/]' <<<"$reponse"
}

echo "1/3 Ressource Foundry $FOUNDRY (lecture seule)"
region=$(az_tenace cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --query location -o tsv)
sous_domaine=$(az_tenace cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" \
  --query properties.customSubDomainName -o tsv)
ressource=$(az_tenace cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --query id -o tsv)
case "$ressource" in
  /subscriptions/*/providers/Microsoft.CognitiveServices/accounts/*) ;;
  *) echo "Identifiant ARM inattendu pour $FOUNDRY : arrêt." >&2; exit 1 ;;
esac
if [ -z "$region" ] || [ -z "$sous_domaine" ]; then
  echo "Région ou sous-domaine absent sur $FOUNDRY : arrêt." >&2
  exit 1
fi
point_acces="https://$sous_domaine.cognitiveservices.azure.com"
echo "   région $region ; point d'accès $point_acces"

# Les quatre variables, chacune avec sa valeur exacte (noms uniques dans un conteneur). Un
# identifiant ARM mutilé par Git Bash ne vérifierait pas la condition : la révision serait refusée.
VOIX_EN_PLACE="length(properties.template.containers[0].env[?(name=='VOIX_FOURNISSEUR' && value=='azure') || (name=='SPEECH_REGION' && value=='$region') || (name=='SPEECH_ENDPOINT' && value=='$point_acces') || (name=='SPEECH_RESOURCE_ID' && value=='$ressource')]) == \`4\`"

for env in "${environnements[@]}"; do
  api=$(app_api "$env")
  echo "2/3 API $api : réglages de la voix et révision contrôlée"
  precedente=$(az_tenace containerapp revision list -g "$GROUPE" -n "$api" \
    --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
  if revision_conforme "$api" "$precedente" "$VOIX_EN_PLACE"; then
    echo "   déjà en place sur $precedente"
  else
    az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
      --revision-weight "$precedente=100" --only-show-errors -o none
    az_tenace containerapp update -g "$GROUPE" -n "$api" --only-show-errors -o none \
      --set-env-vars VOIX_FOURNISSEUR=azure SPEECH_REGION="$region" \
      SPEECH_ENDPOINT="$point_acces" SPEECH_RESOURCE_ID="$ressource"
    # Nom relu sur l'application, jamais pris dans la réponse de `update` (INC-07).
    nouvelle=$(nouvelle_revision "$api" "$precedente" "$VOIX_EN_PLACE")
    fqdn=$(az_tenace containerapp revision show -g "$GROUPE" -n "$api" --revision "$nouvelle" \
      --query properties.fqdn -o tsv)
    if ! attendre "https://$fqdn/health"; then
      echo "Contrôle échoué : le trafic reste sur $precedente" >&2
      exit 1
    fi
    if ! synthese "https://$fqdn"; then
      echo "La synthèse échoue sur $nouvelle : le trafic reste sur $precedente" >&2
      exit 1
    fi
    az_tenace containerapp ingress traffic set -g "$GROUPE" -n "$api" \
      --revision-weight "$nouvelle=100" --only-show-errors -o none
    echo "   trafic : 100 % sur $nouvelle (précédente conservée : $precedente)"
  fi

  echo "3/3 Essai : synthèse de SC-10 sur l'adresse publique"
  public=$(az_tenace containerapp show -g "$GROUPE" -n "$api" \
    --query properties.configuration.ingress.fqdn -o tsv)
  if ! synthese "https://$public"; then
    echo "La synthèse échoue sur $public : voir docs/exploitation.md, section 6" >&2
    exit 1
  fi
  echo "   synthèse rendue (200) ; écran « Démonstration » de la console prêt."
done
