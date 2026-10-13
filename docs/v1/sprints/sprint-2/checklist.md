# Sprint 2 : le socle et la chaîne

**Objectif :** déployer un squelette de bout en bout qui marche : API, interface minimale et un
appel au LLM qui répond, livrés par une chaîne CI/CD bloquante jusqu'à la production.
**Périmètre :** V1 (`docs/v1/dossier-conception-v1.md`), éléments V-01 à V-03. Rien de
fonctionnellement riche ; tout ce qui suivra passera par cette chaîne.
**Méthode :** pas à pas. Chaque étape est validée par le porteur avant la suivante. Une case n'est
cochée qu'avec sa preuve (fichier, capture ou exécution de la chaîne).

## Critères d'évaluation par le pair, et étapes qui les prouvent

| N°  | Critère du pair                                                                        | Étapes | Preuve attendue                                                  |
| --- | -------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------- |
| P1  | Le squelette tourne ailleurs que sur la machine du présenté, sur l'URL de production   | 5, 6   | URL de production ouverte par l'évaluateur                       |
| P2  | Une fusion déclenche la livraison sans action manuelle                                 | 4, 6   | Démonstration en direct ou journal de la chaîne                  |
| P3  | Un commit cassé est bloqué                                                             | 7      | Démonstration en direct, PR rouge conservée                      |
| P4  | Le rollback est montré                                                                 | 8      | Démonstration en direct et journal                               |
| P5  | Les secrets ne sont pas dans le dépôt ; l'environnement se reconstruit depuis le dépôt | 1, 9   | Recherche de secrets en CI ; reconstruction depuis un clone neuf |
| P6  | Les retours de l'atelier n° 1 sont traités, reportés ou écartés                        | 0, 10  | `eval/ateliers/sprint-1-retours.md`                              |

## Étapes

### Étape 0 : cadrage du sprint

- [x] Checklist rédigée et versionnée (ce fichier). Preuve : commit `95f7dd7`.
- [x] Décision D-43 : les écarts de calendrier exigés par la consigne du sprint 2 (déploiement automatique et environnements avancés) sont validés par le porteur. Preuve : `docs/decisions.md`.
- [x] Retours de l'atelier n° 1 : le porteur décide de ne pas les consigner dans le dépôt (13 octobre 2026). Le critère P6 sera présenté oralement.
- [x] Grille de l'atelier n° 1 : non versée, même décision du porteur.
- [ ] Clé d'API du LLM disponible pour l'appel réel (D-32, D-33) ; elle reste hors du dépôt. En cours chez le porteur, non bloquante : le faux fournisseur sert en attendant.

### Étape 1 : un dépôt propre et reproductible

- [x] Structure du code (`src/muninn/`, `tests/`, `docker/`), conforme au dossier V1.
- [x] Projet Python géré par uv : dépendances figées (`uv.lock`), Python 3.12 ; aucune version publiée depuis moins de deux semaines.
- [x] Image Docker de l'application (utilisateur non administrateur) ; `docker compose` lance l'API, la console et PostgreSQL. Vérifié le 13 octobre 2026.
- [x] Secrets hors du dépôt : `.env` ignoré, `.env.example` versionné, gitleaks sans découverte sur l'historique et le dossier (un faux positif vérifié et consigné dans `.gitleaksignore`). La recherche en CI viendra à l'étape 4.
- [x] README : lancer le projet en local en trois commandes.

### Étape 2 : le squelette

- [ ] Route API `GET /health` (état) et `GET /version` (version et SHA livrés).
- [ ] Route API qui appelle le LLM et rend sa réponse, derrière une interface de fournisseur, avec un faux fournisseur pour les tests (R8, D-32).
- [ ] Interface minimale : une page de la console qui appelle l'API et affiche la réponse du LLM et la version livrée (test visuel).
- [ ] Aucun secret ni donnée personnelle dans les journaux (R4).

### Étape 3 : les tests

- [ ] Tests unitaires et d'intégration (API, console, faux fournisseur).
- [ ] ruff et mypy sans erreur.
- [ ] Contrôle d'accessibilité automatique de la page (axe-core) [H : à confirmer si le temps du sprint le permet, sinon sprint 5].

### Étape 4 : la chaîne d'intégration continue

- [ ] Workflow GitHub Actions sur chaque PR : lint, puis tests, puis build de l'image.
- [ ] Contrôle unique et obligatoire `verdict` ; protection de `main` : fusion impossible si `verdict` est rouge.

### Étape 5 : les environnements Azure

- [ ] Commandes Azure préparées et relues ; ressources créées par le porteur (R10) : registre, environnement Container Apps, préproduction et production, PostgreSQL flexible, alerte de budget à 60 € par mois (D-34).
- [ ] Identité de déploiement sans secret (OIDC) entre GitHub Actions et Azure.

### Étape 6 : la livraison continue

- [ ] Sur fusion dans `main`, sans action manuelle : image étiquetée par le SHA, poussée dans le registre, déployée en préproduction, contrôlée, puis déployée en production.
- [ ] URL de production qui affiche la console, la réponse du LLM et le SHA livré.

### Étape 7 : la preuve du blocage

- [ ] Une PR volontairement cassée (test en échec) est arrêtée : `verdict` rouge, fusion refusée.
- [ ] Preuve versionnée : lien de l'exécution, capture et extrait du journal dans `docs/v1/sprints/sprint-2/preuves/`.

### Étape 8 : le rollback

- [ ] Retour à la version précédente en une opération (workflow manuel ou commande unique).
- [ ] Rollback répété au moins deux fois ; durée mesurée ; preuve versionnée.

### Étape 9 : la reconstruction depuis le dépôt

- [ ] Depuis un clone neuf : le projet se lance en local et la chaîne redéploie, sans fichier extérieur au dépôt hormis les secrets.
- [ ] Procédure écrite et testée.

### Étape 10 : la clôture du sprint

- [ ] Retours de l'atelier n° 1 : chacun traité, reporté ou écarté.
- [ ] Compte rendu de sprint (C16) ; fiches d'incident s'il y en a eu (C21).
- [ ] Suivi des tâches et des compétences à jour ; commit et push.

## Écarts avec le dossier V1 gelé (décision D-43, validée le 13 octobre 2026)

| Élément                            | Prévu par le dossier V1                         | Exigé par la consigne du sprint 2           | Effet sur le périmètre                          |
| ---------------------------------- | ----------------------------------------------- | ------------------------------------------- | ----------------------------------------------- |
| Déploiement automatique sur fusion | 20 octobre (V1.0 complète), script manuel avant | Sprint 2                                    | Aucun : avancé dans le temps                    |
| Environnement de préproduction     | V1.1 (2 et 3 novembre)                          | Sprint 2 (« à travers les environnements ») | Aucun : avancé dans le temps                    |
| Appel réel au LLM                  | Sprint 4, après le choix du modèle (D-32, D-33) | Sprint 2 (« un appel au LLM qui répond »)   | Aucun : modèle provisoire, Mistral Small (D-32) |
