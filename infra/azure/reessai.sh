#!/usr/bin/env bash
# Reprise d'une commande `az` sur erreur passagère d'Azure (INC-05).
#
# Azure Resource Manager répond parfois « Too Many Requests » (429) ou « Service Unavailable »
# (503) pendant une livraison. Sans reprise, la livraison s'arrêtait entre l'API et la console,
# qui restaient sur deux versions différentes jusqu'à la livraison suivante.
#
# Le 26 octobre 2026, une livraison s'est arrêtée sur « (ServerTimeout) The request timed out »
# (INC-08), autre erreur passagère d'Azure Resource Manager, ajoutée à la liste.
#
# `az_tenace <arguments de az>` : lance `az`, et sur une erreur passagère seulement (429, 503,
# 504, ServerTimeout), recommence jusqu'à REESSAI_ESSAIS fois, avec une pause croissante
# (REESSAI_PAUSE_S, puis le double, etc.). Toute autre erreur est rendue tout de suite, telle quelle. La sortie standard
# de la commande réussie est rendue sans changement.

REESSAI_ESSAIS="${REESSAI_ESSAIS:-4}"
REESSAI_PAUSE_S="${REESSAI_PAUSE_S:-15}"

az_tenace() {
  local essai sortie erreur statut
  erreur=$(mktemp)
  for ((essai = 1; essai <= REESSAI_ESSAIS; essai++)); do
    statut=0
    sortie=$(az "$@" 2>"$erreur") || statut=$?
    if [ "$statut" -eq 0 ]; then
      rm -f "$erreur"
      if [ -n "$sortie" ]; then printf '%s\n' "$sortie"; fi
      return 0
    fi
    if ! grep -qE "Too Many Requests|Service Unavailable|Gateway Timeout|ServerTimeout|\(429\)|\(503\)|\(504\)" "$erreur" ||
      [ "$essai" -eq "$REESSAI_ESSAIS" ]; then
      cat "$erreur" >&2
      rm -f "$erreur"
      return "$statut"
    fi
    echo "Azure : erreur passagère (essai $essai sur $REESSAI_ESSAIS), nouvel essai dans $((REESSAI_PAUSE_S * essai)) s" >&2
    sleep "$((REESSAI_PAUSE_S * essai))"
  done
}

# Nouvelle révision d'une application après `az containerapp update` (INC-07).
#
# La réponse de `update` peut porter un `latestRevisionName` périmé : le 23 octobre 2026, elle a
# rendu la révision en service au lieu de celle qui venait d'être créée, et le script a contrôlé
# puis basculé l'ancienne. Le nom n'est donc jamais pris dans cette réponse : il est relu sur
# l'application jusqu'à ce que la révision la plus récente diffère de la révision en service et,
# si une condition est donnée, qu'elle la vérifie (condition JMESPath sur la révision, qui doit
# valoir vrai : image livrée, variable posée…).
#
# `nouvelle_revision <application> <révision en service> [condition]` : rend le nom, ou échoue
# après REVISION_ESSAIS lectures espacées de REVISION_PAUSE_S secondes, sans rien basculer.
# Relancer un script après un tel échec est sans risque : la révision déjà créée est retrouvée.

REVISION_ESSAIS="${REVISION_ESSAIS:-24}"
REVISION_PAUSE_S="${REVISION_PAUSE_S:-5}"

# `revision_conforme <application> <révision> <condition>` : vrai si la révision vérifie la
# condition JMESPath. Sert aussi à rendre un script relançable : rien à faire si la révision en
# service porte déjà la modification.
revision_conforme() {
  local verdict
  verdict=$(az_tenace containerapp revision show -g "$GROUPE" -n "$1" --revision "$2" \
    --query "$3" -o tsv) || return 1
  [ "${verdict,,}" = "true" ]
}

nouvelle_revision() {
  local app="$1" en_service="$2" condition="${3:-}" essai nom
  for ((essai = 1; essai <= REVISION_ESSAIS; essai++)); do
    nom=$(az_tenace containerapp show -g "$GROUPE" -n "$app" \
      --query properties.latestRevisionName -o tsv)
    if [ -n "$nom" ] && [ "$nom" != "$en_service" ]; then
      if [ -z "$condition" ] || revision_conforme "$app" "$nom" "$condition"; then
        printf '%s\n' "$nom"
        return 0
      fi
    fi
    if [ "$essai" -lt "$REVISION_ESSAIS" ]; then sleep "$REVISION_PAUSE_S"; fi
  done
  echo "Aucune nouvelle révision conforme pour $app (en service : $en_service)" >&2
  return 1
}
