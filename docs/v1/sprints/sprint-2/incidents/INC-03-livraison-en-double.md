# INC-03 : livraison en échec sur un commit déjà livré

| Champ                  | Valeur                                                                                        |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| Date                   | 14 octobre 2026 ; détecté le 15 octobre 2026, en préparant la démonstration du sprint 2       |
| Environnement          | Chaîne de livraison, job `preproduction`                                                      |
| Gravité                | Faible : rien de servi n'a changé ; une exécution rouge apparaît dans le journal de la chaîne |
| Durée                  | Exécution en échec le 14 octobre à 16:28 UTC ; correctif fusionné le 15 octobre               |
| Statut                 | Résolu                                                                                        |
| Compétences illustrées | C21 (résoudre et documenter un incident), C13 et C19 (livraison continue)                     |

## Symptôme

Deux exécutions de la chaîne sont parties pour le même commit `e184fd0`, fusion de la PR n° 21 :

| Exécution   | Créée à (UTC) | Résultat                                                 |
| ----------- | ------------- | -------------------------------------------------------- |
| 38596675377 | 16:16:32      | Réussie : `e184fd0` livré en préproduction et production |
| 38596692823 | 16:16:40      | Échec du job `preproduction` ; `production` ignoré       |

Journal de la seconde : `Aucune nouvelle révision créée pour ca-muninn-api-preprod`, sortie en
erreur.

## Diagnostic

1. Les deux exécutions ont l'événement `push`, le même SHA et la même heure de commit (16:16:28).
2. Le journal d'activité de `main` (`gh api repos/Bealph/Muninn/activity`) enregistre deux fois la
   même fusion `be1fb24` vers `e184fd0`, à la même seconde. Il n'y a pas eu de seconde poussée de
   ma part : GitHub a émis deux événements `push` identiques. La raison n'est pas déterminée.
3. Le verrou de livraison (`concurrency`, sans annulation) a fait attendre la seconde exécution.
   Quand elle a démarré, `e184fd0` était déjà en service.
4. `az containerapp update` avec une image et des variables identiques ne crée pas de révision.
   Le script `deployer.sh` traitait ce cas comme une erreur.

## Cause racine

Le script de livraison n'était pas idempotent : livrer une seconde fois le commit déjà en service
échouait, alors que l'état voulu était déjà atteint. Le double événement de GitHub n'a fait que
révéler ce défaut ; une relance manuelle du job l'aurait révélé aussi.

## Correctif

`infra/azure/deployer.sh`, étape 0 de `livrer()` : si la révision en service porte déjà l'image
`muninn:<sha>` demandée, le script l'annonce (« déjà en service : rien à livrer ») et passe à
l'application suivante. Les contrôles finaux par l'adresse publique (`/health`, puis `/version`
qui doit rendre ce SHA) s'exécutent toujours.

Le cas « aucune nouvelle révision » reste une erreur quand l'image en service est différente :
il signale alors une anomalie réelle.

Le cas après un retour arrière n'est pas touché : la révision en service porte l'ancienne image,
la livraison du dernier commit se poursuit normalement.

## Vérification

- La requête qui lit l'image de la révision en service a été essayée en lecture seule sur la
  production : elle rend `crmuninn.azurecr.io/muninn:a54301e…`.
- Contrôle des options `az` des scripts (`verifier-options.py`) : aucune option absente.
- Livraison normale de la fusion du correctif (PR n° 26, commit `43d969d`, exécution
  38702093700, tentative 1) : tous les jobs verts ; nouvelle révision créée, contrôlée et mise en
  service en préproduction et en production. Le chemin habituel n'a pas changé.
- Relance des jobs de livraison de la même exécution (tentative 2, le 15 octobre 2026 à
  08:04 UTC), le commit étant déjà en service :

  ```text
  preproduction | crmuninn.azurecr.io/muninn:43d969dc… déjà en service : rien à livrer
  preproduction | Livré en preproduction : 43d969dc106413f545396e8a7385cf1aa3cc4c3d
  production    | crmuninn.azurecr.io/muninn:43d969dc… déjà en service : rien à livrer
  production    | Livré en production : 43d969dc106413f545396e8a7385cf1aa3cc4c3d
  ```

  Les deux jobs réussissent (1 min 18 s et 45 s). Avant et après la relance, chacune des quatre
  applications compte 19 révisions et sert la même (`--0000018`) : aucune révision créée, aucun
  trafic déplacé. `/version` en production rend `43d969d`.

## Non-régression

Toute relance d'une livraison du commit en service réussit sans rien changer. Ne jamais relancer
l'exécution en échec 38596692823 : elle livrerait `e184fd0`, un commit ancien.

## Ce qui change dans la façon de travailler

Un script de livraison doit être rejouable : le relancer sur l'état qu'il vise ne doit ni échouer
ni rien changer.
