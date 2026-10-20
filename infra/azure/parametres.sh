# shellcheck shell=bash disable=SC2034
# Paramètres communs des scripts Azure de Muninn (V1). Aucun secret ici.
# Chargé par les autres scripts : `source infra/azure/parametres.sh`.

# Git Bash convertit les arguments commençant par « / » en chemins Windows, ce qui casse les
# identifiants de ressources Azure. Sans effet hors Git Bash.
export MSYS_NO_PATHCONV=1

GROUPE="adialloRG"
REGION="francecentral"
# Étiquette posée sur toutes les ressources de Muninn : le budget filtre sur elle, car le groupe
# de ressources héberge aussi d'autres projets.
ETIQUETTE="projet=muninn"

JOURNAUX="log-muninn"
REGISTRE="crmuninn"
ENVIRONNEMENT_CA="cae-muninn"
POSTGRES="psql-muninn"
POSTGRES_ADMIN="muninnadmin"

# Identités managées : l'une pour l'exécution (tirer les images, appeler le modèle), l'autre pour
# le déploiement depuis GitHub Actions (OIDC, sans secret).
IDENTITE_EXECUTION="id-muninn-execution"
# Évaluation de l'agent en CI (D-64) : identité à part, un seul droit (appeler le modèle).
IDENTITE_EVALUATION="id-muninn-evaluation"
IDENTITE_DEPLOIEMENT="id-muninn-deploiement"
DEPOT_GITHUB="Bealph/Muninn"
# Sujet OIDC « immuable » du dépôt (identifiants du compte et du dépôt) : voir oidc-github.sh.
SUJET_OIDC_PREFIXE="repo:Bealph@60009382/Muninn@1415464389"

# Ressource Azure AI Foundry des modèles A et B (D-46).
FOUNDRY="adialloext-muninn1-resource"
FOUNDRY_ENDPOINT="https://adialloext-muninn1-resource.services.ai.azure.com"
MODELE_A="gpt-5.4-mini"
MODELE_B="mistral-medium-3-5"

# Deux environnements applicatifs (D-43), chacun avec son API et sa console.
ENVIRONNEMENTS_APP=("preproduction" "production")
app_api()     { echo "ca-muninn-api-${1/production/prod}"; }
app_console() { echo "ca-muninn-console-${1/production/prod}"; }
base_de_donnees() { echo "muninn_${1/production/prod}"; }
# Tâche Container Apps des données de chaque environnement (D-58) : migrations, rôles, ingestion.
tache_donnees() { echo "job-muninn-donnees-${1/production/prod}"; }

BUDGET_MENSUEL_EUR=60

# Rôles désignés par leur identifiant, stable même si Microsoft renomme le rôle.
# Foundry User (ex-Azure AI User) : inférence par Entra ID, modèles OpenAI et non OpenAI.
ROLE_FOUNDRY_USER="53ca6127-db72-4b80-b1b0-d745d6d5456d"
ROLE_CONTAINER_APPS_CONTRIBUTOR="358470bc-b998-42bd-ab17-a7e34c199c0f"
# Container Apps Contributor ne donne aucun droit sur les tâches (actions containerApps/* seulement,
# lu le 16 octobre 2026) : rôle dédié pour mettre à jour l'image d'une tâche et la lancer.
ROLE_CONTAINER_APPS_JOBS_CONTRIBUTOR="4e3d2b60-56ae-4dc6-a233-09c8e5a82e68"
