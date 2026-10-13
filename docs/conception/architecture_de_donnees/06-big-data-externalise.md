# Traitement big data externalisé : comparaison des services gérés

**Version :** 1.1
**Date :** 12 octobre 2026
**Historique :** la v1.1 ajoute la section « Décision » (D-19, D-27). Les sections 1 à 7 sont
gardées telles quelles comme historique de la comparaison.
**Phase :** 1 (conception)
**Statut :** décidé (D-27)
**Compétences servies :** C1 (extraction depuis un système big data), C2 (requêtes SQL d'extraction)

## Décision

**Option A retenue, décidée par le porteur : D-27.** Elle clôt D-09.

| Élément                | Choix                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Stockage               | Lac de données Azure Data Lake Storage Gen2 (espace de noms hiérarchique), qui reçoit les fichiers stock Sirene en Parquet |
| Calcul                 | Tâche planifiée Azure Container Apps qui interroge les fichiers Parquet en SQL avec un moteur en colonnes                  |
| Sortie                 | Agrégats écrits dans PostgreSQL, schéma `market`, après secret statistique (document 02, section 4)                        |
| Région et rattachement | France Central, dans le groupe de ressources du porteur                                                                    |
| Fichiers bruts         | Supprimés du lac à la fin du traitement, au plus tard sous 24 heures [H] (document 05, RT-07)                              |

Pourquoi ce choix :

- **Synapse n'est pas accessible.** D-19 a relu les droits Azure : rôle Reader sur l'abonnement,
  Owner du seul groupe de ressources du porteur, fournisseur `Microsoft.Synapse` non enregistré.
  Le premier choix de la section 6.1 demandait de l'enregistrer : il dépendrait de l'organisme de
  formation.
- **Services déjà enregistrés et en disponibilité générale**, coût quasi nul pour un traitement
  mensuel de 3 Go (D-27).
- **C1 et C2 restent couverts** : les fichiers sont lus dans un lac de données, par des requêtes
  SQL, et seuls les agrégats en sortent.
- **R5** : stockage et calcul en France Central.

Ce que la décision ne fixe pas : le moteur SQL en colonnes exact et sa version, la taille de la
tâche et sa planification. Ils relèvent de l'architecture technique de la phase 2 (ADR-16). Le
flux F-10 de la phase 0 (document 02) décrit le traitement retenu.

**Statut des sections suivantes.** Elles forment l'historique de la comparaison du 12 octobre
2026. Leurs recommandations (Synapse en premier choix, MotherDuck en repli) ne sont plus en
vigueur ; la section 5 est dépassée par la relecture des droits de D-19.

## 1. Objet et méthode

Ce document compare les services gérés capables d'exécuter le traitement Sirene de Muninn. Il
propose un premier choix et une solution de repli.

Méthode :

- chaque fait sur un service est adossé à une page officielle, consultée le 12 octobre 2026 ;
- les prix Azure viennent de l'API publique des prix de détail (`prices.azure.com`), en euros,
  hors taxes, tarif public sans remise ;
- les droits Azure ont été lus en lecture seule, sans aucune commande de création, d'inscription
  ni de mise à jour ;
- une affirmation non vérifiée porte la marque [H] et figure aussi en section 7.

## 2. Besoin rappelé

| Élément             | Valeur                                                                                    |
| ------------------- | ----------------------------------------------------------------------------------------- |
| Source              | Fichiers stock Sirene de l'INSEE en Parquet sur data.gouv.fr, Licence Ouverte 2.0         |
| StockEtablissement  | 44,3 millions de lignes, 54 colonnes, 2,22 Go                                             |
| StockUniteLegale    | 30,1 millions de lignes, 0,71 Go                                                          |
| Traitement          | Projection, filtres (actifs, NAF 43.xx), jointure sur `siren`, agrégats                   |
| Axes d'agrégation   | NAF, tranche d'effectif, catégorie juridique, département                                 |
| Sortie conservée    | Agrégats seulement                                                                        |
| Fréquence           | Mensuelle au plus (data.gouv.fr publie les stocks Parquet chaque mois)                    |
| Contrainte RGPD     | Données personnelles d'entrepreneurs individuels présentes, hébergement UE exigé (R5)     |
| Contrainte d'action | Toute création de compte ou de ressource payante est faite par le porteur (R10)           |
| Échéances           | Démo le 29 octobre 2026, oral le 12 novembre 2026, service disponible jusqu'à mi-novembre |

Volume de référence du calcul de coût : 2,93 Go de Parquet compressé par mois (2,22 + 0,71),
arrondi à 3 Go.

## 3. Table comparative

Légende des colonnes : « Parquet » signifie lecture directe du fichier Parquet sans chargement
préalable dans une table ; « Mise en place » est une estimation [H] du temps du porteur ;
« Risque » vise une indisponibilité avant le 12 novembre 2026.

| Candidat                      | SQL | Parquet                    | Région UE                    | Coût mensuel estimé  | Prérequis de compte                          | Mise en place [H] | Risque | Valeur jury | R5                    |
| ----------------------------- | --- | -------------------------- | ---------------------------- | -------------------- | -------------------------------------------- | ----------------- | ------ | ----------- | --------------------- |
| Synapse serverless SQL + ADLS | oui | oui, depuis ADLS ou Blob   | oui, France Central          | moins de 1 €         | Abonnement Azure, droits de création         | 2 à 3 h           | faible | forte       | conforme              |
| Azure Databricks              | oui | oui                        | oui, France Central          | 3 à 10 € [H]         | Contributor ou Owner, quota vCPU             | 3 à 5 h           | moyen  | forte       | conforme              |
| Microsoft Fabric (essai)      | oui | oui, après dépôt OneLake   | oui, France Central          | 0 € pendant 60 jours | Essai autorisé par le locataire              | 2 à 3 h           | moyen  | forte       | conforme si région UE |
| BigQuery sandbox              | oui | non, chargement requis [H] | oui, multirégion EU ou Paris | 0 €                  | Compte Google, sans carte bancaire           | 2 à 4 h           | élevé  | moyenne     | conforme si région UE |
| MotherDuck Lite               | oui | oui, par HTTPS             | oui, Francfort ou Dublin     | 0 €                  | Compte MotherDuck, sans carte bancaire       | 1 à 2 h           | faible | moyenne     | à confirmer (DPA)     |
| Databricks Free Edition       | oui | non vérifié                | non garantie                 | 0 €                  | Compte Databricks, usage personnel seulement | 1 à 2 h           | élevé  | moyenne     | non conforme          |
| Snowflake (essai)             | oui | oui, depuis un stage       | oui, Paris, Francfort, etc.  | 0 € pendant 30 jours | Compte Snowflake, sans carte bancaire        | 2 à 4 h           | moyen  | forte       | conforme si région UE |

## 4. Fiches par candidat

### 4.1 Azure Synapse Analytics, serverless SQL pool sur ADLS Gen2

**Principe.** Les fichiers Parquet sont copiés dans un compte de stockage ADLS Gen2. Le pool SQL
serverless, présent dans tout espace de travail Synapse, les interroge en T-SQL avec
`OPENROWSET(BULK ..., FORMAT = 'PARQUET')` ou par table externe. Aucune machine n'est à démarrer.

| Critère                 | Constat                                                                                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, T-SQL                                                                                                                                     |
| Lecture directe Parquet | Oui, mais seulement depuis un stockage Azure (Blob, ADLS Gen1 ou Gen2). Une URL data.gouv.fr ne peut pas être lue directement                  |
| Région UE               | France Central et West Europe ont un prix publié pour le compteur « Serverless SQL Pool, Data Processed »                                      |
| Modèle de prix          | Au volume de données traitées. Minimum de 10 Mo par requête, arrondi au Mo supérieur                                                           |
| Prix unitaire           | 6,1598 € par To en France Central, 4,3999 € par To en West Europe (API des prix de détail, 12 octobre 2026)                                    |
| Stockage ADLS Gen2      | Hot LRS en France Central : 0,0156 à 0,0169 € par Go et par mois selon le palier                                                               |
| Contrôle des coûts      | Plafond de données traitées par jour, semaine ou mois (`sp_set_data_processed_limit`), en To entiers                                           |
| Prérequis               | Fournisseurs `Microsoft.Synapse` et `Microsoft.Storage` inscrits [H] ; droit de créer un espace de travail et un compte de stockage            |
| Rôles                   | Pour un stockage existant, la documentation demande Owner et Storage Blob Data Owner ; l'identité managée reçoit Storage Blob Data Contributor |
| Fin de service          | Aucune annonce de retrait trouvée. Les pages Microsoft Learn de Synapse orientent les nouveaux projets vers Fabric Data Warehouse              |
| Mise en place [H]       | 2 à 3 h : groupe de ressources, stockage, espace de travail, copie des deux fichiers, première requête                                         |
| Risque avant le 12/11   | Faible si les droits sont présents. Le risque principal est l'absence de droits sur l'abonnement de formation                                  |
| Valeur de démonstration | Forte : lac de données plus moteur SQL distribué serverless, cas d'école de C1 et C2                                                           |
| Cohérence R5            | Conforme : stockage et calcul en France Central                                                                                                |

**Calcul du coût mensuel.** La documentation définit les données traitées comme la somme des
données lues, des résultats intermédiaires échangés entre nœuds et des données écrites. Sur du
Parquet, seules les colonnes projetées sont lues.

- Borne haute d'une exécution, lecture intégrale des deux fichiers : 2,93 Go lus. On ajoute [H]
  un facteur 2 pour les échanges intermédiaires non compressés de la jointure : environ 6 Go, soit
  0,006 To, soit 0,04 € en France Central.
- Mise au point le premier mois [H] : 30 requêtes à la borne haute, soit 0,18 To, soit 1,11 €.
- Régime mensuel ensuite : 1 exécution, moins de 0,05 €.
- Stockage : 3 Go × 0,0169 € = 0,05 € par mois. Les transactions de lecture et d'écriture sont
  négligeables à ce volume [H].
- Total : environ 1,2 € le premier mois, moins de 0,10 € les mois suivants. Un plafond de 1 To
  par mois borne le risque à 6,16 € de données traitées.

**Point d'attention sur les rôles.** L'accès de l'identité managée au stockage demande une
attribution de rôle, donc un rôle Owner ou User Access Administrator [H]. Sans ce droit, une
identification par jeton SAS, déclaré dans des informations d'identification de base de
données, reste possible, selon la page OPENROWSET.

Sources (consultées le 12 octobre 2026) :

- <https://learn.microsoft.com/en-us/azure/synapse-analytics/sql/data-processed>
- <https://learn.microsoft.com/en-us/azure/synapse-analytics/sql/develop-openrowset>
- <https://learn.microsoft.com/en-us/azure/synapse-analytics/quickstart-create-workspace>
- <https://azure.microsoft.com/en-us/pricing/details/synapse-analytics/>
- <https://prices.azure.com/api/retail/prices> (filtre `serviceName eq 'Azure Synapse Analytics'`)

### 4.2 Azure Databricks

**Principe.** Un espace de travail Databricks dans l'abonnement Azure. Lecture des Parquet depuis
ADLS, requêtes en Spark SQL depuis un entrepôt SQL serverless ou un cluster.

| Critère                 | Constat                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, Spark SQL et Databricks SQL                                                                                                    |
| Lecture directe Parquet | Oui, depuis ADLS                                                                                                                    |
| Région UE               | Prix publiés pour France Central, y compris « Premium Serverless SQL »                                                              |
| Modèle de prix          | À l'heure de DBU, plus les machines virtuelles pour le calcul classique                                                             |
| Prix unitaire           | France Central : Premium Serverless SQL 0,8008 € par DBU-heure ; Premium Jobs Compute 0,264 € par DBU-heure                         |
| Essai                   | Niveau « Trial (Premium, 14-Days Free DBUs) » : DBU gratuits 14 jours. Abonnement Free Trial exclu                                  |
| Prérequis               | Rôle Contributor ou Owner sur l'abonnement, ou rôle personnalisé ; fournisseurs Compute, Network, Storage, ManagedIdentity inscrits |
| Fin de service          | Aucune annonce trouvée                                                                                                              |
| Mise en place [H]       | 3 à 5 h, dont le réglage de l'accès à ADLS                                                                                          |
| Risque avant le 12/11   | Moyen : quotas vCPU et droits de l'abonnement de formation inconnus ; l'essai de 14 jours ne couvre pas la période                  |
| Valeur de démonstration | Forte : moteur Spark, référence du secteur                                                                                          |
| Cohérence R5            | Conforme en France Central                                                                                                          |

**Calcul du coût mensuel [H].** La consommation en DBU par heure d'un entrepôt SQL serverless de
plus petite taille n'a pas été vérifiée. Avec une hypothèse de 4 DBU par heure : 4 × 0,8008 =
3,20 € par heure d'entrepôt actif. Avec 1 à 3 h actives par mois : 3 à 10 €, stockage ADLS en sus
(0,05 €).

Sources (consultées le 12 octobre 2026) :

- <https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-trial>
- <https://prices.azure.com/api/retail/prices> (filtre `serviceName eq 'Azure Databricks'`)

### 4.3 Microsoft Fabric (Lakehouse, point de terminaison SQL)

**Principe.** Un Lakehouse dans OneLake reçoit les Parquet. Le point de terminaison SQL analytique
permet des requêtes T-SQL en lecture.

| Critère                 | Constat                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, T-SQL                                                                                                                          |
| Lecture directe Parquet | Oui une fois les fichiers déposés dans OneLake [H sur le mode exact : table Delta ou lecture de fichier]                            |
| Région UE               | France Central, West Europe et North Europe proposent toutes les charges de travail Fabric                                          |
| Essai                   | 60 jours gratuits, capacité F4 ou F64, 1 To de stockage OneLake                                                                     |
| Conditions de l'essai   | L'administrateur du locataire doit autoriser « Users can try Microsoft Fabric paid features ». Nombre d'essais par locataire limité |
| Région de l'essai       | Par défaut la région d'origine du locataire, modifiable au démarrage de l'essai                                                     |
| Fin de l'essai          | Les éléments non Power BI deviennent inaccessibles ; contenu conservé 7 jours dans OneLake                                          |
| Prix après l'essai [H]  | Compteurs de capacité à 0,176 € par CU-heure en France Central ; une F2 coûterait environ 0,35 € par heure active                   |
| Stockage OneLake        | 0,0211 € par Go et par mois (Hot), France Central                                                                                   |
| Fin de service          | Aucune ; Fabric est la plateforme mise en avant par Microsoft                                                                       |
| Mise en place [H]       | 2 à 3 h si l'essai est autorisé                                                                                                     |
| Risque avant le 12/11   | Moyen : un essai lancé le 13 octobre finit le 12 décembre, mais l'autorisation du locataire de formation est inconnue               |
| Valeur de démonstration | Forte                                                                                                                               |
| Cohérence R5            | Conforme si la région choisie est dans l'UE ; la région d'origine du locataire n'a pas été lue                                      |

**Calcul du coût mensuel.** 0 € pendant les 60 jours d'essai. Hors essai [H] : F2 en pause hors
usage, 10 h actives par mois × 0,35 € = 3,5 €, plus 3 Go × 0,0211 € = 0,06 €.

Sources (consultées le 12 octobre 2026) :

- <https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial>
- <https://learn.microsoft.com/en-us/fabric/admin/region-availability>
- <https://prices.azure.com/api/retail/prices> (filtre `serviceName eq 'Microsoft Fabric'`)

### 4.4 Google BigQuery, sandbox

| Critère                 | Constat                                                                                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, GoogleSQL                                                                                                                                      |
| Lecture directe Parquet | Non vérifiée en sandbox. Les tables externes visent Cloud Storage, dont l'usage sans facturation n'est pas confirmé                                 |
| Chargement              | Parquet accepté. Depuis la console, un fichier local ne peut pas dépasser 100 Mo                                                                    |
| Région UE               | Multirégion `EU` (données en Belgique ou aux Pays-Bas) et région `europe-west9` (Paris)                                                             |
| Carte bancaire          | Non requise                                                                                                                                         |
| Limites                 | 10 Gio de stockage à vie, non restitués après suppression ; 1 Tio de requêtes par mois                                                              |
| Expiration              | Tables, vues et partitions expirent après 60 jours                                                                                                  |
| Fonctions absentes      | Streaming, DML, Data Transfer Service                                                                                                               |
| Fin de service          | Aucune annonce trouvée                                                                                                                              |
| Mise en place [H]       | 2 à 4 h, selon la voie de chargement                                                                                                                |
| Risque avant le 12/11   | Élevé : chargement d'un fichier de 2,22 Go non garanti ; quota de 10 Gio à vie probablement dépassé par la taille logique de StockEtablissement [H] |
| Valeur de démonstration | Moyenne : bon moteur, mais la sandbox impose des contournements                                                                                     |
| Cohérence R5            | Conforme si le jeu de données est créé en `EU` ou `europe-west9`                                                                                    |

**Calcul du coût mensuel.** 0 €. Le quota de 1 Tio de requêtes couvre largement 3 Go mensuels.
Le stockage est le facteur limitant : chaque rechargement consomme le quota de 10 Gio à vie.

Sources (consultées le 12 octobre 2026) :

- <https://docs.cloud.google.com/bigquery/docs/sandbox>
- <https://docs.cloud.google.com/bigquery/docs/locations>
- <https://docs.cloud.google.com/bigquery/docs/batch-loading-data>
- <https://docs.cloud.google.com/bigquery/external-data-cloud-storage>

### 4.5 MotherDuck, offre Lite

| Critère                 | Constat                                                                                                              |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, dialecte DuckDB                                                                                                 |
| Lecture directe Parquet | Oui : `read_parquet` accepte une URL HTTPS, donc les fichiers de data.gouv.fr                                        |
| Région UE               | `eu-central-1` (Francfort) et `eu-west-1` (Dublin). Région choisie à la création de l'organisation                   |
| Offre gratuite          | Plan Lite : 10 Go de stockage, 10 h de calcul « Pulse » par mois                                                     |
| Carte bancaire          | Non requise pour le plan Lite                                                                                        |
| Fin de service          | Aucune annonce trouvée                                                                                               |
| Mise en place [H]       | 1 à 2 h                                                                                                              |
| Risque avant le 12/11   | Faible : pas de date d'expiration annoncée pour le plan Lite                                                         |
| Valeur de démonstration | Moyenne : SQL sur Parquet distant, mais moteur mono-nœud ; l'argument « big data » est plus faible devant un jury    |
| Cohérence R5            | À confirmer : la disponibilité de la région UE sur le plan Lite et l'accord de traitement (DPA) ne sont pas vérifiés |

**Calcul du coût mensuel.** 0 € dans les limites du plan Lite. Le résultat agrégé tient en
quelques Mo, sous la limite de 10 Go. La consommation de calcul d'une exécution n'est pas mesurée.

Sources (consultées le 12 octobre 2026) :

- <https://motherduck.com/pricing/>
- <https://motherduck.com/docs/concepts/architecture-and-capabilities/>
- <https://motherduck.com/docs/about-motherduck/cloud-regions/>
- <https://motherduck.com/docs/integrations/file-formats/parquet.md>

### 4.6 Databricks Free Edition

| Critère                 | Constat                                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui, éditeur SQL                                                                                                              |
| Lecture directe Parquet | Non vérifiée ; emplacement de stockage personnalisé non pris en charge                                                        |
| Région UE               | Non garantie. Les conditions excluent toute garantie sur l'emplacement des données                                            |
| Conditions              | Usage personnel et non lucratif. Calcul serverless seulement, quotas journaliers                                              |
| Données                 | Le personnel Databricks a accès au compte et aux données. Licence accordée à Databricks, y compris pour entraîner des modèles |
| Arrêt                   | Databricks peut arrêter le service ou supprimer le contenu à tout moment                                                      |
| Édition communautaire   | Retirée en 2025                                                                                                               |
| Mise en place [H]       | 1 à 2 h                                                                                                                       |
| Risque avant le 12/11   | Élevé : arrêt possible sans préavis, coupure quotidienne en cas de dépassement de quota                                       |
| Valeur de démonstration | Moyenne                                                                                                                       |
| Cohérence R5            | Non conforme : pas d'engagement de région UE, accès du personnel, licence d'usage sur des données personnelles                |

**Calcul du coût mensuel.** 0 €. Candidat écarté pour R5.

Sources (consultées le 12 octobre 2026) :

- <https://docs.databricks.com/aws/en/getting-started/free-edition-limitations>
- <https://docs.databricks.com/aws/en/getting-started/free-edition>
- <https://www.databricks.com/learn/free-edition>
- <https://www.databricks.com/legal/databricks-free-edition>

### 4.7 Snowflake, essai

| Critère                 | Constat                                                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| SQL                     | Oui                                                                                                              |
| Lecture directe Parquet | Oui depuis un stage interne ou externe ; pas depuis une URL HTTPS quelconque [H]                                 |
| Région UE               | AWS `eu-west-3` (Paris), `eu-central-1` (Francfort), Azure `westeurope`, `northeurope`, GCP `europe-west3`, etc. |
| Durée de l'essai        | 30 jours après l'inscription, ou jusqu'à épuisement du solde                                                     |
| Montant du solde        | Non trouvé dans la documentation officielle lue ; 400 $ selon la page d'inscription, non lue directement         |
| Carte bancaire          | Non requise                                                                                                      |
| Fin de l'essai          | Compte suspendu, plus de requête ni de chargement possible sans passage au payant                                |
| Mise en place [H]       | 2 à 4 h                                                                                                          |
| Risque avant le 12/11   | Moyen : un essai ouvert avant le 13 octobre expire avant l'oral ; il faut l'ouvrir entre le 14 et le 28 octobre  |
| Valeur de démonstration | Forte                                                                                                            |
| Cohérence R5            | Conforme si une région UE est choisie à l'inscription                                                            |

**Calcul du coût mensuel.** 0 € pendant 30 jours. Le coût hors essai n'a pas été calculé : le
prix du crédit par région n'a pas été lu.

Sources (consultées le 12 octobre 2026) :

- <https://docs.snowflake.com/en/user-guide/admin-trial-account>
- <https://docs.snowflake.com/en/user-guide/intro-regions>

## 5. Droits constatés sur les abonnements Azure (lecture seule)

Commandes lancées : `az account show`, `az account list`, `az provider list`,
`az role assignment list`, `az consumption budget list`. Aucune commande de modification.

| Abonnement                             | État    | Par défaut | Fournisseurs inscrits | Rôles du porteur | Budget |
| -------------------------------------- | ------- | ---------- | --------------------- | ---------------- | ------ |
| REMOTE_WCS_211537_DEV IA               | Enabled | oui        | non lus (MFA expirée) | non lus          | non lu |
| Inter-IUT_ARA_Lyon_Ecole IA_148637_ALT | Enabled | non        | non lus (MFA expirée) | non lus          | non lu |
| ARA_Bourg-en-B_DataEng_207803_INT_SWS  | Enabled | non        | non lus (MFA expirée) | non lus          | non lu |

Constat : seules les informations en cache de la session `az` sont lisibles. Les appels à Azure
Resource Manager et à Microsoft Graph échouent avec l'erreur `AADSTS50078` : l'authentification
multifacteur de la session a expiré selon la politique de l'organisme. Les droits réels restent
donc inconnus.

Action du porteur : se reconnecter (`az login`, avec MFA), puis relancer ces quatre lectures, ou
les lancer sous supervision lors de la prochaine session :

```bash
az provider list --query "[?registrationState=='Registered'].namespace" -o tsv
az role assignment list --assignee <utilisateur> --all -o table
az consumption budget list
```

Ce qu'il faut y chercher : `Microsoft.Synapse` et `Microsoft.Storage` parmi les fournisseurs ;
un rôle Contributor ou Owner sur l'abonnement ou sur un groupe de ressources ; un éventuel budget.

## 6. Recommandation

### 6.1 Premier choix : Synapse serverless SQL pool sur ADLS Gen2, en France Central

Raisons :

- C1 et C2 : un lac de données (ADLS Gen2) interrogé par un moteur SQL distribué serverless
  répond à la lettre à « extraction depuis un système big data » et à « requêtes SQL
  d'extraction » ;
- coût : environ 1,2 € le premier mois, moins de 0,10 € ensuite, borné par un plafond de données
  traitées ;
- pas de date d'expiration : le paiement à l'usage ne dépend d'aucun essai, contrairement à
  Fabric (60 jours) et Snowflake (30 jours) ;
- R5 : stockage et calcul en France Central ;
- cohérence : l'organisme fournit déjà des abonnements Azure.

Faiblesse assumée : Microsoft oriente les nouveaux projets vers Fabric. Aucun retrait n'est
annoncé ; le risque avant le 12 novembre 2026 est donc faible.

Condition : les droits de l'abonnement par défaut doivent permettre la création d'un compte de
stockage et d'un espace de travail Synapse. Si l'inscription de `Microsoft.Synapse` ou
l'attribution de rôle est refusée, passer au repli sans attendre.

Actions du porteur (R10) :

1. Se reconnecter à Azure et relire les droits (section 5).
2. Créer un groupe de ressources en France Central dans « REMOTE_WCS_211537_DEV IA ».
3. Créer un compte de stockage ADLS Gen2 (espace de noms hiérarchique activé).
4. Créer l'espace de travail Synapse rattaché à ce stockage. Ne créer ni pool SQL dédié ni pool
   Spark : ils sont facturés à l'heure.
5. Fixer le plafond de données traitées (1 To par mois) et, si les droits le permettent, un budget
   d'abonnement.
6. Déposer chaque mois les deux fichiers Parquet dans le conteneur.

### 6.2 Repli : MotherDuck Lite en région Europe (Francfort)

Raisons : aucune carte bancaire, pas d'expiration annoncée, lecture directe des Parquet de
data.gouv.fr par HTTPS, région UE disponible. Indépendant des droits Azure, il couvre le cas où
l'abonnement de formation bloque la création de ressources.

Coût : 0 €.

Limites : moteur mono-nœud, argument « big data » plus faible ; disponibilité de Francfort sur le
plan Lite et accord de traitement des données à vérifier avant tout chargement.

Actions du porteur (R10) :

1. Vérifier, avant inscription, que la région `eu-central-1` est proposée sur le plan Lite.
2. Lire et accepter l'accord de traitement des données (DPA) de MotherDuck.
3. Créer l'organisation en `eu-central-1`. La région ne peut plus être changée ensuite.

### 6.3 Alternatives écartées ou conditionnelles

- Fabric : à retenir si l'organisme autorise l'essai sur son locataire. À démarrer après le
  13 octobre pour couvrir le 12 novembre.
- Snowflake : bonne valeur de démonstration, mais un essai de 30 jours impose une fenêtre
  d'ouverture étroite (14 au 28 octobre).
- Azure Databricks : mêmes prérequis de droits que Synapse, coût plus élevé, mise en place plus
  longue.
- BigQuery sandbox : quota de stockage à vie et chargement du gros fichier incertains.
- Databricks Free Edition : non conforme à R5.

## 7. Non vérifié

- Droits, fournisseurs inscrits et budgets des trois abonnements Azure : lecture bloquée par
  l'expiration de la MFA.
- Région d'origine du locataire Microsoft de l'organisme, et autorisation de l'essai Fabric.
- Inscription de `Microsoft.Synapse` nécessaire et droit de l'inscrire avec un rôle Contributor.
- Rôle exact exigé pour que l'assistant de création Synapse attribue le rôle de stockage à
  l'identité managée.
- Facteur 2 appliqué aux échanges intermédiaires de la jointure dans le calcul Synapse.
- Correspondance entre les compteurs Fabric à 0,176 € par CU-heure et le prix d'une capacité F2
  à l'usage.
- Consommation en DBU par heure du plus petit entrepôt SQL serverless Azure Databricks.
- Possibilité, en sandbox BigQuery, de créer un compartiment Cloud Storage ou de charger un
  fichier local de 2,22 Go par l'outil `bq`.
- Taille logique de StockEtablissement une fois chargé dans BigQuery.
- Disponibilité de la région Francfort sur le plan Lite de MotherDuck, contenu de son DPA, et
  exécution côté serveur des lectures HTTPS.
- Montant du solde d'essai Snowflake (400 $ cités par des tiers) et prix du crédit en région UE.
- Région et lecture de Parquet dans Databricks Free Edition.
- Temps de mise en place : estimations, non mesurées.
- Correspondance exacte entre les fichiers Parquet de data.gouv.fr et les noms StockEtablissement
  et StockUniteLegale : la page liste des tailles (2,1 Go et 680,5 Mo) sans nommer les fichiers.
