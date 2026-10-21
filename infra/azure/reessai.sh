#!/usr/bin/env bash
# Reprise d'une commande `az` sur erreur passagère d'Azure (INC-05).
#
# Azure Resource Manager répond parfois « Too Many Requests » (429) ou « Service Unavailable »
# (503) pendant une livraison. Sans reprise, la livraison s'arrêtait entre l'API et la console,
# qui restaient sur deux versions différentes jusqu'à la livraison suivante.
#
# `az_tenace <arguments de az>` : lance `az`, et sur une erreur passagère seulement (429, 503,
# 504), recommence jusqu'à REESSAI_ESSAIS fois, avec une pause croissante (REESSAI_PAUSE_S, puis
# le double, etc.). Toute autre erreur est rendue tout de suite, telle quelle. La sortie standard
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
    if ! grep -qE "Too Many Requests|Service Unavailable|Gateway Timeout|\(429\)|\(503\)|\(504\)" "$erreur" ||
      [ "$essai" -eq "$REESSAI_ESSAIS" ]; then
      cat "$erreur" >&2
      rm -f "$erreur"
      return "$statut"
    fi
    echo "Azure : erreur passagère (essai $essai sur $REESSAI_ESSAIS), nouvel essai dans $((REESSAI_PAUSE_S * essai)) s" >&2
    sleep "$((REESSAI_PAUSE_S * essai))"
  done
}
