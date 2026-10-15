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

- [x] Communes de l'API Géo (SRC-03) : un seul appel, champs utiles seulement (ni population ni géométrie), agent identifié ; rejets motivés (champ manquant, format, doublon). Preuve : `src/muninn/ingestion/api_geo.py`.
- [x] Recoupement avec le COG et les codes postaux, écarts enregistrés dans `ref.commune_source_gaps` (VD-09). Sur les vraies données du 15 octobre 2026, dans un PostgreSQL 16 local : 34 969 communes comparées en 2 s ; aucune commune du COG absente de l'API, aucun nom différent ; 94 codes en plus, tous dans la liste figée de l'outre-mer (975 à 989) ; codes postaux identiques à ceux de La Poste pour chaque commune présente dans les deux sources ; rejeu sans version créée.

### Étape 4 : la page web (C1)

- [x] Catégorie « Lexique en français de la plomberie » du Wiktionnaire (SRC-12) : une seule requête sur `/wiki/` (autorisé par `robots.txt`), agent identifié avec le contact choisi par le porteur (profil GitHub public), titres lus dans le seul bloc `mw-pages`. Le 15 octobre 2026 : 123 termes lus, 121 gardés, 2 écartés (même forme normalisée), version `2026.10.1` au statut `candidate` ; rejeu sans version créée. Preuve : `src/muninn/ingestion/lexique.py`.
- [x] Attribution CC BY-SA 4.0 conservée par terme : source, titre de page et licence en base, lien vers la page reconstruit pour chaque terme ; seuls les titres sont repris, jamais les définitions (US-48, critère 4).

### Étape 5 : la base de données (C1, C2)

- [x] Requête SPARQL sur Wikidata (SRC-11), versionnée dans `src/muninn/ingestion/requetes/wikidata_marques_plomberie.rq` : fabricants d'équipements de plomberie (P1056) ou du secteur (P452), établis en Europe ; licence CC0 ; empreinte de la requête au rapport. Le 15 octobre 2026 : 21 entités. Pertinence faible, assumée comme en phase 0 (entreprises de service mêlées aux marques, aucun tri à la main en V1).
- [x] Fusion du lexique : Wiktionnaire et Wikidata, un terme par forme normalisée, source, référence et licence par terme, termes `accepted` par règles écrites. Aucune saisie à la main en V1 (relecture humaine retirée, dossier V1, V-04). Version `2026.10.2` : 142 termes (121 du Wiktionnaire, 21 marques), statut `candidate` jusqu'à l'évaluation de l'étape 7.
- [x] Repli : instantané versionné des deux sources (`src/muninn/ingestion/donnees/lexique-secours-plomberie.json`, réécrit par `muninn-ingestion lexique-secours`) ; une source qui ne répond pas passe par lui, et le rapport de la version dit « secours », avec la raison. Testé avec un refus 429 de Wikidata.

### Étape 6 : le système big data et la commande unique (C1, C2, C4)

- [x] Sirene (SRC-01) : lecture à distance des Parquet de data.gouv.fr avec DuckDB 1.5.6, requête versionnée (`src/muninn/ingestion/requetes/sirene_etablissements.sql`), jointure des unités légales pour la catégorie juridique, minimisation et secret statistique avant écriture dans `market` ; contrôles VD-21, VD-23 et seuil, bloquants. Stock du 1er octobre 2026 : 260 926 établissements actifs, 2 614 lignes servies (dont 11 masquées), 1 529 établissements sans commune écartés et comptés.
- [x] Durée et volume mesurés le 15 octobre 2026 : 290,6 Mo transférés en 2 640 requêtes HTTP partielles, sur 2,9 Go de fichiers ; calcul de 94 à 188 s selon le réseau. Le repli (agrégats versionnés) n'est pas nécessaire.
- [x] Une commande lance tout le pipeline, ou une étape : `muninn-ingestion tout` (`cog`, `codes-postaux`, `api-geo`, `lexique`, `sirene`). Sur une base neuve : 255 s, cinq sources chargées, tous les contrôles réussis.
- [x] Rejouable : second passage en 22 s, aucune version créée (empreinte de fichier, de lexique, ou date de stock et version de requête) ; une source modifiée crée une nouvelle version ; un échec de contrôle ou une panne laisse la version servie intacte (tests en base).
- [x] Journal de chaque passage : une ligne par source (statut, comptes, contrôles) à la sortie, rapport détaillé en base (`report`) ; aucune valeur recherchée ni donnée personnelle.

### Étape 7 : l'ancrage, l'API des référentiels (C2, C5)

- [x] Communes candidates pour un nom, un code postal, ou les deux : égalité exacte après normalisation ; commune déléguée et arrondissement renvoyés à leur commune ; nom et code incohérents signalés sans correction. Sur les vraies données : « Vincennes » rend 94300, « Montreuil » trois candidates (28, 85, 93), « Bagnolet » avec 93100 est incohérent (93170).
- [x] Terme du lexique le plus proche d'un mot, pour un métier : similarité trigramme ; sous le seuil de 0,55, refus « hors corpus » ; métier sans lexique publié, « hors périmètre ».
- [x] Agrégats Sirene lus par l'API (`GET /v1/referentiels/marche/{metier}`), avec la date du stock et la règle du secret statistique.
- [x] Sources citées dans chaque réponse (jeu, source, titre, éditeur, licence, adresse, dates, version, table) et, pour chaque valeur, la table et la clé de la ligne ; un test remonte de la référence à la ligne de la base. Note : `api-referentiels.md`.
- [x] Refus motivés, sans valeur inventée : `hors_corpus`, `hors_perimetre`, `incoherent` ; 422 pour une entrée mal formée ou un champ non prévu.
- [x] SQL sécurisé : requêtes paramétrées seulement, connexion en lecture seule quel que soit le rôle, délai de 3 s par requête, versions publiées seules ; valeurs reçues ni journalisées ni stockées. Une tentative d'injection est un simple « hors corpus », tables intactes (test).
- [x] Seuil calibré par un protocole commité avant la mesure (commit `f6d19db`) : 0,55, le plus bas sans fausse acceptation ; rappel 24/25 (IC 95 % [0,80 ; 0,99]), 0 fausse acceptation sur 20 (borne haute 0,16) ; marge étroite, dite. Le lexique n'est publié que si son empreinte est évaluée. Preuve : `calibration-seuil.md`.
- [x] Tests : 25 tests de l'API sur une base chargée par la vraie commande (sources, références, refus, entrées mal formées, injection, lecture seule, base indisponible, limite de débit, cohérence du seuil, lexique non évalué) ; 111 tests au total.

### Étape 8 : la vue pour l'évaluateur (D-57)

- [x] Écran « Référentiels » de la console (`/referentiels`) : trois questions (commune, terme de métier, marché), la question rappelée, la réponse et ses sources (titre, éditeur, licence, dates lisibles, version, table, lien vers la source), ou le refus et son motif ; Swagger de l'API en plus (`/docs`). Captures sur les vraies données locales : `preuves/etape-8-*.png`.
- [x] Limite de débit sur les points de lecture exposés : 120 par minute et 5 000 par jour, globale (étape 7, testée).
- [x] Contrôle d'accessibilité axe-core (WCAG 2.2 AA) sur les 9 états de l'écran, en CI ; une violation trouvée et corrigée (zone de résultat étiquetée par un titre absent, à l'état vide).

### Étape 9 : la minimisation RGPD, documentée

- [x] Note du sprint (`rgpd.md`) : données personnelles par source ; minimisation appliquée à Sirene (colonnes lues, aucun fichier sur disque, SIREN en mémoire seulement, agrégats sous secret statistique) ; non-applicabilité argumentée pour les cinq autres sources ; valeurs recherchées ni journalisées ni stockées, prouvé par un test ; écarts avec la fiche RT-07 de la phase 1, tous plus protecteurs ou neutres.

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
