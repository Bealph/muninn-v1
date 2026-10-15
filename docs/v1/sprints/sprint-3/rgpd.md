# Minimisation RGPD du sprint 3 (étape 9, critère P1)

**Rédigé le :** 15 octobre 2026.
**Références :** registre RGPD de la phase 1 (`docs/conception/architecture_de_donnees/05-registre-rgpd.md`,
fiche RT-07) ; registre des sources du sprint (`sources.md`).

## 1. Données personnelles, source par source

| Source                                                 | Données personnelles                                                                                       | Décision                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| COG (SRC-07), codes postaux (SRC-06), API Géo (SRC-03) | Aucune : découpage administratif et adresses d'acheminement, sans personne                                 | Non applicable, argumenté                  |
| Wiktionnaire (SRC-12), Wikidata (SRC-11)               | Aucune : titres de pages et noms de marques ou d'entreprises                                               | Non applicable, argumenté                  |
| Sirene (SRC-01)                                        | Oui : un entrepreneur individuel est une personne physique, désignée par son SIREN, son nom et son adresse | Minimisation appliquée avant tout stockage |
| Questions posées à l'API et à la console               | Possible : quelqu'un peut taper un nom de personne à la place d'une commune                                | Ni journalisées, ni stockées               |

## 2. Sirene : ce qui est lu, ce qui est gardé

| Étape              | Ce qui se passe                                                                                                                                                                                                   | Preuve                                                       |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Lecture            | Lecture à distance, par plages, des seules colonnes de la requête : activité, tranche d'effectifs, commune, état, catégorie juridique, SIREN. Aucun nom, aucune adresse fine, aucune géolocalisation, aucun SIRET | `requetes/sirene_etablissements.sql` ; 290 Mo lus sur 2,9 Go |
| Disque             | Aucun fichier Sirene n'est écrit sur disque : DuckDB lit les plages en mémoire                                                                                                                                    | `sirene.py`                                                  |
| Mémoire            | Le SIREN sert à joindre la catégorie juridique et à compter les entreprises distinctes, puis la table est supprimée                                                                                               | `sirene.calculer`                                            |
| Base               | Seuls des comptages par département sont écrits ; le schéma `market` n'a aucune colonne pour un SIREN, un SIRET, une commune ou un code postal                                                                    | Migration `0001`                                             |
| Secret statistique | Seuil de 5 : une cellule plus petite rejoint une cellule `ZZ`, masquée si elle reste sous le seuil ; total national arrondi quand la `ZZ` est masquée. Contrôle bloquant : aucune mesure servie sous 5            | `test_sirene.py` ; vérifié en base sur le vrai stock         |
| Usage              | Dimensionnement du marché seulement ; aucune prospection (code de commerce, article A123-96)                                                                                                                      | Registre de la phase 1, RT-07                                |

**Écarts avec la fiche RT-07 de la phase 1, tous plus protecteurs ou neutres :**

- RT-07 prévoyait un lac de données et la suppression des fichiers sous 24 heures : la V1 n'écrit
  aucun fichier (D-39).
- RT-07 lisait le code postal, le statut de diffusion et les dates : la V1 ne les lit pas.
- La V1 lit le SIREN, que RT-07 ne citait pas parmi les colonnes lues, pour compter les
  entreprises distinctes ; il ne quitte pas la mémoire du traitement.

**Statut de diffusion partielle.** Les établissements en diffusion partielle (statut « P »)
entrent dans les comptages : seuls leur identité, leur adresse dans la commune et leur
géolocalisation sont masquées par l'INSEE, et Muninn ne lit ni ne diffuse aucune de ces données.
Un comptage par département, sous secret statistique, ne permet pas de les retrouver. [H : lecture
de la règle de l'INSEE par moi, non confirmée par un juriste.]

## 3. Questions posées à l'API et à la console

- Les valeurs cherchées passent dans le corps des requêtes, jamais dans l'adresse : le journal
  d'accès du serveur ne voit que le chemin (`POST /v1/referentiels/communes`). Seul le métier du
  marché passe dans l'adresse, et ce n'est pas une donnée personnelle.
- Le code ne journalise aucune valeur reçue ; une erreur de base est journalisée par son seul
  type.
- Aucune question n'est stockée : la base de l'API est ouverte en lecture seule.
- **Preuve :** `test_valeurs_recherchees_absentes_des_journaux` envoie une valeur témoin à l'API et à
  la console, capture tous les journaux à tous les niveaux, et vérifie qu'elle n'y figure pas.

## 4. Ce qui reste à confirmer

- La lecture de la règle de diffusion partielle (section 2), par un juriste.
- La durée de conservation des agrégats (5 ans dans RT-07, hypothèse) : sans objet pour la V1, qui
  s'arrête après les oraux.
