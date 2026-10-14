#!/usr/bin/env bash
# Étape 5, partie 1 : socle Azure de Muninn (V1), créé par le porteur (R10).
# Crée : espace Log Analytics, registre d'images, environnement Container Apps, deux identités
# managées et leurs rôles sur le registre et sur Foundry, serveur PostgreSQL et ses deux bases.
#
# Prérequis : `az login` ; variable POSTGRES_MOT_DE_PASSE définie dans le shell, jamais écrite
# dans un fichier suivi (générer par exemple avec `openssl rand -hex 24`).
# Relançable : chaque ressource existante est laissée telle quelle.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
: "${POSTGRES_MOT_DE_PASSE:?Définir POSTGRES_MOT_DE_PASSE avant de lancer le script.}"

existe() { "$@" --only-show-errors >/dev/null 2>&1; }

echo "1/7 Espace Log Analytics $JOURNAUX (30 jours, plafond de 0,5 Go par jour)"
existe az monitor log-analytics workspace show -g "$GROUPE" -n "$JOURNAUX" ||
  az monitor log-analytics workspace create -g "$GROUPE" -n "$JOURNAUX" -l "$REGION" \
    --retention-time 30 --quota 0.5 --tags "$ETIQUETTE" --only-show-errors -o none

echo "2/7 Registre d'images $REGISTRE (Basic, compte administrateur désactivé)"
existe az acr show -g "$GROUPE" -n "$REGISTRE" ||
  az acr create -g "$GROUPE" -n "$REGISTRE" -l "$REGION" --sku Basic \
    --admin-enabled false --tags "$ETIQUETTE" --only-show-errors -o none

# Tirage des images par identité managée : le registre doit accepter les jetons d'audience ARM.
if [ "$(az acr config authentication-as-arm show -r "$REGISTRE" --query status -o tsv)" != "enabled" ]; then
  az acr config authentication-as-arm update -r "$REGISTRE" --status enabled --only-show-errors -o none
fi

echo "3/7 Environnement Container Apps $ENVIRONNEMENT_CA (consommation)"
if ! existe az containerapp env show -g "$GROUPE" -n "$ENVIRONNEMENT_CA"; then
  ws_id=$(az monitor log-analytics workspace show -g "$GROUPE" -n "$JOURNAUX" --query customerId -o tsv)
  ws_cle=$(az monitor log-analytics workspace get-shared-keys -g "$GROUPE" -n "$JOURNAUX" \
    --query primarySharedKey -o tsv)
  az containerapp env create -g "$GROUPE" -n "$ENVIRONNEMENT_CA" -l "$REGION" \
    --logs-workspace-id "$ws_id" --logs-workspace-key "$ws_cle" \
    --tags "$ETIQUETTE" --only-show-errors -o none
  unset ws_cle
fi

echo "4/7 Identités managées $IDENTITE_EXECUTION et $IDENTITE_DEPLOIEMENT"
for identite in "$IDENTITE_EXECUTION" "$IDENTITE_DEPLOIEMENT"; do
  existe az identity show -g "$GROUPE" -n "$identite" ||
    az identity create -g "$GROUPE" -n "$identite" -l "$REGION" --tags "$ETIQUETTE" \
      --only-show-errors -o none
done

echo "5/7 Rôles : AcrPull et Foundry User pour l'exécution ; AcrPush et assignation pour le déploiement"
registre_id=$(az acr show -g "$GROUPE" -n "$REGISTRE" --query id -o tsv)
foundry_id=$(az cognitiveservices account show -g "$GROUPE" -n "$FOUNDRY" --query id -o tsv)
execution_principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_EXECUTION" --query principalId -o tsv)
deploiement_principal=$(az identity show -g "$GROUPE" -n "$IDENTITE_DEPLOIEMENT" --query principalId -o tsv)
attribuer() { # principal, rôle, portée
  if [ -z "$(az role assignment list --assignee "$1" --role "$2" --scope "$3" --query '[0].id' -o tsv)" ]; then
    az role assignment create --assignee-object-id "$1" --assignee-principal-type ServicePrincipal \
      --role "$2" --scope "$3" --only-show-errors -o none
  fi
}
attribuer "$execution_principal" "AcrPull" "$registre_id"
attribuer "$execution_principal" "$ROLE_FOUNDRY_USER" "$foundry_id"
# Le déploiement met à jour des applications qui portent l'identité d'exécution : droit
# « assign » sur cette identité seulement.
attribuer "$deploiement_principal" "Managed Identity Operator" \
  "$(az identity show -g "$GROUPE" -n "$IDENTITE_EXECUTION" --query id -o tsv)"
attribuer "$deploiement_principal" "AcrPush" "$registre_id"

echo "6/7 Serveur PostgreSQL $POSTGRES (16, Burstable B1ms, 32 Go, accès depuis les services Azure)"
if ! existe az postgres flexible-server show -g "$GROUPE" -n "$POSTGRES"; then
  az postgres flexible-server create -g "$GROUPE" -n "$POSTGRES" -l "$REGION" \
    --version 16 --tier Burstable --sku-name Standard_B1ms --storage-size 32 \
    --admin-user "$POSTGRES_ADMIN" --admin-password "$POSTGRES_MOT_DE_PASSE" \
    --public-access 0.0.0.0 --high-availability Disabled --backup-retention 7 \
    --tags "$ETIQUETTE" --yes --only-show-errors -o none
fi

echo "7/7 Bases de données par environnement"
for env in "${ENVIRONNEMENTS_APP[@]}"; do
  base=$(base_de_donnees "$env")
  existe az postgres flexible-server db show -g "$GROUPE" -s "$POSTGRES" -d "$base" ||
    az postgres flexible-server db create -g "$GROUPE" -s "$POSTGRES" -d "$base" \
      --only-show-errors -o none
done

echo "Socle prêt. Étape suivante : 02-image-initiale.sh"
