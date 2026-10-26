# Ressources Azure de Muninn (V1)

Scripts versionnés qui créent les environnements de préproduction et de production (sprint 2,
étape 5). Le porteur les lance lui-même (R10) ; ils servent aussi à reconstruire l'ensemble
depuis le dépôt (étape 9). Aucun secret n'est écrit dans ces fichiers.

## Schémas

Cinq schémas de la chaîne de livraison et de l'exécution, établis le 26 octobre 2026 à la lecture
des scripts de ce dossier, des workflows `ci`, `donnees` et `retour-arriere`, et de
`alertes/al04.kql`. Les scripts et les workflows font foi ; chaque bloc ci-dessous en est une
lecture datée, à reprendre quand ils changent. Chaque bloc a sa planche dessinée, au même
contenu, pour la soutenance : `schemas/svg/` pour l'écran, `schemas/png/` (double résolution,
fond blanc) pour les documents. Les planches sont décrites dans `schemas/generer.py` ; un
changement de bloc se reporte dans ce fichier. Pour les régénérer :
`uv run playwright install chromium` une fois, puis
`uv run python infra/azure/schemas/generer.py --png`. Le test `tests/test_schemas.py` refuse un
SVG qui ne correspond plus au générateur, ou un PNG manquant.

Sigles : R10, règle du porteur (il lance lui-même les scripts qui modifient Azure) ; OIDC,
connexion de GitHub Actions à Azure sans secret ; INC-03 et INC-07, incidents corrigés (même
image livrée deux fois ; nom de révision mal lu) ; D-64, plafond de 1 € par évaluation ; AL-04,
alerte sur les erreurs du modèle (`docs/exploitation.md`, section 1).

### 1. Chaîne de livraison (`ci.yml`)

<!-- schema: 1-chaine-de-livraison -->
```text
 Pull request vers main                                    Fusion sur main (push)
          |                                                          |
          v                                                          v
+------------------------------------------------------------------------------------+
| GitHub Actions : ci                                                                |
|                                                                                    |
| +-----------+   +-----------------------+   +-----------------------------------+  |
| | lint      |-->| tests                 |-->| build                             |  |
| | make lint |   | PostgreSQL 16 de test |   | image Docker GIT_SHA=<sha>        |  |
| | types     |   | Chromium (axe-core)   |   | fumee : /health, /version = <sha>,|  |
| +-----------+   | make tests            |   | utilisateur muninn, migrations,   |  |
|                 +-----------------------+   | muninn-donnees, muninn-questions  |  |
|                        |                    +-----------------------------------+  |
|                        v                                                           |
| +-----------------------------------------+ +-----------------------------------+  |
| | evaluation (environnement evaluation)   | | secrets                           |  |
| | empreinte du paquet != main, ou a la    | | gitleaks 8.21.2 (empreinte        |  |
| | demande ; sinon « non requise »         | | verifiee), tout l'historique      |  |
| | OIDC id-muninn-evaluation (Foundry User)| +-----------------------------------+  |
| | Langfuse projet muninn-evaluation       |                                        |
| | plafond 1 EUR (D-64)                    |                                        |
| +-----------------------------------------+                                        |
|                        \_____ lint, tests, build, secrets, evaluation ____/        |
|                                             v                                      |
|                        +------------------------------------+                      |
|                        | verdict : les 5 doivent reussir    |  <- PR : fin ici     |
|                        | (seul controle requis sur main)    |                      |
|                        +------------------------------------+                      |
|                                             | push sur main seulement              |
|                                             v                                      |
| +--------------------------------------------------------------------------------+ |
| | preproduction   env. GitHub preproduction, verrou livraison-preproduction      | |
| |  OIDC id-muninn-deploiement ; extension containerapp 1.3.0b5                   | |
| |  verifier-options.py ; image crmuninn.azurecr.io/muninn:<sha> construite,      | |
| |  poussee ; deployer.sh preproduction <sha>                                     | |
| +--------------------------------------------------------------------------------+ |
|                                             | si vert                              |
|                                             v                                      |
| +--------------------------------------------------------------------------------+ |
| | production      environnement GitHub production, verrou livraison-production   | |
| |  meme image, non reconstruite ; deployer.sh production <sha>                   | |
| +--------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------+
```

Images : [SVG](schemas/svg/1-chaine-de-livraison.svg), [PNG](schemas/png/1-chaine-de-livraison.png).

### 2. Livraison dans un environnement (`deployer.sh <env> <sha>`)

<!-- schema: 2-deployer -->
```text
 Pour ca-muninn-api-<env>, puis ca-muninn-console-<env> :

 +--------------------+  oui  +------------------------------------------+
 | 0. image <sha>     |------>| rien a livrer (INC-03), pas une erreur   |
 |    deja en service?|       +------------------------------------------+
 +--------------------+
          | non
          v
 +--------------------+   +-------------------------+   +---------------------------------+
 | 1. trafic fige     |-->| 2. update --image <sha> |-->| 3. controle a l'adresse de la   |
 |    100 % sur la    |   |    nom de la revision   |   |    revision :                   |
 |    revision en     |   |    relu (INC-07), 0 %   |   |    API : /health, /version=<sha>|
 |    service         |   |                         |   |     POST /llm/essai (modele A)  |
 +--------------------+   +-------------------------+   |    console : /health, <sha>     |
                                                        |     affiche sur /               |
                                                        +---------------------------------+
                                                           | ok                  | echec
                                                           v                     v
                                              +------------------------+  +------------------+
                                              | 4. bascule 100 %       |  | trafic laisse    |
                                              | precedente active a 0 %|  | sur la precedente|
                                              +------------------------+  | arret en erreur  |
                                                                          +------------------+
 Puis : job-muninn-donnees-<env> -> image <sha> (s'il existe) ;
        controle final : /health des deux adresses publiques, /version=<sha> de l'API.
```

Images : [SVG](schemas/svg/2-deployer.svg), [PNG](schemas/png/2-deployer.png).

### 3. Workflows manuels (même verrou `livraison-<env>` que la livraison)

<!-- schema: 3-workflows-manuels -->
```text
+----------------------------------------------+   +----------------------------------------------+
| retour-arriere  (workflow_dispatch)          |   | donnees  (workflow_dispatch)                 |
| entrees : environnement, sha (facultatif)    |   | entree : environnement                       |
| retour-arriere.sh :                          |   | donnees.sh :                                 |
|  sans sha : revision creee juste avant       |   |  lance job-muninn-donnees-<env>, suivi       |
|   celle en service ; avec sha : la plus      |   |  jusqu'au terme (migrations, roles,          |
|   recente qui porte ce commit                |   |  ingestion ; source inchangee = aucune       |
|  console alignee sur le meme commit          |   |  version creee)                              |
|  revision reactivee si besoin, 100 % trafic  |   |  puis muninn-questions contre l'API          |
|  controle /version, duree mesuree            |   |  publique                                    |
|  aucune image reconstruite                   |   |                                              |
+----------------------------------------------+   +----------------------------------------------+
```

Images : [SVG](schemas/svg/3-workflows-manuels.svg), [PNG](schemas/png/3-workflows-manuels.png).

### 4. Mise en place de l'infrastructure (scripts lancés par le porteur, R10, tous relançables)

<!-- schema: 4-mise-en-place -->
```text
+--------------------------------------------------------------------------------------------+
| 00-foundry   adialloext-muninn1-resource (West Europe, AIServices S0)                      |
|              gpt-5.4-mini (50 k) et mistral-medium-3-5 (20 k), Zone de donnees UE,         |
|              mise a niveau automatique desactivee                                          |
+--------------------------------------------------------------------------------------------+
        v
+--------------------------------------------------------------------------------------------+
| 01-socle     (France Central) log-muninn (30 j, 0,5 Go/j) ; crmuninn (Basic, sans admin) ; |
|              cae-muninn ; id-muninn-execution (AcrPull, Foundry User) ;                    |
|              id-muninn-deploiement (AcrPush, Managed Identity Operator) ;                  |
|              psql-muninn (16, B1ms, 32 Go, 7 j) ; bases muninn_preprod, muninn_prod        |
| 02-image     premiere image muninn:<sha>, construite sur le poste                          |
| 03-applis    ca-muninn-api/console-preprod et -prod (0 a 1 replique, 0,5 vCPU, 1 Gio,      |
|              revisions multiples) ; Container Apps Contributor ; OIDC GitHub preprod/prod  |
| 04-budget    budget-muninn 60 EUR/mois, alertes 50/80/100 % reel et 100 % prevu            |
+--------------------------------------------------------------------------------------------+
        v
+--------------------------------------------------------------------------------------------+
| 05-donnees   pg_trgm ; job-muninn-donnees-<env> (1 vCPU, 2 Gio, le 3 du mois) ;            |
|              Jobs Contributor pour le deploiement ; API au role de lecture <base>_api      |
| 06-evaluation id-muninn-evaluation : Foundry User seul ; OIDC environnement evaluation     |
| 07-langfuse  cles du projet muninn sur l'API ; cles muninn-evaluation dans GitHub          |
| 08-traitements role <base>_traitements ; DATABASE_URL_TRAITEMENTS sur l'API                |
| 09-observabilite appi-muninn (France Central), lie a log-muninn ; chaine de connexion API  |
| 10-classeur  classeur « Muninn, exploitation » (modele ARM)                                |
| 11-alertes   ag-muninn (courriel) et regle al04-muninn-modele (15 min, fenetre 1 h)        |
| 12-panne     exercice : mauvais point d'acces sur une revision (--provoquer / --reparer)   |
| 13-voix      VOIX_FOURNISSEUR=azure et SPEECH_* sur l'API, controle par une synthese reelle|
+--------------------------------------------------------------------------------------------+
 Scripts 07, 08, 09, 12, 13 : meme patron que deployer.sh (trafic fige, revision controlee,
 bascule, precedente conservee).
```

Images : [SVG](schemas/svg/4-mise-en-place.svg), [PNG](schemas/png/4-mise-en-place.png).

Unités : « 50 k » et « 20 k », capacité des modèles en milliers de jetons par minute
(`00-foundry.sh`) ; « 0,5 Go/j », plafond d'ingestion quotidien de `log-muninn` ; « 7 j », durée
de rétention des sauvegardes de PostgreSQL. « Même patron que deployer.sh » : la séquence du
schéma 2 (trafic figé, nouvelle révision contrôlée à son adresse, bascule, précédente conservée).

### 5. Exécution (un environnement ; préproduction et production identiques)

<!-- schema: 5-execution -->
```text
                                    navigateur
                                        |  HTTPS (ingress externe)
                                        v
                   +------------------------------------------+
                   | ca-muninn-console-<env>                  |
                   +------------------------------------------+
                                        |  http://ca-muninn-api-<env>  (adresse interne)
                                        v
+-----------------------------------------------------------------------------------------+
| ca-muninn-api-<env>   identite id-muninn-execution (Entra, sans cle)                    |
+-----------------------------------------------------------------------------------------+
     |                   |                          |                       |
     v                   v                          v                       v
+------------------+ +---------------------------+ +----------------------+ +--------------+
| Foundry, West    | | psql-muninn / muninn_<env>| | appi-muninn          | | Langfuse     |
| Europe           | |  lecture : <base>_api     | | (traces OpenTelemetry| | Cloud UE     |
|  modeles A et B  | |  ecriture des traitements | |  depuis l'API)       | | projet muninn|
|  Speech (voix)   | |   : <base>_traitements    | +----------------------+ +--------------+
+------------------+ +---------------------------+            |
                                 ^                            v
                                 |              +------------------------------------------+
+-------------------------------------------+   | log-muninn (Log Analytics)               |
| job-muninn-donnees-<env> (le 3 du mois,   |   |  - journaux de cae-muninn                |
|  ou workflow donnees) : migrations, roles,|   |    (ContainerAppConsoleLogs_CL)          |
|  ingestion INSEE, data.gouv, Wikidata,    |   |  - donnees d'appi-muninn                 |
|  geo.api.gouv                             |   +------------------------------------------+
+-------------------------------------------+         |                         |
                                                      v                         v
                                     +------------------------+  +---------------------------+
                                     | classeur « Muninn,     |  | al04-muninn-modele        |
                                     |  exploitation »        |  |  API de production, 15 min|
                                     +------------------------+  |  -> ag-muninn -> courriel |
                                                                 +---------------------------+
```

Images : [SVG](schemas/svg/5-execution.svg), [PNG](schemas/png/5-execution.png).

La règle AL-04 ne lit que les journaux de `ca-muninn-api-prod` : une panne en préproduction
n'envoie pas de courriel (`docs/exploitation.md`, section 1.2).

## Ce qui est créé

Groupe de ressources `adialloRG`, région France Central. Toutes les ressources portent
l'étiquette `projet=muninn`.

| Ressource                     | Nom                                                  | Réglage                                                                              |
| ----------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Espace Log Analytics          | `log-muninn`                                         | 30 jours de rétention, plafond de 0,5 Go par jour                                    |
| Registre d'images             | `crmuninn`                                           | Basic, compte administrateur désactivé                                               |
| Environnement Container Apps  | `cae-muninn`                                         | Plan consommation                                                                    |
| Identité d'exécution          | `id-muninn-execution`                                | AcrPull sur le registre ; Foundry User sur la ressource Foundry                      |
| Identité de déploiement       | `id-muninn-deploiement`                              | AcrPush ; Container Apps Contributor ; OIDC avec GitHub Actions                      |
| Serveur PostgreSQL            | `psql-muninn`                                        | Version 16, Burstable B1ms, 32 Go, sauvegardes 7 jours                               |
| Bases de données              | `muninn_preprod`, `muninn_prod`                      | Une par environnement, sur le même serveur                                           |
| Applications de préproduction | `ca-muninn-api-preprod`, `ca-muninn-console-preprod` | 0 à 1 réplique, 0,5 vCPU, 1 Gio, révisions multiples                                 |
| Applications de production    | `ca-muninn-api-prod`, `ca-muninn-console-prod`       | Mêmes réglages                                                                       |
| Budget                        | `budget-muninn`                                      | 60 € par mois, filtré sur l'étiquette ; alertes à 50, 80, 100 % réels et 100 % prévu |

## Procédure

Dans Git Bash, depuis la racine du dépôt, sur un commit de `main` sans modification locale :

```bash
az login
python infra/azure/verifier-options.py infra/azure/*.sh   # doit finir par « options absentes : 0 »
export POSTGRES_MOT_DE_PASSE="$(openssl rand -hex 24)"   # à conserver hors du dépôt
export COURRIEL_ALERTE="adresse@exemple.fr"               # destinataire des alertes de budget
bash infra/azure/00-foundry.sh          # ressource Foundry et modèles (reconstruction seulement)
bash infra/azure/01-socle.sh            # environ 10 min (PostgreSQL est le plus long)
bash infra/azure/02-image-initiale.sh   # Docker doit tourner
bash infra/azure/03-applications.sh     # affiche les adresses et les identifiants pour GitHub
bash infra/azure/04-budget.sh
```

Le mot de passe PostgreSQL n'est stocké que dans les secrets des applications de l'API. Le
conserver dans un gestionnaire de mots de passe : il sera demandé si l'on relance le script 03.

Les scripts sont relançables : une ressource déjà présente est laissée telle quelle. Seul le
secret `database-url` des applications d'API est réécrit à chaque passage du script 03. Pour
changer le mot de passe : `az postgres flexible-server update -g adialloRG -n psql-muninn
--admin-password ...`, puis relancer le script 03 avec la nouvelle valeur.

Si un script s'arrête sur une erreur, ne pas lancer le suivant : le script 03 refuse de
s'exécuter si le serveur PostgreSQL manque.

## Coût estimé

Prix publics de détail en France Central, lus le 13 octobre 2026 (API `prices.azure.com`).

| Poste                                 | Calcul                                             | Coût mensuel estimé            |
| ------------------------------------- | -------------------------------------------------- | ------------------------------ |
| PostgreSQL B1ms                       | 0,0167 € par heure × 730 h                         | 12,2 €                         |
| Stockage PostgreSQL 32 Go             | Prix non relu                                      | environ 4 € [H]                |
| Registre Basic                        | 0,1466 € par jour × 30,4 j                         | 4,5 €                          |
| Container Apps                        | Zéro réplique au repos ; offre gratuite mensuelle  | proche de 0 €                  |
| Log Analytics                         | 2,43 € par Go ingéré ; plafond de 0,5 Go par jour  | moins de 1 € attendu           |
| Appels aux modèles                    | Essais de démonstration                            | quelques centimes              |
| **Total**                             |                                                    | **environ 21 € sur 60 €**      |

L'offre gratuite de Container Apps (180 000 vCPU-secondes, 360 000 Gio-secondes, 2 millions de
requêtes par mois) est partagée par tout l'abonnement. Le serveur PostgreSQL peut être arrêté
quand il ne sert pas : son calcul n'est alors plus facturé.

## Choix et justifications

| Choix                                                    | Raison                                                                                                     |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Budget filtré sur l'étiquette `projet=muninn`            | Le groupe de ressources héberge d'autres projets ; le porteur ne peut pas créer de groupe dédié            |
| Identités managées plutôt qu'une application Entra       | Le porteur n'a de droits que sur le groupe de ressources ; OIDC sans secret                                 |
| Une identité d'exécution affectée par l'utilisateur      | Elle existe avant les applications : les droits de tirage d'image sont posés avant leur création           |
| Préproduction et production dans le même environnement   | Une seule infrastructure à payer ; séparation par application, base et variables                           |
| Un serveur PostgreSQL, deux bases                        | Un serveur par environnement doublerait le poste le plus cher                                              |
| Accès PostgreSQL depuis les services Azure (0.0.0.0)     | Pas de réseau privé en V1 (coût et complexité) ; TLS exigé et mot de passe aléatoire de 48 caractères      |
| Une réplique au plus, zéro au repos                      | Coût et abus bornés sur une démonstration publique                                                         |
| Révisions multiples                                      | Retour arrière par le trafic, en une opération (étape 8)                                                   |

## Risques connus

- **Pare-feu PostgreSQL.** La documentation indique qu'il faut être propriétaire ou contributeur
  de l'abonnement pour créer une règle de pare-feu ; le porteur ne l'est que du groupe de
  ressources. Si le script 01 échoue à cette étape, s'arrêter et le signaler.
- **Accès depuis tout Azure.** La règle 0.0.0.0 ouvre le serveur aux services Azure de tous les
  clients, pas seulement aux nôtres. La protection repose sur TLS et sur le mot de passe.
- **Foundry User** permet aussi de lire les clés de la ressource Foundry. Rôle retenu parce que
  la documentation Foundry le recommande pour l'inférence par Entra ID, modèles non OpenAI
  compris.
- **Démarrage à froid.** Avec zéro réplique au repos, le premier appel prend plusieurs secondes.
  Avant une démonstration, passer le minimum à une réplique.
- **Monnaie du budget.** Le montant s'exprime dans la monnaie de facturation de l'abonnement.

## Sources

- OIDC avec une identité managée :
  <https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect>
- Sujet du jeton GitHub pour un environnement :
  <https://docs.github.com/en/actions/reference/security/oidc>
- Tirage d'image par identité managée :
  <https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull>
- Rôles Foundry : <https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry>
- Budget par API : <https://learn.microsoft.com/en-us/rest/api/consumption/budgets/create-or-update>
- Pare-feu PostgreSQL :
  <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-firewall-rules>
- Facturation de Container Apps : <https://learn.microsoft.com/en-us/azure/container-apps/billing>

## Livraison continue

Sur chaque fusion dans `main`, après un `verdict` vert, le workflow `ci` livre sans action
manuelle (`.github/workflows/ci.yml`, jobs `preproduction` puis `production`) :

1. connexion à Azure par OIDC avec l'identité `id-muninn-deploiement` (aucun secret) ;
2. image construite et étiquetée par le SHA du commit, poussée dans `crmuninn` ;
3. `deployer.sh preproduction <sha>` : pour l'API puis la console, nouvelle révision créée sans
   trafic, contrôlée à sa propre adresse (santé, SHA livré, appel réel au modèle A pour l'API),
   puis bascule de 100 % du trafic ; la révision précédente reste active ;
4. `deployer.sh production <sha>` : même image, mêmes contrôles.

Si un contrôle échoue, le trafic reste sur la révision précédente et la livraison s'arrête ;
la production n'est jamais touchée si la préproduction échoue. Les environnements GitHub
`preproduction` et `production` n'acceptent que les branches protégées.

## Retour arrière

Chaque livraison garde la révision précédente active, à 0 % du trafic. Le retour arrière ramène
100 % du trafic de l'API et de la console sur une révision antérieure, en une opération, sans
reconstruire d'image :

```bash
gh workflow run retour-arriere -f environnement=production          # version précédente
gh workflow run retour-arriere -f environnement=production -f sha=<sha>   # commit précis
```

Le workflow (`.github/workflows/retour-arriere.yml`) lance `retour-arriere.sh`, vérifie que
l'adresse publique sert bien le commit visé et affiche la durée mesurée. Il partage un verrou avec
la livraison du même environnement : les deux ne tournent jamais en même temps. La livraison
suivante repart de la révision servie après le retour arrière.

## Données (sprint 3)

Mise en place, une fois, par le porteur (R10), depuis Git Bash, à la racine du dépôt :

```bash
az login
python infra/azure/verifier-options.py infra/azure/*.sh   # doit finir par « options absentes : 0 »
export POSTGRES_MOT_DE_PASSE="..."                        # celui de 01-socle.sh
bash infra/azure/05-donnees.sh preproduction              # puis : bash infra/azure/05-donnees.sh production
```

Pour chaque environnement, le script :

1. autorise l'extension `pg_trgm` sur le serveur (paramètre `azure.extensions`, dynamique : sans
   redémarrage) ;
2. crée la tâche Container Apps `job-muninn-donnees-<env>` (même image que l'API, 1 vCPU,
   2 Gio), qui lance `muninn-donnees` : migrations, rôles de connexion, puis ingestion avec le
   seul rôle d'écriture. Elle est planifiée le 3 de chaque mois, en UTC (préproduction à 3 h,
   production à 4 h), deux jours après la publication mensuelle du stock Sirene. Le type de
   déclenchement ne se change pas par `job update` : une tâche encore manuelle est supprimée
   puis recréée, avec ses mots de passe ; l'historique de ses exécutions est alors perdu, leurs
   journaux restent dans Log Analytics ;
3. donne à l'identité de déploiement le rôle « Container Apps Jobs Contributor » sur la tâche
   (« Container Apps Contributor » ne couvre pas les tâches) ;
4. lance une exécution et la suit (environ 6 min) ;
5. bascule l'API sur le rôle de lecture `<base>_api`, puis redémarre sa révision ;
6. rejoue le jeu de questions de démonstration contre l'API publique.

Les mots de passe des deux rôles sont tirés au hasard au premier passage et gardés dans les
secrets de la tâche ; un rejeu les réutilise, sans couper l'API. Le script est relançable.

Ensuite, le chargement se rejoue en une commande, sans le poste :

```bash
gh workflow run donnees -f environnement=production
```

Le workflow (`.github/workflows/donnees.yml`) lance `donnees.sh` : exécution de la tâche, suivie
jusqu'à son terme, puis jeu de questions. Une source inchangée ne crée aucune version. Chaque
livraison met à jour l'image de la tâche (`deployer.sh`).

**Coût :** un premier chargement consomme environ 360 vCPU-secondes et 720 Gio-secondes
(mesuré en local, 1 vCPU et 2 Gio, 345 s) ; une exécution sans nouveauté, environ 80 s. La franchise mensuelle de Container Apps est de 180 000
vCPU-secondes et 360 000 Gio-secondes par abonnement (page de facturation de Container Apps) ;
au-delà, l'API de prix ne publie pas de tarif exploitable pour France Central [H : quelques
centimes par exécution au plus].

## Traitements enregistrés (sprint 5)

`bash infra/azure/08-traitements.sh [preproduction] [production]`, à lancer une fois après la
livraison du code de l'étape 1 du sprint 5 (D-82, D-85). Il tire au hasard le mot de passe du rôle
`<base>_traitements` (ou relit celui des secrets de la tâche), l'ajoute à la tâche des données, lance
une exécution (migration du schéma `app`, création du rôle), puis donne à l'API l'adresse de ce rôle
dans le secret `database-url-traitements` ; la nouvelle révision ne reçoit le trafic qu'après un
contrôle, comme une livraison. Le rôle n'écrit que dans le schéma `app` ; l'API garde son rôle en
lecture seule pour les référentiels. Sans cette adresse, l'API traite les appels sans les enregistrer.

## Traces vers Application Insights (sprint 5)

`bash infra/azure/09-observabilite.sh [preproduction] [production]` crée le composant
`appi-muninn`, lié à l'espace `log-muninn` et étiqueté pour le budget, puis donne sa chaîne de
connexion à l'API de chaque environnement (secret `appinsights-connection-string`), avec une
révision contrôlée (D-87). Sans cette chaîne, l'API ne trace rien vers Azure et n'échoue pas.
Coût vérifié le 23 octobre 2026 : ingestion facturée par l'espace, 5 Go gratuits par mois, sous le
plafond de 0,5 Go par jour de `log-muninn`.

## Consulter une base, en lecture seule

`bash infra/azure/consulter-base.sh [production|preproduction] [--interactif] [--traitements]`
affiche un aperçu
de la base (tables, versions chargées, exemples), ou ouvre psql. Le script ouvre le pare-feu du
serveur PostgreSQL à la seule adresse IP du poste, par une règle temporaire supprimée à la sortie ;
il se connecte avec le rôle de lecture de l'API, en lecture seule forcée, sans jamais afficher
l'adresse de connexion. Docker est requis (client psql en conteneur). Essayé par le porteur sur la
production le 19 octobre 2026.

Avec `--traitements`, le script se connecte avec le rôle des traitements, le seul qui voit le
schéma `app`, toujours en lecture seule forcée ; l'aperçu montre les mesures des traitements, jamais
le contenu d'un dossier.

Après une fermeture brutale du terminal, vérifier que la règle `consultation-porteur` a disparu :
`az postgres flexible-server firewall-rule list -g adialloRG -s psql-muninn -o table`.
