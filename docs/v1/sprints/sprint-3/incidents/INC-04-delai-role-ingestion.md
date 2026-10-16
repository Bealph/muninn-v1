# INC-04 : première exécution de la tâche des données annulée par un délai

| Champ                  | Valeur                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------- |
| Date                   | 16 octobre 2026                                                                                   |
| Environnement          | Préproduction, tâche `job-muninn-donnees-preprod`, exécution `job-muninn-donnees-preprod-x1f19gl` |
| Gravité                | Faible : la version du COG a été annulée en bloc ; l'API n'a pas été touchée                      |
| Durée                  | Environ 25 min, de l'échec à la livraison du correctif (PR n° 41)                                 |
| Statut                 | Résolu                                                                                            |
| Compétences illustrées | C21 (résoudre et documenter un incident), C4 (base et import), C13 (tests)                        |

## Symptôme

La tâche des données réussit ses migrations et crée les deux rôles de connexion, puis l'ingestion
échoue au chargement du COG :

```text
3/3 Ingestion, avec le rôle d'écriture
  File ".../muninn/ingestion/cog.py", line 98, in controler
    orphelines = valeur(
psycopg.errors.QueryCanceled: canceling statement due to statement timeout
```

## Diagnostic

1. La requête annulée est le contrôle VD-11 (communes déléguées sans commune parente), qui
   parcourt les 37 496 communes de la version.
2. Le rôle `<base>_ingestion` avait reçu `statement_timeout = 5s`, comme le rôle de l'API :
   `src/muninn/db/roles.py` appliquait le même délai aux deux rôles.
3. Sur le serveur Burstable B1ms, sans statistiques encore calculées sur les tables tout juste
   remplies, la requête dépasse 5 s. Sur le poste, elle prend une fraction de seconde : les tests
   ne pouvaient pas le voir.

## Cause racine

Un réglage pensé pour l'API (des lectures courtes, sur un service public) a été appliqué au rôle
d'ingestion, dont les contrôles portent sur des dizaines de milliers de lignes.

## Correctif

PR n° 41 : chaque rôle reçoit son propre délai. `<base>_api` garde 5 s, en lecture seule ;
`<base>_ingestion` reçoit 15 min, borné. Le réglage est réécrit à chaque passage de la tâche, ce
qui a corrigé le rôle déjà créé.

## Vérification

Exécution `job-muninn-donnees-preprod-puq2mss`, après la livraison du correctif : réussie en
5 min 27 s ; jeu de questions à 10 sur 10. Même résultat en production
(`job-muninn-donnees-prod-qneei67`, 5 min 24 s).

## Non-régression

`tests/test_donnees.py` vérifie le délai et le mode de chaque rôle : 5 s et lecture seule pour
l'API, 15 min et écriture pour l'ingestion.

## Ce qui change dans la façon de travailler

Un réglage de sécurité se pose rôle par rôle, d'après ce que chacun fait. Une mesure locale ne
dit rien de la durée sur le serveur de production : la première exécution s'y fait en
préproduction.
