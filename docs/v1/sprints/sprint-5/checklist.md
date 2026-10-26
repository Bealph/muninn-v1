# Sprint 5 : la vigie et la démo

**Objectif (consigne) :** rendre le système pilotable et reprenable : métriques et traces, tableau
de bord lisible par un non-développeur, alertes à seuils argumentés chacune liée à une action,
documentation d'exploitation qu'un tiers peut suivre seul. Le sprint se termine par la répétition
de la démonstration finale.
**Périmètre :** V1 (`docs/v1/dossier-conception-v1.md`), éléments V-09, V-10 et V-12, plus la
« V1.0 complète » : traces OpenTelemetry vers Application Insights et alerte Azure Monitor (§ 2.4,
D-40, D-52). Rien hors V1. Les sprints sont reliés : la vigie mesure la composante du sprint 4,
livrée par la chaîne du sprint 2, sur les référentiels du sprint 3 ; les reprises du sprint 4 sont
dans `../sprint-4/signaux-sprint-5.md`, § 4.
**Méthode :** pas à pas. Chaque étape est validée par le porteur avant la suivante. Une case n'est
cochée qu'avec sa preuve (fichier, capture, exécution de la chaîne ou de la commande).
**Calendrier (D-81) :** du jeudi 22 au dimanche 25 octobre 2026 au matin ; la feuille de route le
plaçait les 20 et 21 octobre. Premier oral blanc le 29 octobre, livrables gelés le 28.

## Ce que veut dire la consigne pour Muninn

| Travail attendu                | Pour Muninn (V1)                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Instrumenter                   | Métriques tirées de la base (V-10) : latence, coût, taux d'erreur, taux de refus, et les signaux propres à la composante (part « à vérifier », garde-fous déclenchés, borne d'outils, brouillons de secours, corrections par champ). Traces OpenTelemetry du parcours principal vers Application Insights (D-40). Aucun contenu dans un signal (OB-1). Références : `signaux-sprint-5.md` |
| Construire le tableau de bord  | Écran « Qualité » de la console (V-10) : la santé du service dite en mots et en couleurs (bon, à surveiller, en alerte), compréhensible sans explication ; chiffres et tendances en second plan                                                                                                                                                                                           |
| Configurer les alertes         | Pour chaque signal clé : un seuil argumenté (objectifs de service de la phase 2, valeurs mesurées au sprint 4), une alerte, une action documentée dans `docs/exploitation.md`. AL-01 (part « à vérifier ») calculée et affichée par l'application ; au moins une alerte Azure Monitor (D-40)                                                                                              |
| Documentation d'exploitation   | `docs/exploitation.md` : déployer, diagnostiquer une panne type, faire un retour arrière ; écrite pour un tiers sans aide, testée comme telle                                                                                                                                                                                                                                             |
| Durcir                         | Écarts du contrat personnel : CA-5 (correction et validation, V-09), CA-6 partie 2 (retour arrière puis SC-01), CA-8 (voix, V-12, D-74). Reprises du sprint 4 : dialogues de l'annexe A selon la trame v1.2, contrôles de la vérification du serveur, rôle Foundry restreint. Retours des ateliers et des pairs                                                                           |
| Répéter la démo des 10 minutes | Écran « Démonstration » (maquette validée le 21 octobre) : deux téléphones, conversation à deux voix, chaîne animée jusqu'au dossier ; une livraison automatique réelle ; une alerte déclenchée par une dérive simulée. Scénario écrit, chronométré, répété                                                                                                                               |

## Stack, ressources et interfaces externes du sprint

Relevé le 22 octobre 2026 dans le dépôt (`pyproject.toml`, `uv.lock`) et dans le groupe de
ressources Azure. « Nouveau » : à ajouter ou à créer pendant le sprint ; toute création de
ressource Azure est faite par le porteur, par un script relu (R10). Les coûts marqués « à
vérifier » le seront dans la documentation officielle avant la création.

| Élément                                     | Rôle dans le sprint                                                                              | État                                                              | Étapes   |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | -------- |
| Python, FastAPI, Pydantic, Jinja            | API et console : enregistrement, correction, écrans Qualité et Démonstration                     | Existant                                                          | 1 à 6    |
| PostgreSQL flexible `psql-muninn`           | Dossiers, messages, corrections, métriques (D-82)                                                | Existant ; nouvelles tables                                       | 1, 2, 3  |
| SQLAlchemy, Alembic                         | Migration des nouvelles tables                                                                   | Existant                                                          | 1        |
| OpenTelemetry SDK (Python)                  | Traces du parcours principal                                                                     | Existant, déjà installé par Langfuse                              | 3        |
| Exportateur vers Application Insights       | Envoi des traces (D-40) ; exportateur Azure Monitor ou collecteur, à trancher                    | Nouveau ; version à choisir selon `exclude-newer`                 | 3        |
| Application Insights                        | Traces et requêtes ; une ressource liée à l'espace `log-muninn` existe-t-elle déjà pour Muninn ? | Plusieurs composants existent ; choix à l'étape 3                 | 3        |
| Log Analytics `log-muninn`                  | Journaux de l'application, source de l'alerte AL-04                                              | Existant                                                          | 3, 5, 8  |
| Azure Monitor : règle d'alerte sur journaux | AL-04 (D-83)                                                                                     | Nouveau ; coût à vérifier                                         | 5        |
| Azure Monitor : groupe d'actions            | Courriel au porteur quand AL-04 se déclenche                                                     | Nouveau                                                           | 5        |
| Classeurs Azure Monitor (Workbooks)         | Vue technique à côté de l'écran Qualité : traces, journaux, alertes (phase 2, § 2.1)             | Nouveau ; sans service ni coût fixe annoncés, à vérifier          | 4        |
| Azure AI Speech (ressource Foundry)         | Synthèse à deux voix et transcription (D-50, V-12) ; rôle Speech à donner à l'identité           | Nouveau usage ; coût à vérifier ; rôle à attribuer par le porteur | 6        |
| Azure AI Foundry, gpt-5.4-mini              | Qualification et agent, inchangés ; rafale de la dérive (D-84)                                   | Existant                                                          | 5, 9     |
| Langfuse Cloud UE                           | Traces des appels au modèle, inchangées (V-13)                                                   | Existant                                                          | 3        |
| Azure Container Apps, registre `crmuninn`   | Livraison, révisions, retour arrière                                                             | Existant                                                          | 8, 10    |
| GitHub Actions (`ci`, `retour-arriere`)     | Livraison automatique de la démo, retour arrière de CA-6                                         | Existant                                                          | 8, 9, 10 |
| Playwright, axe-core                        | Accessibilité des nouveaux écrans en CI                                                          | Existant                                                          | 2, 4, 6  |
| Navigateur : Web Audio, lecture audio       | Sonnerie et voix dans l'écran Démonstration                                                      | Nouveau usage, sans dépendance                                    | 6        |
| Chrome (poste)                              | Captures des infographies (Edge 155 ne démarre plus sans interface)                              | Existant                                                          | 11       |

Aucune nouvelle source de données externe : les référentiels du sprint 3 sont déjà chargés.

## Critères d'évaluation par le pair, et étapes qui les prouvent

| N° | Critère du pair                                                                            | Étapes  | Preuve attendue                                                                                                |
| -- | ------------------------------------------------------------------------------------------ | ------- | -------------------------------------------------------------------------------------------------------------- |
| P1 | Une dérive simulée déclenche l'alerte prévue, et l'action documentée existe (en direct)    | 3, 5, 8 | Dérive provoquée en production, alerte affichée, action suivie depuis `docs/exploitation.md`                   |
| P2 | Le tableau de bord est compris par l'évaluateur sans explication orale                     | 4       | Écran « Qualité » en production ; questions de compréhension posées à l'évaluateur, réponses consignées        |
| P3 | Le test de la doc : déployer, diagnostiquer la panne simulée, faire le retour arrière seul | 8       | `docs/exploitation.md` ; essai par un tiers ; chaque point bloquant consigné comme trou de la doc, puis traité |
| P4 | La démo répétée tient en 10 minutes et montre du réel                                      | 6, 10   | `demonstration.md` chronométré, au moins deux répétitions mesurées ; tout en production                        |
| P5 | Grille de retours tenue sur l'ensemble de la série                                         | 0, 11   | Grille de la série (sprints 2 à 5) : chaque retour, sa décision, sa justification, son lien                    |

## Étapes

### Étape 0 : cadrage du sprint

- [x] Checklist rédigée et versionnée (ce fichier).
- [x] Calendrier et périmètre recalés par décision écrite (accord du porteur du 21 octobre 2026) : dates du sprint, ordre des étapes, ce qui passe en réserve si le temps manque. Preuve : D-81, du 22 au 25 octobre au matin.
- [x] Décision : enregistrement des dossiers et des messages en base pour la correction, la validation et les métriques (V-09, V-10) ; données synthétiques seulement ; durée de conservation ; aucune transcription ni audio stockés. Preuve : D-82, 30 jours, purge par commande.
- [x] Décision : les signaux clés, leurs seuils et leurs alertes (lesquelles calculées par l'application, laquelle par Azure Monitor), et la dérive simulée de la démonstration. Preuve : D-83 (AL-01, AL-16 dans l'application ; AL-04 dans Azure Monitor), D-84 (rafale d'appels ambigus).
- [x] Journal des retours du sprint (D-59) : `retours.md` ; grille de la série amorcée (retours des sprints 2 à 4). Preuve : `retours.md`, `../retours-serie.md`.

### Étape 1 : les traitements enregistrés (V-09, V-10)

- [x] Tables des dossiers, des messages, des traitements (métriques sans contenu) et des corrections (champ corrigé, jamais la valeur) ; migration ; rôles. Preuve : migration `0003_traitements.py` (schéma `app`, rôle de groupe `<base>_app`), rôle de connexion `<base>_traitements` (`roles.py`, D-85), `tests/test_traitements_base.py`.
- [x] Chaque traitement de l'API écrit son enregistrement ; aucune transcription en base ; tests. Preuve : `src/muninn/traitements/enregistrement.py`, appelé par `/v1/demo/runs` et `/v1/extract/text`, refus compris ; purge à 30 jours (`muninn-purge`) ; 430 tests, base comprise, aucun ignoré.
- [x] En production : `08-traitements.sh` lancé par le porteur ; enregistrement vérifié avec `consulter-base.sh <env> --traitements`. Preuve : sortie du porteur du 22 octobre 2026 (préproduction et production : migration, rôle, révision contrôlée ; en production, SC-01 enregistré, une ligne `dossier`, dossier « brouillon »).

### Étape 2 : correction et validation (V-09, CA-5)

- [x] Route de correction et de validation : le serveur rejoue le contrôle ; état « brouillon » puis « validé » ; une ligne de correction par champ, sans la valeur. Preuve : `POST /v1/demo/runs/{draft_id}/review` (D-86), `src/muninn/traitements/revue.py`, `tests/test_revue_base.py`.
- [x] Écran : corriger un champ, « Valider » ; SC-03 de bout en bout ; accessibilité contrôlée (axe-core). Preuve : formulaire « Corriger et valider » de l'écran « Agent », route `/agent/valider` ; parcours de la console et pages contrôlées par axe-core (`test_parcours_de_la_console`, `test_dossier_a_valider_accessible`). SC-03 avec le vrai modèle : à l'étape suivante, en production.
- [x] CA-5 vérifié sur Azure, 3 sur 3 ; « 93170 » absent de la table des corrections et des journaux. Preuve : `preuves/etape-2-ca-5.json` (révision `6e80aad`, 22 octobre 2026 : commune et code postal « incohérent » avant, « vérifié » après, 3 sur 3) ; `consulter-base.sh production --traitements` lancé par le porteur : 3 dossiers « valide », 3 corrections ; Log Analytics, 30 minutes : 0 ligne contenant « 93170 », 3 lignes `revue.fin` citant le seul nom du champ ; la colonne `champ` n'accepte que `^[a-z_.]{1,80}$`.

### Étape 3 : instrumenter (métriques et traces)

- [x] Métriques tirées de la base : latence, coût, taux d'erreur, taux de refus, part « à vérifier », garde-fous, borne, brouillons de secours, corrections par champ ; sans contenu. Preuve : `src/muninn/traitements/metriques.py`, route `GET /v1/demo/quality` (fenêtres 1 h, 24 h, 7 j, 30 j ; modèle simulé exclu ; résultat gardé 15 s), `tests/test_metriques_base.py`.
- [x] Traces OpenTelemetry du parcours principal (qualification, agent, outils, contrôles) vers Application Insights (D-40) ; attributs en liste blanche (OB-2) ; vérifiées sur une requête réelle. Preuve : `preuves/etape-3-traces.json`, produite par `eval/production/verifier_traces.py` (révision `8d48d0e`, 23 octobre 2026). SC-10 joué en préproduction et en production : 2 sur 2 conformes. Pour chaque appel : arbre complet (`outil` sous `agent`, toutes les étapes sous `appel`), rôle `preproduction.muninn-api` ou `production.muninn-api`, uniquement des attributs de la liste blanche, durées égales à celles de `steps` à 1 ms près. Le contrôleur refuse les traces du matin, faites avant les PR 180 et 181 (parents absents). Correctifs apportés en route : INC-07 (PR 180), environnement dans le rôle (PR 180), parenté indépendante de Langfuse (PR 181).
- [x] Incident INC-07 corrigé : le 23 octobre, `09-observabilite.sh` a laissé le trafic de production sur l'ancienne révision, car la réponse de `update` était périmée. Les quatre scripts qui créent une révision relisent désormais son nom et vérifient qu'elle porte la modification demandée. Fiche : `incidents/INC-07-revision-perimee-apres-mise-a-jour.md`.
- [x] L'API rend la liste chronologique des étapes d'un traitement, avec leur durée (reprise du sprint 4). Preuve : champ `steps` de `/v1/demo/runs` (appel, contrôle d'entrée, qualification, message, agent, chaque outil, contrôles du serveur), mesuré par `muninn.telemetrie.etape`, `tests/test_telemetrie.py`.

### Étape 4 : le tableau de bord (V-10)

- [x] Écran « Qualité » : état du service en mots et en couleurs, puis les chiffres (latence, coût, refus, erreurs, part « à vérifier », corrections) ; période choisie ; aucune donnée personnelle. Preuve : `preuves/etape-4-ecran-qualite-production.png`, console de production, révision `9aa617b`, 23 octobre 2026, 12:37 UTC (9 appels sur 24 heures, état « pas assez d'appels pour juger »). Note : `ecran-qualite.md` (six choix à valider par le porteur, section 4). PR 183.
- [x] Classeur Azure Monitor (Workbook) : vue technique des traces, des journaux et des alertes, pour l'exploitant ; créé par un script relu, versionné. Preuve : `infra/azure/10-classeur.sh` lancé par le porteur le 23 octobre 2026 (classeur `71e28fe0-f97a-54ea-a0e9-2efb76e9bd8d`, « Muninn, exploitation », lié à `log-muninn`, étiqueté `projet=muninn`) ; contenu relu par l'API REST, identique au dépôt (14 éléments). Note : `classeur.md`. PR 187.
- [x] Relu par un non-développeur : ce qu'il comprend seul est consigné ; les points flous sont corrigés. Relecture **simulée** (agent jouant un artisan sans connaissance informatique, devant la seule capture de production), à la demande du porteur ; dix constats, tous corrigés (PR 187). Détail : `ecran-qualite.md`, section 7.

### Étape 5 : les alertes

- [x] Pour chaque signal clé : seuil argumenté, alerte, action documentée ; tableau dans `docs/exploitation.md`. Preuve : `docs/exploitation.md`, section 1 (AL-01, AL-04, AL-16, budget : seuil, raison, alerte, action pas à pas, manière de la provoquer).
- [x] AL-01 calculée et affichée par l'application (part « à vérifier », 20 extractions au moins). Preuve : `src/muninn/traitements/etat.py`, écran « Qualité » (étape 4, PR 183 à 187), `tests/test_etat.py` (20 % pile : sous le seuil ; 25 % : alerte ; moins de 20 dossiers : non jugé).
- [x] Une alerte Azure Monitor sur les journaux (D-40), avec son groupe d'actions ; créée par le porteur par un script relu (R10). Preuve : `11-alertes.sh` lancé par le porteur le 26 octobre 2026 : règle `al04-muninn-modele` active (15 min, fenêtre 1 h), groupe `ag-muninn` ; courriel d'essai `Succeeded` à 08:36 UTC et reçu par le porteur, après le courriel d'inscription au groupe (`preuves/etape-5-al04.json`). Requête testée sur l'espace et aux seuils exacts.
- [x] Dérive simulée : un moyen reproductible de la provoquer en production, sans données réelles ; alerte constatée. Preuve : `rafale.py --profil derive --nombre 22` (22 appels SC-10, 0,12 €) le 26 octobre 2026, 08:06 à 08:09 UTC, révision `d9c2f81` ; l'écran est passé de « Aucun problème détecté depuis 24 heures » à « Alerte », AL-01 à 100 % (22 sur 22), épisode dans l'historique : `preuves/etape-5-derive.json`, `preuves/etape-5-derive-ecran.png`.

### Étape 6 : la voix et l'écran « Démonstration » (V-12, CA-8)

- [x] Synthèse à deux voix et transcription par Azure AI Speech (D-50), audio jamais écrit sur disque ; faux fournisseur pour les tests. Livré le 26 octobre (PR 193), réglages posés par `13-voix.sh`.
- [x] Écran « Démonstration » selon la maquette validée : deux téléphones, sonnerie de 15 s, conversation jouée, chaîne animée depuis les étapes rendues par l'API (« rejoué ») ; quatre scénarios ; l'écran « Agent » est gardé. Livré le 26 octobre (PR 193), WCAG 2.2 AA après relecture.
- [ ] CA-8 vérifié sur Azure selon l'avenant D-74, 3 sur 3. Troisième mesure du 26 octobre (`preuves/etape-6-ca8.json`, production `74b1e55`) : SC-01 0 sur 3, le téléphone dicté étant le seul écart (4,5 à 15 s pour 45 s permises) ; démonstration 4 sur 4. Limite de la transcription documentée sans contournement (`incidents/INC-09-numero-dicte-mal-transcrit.md`) ; mesures précédentes conservées.

### Étape 7 : durcir

- [ ] Dialogues de l'annexe A réécrits selon la trame v1.2 (consigne de sécurité dite par Muninn dans SC-04), relus par le porteur, figés ; critères et V-08 rejoués. **Reporté après le premier oral** (décision du 26 octobre 2026, sous la délégation du porteur, réversible) : la réécriture demande la relecture du porteur et rejoue tous les critères, V-08 et CA-8 ; à deux jours du gel, elle invaliderait les mesures de l'étape 9, faites sur la révision active. Inscrit au suivi des tâches.
- [x] Contrôles du texte des critères reportés dans `muninn.demo.verification` (dette du sprint 4). Preuve : nom de SC-01, objet L-05 de SC-05, commune et code postal vérifiés pour SC-05 et SC-07, code postal et département des candidates de SC-10 dans `verifier_annexe_a` ; `tests/test_verification.py` (une faute, un écart) ; compléments retirés de `eval/production/verifier_criteres.py`.
- [ ] Rôle de l'identité de l'application limité à l'inférence, si le service le permet ; sinon dette documentée. Vérifié le 26 octobre 2026 : le service le permet avec trois rôles, dont un personnalisé (`role-identite.md`, sources Microsoft Learn) ; **reporté après le premier oral** (changement de droits en production, R10), plan d'essai écrit.
- [x] Retours des ateliers et des pairs traités, chacun avec sa décision. État au 26 octobre 2026 : aucun retour du pair reçu sur la série (sprints 2 à 5 : `retours.md`, `../retours-serie.md`) ; retours de l'atelier n° 1 non consignés dans le dépôt par décision du porteur du 13 octobre 2026, présentés à l'oral (`../sprint-2/checklist.md`).

### Étape 8 : la documentation d'exploitation

- [x] `docs/exploitation.md` : prérequis, déployer, vérifier, diagnostiquer une panne type, faire un retour arrière, tableau des alertes et de leurs actions ; écrite pour un tiers. Relue le 26 octobre 2026 par un agent jouant l'évaluateur pair (lecture seule, sans aide) : 12 constats, tous traités, dont un défaut du retour arrière (une révision de configuration ne se défaisait pas), corrigé et testé (`tests/test_retour_arriere.py`).
- [x] Panne type simulable en production, sans risque pour les données. Preuve : `12-panne.sh production --provoquer` le 26 octobre 2026 (révision `0000095`, point d'accès du modèle mal configuré) ; 20 appels, 20 brouillons de secours, aucun appel perdu, 0 € ; écran « Qualité » en alerte ; AL-04 reçue par courriel à 09:33:42 UTC ; réparation par `--reparer` (révision `0000096`) : `preuves/etape-8-exercice-panne.json`.
- [x] Test de la doc par un tiers, sans aide : chaque point où il bloque est consigné comme trou de la doc, puis corrigé. Deux passes : (1) relecture par un agent jouant l'évaluateur pair, 12 constats corrigés, dont le retour arrière qui ne défaisait pas une révision de configuration ; (2) exercice réel par le porteur, qui n'a pas écrit le guide, avec le seul guide, sans aide : panne, diagnostic, retour arrière, réparation, aucun blocage noté. L'évaluateur pair le refera à l'évaluation.

### Étape 9 : le contrat personnel

- [x] CA-1 à CA-8 vérifiés sur la révision active d'Azure, 3 sur 3 ; CA-6 partie 2 démontrée (version dégradée, retour arrière, SC-01 en moins de 5 minutes) ; `contrat-personnel.md` à jour. Fait le 26 octobre 2026 : CA-6 partie 2 démontrée (version dégradée `0000095`, retour arrière, SC-01 conforme en 2 min 33 s : `preuves/etape-8-exercice-panne.json`) ; CA-1 à CA-8 mesurés le 26 octobre sur la révision active `9dee403` (`contrat-personnel.md`) : contrat 6 sur 6 tenu, CA-7 tenu, CA-8 non atteint sur le téléphone (INC-09).

### Étape 10 : la démo des 10 minutes

- [x] Scénario écrit : parcours principal, une livraison automatique, une alerte déclenchée ; minutage par séquence ; plan B si le direct échoue. Preuve : `demonstration.md` (sept séquences, critères P1 à P5, plan B par séquence).
- [ ] Au moins deux répétitions chronométrées, en production ; durées consignées ; tient en 10 minutes. Fait le 26 octobre 2026 : deux répétitions techniques en production (`eval/production/repetition_demo.py`, `preuves/etape-10-repetition-1.json` et `-2.json` : 33,9 à 36,3 s par appel joué, CA-8 respecté à l'écran). Reste : deux répétitions orales chronométrées par la personne qui présente (`demonstration.md`, § 5).

### Étape 11 : clôture (rituel de fin de sprint)

- [x] Checklist close ; compte rendu de sprint (C16) ; fiches d'incident s'il y en a (C21). Preuve : chaque case cochée avec sa preuve, ou ouverte avec sa décision écrite (étapes 7 et 10) ; `compte-rendu.md` ; INC-07 à INC-10.
- [x] Déroulé de démonstration ; journal des retours ; grille de retours de la série complète. Preuve : `demonstration.md` (séquences, critères P1 à P5, plan B, répétitions) ; `retours.md` ; `../retours-serie.md` (état au 26 octobre : aucun retour reçu).
- [x] Section « Sprint 5 » des deux infographies, rendus régénérés (navigateur de capture à vérifier : Edge 155 ne démarre plus sans interface). Preuve : section 12 de la fiche d'ingénierie, section 11 de la présentation archivée ; PDF, PNG et sections refaits avec Chrome (`../../infographie/README.md`).
- [x] Suivi des tâches et des compétences à jour ; journal de session (local). Preuve : `docs/suivi/taches.md`, `docs/suivi/competences.md` ; journal du 26 octobre (local, hors dépôt).
