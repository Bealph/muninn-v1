# Preuve du retour arrière en une opération (sprint 2, étape 8, critère P4)

**Date :** 14 octobre 2026
**Résultat :** quatre bascules en production, toutes réussies : deux retours arrière vers la
version précédente et deux rétablissements vers la dernière version. Chaque bascule est une seule
opération (un lancement du workflow `retour-arriere`) et se vérifie en moins de 70 secondes.

## Protocole, fixé avant l'essai

1. Point de départ : la production sert la dernière livraison, `fe944e1` (fusion de la PR n° 12).
2. Retour arrière vers la version précédente : `gh workflow run retour-arriere -f
   environnement=production`.
3. Rétablissement de la dernière version par son SHA : `... -f sha=fe944e1...`.
4. Répéter les étapes 2 et 3.
5. Pour chaque bascule, relever :
   - la durée mesurée par le script, du début à la bascule du trafic, puis jusqu'à ce que
     l'adresse publique serve le commit visé ;
   - la durée totale vue du poste, du déclenchement à la fin du workflow ;
   - le commit servi, lu après coup sur `/version`, indépendamment du workflow.

Le mécanisme ne reconstruit aucune image et ne crée aucune révision : il ramène 100 % du trafic de
l'API et de la console sur des révisions déjà présentes (`infra/azure/retour-arriere.sh`).

## Mesures

| N°  | Opération                | Exécution   | Commit servi après | Bascule du trafic (s) | Service vérifié (s) | Total vu du poste (s) |
| --- | ------------------------ | ----------- | ------------------ | --------------------- | ------------------- | --------------------- |
| 1   | Retour arrière           | 38542548307 | `d0f201d`          | 38                    | 66                  | 103                   |
| 2   | Rétablissement (par SHA) | 38542779762 | `fe944e1`          | 40                    | 43                  | 82                    |
| 3   | Retour arrière           | 38542965592 | `d0f201d`          | 33                    | 36                  | 81                    |
| 4   | Rétablissement (par SHA) | 38543138064 | `fe944e1`          | 37                    | 40                  | 81                    |

Lecture :

- La bascule du trafic prend de 33 à 40 s : ce sont les appels à l'API Azure (lecture des
  révisions, puis bascule, pour l'API et pour la console).
- Le service est vérifié en 36 à 66 s. Le cas le plus long (66 s) est le premier ; explication
  probable, non vérifiée : la révision visée était au repos (zéro réplique) et a dû démarrer.
- Le total vu du poste, environ 80 à 100 s, ajoute le démarrage du runner GitHub et la connexion
  à Azure.

Quatre mesures ne suffisent pas pour une statistique : ces durées sont des ordres de grandeur, pas
une garantie de service.

## Extrait du journal (exécution 38542548307)

```text
Retour arrière en production vers d0f201dec08ee8ecbdd158dbc36565c4e1175f3f
   ca-muninn-api-prod : 100 % sur ca-muninn-api-prod--0000003
   ca-muninn-console-prod : 100 % sur ca-muninn-console-prod--0000003
Retour arrière vérifié : https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io sert d0f201dec08ee8ecbdd158dbc36565c4e1175f3f
Durée : bascule du trafic 38 s, jusqu'au service vérifié 66 s
```

## Pour la démonstration en direct

1. Ouvrir la console de production : elle affiche le SHA servi.
2. Lancer `gh workflow run retour-arriere -f environnement=production`, ou passer par l'onglet
   Actions, puis « retour-arriere » et « Run workflow ».
3. Environ 1 min 30 plus tard, recharger la console : elle affiche le SHA précédent.
4. Rétablir avec `-f sha=<dernier SHA>`.

Avant une démonstration, passer la révision servie à une réplique minimum, pour éviter le
démarrage à froid.
