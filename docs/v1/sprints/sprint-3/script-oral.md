# Sprint 3 : texte à dire devant l'évaluateur

**Évaluateur :** un pair technique de la même formation : on peut lui montrer la réponse brute de
l'API derrière l'écran.
**Durée :** environ 15 minutes, démonstration comprise.
**Ordre :** celui de `demonstration.md` (le rejeu des données est lancé en premier, il tourne
pendant les autres critères).
**Se prépare avec :** `demonstration.md`, section 1 (15 minutes avant) ; les réponses aux questions
probables sont dans `explication-resultat.md`, section 7.
**Convention :** le texte entre guillemets est à dire ; les crochets décrivent ce que tu fais.

## Les deux écrans, et quand passer de l'un à l'autre

| Écran                               | Lien                                                                                                                                                        | À quoi il sert                                                                                                        |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Console**, écran « Référentiels » | <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/referentiels>                                                        | Ce que voit un utilisateur : l'évaluateur y tape ses questions (P2, P3) et lit les sources et les refus en clair      |
| **Swagger**, communes               | <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/docs#/r%C3%A9f%C3%A9rentiels/communes_v1_referentiels_communes_post>     | La même réponse, brute, en JSON : statut, candidates, `references` (table et clé), `sources` (P2) ; champ refusé (P3) |
| **Swagger**, termes du métier       | <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/docs#/r%C3%A9f%C3%A9rentiels/termes_v1_referentiels_termes_post>         | Le seuil (0,55), la similarité, la page du Wiktionnaire et sa licence (P2, P3)                                        |
| **Swagger**, marché                 | <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/docs#/r%C3%A9f%C3%A9rentiels/marche_v1_referentiels_marche__metier__get> | Les comptages Sirene, les cellules masquées, la règle du secret statistique (P1)                                      |
| **Version servie**                  | <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/version>                                                                 | Le commit en production (P5)                                                                                          |

**La règle :** la **console** pour ce qu'un utilisateur voit et pour laisser l'évaluateur taper ;
**Swagger** pour prouver ce qu'il y a derrière. Dans Swagger : « Try it out », remplir le corps ou
le paramètre, puis « Execute » ; la réponse s'affiche sous « Response body ».

## 0:00 – 1:30 · Introduction

[Console ouverte, écran vide.]

« Le sprint 3 avait un objectif : brancher Muninn sur ses données. À la fin, l'application devait
répondre à partir de ses propres données, en citant ses sources, et refuser proprement ce qui sort
de son corpus ou de son périmètre, le tout livré par la chaîne du sprint 2.

Pour Muninn, le bon mécanisme d'ancrage n'est pas un RAG. Un RAG retrouve des passages dans des
documents ; nous n'avons aucun document à interroger. Notre agent a besoin de faits exacts : la
liste des communes, leurs codes postaux, le vocabulaire du métier, la taille du marché. Ce sont des
tables. Nous les avons donc rangées dans PostgreSQL, interrogé par du SQL paramétré, en lecture
seule, derrière une API FastAPI. C'est notre décision D-56.

Le résultat : les critères P1 à P5 sont prouvés, en production. Le sixième, le journal des
retours, attend vos retours. Je vais vous le montrer critère par critère, en commençant par lancer
un rechargement complet des données, qui tournera pendant que nous regardons le reste. »

## 1:30 – 2:30 · P4, lancement du rejeu

[Lancer `gh workflow run donnees -f environnement=production`, ou le bouton « Run workflow » de
l'onglet Actions.]

« Une seule commande relance tout le chargement en production : les migrations Alembic, les rôles
de la base, puis l'ingestion des six sources. Elle s'exécute dans une tâche Container Apps qui
lance la même image que l'application. Elle tourne aussi toute seule, le 3 de chaque mois. Nous
reviendrons voir son résultat dans quelques minutes. »

## 2:30 – 3:30 · P5, tout est en production

[**Console** : l'écran « Référentiels ». Puis **Swagger** : la page `/docs`, les trois points
d'accès du groupe « référentiels ». Puis **Version servie**.]

« Tout ce que je vais vous montrer tourne sur Azure : cet écran, et l'API derrière lui, que vous
voyez ici dans Swagger, avec ses trois points d'accès : communes, termes du métier, marché. Rien ne
vient d'un notebook ni de mon poste. Cette adresse donne le commit servi : c'est la chaîne du
sprint 2 qui l'a livré, après les tests. »

## 3:30 – 7:30 · P2, les réponses sont traçables

[**Console.** Laisser le clavier à l'évaluateur. S'il n'a pas d'idée : « Montreuil ».]

« Je vous laisse taper une commune de votre choix. »

[Après sa réponse, lire avec lui la réponse et ses sources dans la console.]

« Pour chaque commune, l'écran cite ses sources : le titre, l'éditeur, la licence, la date de la
source, la date de chargement et la version, avec un lien vers le fichier d'origine. »

[**Swagger, communes** : « Try it out », corps `{"nom": "Montreuil"}`, « Execute ».]

« Voici la même réponse, brute. Le statut est `trouve`, avec trois candidates : 28267, 85148 et
93048. Pour chacune, `references` donne la table et la clé de la ligne qui atteste la valeur, par
exemple `ref.communes`, « version 1, COM 93048 ». Et `sources` donne la licence, l'adresse du
fichier, `date_source` et `charge_le`. On peut donc remonter de la réponse à la ligne en base, puis
au fichier de l'INSEE. Trois communes portent exactement ce nom : l'API ne choisit pas à votre
place. Au sprint 4, c'est l'agent qui départagera avec un indice de l'appel, comme “le 9-3” ; sans
indice, il laissera le champ vide et signalera le dossier. »

[**Swagger, termes du métier** : corps `{"mot": "cumulus", "metier": "plomberie"}`, « Execute ».]

« Pour un mot de métier, la réponse donne le terme le plus proche, sa similarité, ici 1,0, le
seuil appliqué, 0,55, la page du Wiktionnaire et sa licence, CC BY-SA. Chaque terme garde son
attribution, et `attribution` précise que seuls les titres de pages sont repris, jamais les
définitions. »

## 7:30 – 10:30 · P3, le refus hors corpus

[**Console.** Laisser le clavier. S'il n'a pas d'idée : « Gotham City », « ordinateur » en
plomberie, « disjoncteur » en électricité, « Bagnolet » avec 93100.]

« Maintenant, essayez de me piéger : une commune qui n'existe pas, un mot sans rapport avec la
plomberie, ou une question libre. »

[Après chaque refus.]

« Trois refus distincts. `hors_corpus` : la commune n'existe pas, ou aucun terme n'atteint le
seuil ; aucune valeur n'est proposée. `hors_perimetre` : le métier n'a pas de lexique dans la V1.
Et `incoherent` : Bagnolet n'a pas le code 93100 ; l'API montre son vrai code, 93170, mais ne
corrige rien à votre place.

Le seuil vaut 0,55. Je ne l'ai pas choisi au jugé : j'ai écrit le protocole et la règle de choix
avant de mesurer, et je les ai versionnés. Sur 45 mots étiquetés, c'est le plus bas seuil sans
aucune fausse acceptation : 24 bons mots acceptés sur 25. L'hypothèse de départ, 0,8, en aurait
refusé 14. »

[**Swagger, communes** : corps `{"nom": "Vincennes", "sql": "DROP TABLE"}`, « Execute ».]

« Et côté entrée : l'API refuse tout champ qu'elle ne connaît pas, ici une erreur 422,
`extra_forbidden`. Les valeurs reçues ne sont jamais concaténées dans le SQL : les requêtes sont
paramétrées, et la connexion de l'API est en lecture seule, avec un rôle qui ne peut ni écrire ni
créer de table. Une tentative d'injection donne un simple `hors_corpus` : un test le vérifie. »

## 10:30 – 11:30 · P4, résultat du rejeu

[Ouvrir l'exécution du workflow `donnees` dans l'onglet Actions.]

« Le rechargement est terminé. Les cinq jeux chargés, puisque le lexique réunit Wiktionnaire et
Wikidata, sont “inchangée” : comme rien n'a changé à la source, l'empreinte est la même, aucune
version n'a été créée, et aucun doublon. Et le jeu de dix questions de démonstration a été rejoué
contre la production : dix sur dix. Le pipeline est rejouable, en une commande, sans risque. »

[Si le rejeu a échoué : montrer l'exécution du 16 octobre (83 s, 10 sur 10) et
`preuves/etape-10-production.md`.]

## 11:30 – 14:00 · P1, des sources identifiées et licites

[Ouvrir `sources.md`, puis `rgpd.md`.]

« Voici le registre des six sources : pour chacune, sa licence, son adresse et ses conditions
d'usage, revérifiées le 15 octobre sur les pages officielles. Quatre sont sous Licence Ouverte ou
CC0. Le Wiktionnaire est sous CC BY-SA : il impose l'attribution, que nous respectons terme par
terme. L'API Géo ne publie pas de licence : je l'ai écrit dans le registre, et elle ne sert qu'à
recouper le fichier de l'INSEE ; aucune donnée qu'elle seule fournit n'est servie.

Côté RGPD, cinq sources ne contiennent aucune donnée sur une personne : ce sont des lieux et des
mots. Sirene, lui, contient des entrepreneurs individuels. Nous appliquons donc la minimisation :
DuckDB lit à distance les seules colonnes utiles du Parquet, 290 Mo sur 2,9 Go, rien n'est écrit
sur disque, et nous ne gardons que des comptages. »

[**Swagger, marché** : paramètre `metier` = `plomberie`, « Execute ».]

« Voici ce qui est gardé : 673 cellules de comptage, stock Sirene du 1er octobre 2026, par code
d'activité, tranche d'effectifs, catégorie juridique et département. Aucun SIREN, aucun nom,
aucune adresse. Quand une cellule compte moins de cinq établissements, elle rejoint une cellule
`ZZ` ; si elle reste trop petite, elle est masquée : `is_masked` vaut `true` et le comptage est
vide. C'est le secret statistique, rappelé dans `sources`. Un test bloque toute publication sous ce
seuil. »

[Optionnel : la même vue dans la **console**, onglet « marché ».]

« Enfin, ce que vous avez tapé tout à l'heure n'a été ni stocké, ni écrit dans les journaux : un
test envoie une valeur témoin et vérifie qu'elle n'apparaît dans aucun journal. »

## 14:00 – 15:00 · P6 et conclusion

[Ouvrir `retours.md`.]

« Dernier critère : le journal des retours. Il est prêt : chaque retour que vous me ferez y sera
consigné, avec ma décision, sa justification et le lien qui l'atteste. C'est le seul critère que je
ne peux pas encore prouver, puisqu'il attend vos retours.

Pour conclure : Muninn a maintenant ses propres données, exactes, citées et contrôlées, en
production. C'est sur elles que l'agent du sprint 4 s'appuie pour ne jamais inventer une commune ni
un code postal. Merci, je suis à votre disposition pour vos questions. »
