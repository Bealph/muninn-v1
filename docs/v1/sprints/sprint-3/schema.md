# Schéma et stockage du sprint 3 (étape 1)

**Migration :** `src/muninn/db/migrations/versions/0001_referentiels.py`, appliquée par
`muninn-db upgrade`.
**Référence :** modèle physique de la phase 1
(`docs/conception/architecture_de_donnees/02-modele-de-donnees.md`, sections 3 et 4).
**Décision :** D-56 (base relationnelle seule, ancrage par SQL sécurisé).

## 1. Ce que la V1 garde du modèle de la phase 1

| Schéma   | Table                 | Rôle dans la V1                                                                         |
| -------- | --------------------- | --------------------------------------------------------------------------------------- |
| `ref`    | `dataset_versions`    | Traçabilité de chaque chargement : source, adresse, date, empreinte, comptes, statut    |
| `ref`    | `load_rejections`     | Lignes rejetées, avec leur motif : aucune ligne écartée en silence                      |
| `ref`    | `communes`            | Communes du COG (SRC-07), communes déléguées et associées comprises                     |
| `ref`    | `commune_source_gaps` | Écarts entre le COG et l'API Géo (SRC-03)                                               |
| `ref`    | `postal_codes`        | Codes postaux de La Poste (SRC-06)                                                      |
| `ref`    | `naf_trades`          | Codes NAF de la tête de pont vers les métiers ; alimentée par la migration              |
| `ref`    | `trade_lexicons`      | Versions du lexique par métier                                                          |
| `ref`    | `lexicon_terms`       | Termes du lexique (SRC-11, SRC-12, saisie), avec source et licence par terme            |
| `market` | `sirene_runs`         | Exécutions du traitement Sirene (SRC-01) et leurs mesures                               |
| `market` | `sirene_counts`       | Comptages agrégés après secret statistique : aucun SIREN, SIRET, commune ni code postal |

## 2. Ce qui est écarté, et pourquoi

| Table de la phase 1                                   | Raison                                                    |
| ----------------------------------------------------- | --------------------------------------------------------- |
| `ref.ban_streets`                                     | BAN retirée de la V1 (dossier V1, § 2.3)                  |
| `ref.numbering_ranges`                                | Contrôle du numéro retiré de la V1 (dossier V1, § 2.3)    |
| `ref.holiday_zone_departments`, `ref.public_holidays` | Rendez-vous et jours fériés hors V1                       |
| `ref.forwarding_codes`                                | Renvoi d'appel hors V1                                    |
| `market.urssaf_series`, `market.market_estimates`     | Croisement Urssaf (US-53) retiré de la V1                 |
| Schéma `app`                                          | Métadonnées techniques des comptes et appareils : hors V1 |

## 3. Écarts avec le modèle de la phase 1

| Élément                                  | Phase 1                                      | V1                                                                            | Raison                                                                                               |
| ---------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Jeux de `dataset_versions`               | `communes`, `postal_codes`, `ban_streets`, … | `communes`, `postal_codes`, `geo_api_communes`                                | Les seuls jeux de la V1 ; l'appel à l'API Géo est tracé comme un jeu à part, qui n'est jamais servi  |
| Couple jeu et source                     | Libre                                        | Imposé par une contrainte (`communes` avec SRC-07, etc.)                      | Une version ne peut pas citer une autre source que la sienne                                         |
| `communes.department_code`               | Obligatoire                                  | Obligatoire pour `COM` seulement                                              | Le contenu des lignes déléguées sera constaté à l'étape 2 ; la contrainte sera resserrée si possible |
| `trade_lexicons.report`                  | Absent                                       | Ajouté (objet JSON)                                                           | Garder, par version du lexique, l'adresse et la date de collecte de chaque source                    |
| `lexicon_terms.license`                  | Liste fermée                                 | Imposée par la source (SRC-11 : CC0, SRC-12 : CC BY-SA 4.0, saisie : interne) | Registre des sources du sprint 3                                                                     |
| Index trigramme sur `lexicon_terms`      | Absent                                       | Ajouté                                                                        | Recherche du terme le plus proche sous un seuil (D-56, étape 7)                                      |
| `sirene_runs.source_url`, `published_at` | Absents                                      | Ajoutés                                                                       | Citer l'adresse du stock lu et la date de publication dans chaque réponse                            |
| Une exécution Sirene publiée             | Non contraint                                | Une seule par révision NAF (index unique partiel)                             | Même règle que les référentiels : une version servie                                                 |
| `load_rejections.reason_code`            | Dont `end_before_start`                      | Sans ce motif                                                                 | Propre aux tranches de numéros, hors V1                                                              |

## 4. Rôles de base (SQL sécurisé)

| Rôle de groupe    | Droits                                                                                                 | Utilisé par                |
| ----------------- | ------------------------------------------------------------------------------------------------------ | -------------------------- |
| `<base>_lecture`  | Connexion à la base ; lecture de `ref` et `market`                                                     | L'API (étape 7)            |
| `<base>_ecriture` | Lecture et écriture des lignes de `ref` et `market`, sauf `ref.naf_trades` ; aucun droit sur le schéma | L'ingestion (étapes 2 à 6) |
| Propriétaire      | Crée et modifie les schémas                                                                            | Les migrations seules      |

- Les rôles portent le nom de la base : la préproduction et la production partagent le serveur
  PostgreSQL (D-47), et un rôle de l'une ne doit rien pouvoir lire dans l'autre.
- Les rôles de groupe ne se connectent pas. Les rôles de connexion, avec leur mot de passe, sont
  créés hors des migrations et rattachés à un groupe ; en production, avec la tâche d'ingestion
  (D-58), par le porteur (R10).
- Les tests le vérifient sur une base neuve : le rôle de lecture ne peut ni écrire, ni créer de
  table ; le rôle d'écriture charge des lignes, mais ne touche ni à `ref.naf_trades`, ni au schéma.

## 5. Ce qu'il faudra faire en production

- **Extension `pg_trgm` :** sur PostgreSQL flexible d'Azure, une extension doit d'abord être
  autorisée par le paramètre de serveur `azure.extensions` [H : à vérifier dans la documentation
  Azure avant de lancer la commande]. Action du porteur, sans coût.
- **Application des migrations :** par la tâche Container Apps de D-58, avec le rôle propriétaire,
  avant la livraison de l'API qui lit ces tables. L'API ne reçoit jamais ce rôle.
