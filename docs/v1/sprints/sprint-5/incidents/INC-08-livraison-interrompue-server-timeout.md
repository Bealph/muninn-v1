# INC-08 : livraison interrompue par une expiration côté Azure (ServerTimeout)

| Champ                  | Valeur                                                                                                        |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| Date                   | 26 octobre 2026, 09:08 UTC                                                                                    |
| Environnement          | Préproduction, job `preproduction` du workflow `ci` (run 40296513654, PR 190), `deployer.sh`                  |
| Gravité                | Faible : aucune coupure ; le trafic est resté sur la révision précédente, la production n'a pas été livrée    |
| Durée                  | Environ 11 minutes : erreur à 09:08, livraison réussie à 09:19 après relance du job (`gh run rerun --failed`) |
| Détection              | Le jour même, en suivant la livraison jusqu'à son verdict (pratique adoptée après INC-05)                     |
| Statut                 | Corrigé : `ServerTimeout` ajouté aux erreurs passagères reprises par `az_tenace`                              |
| Compétences illustrées | C21 (résoudre et documenter un incident), C13 (livraison continue), C18 (tests en CI)                         |

## Symptôme

```
   nouvelle révision ca-muninn-api-preprod--0000094
ERROR: (ServerTimeout) The request timed out. Diagnostic information: timestamp '20261026T090841Z', …
##[error]Process completed with exit code 1.
```

État constaté ensuite : la révision `0000094` (nouvelle image) existait sans trafic ; `0000093`
(version précédente) gardait 100 % du trafic, en préproduction comme en production.

## Diagnostic

1. Entre « nouvelle révision » et l'erreur, `deployer.sh` ne lance qu'une commande `az` : la
   bascule du trafic (`az containerapp ingress traffic set`). Les contrôles de la révision, faits
   par `curl` (santé, SHA livré, appel réel au modèle), étaient passés.
2. `ServerTimeout` est une expiration côté Azure Resource Manager, comme les 429 et 503 d'INC-05 :
   une erreur passagère, pas un défaut du code livré. La relance du job, sans changement, a réussi.
3. `az_tenace` ne reprenait que « Too Many Requests », « Service Unavailable », « Gateway
   Timeout » et les codes 429, 503, 504 : le message `ServerTimeout` n'y figurait pas.

## Cause racine

Liste incomplète des erreurs passagères d'Azure dans la reprise d'INC-05.

## Correctif

`infra/azure/reessai.sh` : `ServerTimeout` est ajouté aux motifs repris. La bascule du trafic est
idempotente (elle fixe un poids, sans rien créer) : la reprendre est sans risque.

## Non-régression

`tests/test_livraison.py` : le message exact du 26 octobre est rejoué par le faux `az` ; la commande
est reprise puis réussit.

## Ce qui a bien marché

Le garde-fou de la livraison : un échec après la création de la révision laisse le trafic sur
l'ancienne. Personne n'a été servi par une révision non basculée, et l'exercice de panne prévu
juste après a été retardé jusqu'à la fin de la livraison, pour ne pas mêler deux changements.
