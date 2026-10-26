# INC-10 : livraisons interrompues par le miroir Ubuntu et par une révision dite invalide

| Champ                  | Valeur                                                                                                        |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| Date                   | 26 octobre 2026, de 13:40 à 15:16 UTC                                                                         |
| Environnement          | Workflow `ci` : PR 195 (run 40332499724) et fusion de la PR 196 sur `main` (run 40340545477)                  |
| Gravité                | Faible : aucune coupure ; pendant 4 minutes, l'API de production servait `74b1e55` et la console `a714586`    |
| Durée                  | Livraison de la PR 196 achevée à 15:16 UTC, 44 minutes après la fusion (14:32), au lieu d'environ 10          |
| Détection              | En suivant chaque livraison jusqu'à son verdict (pratique adoptée après INC-05)                               |
| Statut                 | Corrigé : limite du job `tests` portée à 30 minutes ; « is not a valid revision name » repris par `az_tenace` |
| Compétences illustrées | C21 (résoudre et documenter un incident)                                                                      |

## Symptômes

1. Deux fois, le job `tests` est arrêté à sa limite de 15 minutes (« The operation was canceled »),
   avant ou pendant pytest. Le verdict échoue, la livraison n'a pas lieu.
2. Après relance du job, la livraison en production s'arrête sur la console :

```
== ca-muninn-console-prod : révision en service ca-muninn-console-prod--0000095
ERROR: Revision 'ca-muninn-console-prod--0000095' is not a valid revision name.
```

## Diagnostic

1. Durée des étapes du job `tests`, lue dans les journaux : l'étape « Navigateur du contrôle
   d'accessibilité » (`playwright install --with-deps chromium`, paquets Ubuntu) a pris 13 min 8 s
   (run 40332499724, première tentative) et plus de 15 minutes (run 40340545477), contre 21 s
   d'ordinaire. Les paquets arrivaient de `azure.archive.ubuntu.com` en 10 à 90 s chacun. Les
   tests eux-mêmes durent 1 min 30 s. La relance du run 40340545477 a fini en 14 min 59 s.
2. Lecture des révisions de la console de production juste après l'échec : `0000095` existait,
   active, à 100 % du trafic. Le message d'Azure était donc faux ; la relance du seul job
   `production` a livré la console (`0000096`) sans changement de code, l'API déjà livrée étant
   ignorée sans erreur (INC-03).

## Causes racines

- Limite de 15 minutes trop proche de la durée du job quand le miroir Ubuntu est lent.
- Réponse incohérente passagère d'Azure Resource Manager, absente des motifs de reprise
  d'`az_tenace` (INC-05, INC-08).

## Correctifs

- `.github/workflows/ci.yml` : limite du job `tests` de 15 à 30 minutes.
- `infra/azure/reessai.sh` : « is not a valid revision name » ajouté aux erreurs passagères ; une
  erreur réelle échoue quand même après les essais. `tests/test_livraison.py` rejoue le message
  exact.

## Reste à surveiller

Une mise en cache des dépendances du navigateur supprimerait l'attente sur le miroir ; non faite,
la limite plus large suffisant au rythme actuel des livraisons.
