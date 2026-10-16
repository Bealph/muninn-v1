# Compte rendu du sprint 3 : les données et l'ancrage

**Période :** 15 et 16 octobre 2026
**Périmètre :** V1, éléments V-04 à V-06 (`docs/v1/dossier-conception-v1.md`), décisions D-56 à
D-60
**Compétences servies :** C1, C2, C3, C4, C5 ; C10, C13, C16, C17, C21 en partie

## 1. Objectif et résultat

**Objectif (consigne) :** brancher le projet sur ses données (ingestion, stockage, mécanisme
d'ancrage). L'application répond à partir de ses données en citant ses sources, et refuse
proprement ce qui sort de son corpus ou de son périmètre, livrée par la chaîne du sprint 2.

**Résultat : atteint, sauf le journal des retours du pair (en attente).** En production, l'écran
<https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/referentiels>
répond à partir des référentiels chargés, cite ses sources, et refuse ce qui sort des données
ou du périmètre.

**Ce que la consigne devient pour Muninn :** pas de corpus documentaire, donc ni RAG ni base
vectorielle ; des référentiels structurés, interrogés par SQL sécurisé (D-56). Une « question »
est une recherche de commune, de code postal, de terme de métier ou de marché.

## 2. Critères de l'évaluation par le pair

| N°  | Critère                                                            | Statut     | Preuve                                                                                          |
| --- | ------------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------- |
| P1  | Sources identifiées et licites ; minimisation ou non-applicabilité | Prouvé     | `sources.md` (six sources revérifiées le 15 octobre) ; `rgpd.md`                                |
| P2  | Réponses traçables : de la question à la source citée              | Prouvé     | Écran de production ; références table et clé ; `preuves/etape-10-production-commune.png`       |
| P3  | Refus hors corpus démontré sur une question de l'évaluateur        | Prouvé     | Statuts `hors_corpus`, `hors_perimetre`, `incoherent` ; `preuves/etape-10-production-refus.png` |
| P4  | Pipeline d'ingestion rejouable en une commande                     | Prouvé     | `gh workflow run donnees -f environnement=production` : 83 s, aucune version créée              |
| P5  | Tout visible en production, pas dans un notebook                   | Prouvé     | Console et API de production ; jeu de questions à 10 sur 10                                     |
| P6  | Journal des retours tenu                                           | En attente | `retours.md` créé ; retours du pair à recevoir                                                  |

## 3. Ce qui a été livré

| Étape | Livrable                                                                                                                                         | PR      |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| 0     | Checklist, décisions D-56 à D-59, registre des six sources revérifié                                                                             | 28      |
| 1     | Schémas `ref` et `market`, rôles de lecture et d'écriture, migrations Alembic, PostgreSQL en CI                                                  | 29      |
| 2, 3  | COG, codes postaux, API Géo : collecte tracée, nettoyage, rejets motivés, contrôles VD                                                           | 30, 31  |
| 4, 5  | Lexique de plomberie (Wiktionnaire, Wikidata), attribution par terme, instantané de secours                                                      | 32, 33  |
| 6     | Agrégats Sirene par DuckDB, secret statistique ; commande unique `muninn-ingestion tout`                                                         | 34      |
| 7     | API des référentiels : sources citées, refus motivés ; seuil du lexique calibré (protocole commité d'avance)                                     | 35      |
| 8     | Écran « Référentiels » de la console, accessibilité contrôlée sur 9 états                                                                        | 36      |
| 9     | Note de minimisation RGPD ; valeurs recherchées absentes des journaux (test)                                                                     | 37      |
| 10    | Tâche Container Apps des données, rôles de connexion, workflow `donnees`, jeu de 10 questions ; production chargée ; tâche planifiée chaque mois | 40 à 43 |
| hors  | `Makefile` des commandes courantes, appelé par la CI                                                                                             | 39      |

## 4. Mesures

| Mesure                                              | Valeur                                                                      | Source                               |
| --------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------ |
| Chargement complet, base neuve, poste               | 255 s ; rejeu 22 s, aucune version créée                                    | `checklist.md`, étape 6              |
| Chargement complet dans l'image, 1 vCPU et 2 Gio    | 345 s ; pic de mémoire échantillonné 494 Mio                                | Mesure du 16 octobre                 |
| Premier chargement en production (tâche Azure)      | 5 min 24 s ; préproduction 5 min 27 s                                       | `preuves/etape-10-production.md`     |
| Rejeu en production, une commande                   | 83 s, aucune version créée                                                  | Exécution GitHub Actions 38874739291 |
| Données chargées                                    | 37 496 communes ; 38 925 codes postaux ; 142 termes ; 2 614 cellules Sirene | Rapports des versions                |
| Sirene, lecture à distance                          | 290,6 Mo lus sur 2,9 Go                                                     | `sirene.py`, mesure DuckDB           |
| Seuil du lexique                                    | 0,55 : rappel 24/25 (IC 95 % [0,80 ; 0,99]), 0 fausse acceptation sur 20    | `calibration-seuil.md`               |
| Jeu de questions de démonstration                   | 10 sur 10, en préproduction et en production                                | Workflow `donnees`                   |
| Tests                                               | 143, en local et en CI, base comprise                                       | `make verifier`                      |
| CI sur une PR (21 exécutions, depuis le 15 octobre) | 103 à 178 s, médiane 134 s                                                  | Historique GitHub Actions            |
| Livraisons sur `main` (depuis le 15 octobre)        | 16 réussies, 0 échouée ; 8,2 à 13,1 min                                     | Historique GitHub Actions            |

Ces mesures portent sur peu d'exécutions : ce sont des ordres de grandeur.

## 5. Incidents

| Fiche  | Incident                                                        | Cause racine                                                      | Non-régression                                  |
| ------ | --------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| INC-04 | Première exécution de la tâche des données annulée par un délai | Délai de 5 s pensé pour l'API, appliqué aussi au rôle d'ingestion | Délai propre à chaque rôle, vérifié par un test |

Une autre exécution a échoué la même matinée, sans défaut du code : le mot de passe administrateur
fourni au script était faux. Il a été repris du secret de l'API, sans l'afficher
(`preuves/etape-10-production.md`).

Défauts trouvés et corrigés avant toute livraison, sans incident : clé d'unicité des codes postaux
(108 lignes légitimes auraient été rejetées), encodage de La Poste annoncé à tort en UTF-8,
transaction englobante implicite dans l'ingestion, catégorie juridique de Sirene absente du
fichier attendu, champs inconnus acceptés par l'API, base non installée en erreur 500, violation
d'accessibilité sur l'écran vide, `curl` de Windows incapable d'écrire dans `/dev/null`.

## 6. Décisions du sprint

D-56 (ancrage par SQL sécurisé), D-57 (écran « Référentiels » et exposition en lecture seule),
D-58 (ingestion en production par une tâche Container Apps), D-59 (journal des retours par
sprint), D-60 (tâche planifiée chaque mois). Détail dans `docs/decisions.md`.

## 7. Dettes et risques ouverts

| Sujet                                                             | Risque                                             | Traitement proposé                                                 |
| ----------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------ |
| Marge étroite du seuil du lexique (0,07)                          | Un autre lexique déplace le seuil                  | Publication conditionnée à l'évaluation de l'empreinte (en place)  |
| Wikidata peu pertinent (entreprises de service parmi les marques) | Termes inutiles dans le lexique                    | Assumé en V1 ; relecture humaine après la V1                       |
| Migrations non lancées par la livraison                           | Une future migration livrée avant d'être appliquée | Lancer `donnees` juste après la fusion ; à automatiser au sprint 4 |
| Mot de passe administrateur dans les secrets de la tâche          | Rôle propriétaire disponible dans la tâche         | Nécessaire aux migrations ; tâche sans entrée publique             |
| Extension de DuckDB téléchargée au démarrage                      | Dépendance réseau au moment de l'exécution         | Embarquer l'extension dans l'image                                 |
| Points des référentiels publics (écart avec le contrat)           | Abus                                               | Lecture seule, limite de débit, données ouvertes (D-57)            |
| Lecture de la règle de diffusion partielle de Sirene              | Interprétation juridique non confirmée             | Avis d'un juriste                                                  |
| Journal des retours du pair                                       | Critère P6 non prouvé                              | Retours à recevoir et à consigner dans `retours.md`                |
