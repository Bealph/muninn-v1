# Compte rendu du sprint 2 : le socle et la chaîne

**Période :** 13 et 14 octobre 2026
**Périmètre :** V1, éléments V-01 à V-03 (`docs/v1/dossier-conception-v1.md`), écarts de
calendrier validés (D-43)
**Compétences servies :** C13, C16, C17, C18, C19, C20, C21 ; C8, C9, C10 en partie

## 1. Objectif et résultat

**Objectif :** déployer un squelette de bout en bout (API, interface minimale, appel au LLM qui
répond), livré par une chaîne CI/CD bloquante jusqu'à la production, à travers les
environnements, avec un retour arrière en une opération, des secrets hors du dépôt et un
environnement reconstructible depuis le dépôt.

**Résultat : atteint.** Les onze étapes de la checklist sont faites
(`checklist.md`). La production sert le squelette à
<https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io>.

## 2. Critères de l'évaluation par le pair

| N°  | Critère                                                | Statut            | Preuve                                                                     |
| --- | ------------------------------------------------------ | ----------------- | -------------------------------------------------------------------------- |
| P1  | Le squelette tourne sur l'URL de production            | Prouvé            | URL ci-dessus ; `/version` rend le SHA livré                               |
| P2  | Une fusion déclenche la livraison sans action manuelle | Prouvé            | Six livraisons automatiques réussies (section 4)                           |
| P3  | Un commit cassé est bloqué                             | Prouvé            | PR n° 10, laissée ouverte ; `preuves/etape-7-blocage.md`                   |
| P4  | Le rollback est montré                                 | Prouvé            | Quatre bascules en production ; `preuves/etape-8-retour-arriere.md`        |
| P5  | Secrets hors du dépôt ; reconstruction depuis le dépôt | Prouvé            | gitleaks en CI sur tout l'historique ; `preuves/etape-9-reconstruction.md` |
| P6  | Retours de l'atelier n° 1 traités, reportés ou écartés | Présenté à l'oral | Décision du porteur du 13 octobre : non consignés dans le dépôt            |

## 3. Ce qui a été livré

| Étape | Livrable                                                                                                     | PR               |
| ----- | ------------------------------------------------------------------------------------------------------------ | ---------------- |
| 1     | Socle reproductible : uv, image Docker non administrateur, docker compose, secrets hors du dépôt             | Avant la CI      |
| 2     | API `/health`, `/version`, `/llm/essai` (modèles A et B, faux fournisseur) ; console d'essai                 | Avant la CI      |
| 3     | Tests (20 à cette étape, 22 en fin de sprint), dont 3 contrôles axe-core (WCAG 2.2 AA) ; ruff et mypy strict | Avant la CI      |
| 4     | CI : lint, tests, build et test de fumée, gitleaks ; contrôle unique `verdict` ; protection de `main`        | 1                |
| 5     | Azure : registre, environnement Container Apps, préproduction et production, PostgreSQL, budget, OIDC        | 3, 4, 5, 6       |
| 6     | Livraison continue sur fusion, contrôlée avant bascule du trafic                                             | 7, 8, 9          |
| 7     | Preuve du blocage                                                                                            | 10 (ouverte), 11 |
| 8     | Retour arrière en une opération                                                                              | 12, 13           |
| 9     | Procédure de reconstruction ; réglages GitHub et ressource Foundry scriptés                                  | 14               |

## 4. Mesures

| Mesure                                              | Valeur                                   | Source                                |
| --------------------------------------------------- | ---------------------------------------- | ------------------------------------- |
| Durée de la CI sur une PR (15 exécutions vertes)    | 93 à 154 s, moyenne 108 s                | Historique GitHub Actions             |
| Durée d'une livraison, de la fusion à la production | 8 à 10 min (6 livraisons)                | Exécutions sur `main`                 |
| Livraisons automatiques                             | 6 réussies, 1 échouée (INC-02)           | Exécutions sur `main`                 |
| Retour arrière, jusqu'au service vérifié            | 36 à 66 s (4 bascules)                   | `preuves/etape-8-retour-arriere.md`   |
| Coût mensuel estimé                                 | Environ 21 € pour un budget de 60 €      | `infra/azure/README.md`, prix publics |
| Dépense relevée par le budget au 14 octobre         | 0 € ; Azure publie les coûts avec retard | `budget-muninn`                       |

Ces mesures portent sur peu d'exécutions : ce sont des ordres de grandeur.

## 5. Incidents

| Fiche  | Incident                                               | Cause racine                                                                                   | Non-régression                                          |
| ------ | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| INC-01 | Serveur PostgreSQL non créé par le script du socle     | Options retirées d'`az` 2.89 ; scripts relus contre la documentation, pas contre l'aide locale | `verifier-options.py` ; le script 03 vérifie le serveur |
| INC-02 | Première livraison bloquée à la connexion Azure (OIDC) | Sujet OIDC « immuable » du dépôt, non lu avant de créer la confiance                           | Confiance créée ou corrigée par `oidc-github.sh`        |

Deux erreurs de méthode, sans effet sur ce qui est servi, ont aussi été corrigées :

- un `git add -A` a embarqué dans une PR un renommage en cours chez le porteur. Le renommage a
  été retiré de la branche sans force-push ; depuis, seuls les fichiers modifiés sont ajoutés,
  nommément ;
- la première version du contrôle des options ne détectait pas les défauts qu'elle visait. Elle
  a été réécrite, puis vérifiée sur l'ancienne version fautive et sur une option inventée.

## 6. Décisions du sprint

D-43 (écarts de calendrier), D-44 à D-46 (modèles et ressource Foundry), D-47 (mise en place
Azure : budget filtré par étiquette, identités managées, environnements partagés, processus
choisi par variable). Détail dans `docs/decisions.md`.

## 7. Dettes et risques ouverts

| Sujet                                                             | Risque                                       | Traitement proposé                                        |
| ----------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------- |
| Route `/llm/essai` publique, sans limite de débit                 | Coût d'appels abusifs                        | Traité le 14 octobre : 10 appels par minute, 200 par jour |
| Révisions accumulées, toutes actives                              | Encombrement ; aucune facturation au repos   | Désactiver les révisions anciennes, en gardant N-1        |
| Mise à niveau automatique du modèle B                             | Banc d'essai T-06 non reproductible          | Décidé le 14 octobre : `NoAutoUpgrade` (00-foundry.sh)    |
| Foundry User pour l'identité d'exécution                          | Le rôle permet aussi de lire les clés        | Réévaluer quand un rôle plus étroit sera documenté        |
| PostgreSQL ouvert aux services Azure (0.0.0.0)                    | Exposition à d'autres clients Azure          | Accepté en V1 (D-47) ; TLS et mot de passe aléatoire      |
| Démarrage à froid (zéro réplique)                                 | Premier appel lent pendant une démonstration | Une réplique minimum avant chaque démonstration           |
| Avertissement Starlette sur `httpx2`                              | Rupture future du client de test             | Suivre la version de Starlette                            |
| Ressource Foundry `adialloext-muninn` (France Central) inutilisée | Confusion                                    | Décision du porteur : supprimer ou garder                 |

## 8. Pour le sprint 3

La chaîne est en place : tout ce qui suit passe par elle. Le sprint 3 (données et ancrage, V-04
à V-06) peut commencer sur une base qui livre, se contrôle et se défait en une opération.
