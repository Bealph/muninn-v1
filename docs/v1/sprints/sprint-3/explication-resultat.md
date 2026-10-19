# Sprint 3 : expliquer le résultat à l'évaluateur

**Pour qui :** le porteur, pour présenter et défendre le résultat du sprint 3 devant l'évaluateur,
un pair technique de la même formation.
**Écrans à montrer :** la console pour ce que voit l'utilisateur, Swagger pour la réponse brute de
l'API ; liens et moments précis dans `script-oral.md`, section « Les deux écrans ».
**Se lit avec :** `script-oral.md` (texte à dire), `demonstration.md` (déroulé en direct),
`compte-rendu.md` (tableaux et preuves).
**Date :** 19 octobre 2026.

## 1. Le résultat en une phrase

**Muninn répond à partir de ses propres données, en production, en citant la source de chaque
valeur, et refuse proprement ce qui sort de ses données ou de son périmètre.** Les critères P1 à P5
de l'évaluation par le pair sont prouvés ; P6 (journal des retours) attend les retours du pair.

## 2. Ce que la consigne devient pour Muninn

La consigne demande de « brancher le projet sur ses données » et de choisir « le mécanisme d'ancrage
qui convient ». Pour Muninn, le bon mécanisme n'est **pas** un RAG :

- un RAG sert à retrouver des passages dans des documents (contrats, notices, pages) ; Muninn n'a
  aucun document à interroger, et son serveur ne garde aucun dossier client (règle R1) ;
- ce dont l'agent a besoin, ce sont des **faits exacts** : la liste des communes, leurs codes
  postaux, le vocabulaire du métier, la taille du marché. Ce sont des tables, pas des textes.

D'où la décision D-56 : des référentiels dans une base relationnelle (PostgreSQL), interrogés par
**SQL sécurisé** derrière une API. Une « question » est une recherche de commune, de code postal,
de terme de métier ou de marché. L'agent du sprint 4 interroge exactement cette API par ses deux
outils : le sprint 3 lui donne ses données d'ancrage.

## 3. Comment ça marche, en cinq briques

| Brique        | Ce qui se passe                                                                                                                                                                                                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Collecte   | Six sources ouvertes, de cinq types : fichiers (codes postaux de La Poste, communes de l'INSEE), service web (API Géo), page web (Wiktionnaire), base de données (Wikidata, requête SPARQL), big data (Sirene, 2,9 Go). Chaque téléchargement est tracé : adresse, date, empreinte |
| 2. Nettoyage  | Encodage, formats, codes en texte (zéros en tête, Corse 2A et 2B), doublons ; chaque ligne écartée l'est avec son motif. Des contrôles (cas VD de la phase 1) bloquent la publication si les données sont incohérentes                                                             |
| 3. Stockage   | PostgreSQL, schémas `ref` (référentiels) et `market` (agrégats Sirene). Chaque chargement crée une version ; seule une version contrôlée est servie, l'ancienne reste en place en cas d'échec                                                                                      |
| 4. Ancrage    | API en lecture seule : communes par égalité exacte du nom (après normalisation) ou par code postal ; termes du métier par similarité trigramme, avec un seuil ; marché par département. Chaque réponse cite ses sources ; sinon, un refus motivé                                   |
| 5. Production | Une tâche Container Apps lance la même image que l'application, en une commande (`gh workflow run donnees`), et chaque mois automatiquement (D-58, D-60). Tout est livré par la chaîne du sprint 2                                                                                 |

## 4. Les chiffres, et ce qu'ils prouvent

| Chiffre                                                                         | Ce qu'il prouve                                                                              |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 37 496 communes, 38 925 codes postaux, 142 termes, 2 614 cellules Sirene        | Les vraies données sont chargées en production, pas un échantillon                           |
| 10 questions sur 10, en préproduction et en production                          | Le comportement attendu (réponses, ambiguïté, incohérence, refus) est vérifié par la machine |
| Rejeu en production : 83 s, aucune version créée                                | Le pipeline est rejouable sans doublon : relancer ne casse rien                              |
| Sirene : 290 Mo lus sur 2,9 Go, en 94 à 188 s                                   | DuckDB lit à distance les seules colonnes utiles, sans tout télécharger                      |
| Seuil du lexique 0,55 : 24 positifs sur 25, 0 fausse acceptation sur 20         | Le seuil a été choisi par une mesure dont la règle était écrite avant de mesurer             |
| 143 tests, dont les droits des rôles et l'absence des valeurs dans les journaux | La sécurité est vérifiée par des tests, pas seulement décrite                                |

Ces mesures portent sur peu d'exécutions : ce sont des ordres de grandeur.

## 5. Critère par critère

**P1. Sources identifiées et licites.** Le registre `sources.md` donne pour chaque source sa
licence, son adresse et ses conditions d'usage, revérifiées le 15 octobre 2026 sur les pages
officielles : Licence Ouverte 2.0 pour La Poste, l'INSEE et Sirene, CC0 pour Wikidata, CC BY-SA 4.0
pour le Wiktionnaire. L'API Géo ne publie pas de licence : c'est écrit dans le registre, et elle ne
sert qu'à recouper le fichier de l'INSEE. Cinq sources ne contiennent aucune donnée sur une
personne : la non-applicabilité du RGPD y est argumentée. Sirene contient des entrepreneurs
individuels : la minimisation est appliquée (seules les colonnes utiles sont lues, rien n'est écrit
sur disque, seuls des comptages par département sont gardés, sous secret statistique). Le
Wiktionnaire impose l'attribution : chaque terme garde sa source, son titre de page et sa licence.

**P2. Réponses traçables.** Chaque réponse cite ses sources (titre, éditeur, licence, dates,
version) et, pour chaque valeur, la table et la clé de la ligne en base. L'évaluateur peut remonter
de la réponse à la ligne, puis au fichier d'origine par le lien.

**P3. Refus hors corpus démontré.** Trois refus distincts : « hors des données » (commune
inexistante, mot sous le seuil), « hors du périmètre » (métier sans lexique en V1), « incohérent »
(nom et code postal qui ne vont pas ensemble, sans correction silencieuse). Jamais de valeur
inventée.

**P4. Pipeline rejouable en une commande.** `gh workflow run donnees -f environnement=production` :
migrations, rôles, ingestion des six sources, puis rejeu du jeu de questions. Une source inchangée
ne crée pas de version (empreinte) ; une source en panne laisse la version servie intacte.

**P5. Tout visible en production.** L'écran « Référentiels » et l'API (Swagger) tournent sur Azure,
livrés par la chaîne du sprint 2 ; `/version` montre le commit servi. Aucun notebook.

**P6. Journal des retours.** `retours.md` est prêt : chaque retour du pair, sa décision, sa
justification et son lien. Les retours n'ont pas encore été reçus : c'est le seul critère non
prouvé.

## 6. Ce qui n'est pas parfait, à dire avant qu'on le demande

- **Le seuil du lexique a une marge étroite** (0,07 entre le dernier mot accepté et le premier
  refusé) : un autre lexique pourrait le déplacer. Parade : le lexique n'est publié que si son
  empreinte a été évaluée.
- **Wikidata est peu pertinent** : la requête ramène des entreprises de service parmi les marques.
  Assumé en V1, relecture humaine après.
- **Les migrations ne sont pas lancées par la livraison** : il faut lancer le workflow `donnees`
  après une fusion qui en contient une. À automatiser.
- **La règle de diffusion partielle de Sirene** est lue par moi, pas par un juriste.
- **Le journal des retours** attend les retours du pair (P6).

## 7. Questions probables, et réponses

**« Pourquoi pas de RAG, ni de base vectorielle ? »**
Parce qu'il n'y a aucun document à retrouver : Muninn a besoin de faits exacts (une commune, un code
postal), pas de passages de texte proches. Une base vectorielle rendrait « quelque chose de
proche » ; une requête SQL rend la bonne ligne, ou rien, et permet de citer exactement la source.

**« Comment avez-vous choisi le seuil de 0,55 ? »**
Par un protocole écrit et commité avant la mesure (`calibration-seuil.md`) : 45 mots étiquetés
(25 à accepter, 20 à refuser), seuils de 0,30 à 0,95. La règle fixée d'avance : le plus bas seuil
sans aucune fausse acceptation, parce qu'un terme faux dans un dossier coûte plus cher qu'un refus.
Résultat : 0,55. L'hypothèse de départ du contrat (0,8) aurait refusé 14 bons mots sur 25.

**« Que veut dire 24 sur 25, intervalle [0,80 ; 0,99] ? »**
24 bons mots acceptés sur 25. Avec si peu de mots, le vrai taux n'est pas connu exactement :
l'intervalle de confiance à 95 % dit qu'il est probablement entre 80 % et 99 %. De même, zéro
fausse acceptation sur 20 ne prouve pas un taux nul : la borne haute reste de 16 %. Je le dis plutôt
que de présenter un « 100 % ».

**« Pourquoi “Montreuil” donne trois réponses ? »**
Parce que trois communes portent exactement ce nom (Eure-et-Loir, Vendée, Seine-Saint-Denis). L'API
ne choisit pas à la place de l'utilisateur. Au sprint 4, l'agent départage avec un indice de
l'appel (« le 9-3 ») ; sans indice, il laisse le champ vide et signale le dossier.

**« Pourquoi DuckDB pour Sirene ? »**
Le stock fait 2,9 Go et des dizaines de millions de lignes. DuckDB lit les fichiers Parquet à
distance, colonne par colonne : seuls 290 Mo ont été lus, sans serveur à administrer. Le charger
entièrement dans PostgreSQL n'aurait pas été proportionné.

**« Qu'est-ce que le secret statistique ? »**
Une cellule de comptage trop petite (moins de 5 établissements) pourrait permettre d'identifier
quelqu'un. Elle est regroupée dans une cellule « autres », masquée si elle reste sous 5. Un test
bloque toute publication d'une valeur sous ce seuil.

**« Y a-t-il des données personnelles ? »**
Dans cinq sources, non : ce sont des lieux et des mots. Dans Sirene, oui (entrepreneurs
individuels) : seules les colonnes utiles sont lues, rien n'est écrit sur disque, et seuls des
comptages par département sont gardés. Les valeurs que l'on cherche dans l'écran ne sont ni
journalisées ni stockées : un test le vérifie avec une valeur témoin.

**« Comment savez-vous que les données sont justes ? »**
Par des contrôles qui bloquent la publication : formats, doublons, communes sans code postal,
recoupement entre l'API Géo et le fichier de l'INSEE (34 969 communes comparées, aucun écart de nom).
Une version qui échoue n'est jamais servie.

**« Que se passe-t-il si une source ne répond pas ? »**
La version précédente reste servie. Pour le lexique, un instantané de secours versionné prend le
relais, et le rapport du chargement l'indique.

**« Et si on tente une injection SQL ? »**
Les requêtes sont paramétrées : aucune valeur reçue n'entre dans le texte SQL. La connexion de l'API
est en lecture seule, avec un rôle qui ne peut ni écrire ni créer de table. Une tentative
d'injection donne un simple « hors corpus », les tables restent intactes (test).

**« Combien ça coûte en production ? »**
Un rejeu sans nouveauté dure environ 80 secondes, dans la franchise gratuite des tâches Container
Apps. Une alerte de budget est posée à 60 € par mois sur le groupe de ressources (D-34) : elle
prévient, elle ne coupe pas.

**« Quel lien avec la suite ? »**
Le sprint 4 construit l'agent qui interroge cette API par deux outils (communes et termes du
métier). Le sprint 3 lui fournit des données exactes, citées et contrôlées : c'est ce qui l'empêche
d'inventer une commune ou un code postal.
