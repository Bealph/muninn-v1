# INC-01 : serveur PostgreSQL non créé par le script du socle

| Champ                  | Valeur                                                                    |
| ---------------------- | ------------------------------------------------------------------------- |
| Date                   | 14 octobre 2026                                                           |
| Environnement          | Azure, préproduction et production (création initiale, sprint 2, étape 5) |
| Gravité                | Moyenne : aucune donnée, aucun service en production touché               |
| Durée                  | De la création des ressources à la relance du script, le même jour        |
| Statut                 | Résolu                                                                    |
| Compétences illustrées | C21 (résoudre et documenter un incident), C19 (livraison)                 |

## Symptôme

Les applications Container Apps répondaient, mais le serveur `psql-muninn` n'existait pas.
Détecté lors de la vérification en lecture seule qui suit la création : `az postgres
flexible-server show` rendait `ResourceNotFound`.

## Diagnostic

1. Le journal d'activité Azure du groupe ne montrait aucune tentative de création PostgreSQL :
   la commande n'avait pas atteint Azure.
2. Les attributions de rôles de l'étape 5/7 du script étaient toutes présentes : le script
   s'était donc arrêté à l'étape 6/7.
3. L'aide de la version locale d'`az` (2.89.1) montrait que deux options utilisées n'existaient
   plus : `--high-availability` (remplacée par `--zonal-resiliency`) pour la création du serveur,
   et `-d` (remplacée par `--name`) pour la création des bases.

## Cause racine

Les scripts avaient été relus contre la documentation Microsoft, pas contre l'aide de la version
d'`az` installée. `az` a refusé la commande avant tout appel à Azure. Facteur aggravant : le
script 03 ne vérifiait pas la présence du serveur, si bien que les scripts suivants ont été lancés
et ont réussi, masquant l'arrêt du script 01.

## Correctif

PR n° 4 (`infra/azure/01-socle.sh`, `infra/azure/03-applications.sh`) :

- options remplacées par leurs équivalents actuels ;
- le script 03 refuse de s'exécuter si le serveur PostgreSQL manque ;
- le script 03 réécrit le secret `database-url` à chaque passage, pour qu'un nouveau mot de passe
  ne laisse pas les applications avec l'ancien.

Relance des scripts 01 et 03 par le porteur ; aucune ressource existante n'a été recréée.

## Vérification

- Serveur `psql-muninn` : prêt, version 16, B1ms, 32 Go, TLS exigé, bases `muninn_preprod` et
  `muninn_prod`, règle de pare-feu « services Azure ».
- Connexion réelle depuis chaque application d'API, par son secret : `muninn_preprod` et
  `muninn_prod` atteintes, en TLS (`ssl=True`).

## Non-régression

`infra/azure/verifier-options.py` contrôle, sans rien créer, chaque option des commandes `az`
des scripts contre l'aide de la version locale, sous-commandes `$(...)` comprises. Il est lancé
avant les scripts (procédure de `infra/azure/README.md`). Contrôle du contrôle : il détecte les
trois défauts sur l'ancienne version du script 01, une option inventée placée dans une
sous-commande, et aucune anomalie sur les scripts corrigés.

## Ce qui change dans la façon de travailler

- Toute commande d'outil tiers est vérifiée contre l'aide de la version installée, en plus de la
  documentation en ligne.
- Un script qui dépend d'une ressource vérifie qu'elle existe avant d'agir.
