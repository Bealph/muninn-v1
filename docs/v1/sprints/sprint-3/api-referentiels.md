# API des référentiels de la V1 (sprint 3, étape 7)

**Code :** `src/muninn/referentiels/` ; **décisions :** D-56 (SQL sécurisé), D-57 (exposition).
**Interface interactive :** Swagger de l'API, `/docs`.

## 1. Points d'accès

| Point                                  | Question                                       | Ce qui est rendu                                                              |
| -------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------- |
| `POST /v1/referentiels/communes`       | Un nom de commune, un code postal, ou les deux | Communes candidates, leurs codes postaux, la table et la clé de chaque valeur |
| `POST /v1/referentiels/termes`         | Un mot entendu et un métier                    | Le terme du lexique le plus proche, sa similarité, sa page source, sa licence |
| `GET /v1/referentiels/marche/{metier}` | Un métier de la tête de pont                   | Établissements actifs par département, après secret statistique (Sirene)      |

Les valeurs cherchées passent dans le corps de la requête, jamais dans l'adresse ; elles ne sont
ni journalisées ni stockées (contrat d'API, P-05 et TA-23).

## 2. Statuts et refus

| Statut           | Quand                                                                                        | Ce que contient la réponse                  |
| ---------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `trouve`         | Les données répondent                                                                        | Les valeurs, leurs références, les sources  |
| `hors_corpus`    | Aucune commune de ce nom ou de ce code ; mot sous le seuil de 0,55                           | Le motif ; aucune valeur proposée           |
| `hors_perimetre` | Métier inconnu, ou sans lexique publié en V1                                                 | Le motif                                    |
| `incoherent`     | Nom et code postal donnés, mais aucune commune ne les accorde                                | Les communes du nom, avec leurs vrais codes |
| Erreur 422       | Entrée mal formée : rien de donné, code postal hors format, texte trop long, champ non prévu | Le détail de l'erreur                       |
| Erreur 429, 503  | Limite de débit atteinte ; base indisponible ou référentiel non chargé                       | Le motif ; `Retry-After` pour la limite     |

## 3. Sources citées

Chaque réponse porte la liste de ses sources : jeu, identifiant, titre, éditeur, licence,
adresse, date de la source, date de chargement, version et table. Chaque valeur porte en plus la
table et la clé de la ligne qui l'atteste (`ref.communes` : version et code ; `ref.postal_codes`,
`ref.lexicon_terms` : identifiant). L'évaluateur peut ainsi remonter de la réponse à la ligne de la
base, puis au fichier source.

## 4. Écarts avec le contrat de la phase 2

| Point du contrat (`industrialisation/04-contrat-api.md`, § 5)      | V1                                                    | Raison                                                                                      |
| ------------------------------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Service interne, jeton de service                                  | Points exposés en lecture seule, limite de débit      | D-57 : l'évaluateur interroge la production ; données ouvertes, sans donnée personnelle     |
| `POST /v1/checks/postal-commune`, `POST /v1/postal-codes/communes` | `POST /v1/referentiels/communes`                      | Un seul point pour l'outil `chercher_communes` de l'agent (dossier V1, § 3.1)               |
| `GET /v1/lexicons/{trade}` (lexique entier)                        | `POST /v1/referentiels/termes` (terme le plus proche) | L'outil `chercher_terme_metier` de l'agent ; le refus sous le seuil est exigé par le sprint |
| Correspondance approchée des communes, seuil [H : 0,8]             | Égalité exacte après normalisation                    | Politique de l'agent : signaler plutôt que deviner (D-37)                                   |
| Seuil de similarité [H : 0,8]                                      | 0,55 pour le lexique                                  | Calibration du 15 octobre 2026 (`calibration-seuil.md`)                                     |
