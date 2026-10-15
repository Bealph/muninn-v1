# Sprint 3 : les données et l'ancrage

**Objectif (consigne) :** brancher le projet sur ses données : ingestion, stockage, et le mécanisme
d'ancrage qui convient. À la fin du sprint, l'application répond à partir de ses données, en
citant ses sources (si c'est nécessaire, sinon on justifie la décision), et refuse proprement ce
qui sort de son corpus ou de son périmètre, livré par la chaîne du sprint 2.
**Périmètre :** V1 (`docs/v1/dossier-conception-v1.md`), éléments V-04 à V-06 (1,75 jour estimé).
Rien hors V1.
**Méthode :** pas à pas. Chaque étape est validée par le porteur avant la suivante. Une case n'est
cochée qu'avec sa preuve (fichier, capture, exécution de la chaîne ou de la commande).
**Début :** jeudi 15 octobre 2026, avancé par le porteur.

## Ce que veut dire la consigne pour Muninn

| Consigne                         | Pour Muninn (V1)                                                                                                                                                                                                                                            |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Données du projet                | Référentiels ouverts : codes postaux (SRC-06), COG (SRC-07), communes de l'API Géo (SRC-03), lexique métier du Wiktionnaire (SRC-12) et de Wikidata (SRC-11) ; agrégats Sirene (SRC-01). Aucune donnée de client : le serveur ne détient aucun dossier (R1) |
| Stockage                         | Base relationnelle seule (PostgreSQL, schémas `ref` et `market`). Pas de base vectorielle : aucun corpus documentaire à indexer (dossier V1, §3.3)                                                                                                          |
| Ancrage                          | SQL sécurisé : requêtes paramétrées, rôle en lecture seule, derrière l'API des référentiels (V-05). Ce sont les données que l'agent du sprint 4 interrogera par ses outils                                                                                  |
| Une « question »                 | Une recherche dans les référentiels : une commune, un code postal, un mot de métier, un code d'activité                                                                                                                                                     |
| Citer ses sources                | Chaque réponse cite la source de chaque valeur : jeu de données, identifiant de source, éditeur, licence, adresse, date de la source, date de chargement, table et identifiant de ligne                                                                     |
| Refus hors corpus, sous un seuil | Commune absente des référentiels ; mot de métier sous le seuil de similarité (trigrammes, seuil [H : 0,8] à calibrer, contrat d'API §5.2) : refus motivé, sans valeur inventée                                                                              |
| Refus hors périmètre             | Métier non couvert par la V1, question libre, entrée mal formée : refus motivé                                                                                                                                                                              |
| Minimisation RGPD                | Sirene : projection de colonnes sans identité ni adresse, agrégats seulement ; référentiels sans donnée personnelle (non-applicabilité argumentée) ; valeurs recherchées jamais journalisées (TA-23)                                                        |

## Critères d'évaluation par le pair, et étapes qui les prouvent

| N°  | Critère du pair                                                                                             | Étapes      | Preuve attendue                                                                         |
| --- | ----------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------- |
| P1  | Les sources de données sont identifiées et licites (minimisation appliquée ou non-applicabilité argumentée) | 0, 2 à 6, 9 | Registre des sources du sprint : licence, date, URL, données personnelles, minimisation |
| P2  | Les réponses sont traçables : l'évaluateur pose une question et remonte à la source citée                   | 7, 8, 10    | Réponse en production avec sa source ; la ligne citée retrouvée dans la base            |
| P3  | Le refus hors corpus est démontré : l'évaluateur pose lui-même une question hors sujet                      | 7, 8, 10    | Refus motivé en production, sur une question choisie par l'évaluateur                   |
| P4  | Le pipeline d'ingestion est rejouable : une commande, pas une suite de manipulations                        | 6, 10       | Une commande en local, une commande en production ; second passage sans doublon         |
| P5  | Tout est visible en production, pas dans un notebook                                                        | 8, 10       | Écran et API en production, livrés par la chaîne                                        |
| P6  | Journal des retours tenu                                                                                    | 0, 11       | `retours.md` du sprint, à jour (D-59)                                                   |

## Étapes

### Étape 0 : cadrage du sprint

- [x] Checklist rédigée et versionnée (ce fichier).
- [x] Décision D-56 : ancrage par SQL sécurisé sur base relationnelle ; pas de base vectorielle, ni de RAG, ni de reclassement, faute de corpus documentaire. Preuve : `docs/decisions.md`.
- [x] Décision D-57 : écran « Référentiels » minimal dans la console, Swagger en plus ; points de lecture exposés en lecture seule, avec une limite de débit. Preuve : `docs/decisions.md`.
- [x] Décision D-58 : tâche Container Apps qui lance la même image, déclenchée par une commande ; ressource créée par le porteur après chiffrage (R10). Preuve : `docs/decisions.md`.
- [x] Journal des retours (D-59) : `retours.md` dans le dossier de chaque sprint. Retours de l'atelier n° 1 attendus du porteur pour le sprint 2.
- [x] Licences et conditions d'usage des six sources revérifiées le 15 octobre 2026 contre leur page officielle (agent `verificateur-sources`). Preuve : `sources.md`.

### Étape 1 : le schéma et le stockage

- [x] Modèle physique des schémas `ref` et `market`, sous-ensemble de la phase 1 (document 02) utile à la V1 ; écarts motivés. Preuve : `schema.md`.
- [x] Table de traçabilité des chargements (`ref.dataset_versions`) : source, adresse, date de la source, empreinte SHA-256, date de chargement, lignes lues, chargées, filtrées, rejetées ; leur somme est imposée par une contrainte. Preuve : migration `0001`.
- [ ] Migrations Alembic : commande `muninn-db upgrade`, embarquée dans l'image (contrôlé dans le job `build`) ; en local par `docker compose run --rm api muninn-db upgrade`. Reste : application en production par la tâche de D-58, avec l'extension `pg_trgm` autorisée sur le serveur.
- [x] Rôles de groupe `<base>_lecture` (API, lecture seule) et `<base>_ecriture` (ingestion, lignes seulement, sans `ref.naf_trades` ni droit sur le schéma). Preuve : migration `0001`, `schema.md` § 4.
- [x] Tests sur une base neuve, en CI (service PostgreSQL 16, tests de base obligatoires) : tables, correspondance NAF, droits des deux rôles, contraintes, une version publiée par jeu, secret statistique, annulation puis réapplication. 8 tests, 37 au total, tous réussis. Preuve : `tests/test_base.py`, PR n° 29.

### Étape 2 : les fichiers (C1, C3)

- [x] Codes postaux de La Poste (SRC-06, ISO-8859-1 imposé : le serveur l'annonce à tort en UTF-8) et COG de l'INSEE (SRC-07) : téléchargement tracé (adresse, date, empreinte SHA-256, taille), conversion en UTF-8, codes en texte (zéros en tête, Corse 2A et 2B). Preuve : `src/muninn/ingestion/`, PR n° 30.
- [x] Nettoyage selon les cas VD de la phase 1 : rejets motivés (format, champ manquant, doublon, commune inconnue), collectivités d'outre-mer et Monaco filtrées par une liste figée, contrôles VD-01, VD-02, VD-04, VD-08, VD-11. Sur les vrais fichiers du 15 octobre 2026 : COG 37 496 lignes gardées ; codes postaux 39 192 lues, 38 925 gardées, 267 filtrées, 0 rejet.
- [x] Chargement dans `ref`, avec la ligne de traçabilité. En CI sur des fichiers de test : publication, rejeu sans doublon, nouvelle version, échec de contrôle et panne sans effet sur la version servie. Sur les vrais fichiers, dans un PostgreSQL 16 local, le 15 octobre 2026 : 9 s pour les deux sources, tous les contrôles réussis (VD-08 : aucune commune sans code postal), rejeu sans version créée ; Vincennes 94300, trois « Montreuil » (28, 85, 93), Bagnolet 93170.

### Étape 3 : le service web (C1, C3)

- [ ] Communes de l'API Géo (SRC-03) : collecte, respect du quota publié, reprise sur erreur.
- [ ] Agrégation avec le COG et les codes postaux ; écarts entre sources comptés et expliqués.

### Étape 4 : la page web (C1)

- [ ] Une catégorie du Wiktionnaire (SRC-12) pour le métier de la démo : collecte respectueuse (agent identifié, débit limité, robots respectés).
- [ ] Attribution CC BY-SA 4.0 conservée par terme (US-48, critère 4).

### Étape 5 : la base de données (C1, C2)

- [ ] Requête SPARQL sur Wikidata (SRC-11), versionnée dans le dépôt ; licence CC0.
- [ ] Fusion du lexique (Wiktionnaire, Wikidata, saisie) : un terme, sa catégorie, ses sources, sa licence ; termes `accepted` seulement publiés.
- [ ] Repli prévu (risque du dossier, §7.1) : lexique de secours versionné si une source est indisponible ; l'indisponibilité est consignée.

### Étape 6 : le système big data et la commande unique (C1, C2, C4)

- [ ] Sirene (SRC-01) : lecture des Parquet de data.gouv.fr par HTTPS avec DuckDB ; requête SQL versionnée ; projection de colonnes sans identité ni adresse (minimisation) ; agrégats seulement dans `market`.
- [ ] Durée et volume lus mesurés ; repli si trop lent : agrégats calculés une fois et versionnés (risque du dossier, §7.1).
- [ ] Une commande lance tout le pipeline, ou une source : `muninn-ingestion` [nom à confirmer].
- [ ] Rejouable : un second passage sur la même source ne crée aucun doublon ; une source modifiée crée une nouvelle version ; une erreur laisse la version publiée intacte.
- [ ] Journal de chaque passage, sans aucune valeur recherchée ni donnée personnelle.

### Étape 7 : l'ancrage, l'API des référentiels (C2, C5)

- [ ] Communes candidates pour un nom, un code postal, ou les deux : égalité exacte après normalisation (dossier V1, §3.1) ; « Vincennes » rend 94300, « Montreuil » trois candidates.
- [ ] Terme du lexique le plus proche d'un mot, pour un métier : similarité trigramme ; sous le seuil, refus « hors corpus ».
- [ ] Agrégats Sirene lus par l'API.
- [ ] Sources citées dans chaque réponse (jeu, source, licence, adresse, dates, table, identifiant de ligne).
- [ ] Refus motivés : hors corpus, hors périmètre (métier non couvert, entrée mal formée ou trop longue) ; jamais de valeur inventée.
- [ ] SQL sécurisé : requêtes paramétrées seulement, rôle en lecture seule, délai maximal par requête ; valeurs reçues ni journalisées ni stockées (TA-23).
- [ ] Seuil de similarité calibré sur un petit jeu étiqueté (positifs et négatifs), protocole écrit avant la mesure ; résultat et incertitude consignés.
- [ ] Tests : contrat des réponses, sources présentes, refus, injection SQL sans effet.

### Étape 8 : la vue pour l'évaluateur (D-57)

- [ ] Écran « Référentiels » de la console, en production : une question, la réponse et ses sources, ou le refus et son motif ; Swagger en plus.
- [ ] Limite de débit sur les points de lecture exposés.
- [ ] Contrôle d'accessibilité axe-core sur l'écran.

### Étape 9 : la minimisation RGPD, documentée

- [ ] Note du sprint : données personnelles par source, minimisation appliquée (Sirene) ou non-applicabilité argumentée (référentiels), absence de valeurs recherchées dans les journaux ; renvoi au registre de la phase 1 (document 05).

### Étape 10 : le jeu de démonstration et la production

- [ ] Jeu de 5 à 10 questions versionné : couvertes, hors corpus, hors périmètre, chacune avec sa réponse attendue et sa source.
- [ ] Ce jeu tourne en CI sur une base de test, et contre la production après livraison.
- [ ] Ingestion lancée en production par la commande unique ; tables chargées, traçabilité lisible.
- [ ] Tout livré par la chaîne du sprint 2 ; les questions du jeu passent en production.

### Étape 11 : clôture (rituel de fin de sprint)

- [ ] Checklist close ; compte rendu de sprint (C16) ; fiches d'incident s'il y a lieu (C21).
- [ ] Déroulé de démonstration du sprint 3 (`demonstration.md`).
- [ ] Section « Sprint 3 » des deux infographies, rendus régénérés.
- [ ] Suivi des tâches et des compétences (C1 à C5) à jour ; journal de session.
