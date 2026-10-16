# Preuve de la mise en production des données (sprint 3, étape 10)

**Date :** 16 octobre 2026.
**Résultat :** en préproduction et en production, la tâche des données a installé les schémas,
créé les rôles et chargé les cinq sources ; l'API lit avec le rôle `<base>_api`, en lecture
seule ; le jeu de 10 questions de démonstration passe à 10 sur 10 contre l'API publique ; le
rejeu en une commande ne crée aucune version.

## Mise en place, par le porteur (`infra/azure/05-donnees.sh`)

| Environnement | Exécution de la tâche                | Durée      | API basculée sur     | Jeu de questions |
| ------------- | ------------------------------------ | ---------- | -------------------- | ---------------- |
| Préproduction | `job-muninn-donnees-preprod-puq2mss` | 5 min 27 s | `muninn_preprod_api` | 10 sur 10        |
| Production    | `job-muninn-donnees-prod-qneei67`    | 5 min 24 s | `muninn_prod_api`    | 10 sur 10        |

Le rôle utilisé par chaque API a été relu dans son secret de connexion, sans afficher le mot de
passe. L'API n'utilise plus le compte administrateur du serveur (D-56).

## Deux échecs avant la réussite, en préproduction

| Exécution                            | Cause                                                                                                 | Correction                                                       |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `job-muninn-donnees-preprod-94jens6` | Mot de passe administrateur fourni au script incorrect : connexion refusée                            | Mot de passe repris du secret de l'API, sans l'afficher          |
| `job-muninn-donnees-preprod-x1f19gl` | Délai de 5 s imposé aussi au rôle d'ingestion : contrôle VD-11 du COG annulé sur le serveur Burstable | Délai de 5 s réservé à l'API, 15 min pour l'ingestion (PR n° 41) |

Dans les deux cas, rien n'a été écrit à moitié (transaction annulée) et l'API n'a pas été
touchée : le script s'arrête avant de la basculer.

## Rejeu en une commande, sans le poste (critère P4)

```bash
gh workflow run donnees -f environnement=production
```

Exécution GitHub Actions 38874739291 : tâche `job-muninn-donnees-prod-mjab2v3` réussie en 83 s,
puis jeu de questions à 10 sur 10. Journal de la tâche : les cinq sources « inchangée, même
empreinte que la dernière version ; aucune version créée ».

## L'écran de production

Console de production, `/referentiels`, le 16 octobre 2026 :

- `etape-10-production-commune.png` : « Montreuil », trois communes, références en base, source
  citée (COG 2026, chargé le 16/10/2026 à 08:24 UTC) ;
- `etape-10-production-refus.png` : « ordinateur » en plomberie, refus hors corpus.

## Chaîne de livraison

À la livraison du commit `c198dd8`, la chaîne a mis à jour l'image de la tâche de préproduction
(`== job-muninn-donnees-preprod : image c198dd8…`) : le droit « Container Apps Jobs Contributor »
de l'identité de déploiement est effectif.
