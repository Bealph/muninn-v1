# INC-11 : `unknown_service` sur chaque observation des traces Langfuse

| Champ                  | Valeur                                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| Date                   | Relevé le 29 octobre 2026, après la clôture du sprint 5 ; défaut présent depuis le 21 octobre (V-13)     |
| Environnement          | Préproduction et production, API, projet Langfuse `muninn`                                               |
| Gravité                | Faible : aucune perte de trace ni de mesure ; service émetteur non identifiable dans Langfuse            |
| Durée                  | Du 21 octobre (PR n° 151) au 29 octobre, livraison de la PR n° 202 en préproduction puis en production   |
| Détection              | Manuelle : lecture d'une trace de production dans Langfuse, pendant la séance d'observabilité            |
| Statut                 | Corrigé dans le code, avec un test de non-régression (PR n° 202, commit `6f63267`)                       |
| Compétences illustrées | C21 (résoudre et documenter un incident), C11 (monitorer le modèle), C18 (tests en CI)                   |

## Symptôme

Dans Langfuse, chaque observation d'une trace de production affichait, dans ses attributs de
ressource, `service.name = unknown_service`. Les durées, les jetons et les coûts étaient justes ;
seule l'identité du service émetteur manquait.

## Diagnostic

1. `unknown_service` est la valeur par défaut d'OpenTelemetry quand un `TracerProvider` est créé
   sans ressource.
2. `src/muninn/observabilite.py` crée pour Langfuse un `TracerProvider` isolé, volontairement
   distinct du fournisseur global d'Application Insights (V-13, PR n° 151, 21 octobre) :
   `TracerProvider()`, sans argument.
3. La ressource existait déjà : `telemetrie.ressource()`, qui porte `service.name = muninn-api`,
   `service.namespace` = environnement et `service.version` = SHA livré, mais seul le
   fournisseur global, celui d'Application Insights, la recevait.

## Cause racine

Le fournisseur isolé a été créé sans ressource. Aucun test ne vérifiait les attributs de ressource
des traces envoyées à Langfuse : les tests de V-13 portaient sur le contenu des observations
(aucune donnée personnelle), sur la robustesse (une trace en échec ne fait pas échouer l'appel)
et sur le projet de destination, pas sur l'émetteur.

## Correctif

`src/muninn/observabilite.py` : `TracerProvider(resource=ressource())`. Le fournisseur reste isolé,
jamais global ; aucune mesure ne change.

## Non-régression

`tests/test_observabilite.py`, test `test_traceur_isole_porte_le_nom_du_service` : le client
Langfuse est remplacé par une doublure qui capture le `tracer_provider` reçu ; le test exige
`service.name = muninn-api` et `service.namespace = production`. Il échoue sans la correction
(`'unknown_service' == 'muninn-api'`) et passe avec.

## Remise en service

La PR n° 202 a été fusionnée le 29 octobre 2026 à 16:56 UTC. La livraison continue qui a suivi a
réussi en préproduction puis en production (lint, tests, build, évaluation, verdict, préproduction,
production).

Vérifié le 2 novembre 2026 dans le projet Langfuse `muninn`, par son API publique, en lecture
seule : la première observation de chaque trace d'un échantillon, de part et d'autre de la
livraison du correctif. Mesure rejouable : `uv run python eval/production/service_langfuse.py`.

| Trace (UTC)          | Environnement | `service.name`    | Par rapport au correctif |
| -------------------- | ------------- | ----------------- | ------------------------ |
| 2 novembre, 10:59    | production    | `muninn-api`      | après                    |
| 30 octobre, 14:20    | production    | `muninn-api`      | après                    |
| 30 octobre, 14:17    | production    | `muninn-api`      | après                    |
| 27 octobre, 11:42    | production    | `unknown_service` | avant                    |
| 26 octobre, 18:04    | production    | `unknown_service` | avant                    |

La trace du 27 octobre à 11:42 est la dernière avant le correctif : la trace lue le 29 octobre
était sans doute celle-là, ce qui expliquerait la date du 27 octobre citée par le test.

## Ce qui change dans la façon de travailler

Un composant qui crée son propre fournisseur de traces reçoit la même ressource que le fournisseur
global, et un test le vérifie. Lire une trace réelle de bout en bout, et pas seulement les
chiffres agrégés, a révélé ce défaut : la séance d'observabilité sur la production en est la
détection.
