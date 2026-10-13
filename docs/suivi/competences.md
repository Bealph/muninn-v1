# Suivi des compétences

**Mis à jour le :** 13 octobre 2026 (sprint 2, étape 2)

Statuts : « À faire », « En cours », « Preuve produite », « Validée » (validée par le porteur).

Priorité : E1 et E3 sont évalués au premier oral blanc (29 et 30 octobre 2026).

## E1 : collecte, stockage et mise à disposition des données (2 à 5 pages, 15 min)

| Code | Compétence (résumé)                                              | Phase | Preuve prévue                                                               | Statut   |
| ---- | ---------------------------------------------------------------- | ----- | --------------------------------------------------------------------------- | -------- |
| C1   | Automatiser l'extraction (API, scraping, fichier, BDD, big data) | 0, 3  | Sources identifiées et vérifiées (phase 0a) ; scripts en phase 3            | En cours |
| C2   | Requêtes SQL d'extraction (SGBD et big data)                     | 1, 3  | Règles d'extraction SQL et big data conçues (phase 1) ; requêtes en phase 3 | En cours |
| C3   | Agrégation, nettoyage et homogénéisation des données             | 1, 3  | Défauts des sources et cas VD-01 à VD-28 (phase 1) ; script en phase 3      | En cours |
| C4   | Base de données conforme au RGPD (MCD, MPD, import)              | 1, 3  | Modèles conceptuel et physique, registre RGPD (phase 1) ; base en phase 3   | En cours |
| C5   | API REST de mise à disposition du jeu de données                 | 1, 3  | API des référentiels spécifiée (phase 1) ; contrat OpenAPI en phase 2       | En cours |

## E2 : veille, benchmark et paramétrage de services d'IA (15 à 20 pages, 15 min)

| Code | Compétence (résumé)                                    | Phase | Preuve prévue                                                                                                                 | Statut   |
| ---- | ------------------------------------------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------- | -------- |
| C6   | Veille technique et réglementaire organisée            | 0     | Dispositif de veille et synthèses                                                                                             | À faire  |
| C7   | Benchmark de services d'IA existants et recommandation | 0     | Grille comparative et recommandation argumentée                                                                               | À faire  |
| C8   | Paramétrer un service d'IA selon sa documentation      | 4     | Configuration documentée et connecteurs intégrés ; déploiements Foundry en zone UE et authentification Entra ID (D-44 à D-46) | En cours |

## E3 : exposition, intégration et industrialisation du modèle (15 à 20 pages, 20 min dont démo)

| Code | Compétence (résumé)                                            | Phase | Preuve prévue                                                                                                                  | Statut   |
| ---- | -------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------ | -------- |
| C9   | API REST exposant un modèle d'IA                               | 2, 4  | Contrat de l'API d'extraction et DossierDraft 1.1 (phase 2) ; API en phase 4 ; route `POST /llm/essai` du squelette (sprint 2) | En cours |
| C10  | Intégrer l'API d'IA dans une application accessible            | 5     | Interface de démonstration, audit d'accessibilité ; console d'essai du LLM (sprint 2)                                          | En cours |
| C11  | Monitorer un modèle d'IA (métriques, alertes, restitution)     | 2, 4  | Observabilité du modèle : métriques, dérive, 25 alertes (phase 2) ; mise en place en phase 4                                   | En cours |
| C12  | Tests automatisés du modèle (données, préparation, évaluation) | 2, 4  | Cas VE-01 à VE-30, seuils de blocage (phase 1) ; tests en phase 4                                                              | En cours |
| C13  | Livraison continue du modèle (approche MLOps)                  | 2, 4  | Chaîne LLMOps et AgentOps conçue (phase 2) ; workflows en phase 4                                                              | En cours |

## E4 : conception et développement de l'application (15 à 20 pages, 20 min)

| Code | Compétence (résumé)                                                    | Phase | Preuve prévue                                                                             | Statut   |
| ---- | ---------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------- | -------- |
| C14  | Analyse du besoin, spécifications fonctionnelles, accessibilité        | 0     | User stories, flux, accessibilité (phase 0a faite) ; modélisation à compléter en phase 1  | En cours |
| C15  | Cadre technique : architecture, outils, méthodes                       | 2     | Architecture technique, 17 ADR, coûts (phase 2)                                           | En cours |
| C16  | Coordination agile en contexte MLOps                                   | 2 à 7 | Méthode agile, backlog et itérations (phase 2) ; application du 15 octobre au 12 novembre | En cours |
| C17  | Développer composants et interfaces (accessibilité, sécurité, données) | 3 à 5 | Code, revues, tests ; squelette API et console, 17 tests (sprint 2)                       | En cours |
| C18  | Intégration continue des tests                                         | 2, 5  | Intégration continue conçue : contrôle requis, tests, évaluation (phase 2)                | En cours |
| C19  | Livraison continue de l'application                                    | 2, 5  | Livraison continue conçue : staging, étiquette, canari, retour arrière (phase 2)          | En cours |

## E5 : surveillance et résolution d'incidents (2 à 5 pages, 10 min)

| Code | Compétence (résumé)                                                | Phase | Preuve prévue                                                                                                                       | Statut   |
| ---- | ------------------------------------------------------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------- | -------- |
| C20  | Surveiller l'application (journalisation conforme RGPD, détection) | 2, 6  | Journalisation sans DP, alertes et ouverture d'incident conçues (phase 2) ; journaux du LLM sans contenu échangé, testés (sprint 2) | En cours |
| C21  | Résoudre et documenter des incidents techniques                    | 6     | Fiches d'incident et correctifs                                                                                                     | À faire  |
