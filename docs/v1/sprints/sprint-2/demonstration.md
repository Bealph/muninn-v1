# Démonstration du sprint 2 devant l'évaluateur

**But :** faire constater par l'évaluateur, en direct, chacun des six critères de l'évaluation par
le pair. Pour chaque critère : ce que l'évaluateur constate, ce que je fais, la durée, et la preuve
versionnée qui sert de secours si le direct échoue.

**Adresses de production :**

- console : <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io> ;
- API : <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/version>.

## 1. Préparation, la veille ou 15 minutes avant

1. Ouvrir la console et `/version` une première fois, puis 5 minutes avant de commencer. Hors
   trafic, l'application s'endort et le premier appel peut attendre plus de 20 secondes (constaté
   le 15 octobre 2026).
2. Vérifier que `/version` rend le dernier commit de `main` (`git log -1 origin/main`).
3. Préparer une petite PR inoffensive à fusionner en direct (une ligne de documentation), avec un
   `verdict` déjà vert.
4. Préparer en local, sans la pousser, une branche `demo/commit-casse` qui casse
   `test_api_version` (même régression que la PR n° 10).
5. Ouvrir dans le navigateur : la PR n° 10, l'onglet Actions, la page de protection de `main`.

## 2. Ordre de passage

La livraison prend de 8 à 10 minutes : je la lance en premier et je la laisse tourner pendant les
critères suivants. Le retour arrière vient en dernier, une fois la livraison terminée : jamais de
retour arrière pendant une livraison.

| Ordre | Critère | Durée en direct | Ce qui tourne en arrière-plan |
| ----- | ------- | --------------- | ----------------------------- |
| 1     | P2      | 1 min           | Livraison lancée (8 à 10 min) |
| 2     | P1      | 2 min           | Livraison                     |
| 3     | P3      | 3 min           | Livraison                     |
| 4     | P5      | 3 min           | Livraison                     |
| 5     | P6      | 3 min           | Livraison                     |
| 6     | P2, fin | 1 min           | Aucun                         |
| 7     | P4      | 4 min           | Aucun                         |

## 3. Les six critères

### P1. Le squelette tourne ailleurs que sur ma machine

- **L'évaluateur constate :** sur son propre appareil, il ouvre l'adresse de la console de
  production. La page s'affiche et un essai du modèle répond. `/version` rend le SHA du commit
  servi et `environment: production`.
- **Je fais :** je lui donne l'adresse, je ne touche pas à son appareil. Je montre que le SHA lu
  est celui du dernier commit de `main` sur GitHub.
- **Secours :** `compte-rendu.md`, section 1 ; captures `preuves/etape-2-console-*.png`.

### P2. Une fusion déclenche la livraison sans action manuelle

- **L'évaluateur constate :** je fusionne la PR préparée. Dans l'onglet Actions, une exécution
  démarre seule, déclenchée par l'événement `push` sur `main`. Elle enchaîne `verdict`,
  `preproduction`, puis `production`, sans approbation ni commande. Au retour (étape 6), `/version`
  en production rend le SHA de la fusion.
- **Je fais :** un clic sur « Merge », puis plus rien jusqu'au constat.
- **Secours :** le journal de la chaîne, par exemple l'exécution 38600429784 du 14 octobre 2026
  (fusion de la PR n° 24 livrée en production en 9 min 17 s, tous jobs verts) ; six livraisons
  automatiques consignées dans `compte-rendu.md`, section 4.
- **À dire si l'évaluateur la remarque :** l'exécution rouge du 14 octobre 2026 à 16 h 16
  (38596692823) est un second déclenchement pour le même commit `e184fd0`, déjà livré 8 secondes
  plus tôt par l'exécution 38596675377. Le script de livraison refusait alors de redéployer une
  version identique ; la production n'a pas été touchée. Défaut corrigé et documenté :
  `incidents/INC-03-livraison-en-double.md`.

### P3. Un commit cassé est bloqué

- **L'évaluateur constate :** je pousse la branche `demo/commit-casse` et j'ouvre sa PR. Environ
  1 min 30 plus tard, `tests` échoue sur `test_api_version`, `verdict` est rouge et marqué
  « Required », le bouton de fusion est désactivé. La règle de protection de `main` inclut les
  administrateurs.
- **Je fais :** `git push -u origin demo/commit-casse`, puis `gh pr create`. Pendant l'attente, je
  montre la PR n° 10, bloquée de la même façon depuis le 14 octobre. Après le constat, je ferme la
  PR et je supprime la branche.
- **Secours :** `preuves/etape-7-blocage.md` et ses trois captures ; PR n° 10, laissée ouverte.

### P4. Le rollback est montré

- **L'évaluateur constate :** la console affiche le SHA servi. Je lance une seule opération ; environ
  1 min 30 plus tard, la console et `/version` affichent le SHA précédent. Je rétablis ensuite la
  dernière version de la même façon.
- **Je fais :** `gh workflow run retour-arriere -f environnement=production`, puis, pour rétablir,
  `gh workflow run retour-arriere -f environnement=production -f sha=<SHA de la fusion>`.
- **Secours :** `preuves/etape-8-retour-arriere.md` : quatre bascules mesurées, service vérifié en
  36 à 66 secondes.

### P5. Les secrets ne sont pas dans le dépôt ; l'environnement se reconstruit depuis le dépôt

- **L'évaluateur constate :**
  - le job `secrets` (gitleaks) est vert sur la dernière exécution ; il parcourt tout l'historique
    (`fetch-depth: 0`) et échoue à la moindre découverte ;
  - le dépôt n'a aucun secret GitHub, ni au niveau du dépôt ni des environnements : la connexion à
    Azure passe par OIDC ; les trois variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
    `AZURE_SUBSCRIPTION_ID`) sont des identifiants, pas des secrets ;
  - `.env` est ignoré et n'a jamais été commité ; seul `.env.example`, sans valeur, est suivi.
- **Je fais :** `gh secret list` (vide), `git log --all --oneline -- .env` (vide),
  `git ls-files ".env*"` (seul `.env.example`) ; puis j'ouvre le job `secrets`.
- **Reconstruction :** je montre `docs/reconstruction.md` et la preuve de l'étape 9. Un clone neuf
  en direct prend environ 1 min 30 (clonage, image sans cache, tests) : à faire seulement si le
  temps le permet.
- **Secours :** `preuves/etape-9-reconstruction.md`.

### P6. Les retours de l'atelier n° 1 sont traités, reportés ou écartés

- **L'évaluateur constate :** dans le journal des retours, chaque retour de l'atelier n° 1 a une
  décision (traité, reporté ou écarté), une justification et un lien vers ce qui l'atteste
  (commit, PR, décision D-xx ou section du dossier).
- **Je fais :** j'ouvre le journal des retours et je parcours les décisions, une par une.
- **Secours :** aucun ; le journal est la preuve.
- **État :** journal à verser dans `eval/ateliers/sprint-1-retours.md` à partir des retours de
  l'atelier n° 1 fournis par le porteur.

## 4. Après la démonstration

- Fermer la PR de `demo/commit-casse` et supprimer la branche.
- Vérifier que la production sert la dernière version de `main` (`/version`).
