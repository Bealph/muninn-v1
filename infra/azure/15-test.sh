#!/usr/bin/env bash
# C19 : révision de test par PR. Le job « test » de la CI construit l'image de chaque PR, la
# pousse dans un registre à part et la sert sur une application à part, puis la contrôle.
#
# Crée, ou met en conformité :
#   1. le registre crmuninntest (Basic) : le code d'une PR ne peut jamais écraser une image de
#      crmuninn, d'où sortent la préproduction et la production ;
#   2. une image de départ, copiée de celle que sert la préproduction ;
#   3. AcrPull sur ce registre pour id-muninn-evaluation, l'identité d'exécution de
#      l'application de test : elle ne peut déjà qu'appeler le modèle (06-evaluation.sh) ;
#   4. l'application ca-muninn-api-test, dans l'environnement cae-muninn : sans base, sans
#      secret, révision unique, une réplique au plus, zéro au repos. La préproduction n'est
#      jamais touchée : ni son modèle de révision, ni son trafic, ni son retour arrière ;
#   5. l'identité id-muninn-test, distincte des autres ;
#   6. ses droits, et rien d'autre : le rôle personnalisé « Muninn test PR » (roles/test-pr.json,
#      sans aucune suppression) sur l'application de test, sur l'environnement (rattachement) et
#      sur id-muninn-evaluation (assignation) ; AcrPush et AcrDelete sur crmuninntest seulement ;
#   7. la confiance OIDC avec l'environnement GitHub « test » (sujet immuable du dépôt) ;
#   8. l'environnement GitHub « test », ouvert aux branches des PR, et sa variable
#      AZURE_CLIENT_ID (une variable, pas un secret).
#
# Aucun secret. Coût : registre Basic, environ 4,5 € par mois ; application à zéro réplique au
# repos ; appels au modèle facturés à l'usage (un appel court par PR).
# Prérequis : `az login` (propriétaire du groupe de ressources), `gh auth login` (administration
# du dépôt). Relançable.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"

# Une identité ou un rôle tout juste créés ne sont visibles qu'après quelques dizaines de
# secondes (réplication d'Entra ID) : quelques essais espacés avant d'abandonner.
reessayer() { # description, commande…
  local quoi="$1" essai
  shift
  for essai in 1 2 3 4 5 6; do
    if "$@"; then return 0; fi
    if [ "$essai" = 6 ]; then
      echo "$quoi : échec ; relancer le script dans une minute." >&2
      exit 1
    fi
    echo "$quoi : réplication d'Azure en cours, nouvel essai dans 20 s ($essai/6)"
    sleep 20
  done
}

attribuer() { # principal, identifiant du rôle, portée
  if az role assignment list --scope "$3" --query "[?principalId=='$1'].roleDefinitionId" -o tsv |
    grep -q "$2"; then
    return 0
  fi
  reessayer "Rôle $2 sur ${3##*/}" az role assignment create --assignee-object-id "$1" \
    --assignee-principal-type ServicePrincipal --role "$2" --scope "$3" --only-show-errors -o none
}

groupe_id=$(az group show -n "$GROUPE" --query id -o tsv)
environnement_id=$(az containerapp env show -g "$GROUPE" -n "$ENVIRONNEMENT_CA" --query id -o tsv)
evaluation_id=$(az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" --query id -o tsv)
evaluation_client=$(az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" --query clientId -o tsv)
evaluation_principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_EVALUATION" \
  --query principalId -o tsv)

echo "1/8 Registre $REGISTRE_TEST (Basic, compte administrateur désactivé)"
if ! az acr show -g "$GROUPE" -n "$REGISTRE_TEST" --only-show-errors -o none 2>/dev/null; then
  az acr create -g "$GROUPE" -n "$REGISTRE_TEST" -l "$REGION" --sku Basic --admin-enabled false \
    --tags "$ETIQUETTE" --only-show-errors -o none
fi
registre_test_id=$(az acr show -g "$GROUPE" -n "$REGISTRE_TEST" --query id -o tsv)

echo "2/8 Image de départ : celle que sert la préproduction"
api_preprod=$(app_api preproduction)
en_service=$(az containerapp revision list -g "$GROUPE" -n "$api_preprod" \
  --query "[?properties.trafficWeight==\`100\`].name | [0]" -o tsv)
if [ -z "$en_service" ]; then
  echo "Aucune révision de $api_preprod à 100 % du trafic (bascule en cours ?) : relancer." >&2
  exit 1
fi
image_preprod=$(az containerapp revision show -g "$GROUPE" -n "$api_preprod" \
  --revision "$en_service" --query "properties.template.containers[0].image" -o tsv)
sha="${image_preprod##*:}"
if ! az acr repository show -n "$REGISTRE_TEST" --image "muninn:$sha" --only-show-errors \
  -o none 2>/dev/null; then
  az acr import -n "$REGISTRE_TEST" --source "$image_preprod" --image "muninn:$sha" \
    --only-show-errors -o none
fi
echo "   $REGISTRE_TEST.azurecr.io/muninn:$sha"

echo "3/8 AcrPull sur $REGISTRE_TEST pour $IDENTITE_EVALUATION"
attribuer "$evaluation_principal" "$ROLE_ACR_PULL" "$registre_test_id"

echo "4/8 Application $APP_TEST : sans base ni secret, révision unique"
if ! az containerapp show -g "$GROUPE" -n "$APP_TEST" --only-show-errors -o none 2>/dev/null; then
  # Le droit de tirer l'image vient d'être donné : la création peut attendre sa réplication.
  reessayer "Création de $APP_TEST" az containerapp create -g "$GROUPE" -n "$APP_TEST" \
    --environment "$ENVIRONNEMENT_CA" --image "$REGISTRE_TEST.azurecr.io/muninn:$sha" \
    --registry-server "$REGISTRE_TEST.azurecr.io" --registry-identity "$evaluation_id" \
    --user-assigned "$evaluation_id" --ingress external --target-port 8000 \
    --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi --revisions-mode single \
    --tags "$ETIQUETTE" --only-show-errors -o none \
    --env-vars ENVIRONMENT=test GIT_SHA="$sha" LLM_FOURNISSEUR=azure \
    AZURE_AI_ENDPOINT="$FOUNDRY_ENDPOINT" AZURE_AI_MODEL_A="$MODELE_A" \
    AZURE_AI_MODEL_B="$MODELE_B" AZURE_CLIENT_ID="$evaluation_client"
else
  # Mise en conformité : le code d'une PR peut modifier l'application (droit d'écriture). Chaque
  # passage du script réimpose l'échelle et les ressources (coût et quota de l'environnement
  # bornés) et retire toute variable ajoutée hors de la liste ci-dessous.
  az containerapp update -g "$GROUPE" -n "$APP_TEST" \
    --image "$REGISTRE_TEST.azurecr.io/muninn:$sha" --min-replicas 0 --max-replicas 1 \
    --cpu 0.5 --memory 1.0Gi --only-show-errors -o none \
    --replace-env-vars ENVIRONMENT=test GIT_SHA="$sha" LLM_FOURNISSEUR=azure \
    AZURE_AI_ENDPOINT="$FOUNDRY_ENDPOINT" AZURE_AI_MODEL_A="$MODELE_A" \
    AZURE_AI_MODEL_B="$MODELE_B" AZURE_CLIENT_ID="$evaluation_client"
fi
app_test_id=$(az containerapp show -g "$GROUPE" -n "$APP_TEST" --query id -o tsv)
secrets=$(az containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query "length(properties.configuration.secrets || \`[]\`)" -o tsv)
if [ "$secrets" != "0" ]; then
  echo "$APP_TEST porte $secrets secret(s) : refusé, l'application de test n'en a aucun." >&2
  exit 1
fi
# Registre et identité : constatés, pas réimposés ; un écart se corrige à la main, après examen.
registres=$(az containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query "join(',', properties.configuration.registries[].server)" -o tsv)
identites=$(az containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query "join(',', keys(identity.userAssignedIdentities || \`{}\`))" -o tsv)
if [ "$registres" != "$REGISTRE_TEST.azurecr.io" ] || [ "${identites,,}" != "${evaluation_id,,}" ]; then
  echo "$APP_TEST : registre ($registres) ou identité ($identites) inattendus : examiner." >&2
  exit 1
fi

echo "5/8 Identité $IDENTITE_TEST"
if ! az identity show -g "$GROUPE" -n "$IDENTITE_TEST" --only-show-errors -o none 2>/dev/null; then
  az identity create -g "$GROUPE" -n "$IDENTITE_TEST" -l "$REGION" --tags "$ETIQUETTE" \
    --only-show-errors -o none
fi
principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_TEST" --query principalId -o tsv)
client=$(az identity show -g "$GROUPE" -n "$IDENTITE_TEST" --query clientId -o tsv)

echo "6/8 Rôle « $ROLE_TEST » (sans suppression), AcrPush et AcrDelete sur $REGISTRE_TEST"
definition=$(mktemp --suffix=.json)
trap 'rm -f "$definition"' EXIT
sed "s#__PORTEE__#$groupe_id#" "$(dirname "$0")/roles/test-pr.json" >"$definition"
role_id=$(az role definition list --custom-role-only true --scope "$groupe_id" \
  --query "[?roleName=='$ROLE_TEST'].name | [0]" -o tsv)
if [ -n "$role_id" ]; then
  # Mise en conformité : la définition versionnée fait foi.
  sed -i "0,/{/s//{\"Id\": \"$role_id\",/" "$definition"
fi
# Sous Git Bash, az (Python Windows) ne lit pas un chemin /tmp : chemin Windows si cygpath existe.
fichier=$(cygpath -w "$definition" 2>/dev/null || echo "$definition")
if [ -z "$role_id" ]; then
  # Identifiant pris dans la réponse : une relecture immédiate peut ne pas encore le voir.
  role_id=$(az role definition create --role-definition "@$fichier" --only-show-errors \
    --query name -o tsv)
else
  az role definition update --role-definition "@$fichier" --only-show-errors -o none
fi
for portee in "$app_test_id" "$environnement_id" "$evaluation_id"; do
  attribuer "$principal" "$role_id" "$portee"
done
attribuer "$principal" "$ROLE_ACR_PUSH" "$registre_test_id"
attribuer "$principal" "$ROLE_ACR_DELETE" "$registre_test_id"

echo "7/8 Confiance OIDC avec l'environnement GitHub « test »"
nom="github-test"
sujet="$SUJET_OIDC_PREFIXE:environment:test"
actuel=$(az identity federated-credential show -g "$GROUPE" --identity-name "$IDENTITE_TEST" \
  -n "$nom" --query subject -o tsv 2>/dev/null || true)
if [ -z "$actuel" ]; then
  az identity federated-credential create -g "$GROUPE" --identity-name "$IDENTITE_TEST" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
elif [ "$actuel" != "$sujet" ]; then
  az identity federated-credential update -g "$GROUPE" --identity-name "$IDENTITE_TEST" \
    -n "$nom" --issuer "https://token.actions.githubusercontent.com" \
    --subject "$sujet" --audiences "api://AzureADTokenExchange" --only-show-errors -o none
fi

echo "8/8 Environnement GitHub « test », ouvert aux branches des PR (comme « evaluation »)"
gh api -X PUT "repos/$DEPOT_GITHUB/environments/test" --silent --input - <<'EOF'
{"deployment_branch_policy": null}
EOF
gh variable set AZURE_CLIENT_ID -R "$DEPOT_GITHUB" --env test --body "$client"

echo
echo "Rôles de $IDENTITE_TEST (attendu : « $ROLE_TEST » trois fois, AcrPush, AcrDelete) :"
az role assignment list --all --query "[?principalId=='$principal'].[roleDefinitionName, scope]" \
  -o tsv
echo "Rôles de $IDENTITE_EVALUATION (attendu : Foundry User, AcrPull sur $REGISTRE_TEST) :"
az role assignment list --all \
  --query "[?principalId=='$evaluation_principal'].[roleDefinitionName, scope]" -o tsv
echo "Application de test : https://$(az containerapp show -g "$GROUPE" -n "$APP_TEST" \
  --query properties.configuration.ingress.fqdn -o tsv)/docs"
