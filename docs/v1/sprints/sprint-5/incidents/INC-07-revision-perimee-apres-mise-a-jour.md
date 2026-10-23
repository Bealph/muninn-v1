# INC-07 : trafic basculé sur l'ancienne révision après une mise à jour de configuration

| Champ                  | Valeur                                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| Date                   | 23 octobre 2026, 09:07 UTC                                                                                 |
| Environnement          | Production, API `ca-muninn-api-prod`, script `infra/azure/09-observabilite.sh` lancé à la main             |
| Gravité                | Faible : service rendu sans interruption par une révision saine ; traces absentes en production            |
| Durée                  | Jusqu'à la relance du script corrigé                                                                       |
| Détection              | Le jour même, en relisant la sortie du script : « 100 % sur `0000082` (précédente conservée : `0000082`) » |
| Statut                 | Corrigé par la fonction `nouvelle_revision` (`infra/azure/reessai.sh`)                                     |
| Compétences illustrées | C21 (résoudre et documenter un incident), C13 (livraison continue), C18 (tests en CI)                      |

## Symptôme

Le script `09-observabilite.sh` pose la chaîne de connexion d'Application Insights sur l'API de
chaque environnement, puis bascule le trafic sur la nouvelle révision après un contrôle :

| Environnement | Révision en service avant | Révision créée | Trafic après le script | Chaîne de connexion sur la révision en service |
| ------------- | ------------------------- | -------------- | ---------------------- | ---------------------------------------------- |
| Préproduction | `0000082`                 | `0000083`      | `0000083`, 100 %       | oui                                            |
| Production    | `0000082`                 | `0000083`      | `0000082`, 100 %       | non                                            |

En production, la révision `0000083` portait la variable, mais ne recevait aucun trafic.

## Diagnostic

1. Le script prenait le nom de la nouvelle révision dans la réponse de
   `az containerapp update … --query properties.latestRevisionName`.
2. En production, cette réponse a rendu `0000082`, la révision en service. Relu quelques minutes
   plus tard par `az containerapp show`, le même champ valait `0000083`. La réponse de `update`
   était donc périmée, de façon passagère. Le même appel a rendu le bon nom en préproduction.
3. Le script a contrôlé `0000082`, qui est saine, puis a figé le trafic sur elle. Aucune erreur
   n'a été levée. Seule la ligne « précédente conservée : `0000082` », identique à la révision en
   service, trahissait le défaut.
4. Les scripts `07-langfuse.sh` et `08-traitements.sh` lisaient le nom de la même façon, sans
   garde-fou. `deployer.sh` s'arrêtait si le nom rendu était celui de la révision en service : il
   échouait sans dommage, puis contrôlait le SHA livré.

## Cause racine

Le nom de la nouvelle révision était pris dans la réponse d'une commande de modification, sans
être relu sur l'application, et sans vérifier que la révision rendue portait la modification
demandée.

## Correctif

`infra/azure/reessai.sh`, fonction `nouvelle_revision <application> <révision en service>
[condition]` :

- le nom est relu sur l'application (`az containerapp show`), jusqu'à 24 fois, à 5 s d'intervalle ;
- il n'est rendu que s'il diffère de la révision en service et que la révision vérifie la
  condition (variable posée, ou image livrée pour `deployer.sh`) ;
- sinon, la fonction échoue sans rien basculer : le trafic reste sur la révision en service.

Les quatre scripts concernés (`deployer.sh`, `07`, `08`, `09`) l'utilisent. Relancer l'un d'eux
après un échec ou après cet incident est sans risque : la révision déjà créée est retrouvée,
contrôlée, puis mise en service.

Les trois conditions ont été évaluées sur les révisions réelles de la production avant la
correction : elles rendent `true` pour `0000083` et `false` pour `0000082` (chaîne de connexion),
`true` pour une image identique et `false` pour une autre.

## Non-régression

`tests/test_livraison.py`, avec un faux `az` (aucun appel à Azure) :

- réponse périmée, puis nouvelle révision : le bon nom est rendu après relecture ;
- aucune nouvelle révision : échec, aucun nom rendu ;
- révision plus récente sans la modification voulue : refusée ;
- relance : la révision déjà créée est retrouvée ;
- aucun des quatre scripts ne lit plus `latestRevisionName`.

Un essai de mutation a été fait : deux défauts ont été introduits exprès dans la fonction, et
chacun a été détecté par au moins un test.

## Remise en état de la production

La variable a été posée sur le modèle de l'application : `0000083` la porte. La livraison qui suit
la fusion du correctif crée sa révision à partir de ce modèle ; la production reçoit donc la chaîne
de connexion sans autre action.

Le script `09` est rendu relançable : si la révision en service porte déjà la variable, il ne
change rien et passe à l'appel de contrôle. Sinon, il crée la révision, ou retrouve celle déjà
créée, puis la contrôle et y bascule le trafic. On le relance après la livraison pour le vérifier.

## Ce qui change dans la façon de travailler

Une sortie de script se relit en entier, même quand le script finit sans erreur. C'est une ligne
incohérente, et non un code de retour, qui a révélé l'incident.
