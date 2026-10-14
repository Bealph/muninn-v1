#!/usr/bin/env bash
# Étape 5, partie 2 : première image dans le registre, construite sur le poste du porteur.
# Les applications Container Apps ne peuvent être créées qu'avec une image existante ; ensuite,
# c'est la livraison continue (étape 6) qui pousse les images.
#
# Prérequis : `az login`, Docker lancé, dépôt sur un commit de main sans modification locale.

set -euo pipefail
source "$(dirname "$0")/parametres.sh"
cd "$(git rev-parse --show-toplevel)"

if [ -n "$(git status --porcelain)" ]; then
  echo "Le dépôt a des modifications locales : l'image ne correspondrait à aucun commit." >&2
  exit 1
fi
sha=$(git rev-parse HEAD)
image="$REGISTRE.azurecr.io/muninn:$sha"

az acr login -n "$REGISTRE" --only-show-errors
docker build -f docker/Dockerfile --build-arg GIT_SHA="$sha" -t "$image" .
docker push "$image"
echo "Image poussée : $image"
echo "Étape suivante : 03-applications.sh"
