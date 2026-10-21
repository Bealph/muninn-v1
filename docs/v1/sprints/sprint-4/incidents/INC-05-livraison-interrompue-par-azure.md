# INC-05 : livraison en production interrompue par une erreur passagère d'Azure

| Champ                  | Valeur                                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| Dates                  | 16, 19 et 21 octobre 2026 (trois occurrences)                                                            |
| Environnement          | Production, job `production` du workflow `ci`, script `infra/azure/deployer.sh`                          |
| Gravité                | Faible : l'API était livrée et contrôlée ; la console est restée sur la version précédente               |
| Durée                  | Jusqu'à la livraison suivante : 10 min, 24 min et 54 min                                                 |
| Détection              | À la clôture du sprint 4 (21 octobre), en relisant l'historique des livraisons ; pas au moment des faits |
| Statut                 | Résolu par la reprise sur erreur passagère (`infra/azure/reessai.sh`)                                    |
| Compétences illustrées | C21 (résoudre et documenter un incident), C13 (livraison continue), C18 (tests en CI)                    |

## Symptôme

Le job `production` échoue après avoir livré l'API, pendant la livraison de la console :

| Date (UTC)        | Exécution   | Fusion | API                        | Console                                              | Erreur d'Azure      |
| ----------------- | ----------- | ------ | -------------------------- | ---------------------------------------------------- | ------------------- |
| 16 octobre, 16:00 | 38927356517 | PR 114 | `0000042`, 100 % du trafic | Restée sur `0000041`                                 | Too Many Requests   |
| 19 octobre, 13:29 | 39259311534 | PR 124 | `0000050`, 100 % du trafic | Révision `0000049` créée, trafic resté sur `0000048` | Too Many Requests   |
| 21 octobre, 09:47 | 39578385655 | PR 153 | `0000066`, 100 % du trafic | Restée sur `0000063`                                 | Service Unavailable |

## Diagnostic

1. Les trois erreurs viennent d'Azure Resource Manager (réponse HTTP 429 ou 503 à une commande
   `az containerapp`), pas du code livré : aucune n'a été suivie d'un contrôle en échec.
2. `deployer.sh` s'arrête à la première commande `az` en erreur (`set -e`), sans distinguer une
   erreur passagère d'une erreur réelle.
3. Le script livre l'API puis la console. Un arrêt entre les deux laisse les deux applications sur
   des versions différentes ; la bascule de trafic par révision garde chaque application dans un
   état sain (la nouvelle révision de la console ne recevait aucun trafic).
4. La livraison suivante a chaque fois remis les deux applications sur la même version : le
   script livre l'image du commit, quel que soit l'état précédent.

## Cause racine

Aucune reprise sur les erreurs passagères d'Azure, alors que la livraison enchaîne une vingtaine de
commandes de gestion en quelques minutes. Les limites de débit d'Azure Resource Manager sont un
comportement documenté du service, pas une panne : un client doit les absorber.

## Effet sur les preuves du sprint

Le 21 octobre, les prompts hostiles de l'étape 11 ont été tirés depuis la console `0000063`, livrée
par la PR 152 (`8e2dd5d`). Le code de la console était identique à celui de `4151621` : la PR 153
ne modifiait que de la documentation. Les preuves de l'étape 11 restent valables.

## Correctif

`infra/azure/reessai.sh`, fonction `az_tenace` : sur une erreur passagère seulement (429, 503, 504),
la commande est relancée, jusqu'à 4 essais, avec une pause de 15 s, puis 30 s, puis 45 s. Toute
autre erreur est rendue tout de suite, comme avant. `deployer.sh` fait passer ses 11 commandes
`az containerapp` par cette fonction.

## Non-régression

`tests/test_livraison.py`, avec un faux `az` (aucun appel à Azure) : erreur passagère puis succès,
sortie inchangée ; erreur définitive rendue sans reprise ; erreur passagère persistante rendue
après 4 essais ; aucune commande `az containerapp` de `deployer.sh` hors de la reprise.

## Ce qui change dans la façon de travailler

Après chaque fusion, la livraison est suivie jusqu'à son verdict, pas seulement la CI de la PR.
C'est ce qui a manqué : les trois échecs étaient visibles dans l'historique, aucun n'a été vu
avant la clôture. Depuis la PR 159, chaque livraison est suivie jusqu'à `production` réussie.
