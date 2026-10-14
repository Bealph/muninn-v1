# INC-02 : première livraison bloquée à la connexion Azure (OIDC)

| Champ                  | Valeur                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------- |
| Date                   | 14 octobre 2026                                                                         |
| Environnement          | Chaîne de livraison, job `preproduction` (sprint 2, étape 6)                            |
| Gravité                | Faible : la livraison s'est arrêtée avant toute modification ; rien de servi n'a changé |
| Durée                  | Environ 13 minutes, de l'échec (08:27 UTC) à la livraison réussie (08:40 UTC)           |
| Statut                 | Résolu                                                                                  |
| Compétences illustrées | C21 (résoudre et documenter un incident), C13 et C19 (livraison continue)               |

## Symptôme

Première exécution de la livraison après fusion dans `main` (exécution 38535062251) : le job
`preproduction` échoue en 15 secondes à l'étape `azure/login`, avec l'erreur `AADSTS700213: No
matching federated identity record found for presented assertion subject`. Le job `production`
est ignoré.

## Diagnostic

1. Le journal de l'action affiche le sujet présenté par GitHub :
   `repo:Bealph@60009382/Muninn@1415464389:environment:preproduction`.
2. La confiance de l'identité `id-muninn-deploiement` attendait
   `repo:Bealph/Muninn:environment:preproduction`.
3. `gh api repos/Bealph/Muninn/actions/oidc/customization/sub` confirme que le dépôt utilise le
   sujet « immuable » (`use_immutable_subject: true`), qui inclut les identifiants numériques du
   compte et du dépôt.

## Cause racine

Le format du sujet avait été pris dans la documentation générale de GitHub, qui décrit le format
classique, sans lire le réglage réel du dépôt. Azure exige une correspondance exacte du sujet.

## Correctif

PR n° 8 : le format immuable est conservé, car il empêche un dépôt supprimé puis recréé sous le
même nom d'hériter de la confiance. Le script `infra/azure/oidc-github.sh` crée la confiance ou
corrige son sujet ; le préfixe du sujet est déclaré dans `parametres.sh`, avec la commande qui le
lit. Le porteur a lancé le script : les deux confiances ont été corrigées.

## Vérification

Exécution 38535838557, déclenchée par la fusion de la PR n° 8 : tous les jobs sont verts, de
`lint` à `production`. Les adresses publiques de préproduction et de production servent le SHA
`bdd30f66`, et la révision précédente de chaque application reste active à 0 % du trafic.

## Non-régression

Le script 03 appelle désormais `oidc-github.sh` : une reconstruction crée la confiance avec le bon
sujet. Toute dérive est visible au premier job de livraison, qui échoue avant de toucher Azure.

## Ce qui change dans la façon de travailler

Pour un réglage d'un service tiers, lire la configuration réelle (API, réglage du dépôt) en plus de
la documentation générale.
