#!/usr/bin/env bash
# Consulter la base d'un environnement, en lecture seule, depuis le poste du porteur.
#
# Usage (Git Bash, depuis la racine du dépôt, après `az login`) :
#   bash infra/azure/consulter-base.sh [production|preproduction] [--interactif] [--traitements]
#
# Sans option : affiche un aperçu (tables, versions chargées, lignes d'exemple).
# Avec --interactif : ouvre psql, pour des requêtes libres.
# Avec --traitements : se connecte avec le rôle des traitements (`<base>_traitements`, D-85), le
# seul qui voit le schéma `app` ; l'aperçu montre les mesures des traitements, jamais le contenu
# d'un dossier.
#
# Ce que fait le script, et ce qu'il défait :
# - ouvre le pare-feu du serveur PostgreSQL à la seule adresse IP publique de ce poste, par une
#   règle temporaire, supprimée à la sortie du script, même en cas d'erreur ou d'interruption ;
# - se connecte avec le rôle de l'API, en lecture seule (`<base>_api`), et force en plus les
#   transactions en lecture seule ;
# - lit l'adresse de connexion dans le secret de l'application API, sans jamais l'afficher ni
#   l'écrire sur disque.
# Il ne modifie aucune donnée. Le client psql tourne dans un conteneur Docker (postgres:16-alpine).
set -euo pipefail

source "$(dirname "$0")/parametres.sh"

env="production"
interactif=0
traitements=0
for arg in "$@"; do
  case "$arg" in
    production | preproduction) env="$arg" ;;
    --interactif) interactif=1 ;;
    --traitements) traitements=1 ;;
    *) echo "Argument inconnu : $arg" >&2; exit 2 ;;
  esac
done

api=$(app_api "$env")
regle="consultation-porteur"

command -v docker > /dev/null || { echo "Docker est requis (client psql en conteneur)." >&2; exit 1; }
docker info > /dev/null 2>&1 || { echo "Docker ne répond pas : démarre Docker Desktop." >&2; exit 1; }

ip=$(curl -fsS --max-time 10 https://api.ipify.org)
[[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Adresse IP publique illisible." >&2; exit 1; }

fermer() {
  echo "Fermeture du pare-feu : suppression de la règle « $regle »…"
  az postgres flexible-server firewall-rule delete -g "$GROUPE" -s "$POSTGRES" -n "$regle" \
    --yes --only-show-errors -o none \
    || echo "ATTENTION : règle « $regle » non supprimée ; la retirer à la main dans le portail." >&2
}
trap fermer EXIT

echo "Ouverture du pare-feu de $POSTGRES à $ip seulement (règle temporaire « $regle »)…"
az postgres flexible-server firewall-rule create -g "$GROUPE" -s "$POSTGRES" -n "$regle" \
  --start-ip-address "$ip" --end-ip-address "$ip" --only-show-errors -o none

# Adresse de connexion du rôle choisi, gardée en mémoire seulement. Dans les deux cas, les
# transactions sont forcées en lecture seule.
if [[ $traitements -eq 1 ]]; then
  secret=database-url-traitements; suffixe=traitements
else
  secret=database-url; suffixe=api
fi
URL_BASE=$(az containerapp secret show -g "$GROUPE" -n "$api" --secret-name "$secret" \
  --query value -o tsv --only-show-errors)
[[ "$URL_BASE" == postgresql://*_"$suffixe":* ]] || { echo "Le secret $secret de $api n'est pas celui du rôle $suffixe." >&2; exit 1; }
export URL_BASE
export PGOPTIONS="-c default_transaction_read_only=on"
echo "Connexion à $(base_de_donnees "$env") avec le rôle $(base_de_donnees "$env")_$suffixe, en lecture seule."

lancer_psql() { # options supplémentaires de psql
  # -i transmet l'entrée (requêtes de l'aperçu) ; -t seulement dans un vrai terminal.
  local tty=(-i)
  [[ -t 0 && -t 1 ]] && tty=(-it)
  local prefixe=()
  # Terminal mintty (Git Bash hors VS Code) : docker -it a besoin de winpty.
  if [[ "${tty[*]}" == "-it" && "${TERM_PROGRAM:-}" != "vscode" ]] && command -v winpty > /dev/null; then
    prefixe=(winpty)
  fi
  # Guillemets simples voulus : URL_BASE est développée dans le conteneur, jamais sur la ligne de
  # commande de l'hôte.
  # shellcheck disable=SC2016
  "${prefixe[@]}" docker run --rm "${tty[@]}" -e URL_BASE -e PGOPTIONS postgres:16-alpine \
    sh -c 'exec psql "$URL_BASE" "$@"' psql "$@"
}

if [[ $interactif -eq 1 ]]; then
  cat << 'AIDE'

Quelques commandes :
  \dt ref.*            tables des référentiels
  \dt market.*         tables des agrégats Sirene
  \d ref.communes      colonnes d'une table
  select * from ref.communes where name = 'Montreuil';
  \q                   quitter (le pare-feu se referme ensuite)
AIDE
  lancer_psql
elif [[ $traitements -eq 1 ]]; then
  lancer_psql -P pager=off << 'SQL'
\echo '== Traitements enregistrés, par issue (30 jours au plus, D-82)'
select issue, count(*) as nombre, min(recu_le) as premier, max(recu_le) as dernier
  from app.traitements group by issue order by issue;
\echo '== Dix derniers traitements : mesures seulement, aucun contenu'
select to_char(recu_le, 'YYYY-MM-DD HH24:MI:SS') as recu_le, route, scenario_id, issue,
       code_refus, categorie, statut, a_verifier, outils, cout_micro_eur, duree_ms
  from app.traitements order by recu_le desc limit 10;
\echo '== Dossiers par état, messages, corrections'
select 'dossiers ' || etat as quoi, count(*) from app.dossiers group by etat
union all select 'messages', count(*) from app.messages
union all select 'corrections', count(*) from app.corrections;
SQL
else
  lancer_psql -P pager=off << 'SQL'
\echo '== Tables et nombre de lignes (toutes versions, publiées et retirées)'
select 'ref.communes' as table_, count(*) as lignes from ref.communes
union all select 'ref.postal_codes', count(*) from ref.postal_codes
union all select 'ref.lexicon_terms', count(*) from ref.lexicon_terms
union all select 'ref.trade_lexicons', count(*) from ref.trade_lexicons
union all select 'ref.dataset_versions', count(*) from ref.dataset_versions
union all select 'ref.commune_source_gaps', count(*) from ref.commune_source_gaps
union all select 'ref.load_rejections', count(*) from ref.load_rejections
union all select 'ref.naf_trades', count(*) from ref.naf_trades
union all select 'market.sirene_counts', count(*) from market.sirene_counts
union all select 'market.sirene_runs', count(*) from market.sirene_runs;
\echo '== Versions chargées (traçabilité)'
select dataset, source_id, source_date, rows_read as lues, rows_loaded as chargees,
       rows_filtered as filtrees, rows_rejected as rejets, status,
       to_char(retrieved_at, 'YYYY-MM-DD HH24:MI') as charge_le
  from ref.dataset_versions order by id;
\echo '== Lexiques'
select l.trade, l.version, l.status, count(t.id) as termes
  from ref.trade_lexicons l left join ref.lexicon_terms t on t.lexicon_id = l.id
 group by l.id, l.trade, l.version, l.status order by l.id;
\echo '== Calculs Sirene'
select stock_date, naf_revision, rows_after_filter as etablissements_retenus,
       small_cell_threshold as seuil_secret, status from market.sirene_runs order by id;
\echo '== Exemple : les communes « Montreuil » et leurs codes postaux'
select c.insee_code, c.name, c.department_code, p.postal_code
  from ref.communes c left join ref.postal_codes p on p.insee_code = c.insee_code
 where c.name = 'Montreuil' order by c.insee_code;
\echo '== Exemple : dix termes du lexique publié'
select term, category, source_id, license from ref.lexicon_terms
 where lexicon_id = (select id from ref.trade_lexicons where status = 'published' and trade = 'plomberie')
 order by term limit 10;
\echo '== Exemple : plomberie (43.22A) en Seine-Saint-Denis, calcul Sirene publié'
select naf_code, department_code, headcount_band, legal_category_group,
       establishments_count, is_masked
  from market.sirene_counts where naf_code = '43.22A' and department_code = '93'
   and run_id = (select id from market.sirene_runs where status = 'published')
 order by headcount_band, legal_category_group;
SQL
fi
unset URL_BASE
