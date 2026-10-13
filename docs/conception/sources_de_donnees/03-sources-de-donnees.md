# Inventaire des sources de données de Muninn

**Version :** 1
**Date :** 12 octobre 2026
**Phase :** 0a (besoin, flux et sources de données)
**Statut :** proposition, à valider par le porteur
**Compétences servies :** C1 (conception de l'extraction), préparation de C2, C3 et C4

## 1. Objet, périmètre et méthode

Ce document recense les sources de données externes que Muninn peut exploiter. Chaque source
retenue sert une fonction du concept figé :

- normaliser et valider les champs extraits par le LLM (`telephone` en E.164, `code_postal` sur
  5 chiffres, `commune`, `rue`) ;
- alimenter le lexique métier injecté dans la transcription et dans le prompt d'extraction ;
- calculer les créneaux de rendez-vous (`rdv_propose`) et le message hors horaires de l'agent ;
- dimensionner le marché et segmenter la tête de pont (artisans solo, codes NAF 43.xx) ;
- construire les jeux d'évaluation synthétiques (règle R9 de la passation back-end).

Une source qui ne sert le produit que faiblement, et qui est surtout utile pour couvrir un type
d'extraction de C1, est signalée comme telle.

Sources internes du projet :

| Document                                  | Éléments utilisés                                                          |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| Analyse stratégique v2 du 11 octobre 2026 | 1.1 (dimensionnement, action Sirene), 4.3 (lexique métier), 4.4 (MVP)      |
| Passation back-end du 11 octobre 2026     | Règles R1 à R10, contrat DossierDraft, normalisation, table trade_lexicons |
| Feuille de route v2 du 12 octobre 2026    | Point de vigilance « système big data », calendrier d'E1                   |

**Méthode de vérification.** Toutes les vérifications datent du 12 octobre 2026.

- Pages de documentation ouvertes une par une. Quand une page ne s'affiche qu'avec JavaScript,
  la fiche le dit, et l'information vient d'une autre source nommée.
- Points d'accès d'API appelés une fois, sans compte et sans clé, avec une requête minimale.
- Taille des gros fichiers lue dans l'en-tête HTTP (`Content-Length`), sans téléchargement.
- Nombre de lignes des fichiers Parquet de Sirene lu dans leur pied de page par requêtes
  partielles (en-tête `Range`), soit quelques dizaines de kilo-octets lus par fichier.
- Taille décompressée des archives ZIP de Sirene lue dans leur répertoire central, par la même
  méthode.
- Fichiers de moins de 4 Mo téléchargés pour compter les lignes : codes postaux, communes du
  COG, numérotation ARCEP, pages de catégories du Wiktionnaire.

Conventions : **[H]** marque une hypothèse. « DP » signifie données personnelles. Les volumes
sont ceux du 12 octobre 2026, sauf mention contraire.

## 2. Table de synthèse

| ID     | Nom                                              | Fournisseur                             | Type C1             | Format                         | Accès (authentification et quota)                 | Licence                                  | Mise à jour                               | Volume mesuré                                                  | DP  | Usage dans Muninn                                               |
| ------ | ------------------------------------------------ | --------------------------------------- | ------------------- | ------------------------------ | ------------------------------------------------- | ---------------------------------------- | ----------------------------------------- | -------------------------------------------------------------- | --- | --------------------------------------------------------------- |
| SRC-01 | Fichiers stock Sirene                            | INSEE, via data.gouv.fr                 | Big data            | Parquet ; CSV compressé en ZIP | Sans authentification ; aucun quota publié        | Licence Ouverte 2.0                      | Mensuelle                                 | 44 282 364 établissements (2,22 Go en Parquet)                 | Oui | Dimensionnement du marché, segmentation de la tête de pont      |
| SRC-02 | API Recherche d'entreprises                      | Annuaire des Entreprises (data.gouv.fr) | Service web         | JSON                           | Sans authentification ; 7 requêtes/s par IP       | Non précisée par la fiche                | Non précisée                              | 25 résultats par page ; 10 000 résultats au plus par recherche | Oui | Préremplir le compte de l'artisan à partir de son SIREN         |
| SRC-03 | API Découpage administratif (API Géo)            | DINUM, données INSEE                    | Service web         | JSON, GeoJSON                  | Sans authentification ; 50 requêtes/s par IP      | Données sous licences ouvertes (fiche)   | Non précisée                              | 34 969 communes                                                | Non | Valider la commune et le couple code postal et commune          |
| SRC-04 | Géocodage de la Géoplateforme                    | IGN                                     | Service web         | JSON (GeoJSON) ; CSV par lots  | Sans authentification ; 50 requêtes/s par IP      | Licence Ouverte 2.0                      | Index BAN hebdomadaire                    | Index de la BAN (voir SRC-05)                                  | Oui | Normaliser une adresse ; à réserver aux données synthétiques    |
| SRC-05 | Base Adresse Nationale, export national          | IGN et DINUM, via data.gouv.fr          | Fichier             | CSV compressé (gzip)           | Sans authentification ; aucun quota publié        | Licence Ouverte 2.0                      | Quotidienne                               | 26 118 629 adresses ; 938 Mo compressé                         | Non | Valider rue, code postal et commune sans sortie de données      |
| SRC-06 | Base officielle des codes postaux                | La Poste                                | Fichier             | CSV (ISO-8859-1, séparateur ;) | Sans authentification ; aucun quota publié        | Licence Ouverte 2.0 (fiche data.gouv.fr) | Semestrielle (déclarée)                   | 39 192 lignes ; 1,56 Mo                                        | Non | Valider le code postal sur 5 chiffres et la commune associée    |
| SRC-07 | Code officiel géographique 2026                  | INSEE                                   | Fichier             | CSV (UTF-8, séparateur ,)      | Sans authentification ; aucun quota publié        | Licence Ouverte 1.0 (fiche data.gouv.fr) | Annuelle                                  | 37 496 lignes, dont 34 875 communes                            | Non | Noms officiels accentués, communes déléguées, département       |
| SRC-08 | API Jours fériés                                 | DINUM (Etalab)                          | Service web         | JSON ; CSV et ICS              | Sans authentification ; aucun quota publié        | Licence Ouverte (données)                | Régénérée chaque jour                     | 11 jours (métropole 2026) ; 13 (Alsace-Moselle 2027)           | Non | Exclure les jours fériés des créneaux de rendez-vous            |
| SRC-09 | Nomenclatures NAF rév. 2 et NAF 2025             | INSEE                                   | Fichier             | XLS, XLSX, PDF                 | Sans authentification                             | Non indiquée sur la page                 | Ponctuelle (NAF 2025 en 2027)             | Fichier des 5 niveaux NAF rév. 2 : 92 Ko (XLS)                 | Non | Sélectionner les codes de la tête de pont ; correspondance 2027 |
| SRC-10 | Auto-entrepreneurs par secteur d'activité        | Urssaf (open.urssaf.fr)                 | Service web         | JSON (API Explore) ; CSV       | Sans authentification ; quota non vérifié         | ODbL                                     | Semestrielle, avec environ 200 j de délai | 2 448 enregistrements (national) ; 151 793 (départemental)     | Non | Dimensionnement (micro-entrepreneurs du BTP)                    |
| SRC-11 | Wikidata, point d'accès SPARQL                   | Wikimedia                               | Base de données     | JSON (résultats SPARQL)        | Sans authentification ; 60 s de calcul par minute | CC0                                      | Continue                                  | 9 fabricants liés au concept « chaudière »                     | Non | Marques d'équipements pour le lexique ; pertinence faible       |
| SRC-12 | Wiktionnaire, catégories « Lexique en français » | Wikimedia                               | Page web (scraping) | HTML                           | Sans authentification ; /wiki/ non interdit       | CC BY-SA 4.0                             | Continue                                  | 123 (plomberie), 706 (électricité), 139 (serrurerie) pages     | Non | Termes de métier pour le lexique                                |
| SRC-13 | Ressources en numérotation (MAJNUM)              | ARCEP                                   | Fichier             | CSV (ANSI, séparateur ;)       | Sans authentification ; aucun quota publié        | Licence Ouverte 1.0 (fiche data.gouv.fr) | Après chaque collège de l'ARCEP           | 20 886 tranches ; 1,16 Mo                                      | Non | Valider un numéro dicté ; distinguer mobile et fixe             |
| SRC-14 | Fichier des prénoms                              | INSEE                                   | Fichier             | CSV, Parquet                   | Sans authentification                             | Licence Ouverte 2.0 (fiche data.gouv.fr) | Annuelle                                  | Environ 711 000 lignes (niveau national, selon l'INSEE)        | Non | Jeux d'évaluation synthétiques ; variantes d'orthographe        |

Lecture de la colonne DP : « Oui » signifie que la source contient, ou que son usage transmet,
des données relatives à une personne physique. Le traitement prévu est décrit dans chaque fiche
et résumé en section 5.

## 3. Fiches par source

### SRC-01 : fichiers stock Sirene

- **Documentation :** https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
  et les dessins de fichiers publiés dans le même jeu de données.
- **Point d'accès :** fichiers statiques sous
  `https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/`.
  Version du 1er octobre 2026 : `20261001-073823/stock-stocketablissement-parquet.parquet` et
  `20261001-073325/stock-stockunitelegale-parquet.parquet`.
- **Volume mesuré (version du 1er octobre 2026) :** les tailles viennent des métadonnées de
  data.gouv.fr. Les nombres de lignes ne sont publiés nulle part : ils ont été lus par nous dans
  les métadonnées du pied de page Parquet (requêtes partielles `Range`, 12 octobre 2026). Ils
  seront confirmés par un comptage SQL lors de la phase 3.

| Fichier                      | Lignes     | Colonnes   | Parquet (octets) | CSV compressé (octets) | CSV décompressé (octets) |
| ---------------------------- | ---------- | ---------- | ---------------- | ---------------------- | ------------------------ |
| StockEtablissement           | 44 282 364 | 54         | 2 220 887 978    | 2 879 694 907          | 10 090 729 298           |
| StockUniteLegale             | 30 148 401 | 35         | 713 585 991      | 979 789 073            | 4 290 903 675            |
| StockEtablissementHistorique | non mesuré | non mesuré | 877 620 853      | 1 244 801 219          | non mesuré               |

- **Champs utiles :** `siren`, `siret`, `etatAdministratifEtablissement`,
  `activitePrincipaleEtablissement`, `activitePrincipaleNAF25Etablissement`,
  `activitePrincipaleRegistreMetiersEtablissement`, `trancheEffectifsEtablissement`,
  `caractereEmployeurEtablissement`, `codeCommuneEtablissement`, `codePostalEtablissement`,
  `statutDiffusionEtablissement`, `dateCreationEtablissement` ; côté unité légale,
  `categorieJuridiqueUniteLegale` (1000 pour l'entrepreneur individuel) et
  `trancheEffectifsUniteLegale`.
- **Transformation prévue :**
  1. lecture par projection de colonnes : les colonnes d'identité (`nomUniteLegale`,
     `prenom1UniteLegale`, `denominationUsuelle…`, `enseigne…`) et d'adresse fine
     (`numeroVoie…`, `libelleVoie…`, coordonnées Lambert) ne sont jamais lues ;
  2. filtre : établissement actif, NAF dans la liste de la tête de pont (SRC-09) ;
  3. jointure avec les unités légales sur `siren` pour la catégorie juridique ;
  4. agrégation par code NAF, tranche d'effectif, catégorie juridique, département ;
  5. seul l'agrégat est conservé ; le fichier source est supprimé après traitement [H].
- **Point de méthode à corriger dans l'analyse stratégique.** L'analyse cite la « tranche
  d'effectif 0 ». Dans Sirene, le code `00` signifie « 0 salarié (n'ayant pas d'effectif au 31/12
  mais ayant employé des salariés au cours de l'année de référence) ». L'artisan qui n'a jamais
  employé est codé `NN` (« unités non employeuses : pas de salarié au cours de l'année de
  référence et pas d'effectif au 31/12 »). Source : libellés de l'API Sirene repris par le
  catalogue API Entreprise (entreprise.api.gouv.fr, fiches unités légales et établissements) ; la
  documentation de l'API Sirene ne s'affiche pas sans JavaScript. **Nuance à connaître :** une
  page INSEE plus ancienne, sur un autre produit (fichiers stock REE, 2020), libelle `NN`
  « Effectif inconnu » et recommande de regrouper `NN` et `00`. La segmentation retient donc
  `NN` **et** `00` comme « sans salarié au 31/12 », présente `NN` seul en variante, et traite à
  part les valeurs vides [H : part des valeurs vides non mesurée].
- **Risques et limites :**
  - le format CSV doit cesser d'être livré au second semestre 2027, au profit du Parquet (page
    data.gouv.fr) : la chaîne doit lire le Parquet dès le départ ;
  - passage à la NAF 2025 au 1er janvier 2027 : les variables `activitePrincipaleNAF25…` sont
    provisoires et seront supprimées de l'API Sirene début 2027 (note INSEE de juin 2026) ;
  - la tranche d'effectif ne dit pas si l'artisan travaille seul : un gérant de SARL sans salarié
    est aussi `NN`. C'est cohérent avec la cible (« artisan qui travaille seul »), mais un
    micro-entrepreneur en activité secondaire l'est aussi ;
  - Sirene ne dit pas si l'entreprise est économiquement active : le chiffrage en comptes reste une
    borne haute, à croiser avec SRC-10.
- **DP :** oui. Voir section 5.
- **Vérifié le :** 12 octobre 2026 (métadonnées data.gouv.fr, pied de page Parquet, répertoire
  central ZIP, dessins de fichiers).

### SRC-02 : API Recherche d'entreprises

- **Documentation :** https://recherche-entreprises.api.gouv.fr/docs/ (page dynamique, non
  lisible sans JavaScript) ; spécification lue dans https://recherche-entreprises.api.gouv.fr/openapi.json.
- **Point d'accès :** `https://recherche-entreprises.api.gouv.fr/search` et `/near_point`.
- **Accès :** ouvert, sans clé. Limite publiée : 7 requêtes par seconde par adresse IP et
  30 requêtes par seconde par ASN, avec une réponse HTTP 429 et un en-tête `Retry-After` au-delà.
  `per_page` est limité à 25.
- **Mesure :** une recherche sur `activite_principale=43.22A` renvoie `total_results: 10000` et
  `total_pages: 10000` avec `per_page=1`. Le total est donc plafonné à 10 000 : l'API ne permet
  pas de compter une population. La spécification le confirme : l'API « ne permet pas d'accéder
  aux données complètes de la base Sirene ».
- **Champs utiles :** `siren`, `nom_complet`, `activite_principale`,
  `siege.activite_principale_registre_metier`, `siege.code_postal`, `siege.libelle_commune`,
  `siege.liste_rge`, `tranche_effectif_salarie`, `nature_juridique`.
- **Usage dans Muninn :** à l'inscription, l'artisan saisit son SIREN (colonne facultative
  `accounts.siren` de la passation back-end). L'API préremplit le nom d'entreprise
  (`lines.business_name`) et propose le métier (`lines.trade`) à partir du code NAF. C'est un
  usage réel, mais secondaire : le produit fonctionne sans.
- **Transformation prévue :** correspondance NAF vers métier (`plomberie`, `chauffage`,
  `electricite`, `serrurerie`, `autre`) selon SRC-09 ; validation par l'artisan en un geste.
- **Risques et limites :** les entreprises non diffusibles sont exclues de l'API ; un artisan en
  diffusion partielle ne sera donc pas prérempli [H : à confirmer par un test]. La réponse
  contient le bloc `dirigeants` (noms) : il n'est jamais stocké. La licence n'est pas précisée
  dans la fiche du service.
- **Vérifié le :** 12 octobre 2026 (spécification OpenAPI, appel réel).

### SRC-03 : API Découpage administratif (API Géo)

- **Documentation :** https://geo.api.gouv.fr/decoupage-administratif/communes ; fiche du
  service sur data.gouv.fr (API `dataservices`).
- **Point d'accès :** `https://geo.api.gouv.fr/communes` (paramètres `nom`, `codePostal`,
  `code`, `lat` et `lon`, `fields`, `boost=population`).
- **Accès :** ouvert, sans clé. Limite publiée : 50 appels par seconde et par adresse IP.
- **Mesure :** la liste complète renvoie 34 969 communes. Exemple : `codePostal=93100` renvoie
  Montreuil, code INSEE 93048.
- **Champs utiles :** `code`, `nom`, `codesPostaux`, `codeDepartement`, `population`, `centre`.
- **Transformation prévue :** contrôle de cohérence entre `code_postal` et `commune` extraits ;
  désambiguïsation des homonymes (« Montreuil ») par le code postal, puis par la population.
- **Risques et limites :** la fiche ne donne ni la fréquence de mise à jour ni la licence de
  l'API ; elle dit seulement que les données sources sont « sous licences Open Data ». Chaque
  appel transmet une commune, ce qui reste peu identifiant, mais SRC-06 et SRC-07 permettent le
  même contrôle sans appel externe. **Recommandation :** utiliser SRC-03 pour la démonstration et
  comme source de type « service web », et faire le contrôle en production sur les tables locales.
- **Écart à expliquer :** 34 969 communes dans l'API contre 34 875 communes (`COM`) dans le COG
  2026 (SRC-07). La fiche indique que l'API couvre aussi les collectivités d'outre-mer, ce qui
  expliquerait l'écart [H : non vérifié ligne à ligne].
- **Vérifié le :** 12 octobre 2026.

### SRC-04 : géocodage de la Géoplateforme (IGN)

- **Documentation :** https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/geocodage/
- **Point d'accès :** `https://data.geopf.fr/geocodage/search`, `/reverse`, `/getcapabilities` ;
  spécification sur `https://data.geopf.fr/geocodage/openapi`.
- **Migration :** l'API Adresse a été transférée à l'IGN, avec un transfert complet du trafic
  annoncé au 30 juin 2025. L'ancien domaine ne devait être maintenu en redirection que jusqu'en
  janvier 2026 (billet data.gouv.fr du 3 avril 2025). Deux observations du 12 octobre 2026
  divergent : une redirection HTTP 301, puis une réponse directe en GeoJSON. **Seul
  `data.geopf.fr/geocodage/search` est retenu** ; l'ancien domaine ne doit pas être utilisé.
- **Accès :** usage anonyme possible ; 50 requêtes par seconde par adresse IP. Lots CSV
  synchrones de moins de 50 Mo ou 200 000 lignes ; lots asynchrones jusqu'à 1 Go.
- **Mesure :** la requête « 12 rue des lilas montreuil » renvoie « 12 Rue des Lilas 93100
  Montreuil », code INSEE 93048, score 0,97.
- **Champs utiles :** `label`, `housenumber`, `street`, `postcode`, `citycode`, `city`, `score`,
  `type`.
- **Transformation prévue :** normaliser `client.adresse.rue`, `code_postal` et `commune` ;
  utiliser `score` pour abaisser la confiance du champ quand le géocodage est incertain.
- **Risques et limites :** chaque requête envoie une adresse de client final à un tiers. Ce
  n'est pas un stockage, donc la règle R1 n'est pas enfreinte à la lettre, mais l'adresse sort
  de l'infrastructure de Muninn. **Recommandation :** n'envoyer que des adresses synthétiques
  (démonstration, évaluation). En production, préférer une validation locale (SRC-05, SRC-06,
  SRC-07). Sinon, inscrire l'IGN comme destinataire dans le registre des traitements et l'AIPD.
- **Vérifié le :** 12 octobre 2026.

### SRC-05 : Base Adresse Nationale, export national

- **Documentation :** https://www.data.gouv.fr/datasets/base-adresse-nationale/ et
  https://adresse.data.gouv.fr/donnees-nationales
- **Point d'accès :** `https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz`
- **Volume mesuré :** 938 037 043 octets compressés (en-tête HTTP, fichier modifié le
  12 octobre 2026) ; 26 118 629 adresses, dont 19 397 755 certifiées (statistiques publiées par
  `https://plateforme.adresse.data.gouv.fr/ban/stats`).
- **Champs utiles [H : à confirmer sur l'en-tête du fichier] :** numéro, nom de voie, code
  postal, code INSEE, nom de commune, nom de commune déléguée.
- **Transformation prévue :** chargement dans la base de référence du serveur, limité aux
  champs utiles ; contrôle local de l'existence d'une voie dans une commune. Possibilité d'un
  géocodeur auto-hébergé [H : effort non évalué].
- **Usage secondaire :** adresses réalistes pour les scénarios synthétiques (voir section 5).
- **Risques et limites :** volume élevé pour un usage limité à la validation ; un sous-ensemble
  par département peut suffire pour la démonstration [H].
- **Vérifié le :** 12 octobre 2026.

### SRC-06 : base officielle des codes postaux (La Poste)

- **Documentation :** https://datanova.laposte.fr/datasets/laposte-hexasmal (métadonnées lues
  par l'API `data-fair` du portail) ; fiche data.gouv.fr « Base officielle des codes postaux ».
- **Point d'accès :** `https://data.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal/raw`
- **Volume mesuré :** 1 555 485 octets, 39 192 lignes, 5 colonnes ; données mises à jour le
  8 octobre 2026 ; encodage ISO-8859-1, séparateur `;`.
- **Champs utiles :** `#Code_commune_INSEE`, `Nom_de_la_commune`, `Code_postal`,
  `Libellé_d_acheminement`, `Ligne_5` (lieu-dit ou commune déléguée).
- **Transformation prévue :** lecture des codes comme texte ; conversion en UTF-8 ; table de
  correspondance code postal vers communes ; contrôle du format sur 5 chiffres exigé par la
  passation back-end.
- **Anomalies constatées (utiles pour C3) :**
  - le schéma de l'API `data-fair` type `code_postal` et `code_commune_insee` en entiers : une
    lecture par cette API perd le zéro initial (01400 devient 1400). Le fichier brut conserve
    « 01400 » ;
  - les noms sont en majuscules sans accents (« L ABERGEMENT CLEMENCIAT ») : le nom à présenter
    vient de SRC-07 (« L'Abergement-Clémenciat »).
- **Vérifié le :** 12 octobre 2026.

### SRC-07 : Code officiel géographique 2026 (INSEE)

- **Documentation :** fiche data.gouv.fr « Code officiel géographique » (INSEE) ; liste des
  modalités : https://www.insee.fr/fr/information/8740218 (non ouverte, citée par la fiche).
- **Point d'accès :** `https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv` ;
  historique : `v_commune_depuis_1943.csv`.
- **Volume mesuré :** 3 565 935 octets, 37 496 lignes : 34 875 communes (`COM`), 2 105 communes
  déléguées (`COMD`), 471 communes associées (`COMA`), 45 arrondissements municipaux (`ARM`).
- **Champs utiles :** `TYPECOM`, `COM`, `DEP`, `LIBELLE`, `NCC`, `COMPARENT`.
- **Transformation prévue :** nom officiel accentué ; rattachement d'une commune déléguée à sa
  commune nouvelle (un appelant peut citer l'ancien nom) ; département de la commune de
  l'artisan, qui choisit la zone des jours fériés (SRC-08).
- **Risques et limites :** millésime annuel au 1er janvier ; les fusions de communes en cours
  d'année n'y figurent pas.
- **Vérifié le :** 12 octobre 2026.

### SRC-08 : API Jours fériés

- **Documentation :** https://calendrier.api.gouv.fr/jours-feries/ (page ReDoc) ; spécification
  lue dans `https://calendrier.api.gouv.fr/jours-feries/openapi.yml` ; fiche data.gouv.fr
  « Jours fériés en France ».
- **Point d'accès :** `https://calendrier.api.gouv.fr/jours-feries/{zone}/{annee}.json`
- **Mesure :** `metropole/2026` renvoie 11 jours ; `alsace-moselle/2027` en renvoie 13 (Vendredi
  saint et 26 décembre en plus). Zones : `metropole`, `alsace-moselle`, `guadeloupe`, `guyane`,
  `la-reunion`, `martinique`, `mayotte`, `nouvelle-caledonie`, `polynesie-francaise`,
  `saint-barthelemy`, `saint-martin`, `saint-pierre-et-miquelon`, `wallis-et-futuna`.
- **Couverture temporelle :** 20 ans dans le passé et 5 ans dans le futur pour le CSV et le JSON
  (fiche data.gouv.fr).
- **Transformation prévue :** zone choisie selon le département de l'artisan (57, 67 et 68 pour
  l'Alsace-Moselle [H : règle à confirmer dans le Code du travail]) ; exclusion des jours fériés
  dans le calcul des créneaux (`PUT /availability`, `rdv_propose`) et du « jour ouvré suivant »
  du message hors horaires.
- **Risques et limites :** les fichiers sont servis par GitHub Pages (en-tête `Server:
  GitHub.com`) ; aucun engagement de disponibilité n'est publié. Une copie locale annuelle suffit
  [H]. Un jour férié n'est pas forcément chômé par l'artisan : l'exclusion doit rester un réglage.
- **Vérifié le :** 12 octobre 2026.

### SRC-09 : nomenclatures NAF rév. 2 et NAF 2025 (INSEE)

- **Documentation :** https://www.insee.fr/fr/information/2406147 (présentation) ;
  https://www.insee.fr/fr/information/2120875 (fichiers NAF rév. 2) ;
  https://www.insee.fr/fr/information/8617910 (fichiers NAF 2025).
- **Point d'accès :** `https://www.insee.fr/fr/statistiques/fichier/2120875/naf2008_5_niveaux.xls`
  (92 Ko) et `int_courts_naf_rev_2.xls` (304 Ko) ; table de correspondance
  `https://www.insee.fr/fr/statistiques/fichier/8617910/Correspondances_NAFrev2-NAF2025.xlsx`
  (éditée en janvier 2026).
- **Codes de la tête de pont (fiches INSEE ouvertes une par une) :**

| Métier Muninn | Code NAF rév. 2 | Libellé INSEE                                                       | Remarque                                                             |
| ------------- | --------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------- |
| plomberie     | 43.22A          | Travaux d'installation d'eau et de gaz en tous locaux               | Couvre la plomberie et les appareils sanitaires                      |
| chauffage     | 43.22B          | Travaux d'installation d'équipements thermiques et de climatisation | Couvre chaudières et systèmes de chauffage                           |
| electricite   | 43.21A          | Travaux d'installation électrique dans tous locaux                  | Inclut les radiateurs électriques à inertie                          |
| serrurerie    | 43.32B          | Travaux de menuiserie métallique et serrurerie                      | La fiche ne cite pas le dépannage de serrures : couverture partielle |

- **Transformation prévue :** table de référence `code NAF → métier` ; double codage
  NAF rév. 2 et NAF 2025 à partir de la table de correspondance, pour les fichiers Sirene publiés
  après le 1er janvier 2027.
- **Risques et limites :** le serrurier dépanneur peut être enregistré sous un autre code
  [H : à mesurer dans SRC-01]. La page de téléchargement n'indique pas de licence.
- **Vérifié le :** 12 octobre 2026.

### SRC-10 : open data Urssaf sur les auto-entrepreneurs

- **Documentation :** https://open.urssaf.fr/explore/dataset/auto-entrepreneurs-par-secteur-dactivite/
  (métadonnées lues par l'API Explore v2.1).
- **Point d'accès :** `https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/auto-entrepreneurs-par-secteur-dactivite/records`
  et `…/auto-entrepreneurs-par-departement-secteur/records`.
- **Volume mesuré :** 2 448 enregistrements (national) et 151 793 (département et secteur) ;
  séries trimestrielles depuis 2009 ; dernier point : 31 décembre 2025 ; mise à jour annoncée
  « fin de semestre + ~200 jours ».
- **Champs utiles :** `secteur_d_activite_me`, `dernier_jour_du_trimestre`,
  `administrativement_actifs`, `economiquement_actifs`, `chiffres_d_affaires`.
- **Valeurs lues au 31 décembre 2025 (requête du 12 octobre 2026) :**

| Secteur Urssaf                  | Administrativement actifs | Économiquement actifs | Chiffre d'affaires du trimestre (euros) |
| ------------------------------- | ------------------------- | --------------------- | --------------------------------------- |
| F1 - BTP gros-oeuvre            | 83 252                    | 47 754                | 357 418 932                             |
| F2 - BTP travaux d'installation | 75 717                    | 45 820                | 385 076 549                             |
| F3 - BTP travaux de finition    | 122 791                   | 75 528                | 557 556 251                             |

- **Usage dans Muninn :** le secteur F2 est le plus proche de la tête de pont (installation
  d'eau, de gaz, de chauffage, d'électricité [H : contenu exact du regroupement non vérifié]).
  Ces chiffres datés peuvent remplacer le chiffre FFB non daté de l'analyse stratégique (159 600
  auto-entrepreneurs du bâtiment).
- **Risques et limites :** la licence ODbL impose le partage à l'identique d'une base dérivée
  diffusée. L'agrégat reste interne, ou il est diffusé sous ODbL avec attribution. Le
  regroupement F2 ne correspond pas exactement aux quatre métiers. Le quota de l'API n'est pas
  publié dans les métadonnées lues.
- **Vérifié le :** 12 octobre 2026.

### SRC-11 : Wikidata, point d'accès SPARQL

- **Documentation :** https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual ;
  licence : https://www.wikidata.org/wiki/Wikidata:Licensing
- **Point d'accès :** `https://query.wikidata.org/sparql`
- **Accès :** sans clé ; 60 s de calcul par requête, 5 requêtes parallèles par IP, 60 s de calcul
  par minute par couple agent et IP ; en-tête `User-Agent` explicite obligatoire.
- **Mesures :**
  - le concept « chaudière » (Q3195517) est cité comme produit fabriqué (propriété P1056) par
    9 entités seulement, dont Viessmann et Baxi ; Frisquet, Chaffoteaux et ELM Leblanc ne sont
    trouvés sous aucun libellé exact ;
  - homonymie : le libellé français « Atlantic » désigne 24 entités, « Vaillant » 11,
    « De Dietrich » 3 ;
  - le 12 octobre 2026, le service répondait HTTP 429 avec le message « Aggressively
    rate-limiting to 1 req / min - this rule was created during active wdqs outage ».
- **Transformation prévue :** liste de marques avec leurs libellés et alias, filtrée sur des
  entités de type entreprise ; relecture humaine avant entrée dans `trade_lexicons`.
- **Pertinence pour le produit : faible.** La couverture des marques de chauffage présentes en
  France est lacunaire. Cette source est surtout retenue pour couvrir le type « base de données »
  de C1, ce qui est dit ici explicitement. Une liste de marques établie à la main serait plus
  complète [H].
- **Vérifié le :** 12 octobre 2026.

### SRC-12 : Wiktionnaire, catégories « Lexique en français de… »

- **Documentation :** pages de catégorie du Wiktionnaire ; règles d'accès :
  https://fr.wiktionary.org/robots.txt
- **Point d'accès :** `https://fr.wiktionary.org/wiki/Catégorie:Lexique_en_français_de_la_plomberie`,
  `…de_l’électricité`, `…de_la_serrurerie`, `…de_la_construction`.
- **Scraping permis ?** Le fichier robots.txt, commun aux wikis Wikimedia, ne contient pas de
  ligne `Allow: /wiki/` : `/wiki/` est autorisé par défaut, faute d'interdiction générale, sauf
  les pages `Special:` et quelques sous-chemins. Il interdit `/w/` et `/api/`, à quatre
  exceptions explicites près (`/w/load.php?`, `/w/api.php?action=mobileview&`,
  `/api/rest_v1/?doc`, plan du site). La lecture des pages HTML de catégorie
  est donc permise ; l'API MediaWiki ne l'est pas au sens du robots.txt. Contenu sous licence
  CC BY-SA 4.0 (mention en pied de page). Conduite : agent identifié par un `User-Agent`
  explicite, une requête à la fois, pause entre requêtes [H : 1 s].
- **Volume mesuré :** plomberie 123 pages ; électricité 706 pages et 2 sous-catégories (200 par
  page de liste) ; serrurerie 139 pages ; construction 781 pages et 13 sous-catégories. Aucune
  catégorie « chauffage » (réponse 404) ; la catégorie « thermique » ne compte qu'une page.
- **Champs utiles :** le titre de chaque entrée (le terme), sa catégorie d'origine.
- **Transformation prévue :** extraction des termes ; dédoublonnage ; suppression des termes
  hors usage du dépannage (la catégorie électricité mêle des termes de physique) ; relecture
  humaine ; versionnage du lexique par métier dans `trade_lexicons`.
- **Risques et limites :** pas de lexique du chauffage ; bruit à filtrer à la main. La licence
  CC BY-SA 4.0 impose attribution et partage à l'identique si le lexique est diffusé, par exemple
  par l'API de C5 [H : une simple liste de mots peut ne pas être protégée ; avis juridique non
  sollicité].
- **Vérifié le :** 12 octobre 2026.

### SRC-13 : ressources en numérotation téléphonique (ARCEP, fichier MAJNUM)

- **Documentation :** https://www.data.gouv.fr/datasets/ressources-en-numerotation-telephonique/ ;
  spécification des fichiers, version 13.0 du 7 octobre 2024 :
  `https://extranet.arcep.fr/uploads/spec_export_num_arcep.pdf` (texte extrait en partie).
- **Point d'accès :** `https://extranet.arcep.fr/uploads/MAJNUM.csv`
- **Volume mesuré :** 1 159 318 octets (en-tête HTTP, modifié le 8 octobre 2026) ; 20 886
  tranches. La fiche data.gouv.fr annonce 3 760 000 octets : la métadonnée n'est pas à jour.
- **Champs (spécification ARCEP) :** `EZABPQM` (préfixe du bloc, de 1 000 à 1 000 000 numéros,
  ou numéro court), `Tranche_Debut`, `Tranche_Fin`, `Mnémo` (identifiant de communications
  électroniques de l'opérateur attributaire), `Territoire`, `Date_Attribution`.
- **Transformation prévue :** pour un numéro dicté par l'appelant (`telephone.origin = spoken`),
  vérifier qu'il appartient à une tranche attribuée. Un numéro hors tranche est une entrée
  corrompue (C3) : confiance abaissée, champ marqué à vérifier. Le préfixe distingue mobile et
  fixe, utile car les rappels par SMS (PV5) supposent un mobile [H : règle 06 et 07 à confirmer
  dans la spécification ARCEP]. Normalisation en E.164 (+33).
- **Pertinence :** directe pour le champ clé `telephone` du KPI de 90 %.
- **Vérifié le :** 12 octobre 2026.

### SRC-14 : fichier des prénoms (INSEE)

- **Documentation :** https://www.insee.fr/fr/statistiques/8894961 (édition du 9 juillet 2025,
  naissances de 1900 à 2024). La fiche data.gouv.fr pointe encore vers l'édition de 2023
  (https://www.insee.fr/fr/statistiques/7633685).
- **Point d'accès :** liens de téléchargement de la page INSEE (CSV national de 1 Mo, Parquet de
  10 Mo pour l'ensemble des niveaux).
- **Volume (selon l'INSEE) :** environ 711 000 lignes au niveau national, 3,9 millions au niveau
  départemental. Effectifs arrondis au multiple de 5 depuis l'édition 2025.
- **Champs utiles :** `SEXE`, `PRENOM`, `PERIODE`, `VALEUR`.
- **Transformation prévue :** tirage de prénoms selon leur fréquence pour générer les 100
  scénarios synthétiques ; liste de variantes d'orthographe (« Mathéo », « Matteo ») pour tester
  la robustesse de l'extraction du champ `prenom`.
- **Pertinence :** moyenne. Le KPI de 90 % porte sur `nom`, pas sur `prenom`. Aucune source
  ouverte de noms de famille n'a été vérifiée (section 7).
- **Vérifié le :** 12 octobre 2026.

## 4. Couverture des cinq types d'extraction de C1

| Type C1             | Source principale    | Sources complémentaires                | Outil d'extraction envisagé [H]                      | Service rendu au produit                         | Pertinence |
| ------------------- | -------------------- | -------------------------------------- | ---------------------------------------------------- | ------------------------------------------------ | ---------- |
| Service web         | SRC-03 API Géo       | SRC-02, SRC-04, SRC-08, SRC-10         | Client HTTP avec gestion du code 429 et reprise      | Validation de la commune ; jours fériés ; compte | Forte      |
| Page web (scraping) | SRC-12 Wiktionnaire  | aucune                                 | Analyse HTML des pages de catégorie                  | Lexique métier                                   | Moyenne    |
| Fichier de données  | SRC-06 codes postaux | SRC-05, SRC-07, SRC-09, SRC-13, SRC-14 | Lecture CSV, XLS et Parquet ; typage texte des codes | Normalisation code postal, commune, téléphone    | Forte      |
| Base de données     | SRC-11 Wikidata      | Base PostgreSQL du projet              | Requêtes SPARQL                                      | Marques pour le lexique                          | Faible     |
| Système big data    | SRC-01 Sirene        | SRC-05 (26 millions de lignes)         | Moteur SQL en colonnes sur fichiers Parquet          | Dimensionnement et segmentation                  | Forte      |

**Service web.** Cinq API ouvertes servent le produit. L'API Géo est la plus directe : elle
contrôle la commune extraite. La Géoplateforme ne doit recevoir que des adresses synthétiques
(fiche SRC-04).

**Page web.** Le Wiktionnaire est la seule page dont le scraping a été vérifié comme permis par
robots.txt, avec une licence connue. Les pages d'assistance des opérateurs ont été écartées
(section 6).

**Fichier.** Plusieurs fichiers servent directement la normalisation exigée par la passation
back-end (E.164, code postal sur 5 chiffres). Ils présentent des défauts réels, utiles pour C3 :
zéros initiaux perdus selon le mode de lecture, encodage ISO-8859-1, noms sans accents,
métadonnée de taille périmée.

**Base de données.** C'est le point faible de l'inventaire. Aucune base de données publique
interrogeable en SQL et utile au produit n'a été identifiée pendant cet inventaire. Deux options :

- Wikidata par SPARQL : base externe réelle, mais pertinence faible pour le produit et service
  instable le jour de la vérification ;
- la base PostgreSQL de Muninn, une fois chargée avec les référentiels (SRC-06, SRC-07, SRC-13)
  et le lexique : extraction SQL réelle, utile au produit, mais la source est interne au projet.

Le choix revient au porteur (section 8). La seconde option sert aussi C2 (« requêtes SQL
d'extraction depuis un SGBD »).

**Système big data.** Le fichier StockEtablissement de Sirene est le seul candidat dont le volume
a été mesuré à un niveau qui justifie un outillage spécifique :

- 44 282 364 lignes et 54 colonnes ; 2,22 Go en Parquet ; 10,09 Go en CSV décompressé ;
- le poste de développement dispose de 31,7 Go de mémoire vive et de 8 processeurs logiques
  (mesure du 12 octobre 2026). Le CSV décompressé représente environ le tiers de cette mémoire
  avant tout chargement en table. Un chargement complet en mémoire n'est pas une méthode sûre
  [H : surcoût mémoire d'un chargement en table non mesuré] ;
- le format Parquet permet la lecture des seules colonnes utiles (projection) et le filtrage par
  groupes de lignes (358 groupes dans le fichier). Cela réduit le volume lu et évite de charger
  les colonnes de données personnelles ;
- la jointure avec StockUniteLegale (30 148 401 lignes) est nécessaire pour la catégorie
  juridique.

Limite à dire au jury : quelques gigaoctets restent loin des volumes industriels du big data.
L'outillage se justifie par le dépassement d'un traitement en mémoire classique sur le poste,
pas par un besoin de grappe de calcul. Le choix entre un moteur SQL en colonnes embarqué et une
pile distribuée est une décision attendue (section 8).

**Lien avec C2 et C3.** Les requêtes SQL d'extraction porteront sur la base PostgreSQL (SGBD) et
sur les fichiers Parquet de Sirene (système big data). L'agrégation de C3 croise SRC-01, SRC-06,
SRC-07, SRC-09 et SRC-10, avec les anomalies relevées dans les fiches.

## 5. Données personnelles par source

| Source                  | Données personnelles en jeu                                                    | Conduite à tenir                                                                               |
| ----------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| SRC-01                  | Nom, prénoms, adresse des entrepreneurs individuels (catégorie juridique 1000) | Projection de colonnes sans identité ni adresse fine ; agrégats seulement ; pas de prospection |
| SRC-02                  | Données de l'artisan lui-même ; bloc `dirigeants`                              | Appel limité au SIREN saisi par l'artisan ; `dirigeants` jamais stocké                         |
| SRC-04                  | Adresse d'un client final, contenue dans la requête                            | Adresses synthétiques uniquement ; en production, validation locale ou mention dans l'AIPD     |
| SRC-05                  | Aucune en soi ; une adresse devient personnelle une fois liée à une personne   | Ne jamais associer une adresse réelle de la BAN à un nom réel dans un scénario                 |
| SRC-14                  | Aucune : effectifs agrégés, arrondis au multiple de 5                          | Sans objet                                                                                     |
| SRC-03, SRC-06 à SRC-13 | Aucune (référentiels, nomenclatures, agrégats, termes et marques)              | Sans objet                                                                                     |

**Sirene : entrepreneurs individuels et diffusion partielle.** Constats vérifiés :

- le statut de diffusion vaut `O` (diffusible) ou `P` (diffusion partielle). Le statut `N` a
  disparu le 21 mars 2023 : les anciennes unités `N` sont passées en `P` (fiche de l'API Sirene
  sur data.gouv.fr) ;
- pour un entrepreneur individuel en diffusion partielle, l'INSEE masque les nom, prénoms,
  pseudonyme, l'adresse précise dans la commune et la géolocalisation (page INSEE « Demander la
  modification de son statut de diffusion », mise à jour le 2 décembre 2025) ;
- selon l'INSEE (fiche « API Sirene open data » sur data.gouv.fr), les personnes en diffusion
  partielle ne doivent avoir leurs informations personnelles « ni rediffusées entièrement, ni
  utilisées à des fins de prospection ». Cette formule est celle de l'INSEE, pas celle de la loi.
  L'article R123-232-1 du Code de commerce, auquel elle renvoie, organise le droit d'opposition
  et réduit les données diffusées (identifiant et commune pour une personne physique) ;
- la fiche data.gouv.fr rappelle que la base contient des données personnelles soumises au RGPD,
  et qu'il revient au réutilisateur de tenir compte du statut de diffusion le plus récent.

Conduite retenue pour Muninn :

1. **Minimisation par construction.** Les colonnes d'identité et d'adresse fine ne sont jamais
   lues. Le traitement ne charge donc aucune donnée nominative, quel que soit le statut.
2. **Agrégats seulement.** Les sorties sont des comptages par code NAF, tranche, catégorie
   juridique et département. Aucun SIREN n'est conservé après agrégation [H].
3. **Pas de prospection.** Sirene ne sert pas à constituer un fichier de prospects. Si un usage
   commercial apparaît plus tard, il fera l'objet d'une analyse juridique distincte et exclura
   les unités au statut `P`.
4. **Fraîcheur.** Seul le dernier stock mensuel est utilisé ; le précédent est supprimé [H].
5. **Attribution.** Mention de la source et de la date du stock, comme l'exige la Licence
   Ouverte.

**Jeux d'évaluation synthétiques (règle R9).** Les scénarios combinent des prénoms tirés de
SRC-14, des noms de famille fictifs [H : source à définir], des voies réelles de la BAN avec des
numéros fictifs [H], et des numéros de téléphone pris dans des tranches non attribuées ou
réservées à la fiction [H : plage à identifier dans la spécification ARCEP]. Aucune personne
réelle ne doit pouvoir être reconstituée.

## 6. Sources écartées

| Source                                                   | Raison de l'écart                                                                                                                         |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| API Sirene de l'INSEE (portail-api.insee.fr)             | Compte obligatoire (réponse 401 sans clé) ; 30 requêtes par minute ; redondante avec SRC-01 pour des agrégats mensuels                    |
| API Recherche d'entreprises pour le dimensionnement      | Résultats plafonnés à 10 000 par recherche (mesuré) : un comptage de population est impossible                                            |
| API Adresse (api-adresse.data.gouv.fr)                   | Transférée à la Géoplateforme ; ancien domaine à ne pas utiliser ; SRC-04                                                                 |
| API Entreprise (entreprise.api.gouv.fr)                  | Accès restreint, sur habilitation (fiche data.gouv.fr) ; aucun besoin du produit                                                          |
| Liste des entreprises RGE (ADEME)                        | 158 206 lignes avec téléphone et courriel des entreprises ; apport limité au lexique (une vingtaine de libellés de domaines)              |
| Pages d'assistance des opérateurs (codes de renvoi)      | Codes normalisés par le 3GPP (21, 61, 62, 67, 002, 004) ; données peu nombreuses à saisir puis tester ; conditions d'utilisation non lues |
| API MediaWiki du Wiktionnaire                            | Chemins `/w/` et `/api/` interdits par robots.txt ; les pages `/wiki/` suffisent (SRC-12)                                                 |
| Chiffre FFB cité par Coover (159 600 auto-entrepreneurs) | Non daté, sans accès aux données ; remplacé par SRC-10                                                                                    |
| Fichier INSEE des prénoms, édition 2023                  | Remplacé par l'édition du 9 juillet 2025                                                                                                  |

## 7. Non vérifié ou incertain

| Point                                                                                | État                                                                                                            |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Définitions officielles de `trancheEffectifs` (`NN`, `00`) dans le PDF INSEE         | PDF ouvert, texte non extractible ; définitions lues dans une table dérivée (Annuaire des Entreprises)          |
| Part des valeurs vides de tranche d'effectif dans Sirene                             | Non mesurée : exige la lecture du fichier                                                                       |
| Effectif de la tête de pont (NAF 43.21A, 43.22A, 43.22B, 43.32B, tranche NN)         | Non mesuré : c'est le premier livrable de l'extraction big data                                                 |
| Codes NAF des serruriers dépanneurs                                                  | Incertain : la fiche 43.32B ne cite pas le dépannage                                                            |
| Nomenclature des activités artisanales (`activitePrincipaleRegistreMetiers`)         | Variable repérée dans Sirene ; nomenclature non consultée                                                       |
| Licence des fichiers NAF                                                             | Non indiquée sur la page de téléchargement                                                                      |
| Licence et fréquence de mise à jour de l'API Géo et de l'API Recherche d'entreprises | Non précisées dans les fiches lues                                                                              |
| Écart de 94 communes entre l'API Géo et le COG 2026                                  | Explication probable (collectivités d'outre-mer) non vérifiée ligne à ligne                                     |
| Contenu exact du secteur Urssaf F2                                                   | Correspondance avec les codes NAF non vérifiée                                                                  |
| Quota de l'API Explore de l'Urssaf                                                   | Non trouvé dans les métadonnées                                                                                 |
| Conservation des requêtes par la Géoplateforme (journaux de l'IGN)                   | Conditions générales d'utilisation non lues                                                                     |
| Règles mobile et fixe, plages réservées à la fiction (ARCEP)                         | Absentes du texte extrait de la spécification des fichiers ; relèvent du plan de numérotation, non consulté     |
| Colonnes exactes de l'export CSV de la BAN                                           | Fichier non téléchargé (938 Mo)                                                                                 |
| Codes de renvoi d'appel du 3GPP                                                      | Lus dans un document 3GPP de 2000 cité par un moteur de recherche, non ouvert ; version en vigueur non vérifiée |
| Source ouverte de noms de famille pour les scénarios                                 | Aucune source vérifiée                                                                                          |
| Statut juridique d'une liste de termes extraite du Wiktionnaire                      | Avis juridique non sollicité                                                                                    |
| Disponibilité du point SPARQL de Wikidata                                            | Dégradée le 12 octobre 2026 (1 requête par minute) ; durée inconnue                                             |
| Zone Alsace-Moselle des jours fériés (départements 57, 67, 68)                       | Règle connue, non vérifiée dans le Code du travail                                                              |

## 8. Décisions attendues du porteur

1. **Type « base de données » de C1** : Wikidata (externe, pertinence faible) ou base PostgreSQL
   du projet (interne, utile). Recommandation : présenter les deux, en disant au jury que
   Wikidata est retenue pour la couverture et que la base du projet porte l'usage réel.
2. **Outil du système big data** : moteur SQL en colonnes embarqué (proportionné au volume
   mesuré) ou pile distribuée (plus démonstrative, plus coûteuse à installer). À trancher en
   phase 2 avec le choix des outils (C15).
3. **Géocodage en production** : validation locale (SRC-05 à SRC-07) ou appel à la Géoplateforme
   déclaré dans l'AIPD. Recommandation : validation locale, cohérente avec « rien ne sort en
   clair ».
4. **Correction de l'analyse stratégique** : remplacer « tranche d'effectif 0 » par « unité non
   employeuse (NN) », et le chiffre FFB par la série Urssaf datée.

## 9. Sources consultées

Toutes consultées le 12 octobre 2026, par ouverture de la page ou par requête HTTP.

Sirene et entreprises :

- https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
- https://www.data.gouv.fr/api/1/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-073823/stock-stocketablissement-parquet.parquet (pied de page seulement)
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-073325/stock-stockunitelegale-parquet.parquet (pied de page seulement)
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-072713/stock-stocketablissement-csv.zip (répertoire central seulement)
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-072119/stock-stockunitelegale-csv.zip (répertoire central seulement)
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260113-143513/stocketablissement-311-dessin-de-fichier.csv
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260113-143438/stockunitelegale-311-dessin-de-fichier.csv
- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260129-104840/stocketablissement-311-description-fichier-29-01-2026.pdf (ouvert, texte non extrait)
- https://www.insee.fr/fr/information/7456564
- https://www.insee.fr/fr/information/9019311
- https://www.data.gouv.fr/api/1/dataservices/?q=sirene (fiches de l'API Sirene et de l'API Entreprise)
- https://portail-api.insee.fr/ (page dynamique, non lisible)
- https://api.insee.fr/api-sirene/3.11/informations (réponse 401 sans clé)
- https://recherche-entreprises.api.gouv.fr/docs/ (page dynamique, non lisible)
- https://recherche-entreprises.api.gouv.fr/openapi.json
- https://recherche-entreprises.api.gouv.fr/search?activite_principale=43.22A&per_page=1&page=1
- https://raw.githubusercontent.com/annuaire-entreprises-data-gouv-fr/search-api/main/app/labels/tranches-effectifs.json

Géographie et adresses :

- https://geo.api.gouv.fr/communes (requêtes par code postal et liste complète)
- https://geo.api.gouv.fr/decoupage-administratif/communes
- https://github.com/datagouv/api-geo
- https://data.geopf.fr/geocodage/search?q=12+rue+des+lilas+montreuil&limit=1
- https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/geocodage/
- https://adresse.data.gouv.fr/outils/api-doc/adresse
- https://api-adresse.data.gouv.fr/search/ (redirection 301 constatée)
- https://www.data.gouv.fr/api/1/datasets/base-adresse-nationale/
- https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz (en-tête seulement)
- https://plateforme.adresse.data.gouv.fr/ban/stats
- https://www.data.gouv.fr/api/1/datasets/base-officielle-des-codes-postaux/
- https://datanova.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal
- https://data.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal/raw
- https://www.data.gouv.fr/api/1/datasets/code-officiel-geographique-1/
- https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv

Calendrier, nomenclatures, statistiques :

- https://calendrier.api.gouv.fr/jours-feries/metropole/2026.json
- https://calendrier.api.gouv.fr/jours-feries/alsace-moselle/2027.json
- https://calendrier.api.gouv.fr/jours-feries/openapi.yml
- https://www.data.gouv.fr/api/1/datasets/jours-feries-en-france/
- https://github.com/etalab/jours-feries-france-data
- https://www.insee.fr/fr/information/2406147
- https://www.insee.fr/fr/information/2120875
- https://www.insee.fr/fr/information/8617910
- https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/43.22A
- https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/43.22B
- https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/43.21A
- https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/43.32B
- https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/auto-entrepreneurs-par-secteur-dactivite
- https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/auto-entrepreneurs-par-departement-secteur
- https://www.insee.fr/fr/statistiques/8894961
- https://www.insee.fr/fr/statistiques/7633685
- https://www.data.gouv.fr/api/1/datasets/fichier-des-prenoms-depuis-1900/

Lexique et téléphonie :

- https://query.wikidata.org/sparql (requêtes du 12 octobre 2026)
- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual
- https://www.wikidata.org/robots.txt
- https://fr.wiktionary.org/robots.txt
- https://fr.wiktionary.org/wiki/Catégorie:Lexique_en_français_de_la_plomberie (et catégories électricité, serrurerie, construction, chauffage, thermique)
- https://www.data.gouv.fr/api/1/datasets/ressources-en-numerotation-telephonique/
- https://www.data.gouv.fr/datasets/ressources-en-numerotation-telephonique/
- https://extranet.arcep.fr/uploads/MAJNUM.csv

Sources écartées :

- https://www.data.gouv.fr/api/1/datasets/liste-des-entreprises-rge/
- https://data.ademe.fr/data-fair/api/v1/datasets/liste-des-entreprises-rge-2
- robots.txt de assistance.orange.fr, assistance.sfr.fr, www.bouyguestelecom.fr, assistance.free.fr
- https://3gpp.org/ftp/tsg_sa/TSG_SA/TSGS_09/Docs/PDF/SP-000376.pdf (cité par un moteur de recherche, non ouvert)
