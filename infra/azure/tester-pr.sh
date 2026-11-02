#!/usr/bin/env bash
# Révision de test d'une PR (C19), lancée par le job « test » de la CI : sert l'image de la PR sur
# l'application de test ca-muninn-api-test (infra/azure/15-test.sh), puis la contrôle :
#   1. l'application n'a aucun secret (le code d'une PR n'en lit aucun) ;
#   2. nouvelle révision avec l'image <registre de test>/muninn:<sha> ; en révision unique, elle
#      remplace la précédente dès qu'elle démarre ; si elle ne démarre pas, la précédente reste ;
#   3. contrôles à l'adresse de l'application : /version sert le SHA de la PR, /health répond,
#      un appel réel au modèle A aboutit (identité, rôle et point d'accès) ;
#   4. ménage : seules les 10 images les plus récentes restent dans le registre de test.
# La préproduction et la production ne sont jamais touchées.
#
# Usage : bash infra/azure/tester-pr.sh <sha>
# Prérequis : az connecté avec id-muninn-test ; image <registre de test>/muninn:<sha> poussée.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
source "$(dirname "$0")/reessai.sh"

sha="${1:?SHA du commit à tester}"
image="$REGISTRE_TEST.azurecr.io/muninn:$sha"
IMAGES_GARDEES=10
# Attente du SHA de la PR : 60 lectures espacées de 5 s (réglables pour les tests).
ATTENTE_ESSAIS="${ATTENTE_ESSAIS:-60}"
ATTENTE_PAUSE_S="${ATTENTE_PAUSE_S:-5}"

contient() { [[ "$1" == *"$2"* ]]; }

echo "1/4 $APP_TEST : aucun secret"
secrets=$(az_tenace containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query "length(properties.configuration.secrets || \`[]\`)" -o tsv)
if [ "$secrets" != "0" ]; then
  echo "$APP_TEST porte $secrets secret(s) : le code d'une PR ne doit en lire aucun." >&2
  exit 1
fi

echo "2/4 Révision avec $image"
az_tenace containerapp update -g "$GROUPE" -n "$APP_TEST" --image "$image" \
  --set-env-vars GIT_SHA="$sha" --only-show-errors -o none
url="https://$(az_tenace containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query properties.configuration.ingress.fqdn -o tsv)"
if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "url=$url/docs" >>"$GITHUB_OUTPUT"; fi

echo "3/4 Contrôles sur $url"
# Démarrage de la révision, puis démarrage à froid (zéro réplique au repos) : 5 minutes au plus.
servi=""
for _ in $(seq 1 "$ATTENTE_ESSAIS"); do
  servi=$(curl -fsS -m 20 "$url/version" 2>/dev/null || true)
  if contient "$servi" "\"git_sha\":\"$sha\""; then break; fi
  sleep "$ATTENTE_PAUSE_S"
done
if ! contient "$servi" "\"git_sha\":\"$sha\""; then
  echo "L'application de test ne sert pas $sha (réponse : ${servi:-aucune})." >&2
  az_tenace containerapp revision list -g "$GROUPE" -n "$APP_TEST" \
    --query "[].{nom:name, active:properties.active, etat:properties.runningState, image:properties.template.containers[0].image}" \
    -o table >&2 || true
  exit 1
fi
contient "$(curl -fsS -m 20 "$url/health")" '"status":"ok"' ||
  { echo "/health ne répond pas ok" >&2; exit 1; }
reponse=$(curl -fsS -m 90 -X POST "$url/llm/essai" -H "Content-Type: application/json" \
  -d '{"question":"Reponds juste : ok","modele":"A"}') ||
  { echo "Appel au modèle A en échec" >&2; exit 1; }
contient "$reponse" '"fournisseur":"azure"' ||
  { echo "Le modèle A n'a pas répondu par Azure : $reponse" >&2; exit 1; }
echo "   /version = $sha ; /health ok ; modèle A par Azure"

echo "4/4 Registre de test : les $IMAGES_GARDEES images les plus récentes, pas plus"
# Ménage seulement : un échec ne dit rien du code de la PR, il est signalé sans bloquer.
if anciennes=$(az_tenace acr repository show-tags -n "$REGISTRE_TEST" --repository muninn \
  --orderby time_desc -o tsv); then
  tail -n +"$((IMAGES_GARDEES + 1))" <<<"$anciennes" | while read -r etiquette; do
    if [ -n "$etiquette" ] && [ "$etiquette" != "$sha" ]; then
      az_tenace acr repository delete -n "$REGISTRE_TEST" --image "muninn:$etiquette" --yes \
        --only-show-errors -o none ||
        echo "::warning::image muninn:$etiquette non supprimée du registre de test"
    fi
  done
else
  echo "::warning::liste des images du registre de test illisible : ménage non fait"
fi

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "### Révision de test de la PR (C19)"
    echo "- Image : \`$image\`"
    echo "- Contrôles : \`/version\` = \`$sha\`, \`/health\` ok, modèle A par Azure"
    echo "- Interface : [$url/docs]($url/docs) (application de test, sans base de données)"
  } >>"$GITHUB_STEP_SUMMARY"
fi
echo "Révision de test contrôlée : $sha"
