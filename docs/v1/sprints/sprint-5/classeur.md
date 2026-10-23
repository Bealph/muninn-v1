# Sprint 5 : le classeur Azure Monitor

Étape 4 de la checklist, deuxième case. Public : l'exploitant et l'évaluateur pair. Le classeur
est le pendant technique de l'écran « Qualité » (`ecran-qualite.md`) : l'écran dit si le service
va bien, le classeur aide à comprendre pourquoi.

Fichiers : `infra/azure/classeur/requetes.kql` (requêtes), `infra/azure/classeur/construire.py`
(modèle ARM), `infra/azure/10-classeur.sh` (validation et déploiement, lancé par le porteur, R10),
`tests/test_classeur.py`.

## 1. Contenu

Deux paramètres en tête : `Environnement` (`production` ou `preproduction`) et `Requete`
(l'identifiant d'un appel, affiché par l'écran « Qualité », section « Dernier appel »).

| Section                          | Source                       | Ce qu'on y lit                                                       |
| -------------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| Durée de chaque étape (24 h)     | `AppDependencies`            | Nombre, échecs, médiane et 95e centile par étape (`agent`, `outil`…) |
| Appels par heure (24 h)          | `AppDependencies`            | Volume, échecs, 95e centile de la durée d'un appel                   |
| Avertissements et erreurs (24 h) | `ContainerAppConsoleLogs_CL` | Lignes WARNING ou ERROR, traces de pile, échecs `.echec`             |
| Événements des révisions (24 h)  | `ContainerAppSystemLogs_CL`  | Création, démarrage, arrêt, échec de sonde                           |
| Les étapes d'un appel            | `AppDependencies`            | L'arbre d'un appel retrouvé par son identifiant, durées et attributs |
| Les journaux du même appel       | `ContainerAppConsoleLogs_CL` | Les lignes qui portent l'identifiant de l'appel                      |

Aucune donnée d'appel : les traces ne portent que des codes et des nombres (OB-1, OB-2, vérifié à
l'étape 3), et les journaux ne contiennent jamais la transcription (R3).

## 2. Choix techniques et leurs sources

Vérifiés le 23 octobre 2026 par l'agent `verificateur-sources`, sur Microsoft Learn :

| Choix                                                                   | Source                                                                            |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Ressource `Microsoft.Insights/workbooks`, API 2023-06-01                | Référence ARM `microsoft.insights/workbooks`                                      |
| `kind` « shared », `category` « workbook », `version` « Notebook/1.0 »  | Même référence ; page « Programmatically manage workbooks »                       |
| Nom `guid(resourceGroup().id, …)` : même classeur à chaque relance      | Fonctions de chaîne ARM, `guid` : même paramètre, même identifiant                |
| `az deployment group create`, mode incrémental, nom de déploiement fixe | « Deploy resources with ARM templates and Azure CLI » ; « Deployment modes »      |
| Requêtes non facturées : tables au plan Analytics                       | « Azure Monitor Logs cost calculations » ; plan des trois tables lu le 23 octobre |

Une seule portée, l'espace `log-muninn` : `appi-muninn` y écrit ses traces (table
`AppDependencies`), à côté des journaux des applications. Les éléments du classeur se limitent à
ceux des exemples officiels : texte, paramètres texte, requêtes en tableau. Les graphiques, un
paramètre de plage de temps et un lien profond vers la vue de transaction ont des formats non
documentés : ils sont écartés plutôt que devinés.

Le modèle est écrit en ASCII pur : sous Git Bash, Python écrivait dans l'encodage de la console,
que `az` refusait (« unknown decoding »). Le chemin du modèle est converti par `cygpath` : `az`,
programme Windows, ne lit pas `/tmp`.

## 3. Vérification

- Les six requêtes ont été exécutées sur l'espace le 23 octobre 2026, environnement `production` :
  6 étapes, 3 heures d'appels, 76 lignes d'anomalies, 100 événements de révision, l'appel
  `dd2874a4…` retrouvé avec ses étapes et ses 2 lignes de journal.
- Le modèle est validé par Azure (`az deployment group validate`, état `Succeeded`), sans rien
  créer.
- `tests/test_classeur.py` : une requête par section, éléments limités aux types 1, 3 et 9,
  paramètres déclarés pour chaque usage, requêtes d'un appel gardées contre un identifiant vide
  (sans garde, `Log_s has ""` rendrait tout le journal), modèle stable et ASCII.

Ce qui reste à voir à l'écran, après le déploiement par le porteur : l'affichage réel des
tableaux et des paramètres dans le portail.

## 4. Ce que le classeur a déjà révélé

À sa première exécution, la section « Avertissements et erreurs » a remonté 44 erreurs
`Failed to derive Resource from Tracer Provider` de l'exportateur d'Application Insights, et
981 lignes du journal HTTP d'Azure, soit 23 % des octets des journaux de l'application sur
24 heures. Les traces arrivaient malgré tout (réponses 200). Corrigé dans la même PR : le
fournisseur de traces est passé à l'exportateur, et le journal HTTP d'Azure est relevé au niveau
WARNING (`src/muninn/telemetrie.py`, test `test_exportateur_relie_a_notre_fournisseur_et_journal_http_muet`).

Observation non traitée : la table `AppDependencies` est conservée 90 jours, contre 30 pour le
reste de l'espace. La facturation de cette rétention n'a pas été vérifiée.
