# Registre des sources du sprint 3 (critère P1)

**Vérifié le :** 15 octobre 2026, contre les pages officielles citées (agent `verificateur-sources`).
**Inventaire de référence :** `docs/conception/sources_de_donnees/03-sources-de-donnees.md` (phase 0).
Ce registre le met à jour pour les six sources de la V1 ; les écarts sont signalés.

## 1. Les six sources

| ID     | Source                                                | Type C1         | Licence                                                      | Accès retenu                                                                                                                               | Données personnelles            |
| ------ | ----------------------------------------------------- | --------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------- |
| SRC-06 | Base officielle des codes postaux (La Poste)          | Fichier         | Licence Ouverte 2.0                                          | Lien stable data.gouv.fr `https://www.data.gouv.fr/api/1/datasets/r/008a2dda-2c60-4b63-b910-998f6f818089` ; CSV ISO-8859-1, séparateur `;` | Aucune                          |
| SRC-07 | Code officiel géographique 2026 (INSEE)               | Fichier         | Licence Ouverte 2.0 selon l'INSEE (data.gouv.fr indique 1.0) | `https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv` ; UTF-8, virgule, guillemets                                     | Aucune                          |
| SRC-03 | API Découpage administratif (API Géo)                 | Service web     | Aucune licence publiée pour l'API (voir § 3)                 | `https://geo.api.gouv.fr/communes?fields=nom,code,codesPostaux,codeDepartement` ; 50 requêtes/s par IP                                     | Aucune                          |
| SRC-12 | Wiktionnaire, « Lexique en français de la plomberie » | Page web        | CC BY-SA 4.0 ou GFDL, au choix                               | Pages `/wiki/` (catégorie, 123 pages) ; l'API `/w/api.php` est exclue par `robots.txt`                                                     | Aucune                          |
| SRC-11 | Wikidata, point SPARQL                                | Base de données | CC0                                                          | `https://query.wikidata.org/sparql` ; 60 s de calcul par minute, 60 s par requête, 5 requêtes parallèles                                   | Aucune                          |
| SRC-01 | Stock Sirene des établissements (INSEE)               | Big data        | Licence Ouverte 2.0                                          | Parquet par lien stable `https://www.data.gouv.fr/api/1/datasets/r/a29c1297-1f92-4e2a-8f6b-8c902ce96c5f` ; stock au 1er octobre 2026       | Oui : entrepreneurs individuels |

## 2. Obligations qui s'imposent au projet

| Source                   | Obligation                                                                                                                                                     | Comment Muninn la respecte                                                                                                     |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| INSEE (COG, Sirene)      | Mention « Source : Insee » et date de dernière mise à jour ; ne pas altérer les données ni en dénaturer le sens                                                | Chaque réponse cite la source et sa date ; les valeurs servies sont celles du fichier, normalisées seulement pour la recherche |
| La Poste, INSEE (LO 2.0) | Citer la source et la date de dernière mise à jour                                                                                                             | Idem                                                                                                                           |
| Wiktionnaire             | Attribution par lien vers chaque page réutilisée ; mention des modifications ; partage à l'identique de tout texte dérivé redistribué                          | Chaque terme garde l'adresse de sa page, sa licence et la mention « terme extrait, définition non reprise »                    |
| Wikimedia, API Géo       | User-Agent descriptif avec contact (sinon HTTP 403) ; requêtes en série ; 200 requêtes/min au plus pour Wikimedia (limite expérimentale) ; 50/s pour l'API Géo | Collecte en série, débit bridé sous ces plafonds, User-Agent `Muninn/<version> (<contact du projet>)`                          |
| Sirene                   | RGPD et loi 78-17 ; statut de diffusion le plus récent respecté ; aucun champ masqué diffusé ni reconstitué ; aucune prospection (code de commerce, A123-96)   | Minimisation du § 4                                                                                                            |

## 3. Écarts avec l'inventaire de la phase 0, et points ouverts

- **SRC-07 :** l'inventaire indiquait la Licence Ouverte 1.0 (fiche data.gouv.fr). Les mentions
  légales de l'INSEE, mises à jour le 13 avril 2026, placent ses informations publiques sous la
  Licence Ouverte 2.0. Je retiens la 2.0, celle du producteur, et je garde la trace de la
  contradiction.
- **SRC-03 :** aucune licence n'est publiée pour l'API ; sa fiche dit seulement que les sources
  sont « sous licences Open Data ». L'hypothèse retenue [H] : les données héritent de la licence
  du COG (Licence Ouverte 2.0). L'API ne sert qu'à recouper le COG et les codes postaux ; aucune
  donnée qu'elle seule fournit n'est servie.
- **SRC-12 :** la collecte passe par les pages `/wiki/`, autorisées aux « robots amicaux et lents »
  par `robots.txt`. L'API MediaWiki, exclue pour les robots d'exploration, n'est pas utilisée.
- **SRC-06 :** fréquence déclarée semestrielle, mais le fichier a été mis à jour le 8 octobre 2026.
  La date réelle est lue à chaque ingestion, jamais déduite de la fréquence.
- **SRC-01 :** passage à la NAF 2025 en janvier 2027 et fin des fichiers CSV en 2027 : sans effet
  sur la V1 (Parquet, NAF rév. 2).

## 4. Minimisation RGPD

| Source                                 | Décision                                                                                                                                                                                                                                                                                                                                                                                                              |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SRC-03, SRC-06, SRC-07, SRC-11, SRC-12 | **Non applicable, argumenté :** référentiels géographiques et termes de métier, sans aucune donnée relative à une personne                                                                                                                                                                                                                                                                                            |
| SRC-01                                 | **Minimisation appliquée avant tout stockage :** lecture des seules colonnes d'activité, de commune, d'état, de date de création et de tranche d'effectifs ; aucune colonne d'identité, d'adresse ni de géolocalisation, ni SIREN, ni SIRET ; seuls des agrégats sont écrits. Les petits effectifs sont masqués [H : seuil à fixer à l'étape 6, par exemple moins de 5] pour qu'aucun agrégat ne désigne une personne |
| Requêtes de l'évaluateur               | Les valeurs recherchées ne sont ni journalisées, ni stockées, ni renvoyées au-delà du résultat (contrat d'API, TA-23)                                                                                                                                                                                                                                                                                                 |

Renvoi : registre RGPD de la phase 1 (`docs/conception/architecture_de_donnees/05`).
