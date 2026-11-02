# Suivi des compétences

**Mis à jour le :** 2 novembre 2026 (C8 et C19 cochées ; C20, vigie en service, issue réelle attendue)

Statuts : « À faire », « En cours », « Preuve produite », « Validée » (validée par le porteur).

Priorité : E1 et E3 sont évalués au premier oral blanc (29 et 30 octobre 2026).

## E1 : collecte, stockage et mise à disposition des données (2 à 5 pages, 15 min)

| Code | Compétence (résumé)                                              | Phase | Preuve prévue                                                               | Statut          |
| ---- | ---------------------------------------------------------------- | ----- | --------------------------------------------------------------------------- | --------------- |
| C1   | Automatiser l'extraction (API, scraping, fichier, BDD, big data) | 0, 3  | Sources identifiées et vérifiées (phase 0a) ; scripts en phase 3            | Preuve produite |
| C2   | Requêtes SQL d'extraction (SGBD et big data)                     | 1, 3  | Règles d'extraction SQL et big data conçues (phase 1) ; requêtes en phase 3 | Preuve produite |
| C3   | Agrégation, nettoyage et homogénéisation des données             | 1, 3  | Défauts des sources et cas VD-01 à VD-28 (phase 1) ; script en phase 3      | Preuve produite |
| C4   | Base de données conforme au RGPD (MCD, MPD, import)              | 1, 3  | Modèles conceptuel et physique, registre RGPD (phase 1) ; base en phase 3   | Preuve produite |
| C5   | API REST de mise à disposition du jeu de données                 | 1, 3  | API des référentiels spécifiée (phase 1) ; contrat OpenAPI en phase 2       | Preuve produite |

## E2 : veille, benchmark et paramétrage de services d'IA (15 à 20 pages, 15 min)

| Code | Compétence (résumé)                                    | Phase | Preuve prévue                                                                                                                                                  | Statut          |
| ---- | ------------------------------------------------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| C6   | Veille technique et réglementaire organisée            | 0     | Dispositif de veille et synthèses                                                                                                                              | À faire         |
| C7   | Benchmark de services d'IA existants et recommandation | 0     | Grille comparative et recommandation argumentée                                                                                                                | En cours        |
| C8   | Paramétrer un service d'IA selon sa documentation      | 4     | Configuration documentée et connecteurs intégrés ; déploiements Foundry en zone UE et authentification Entra ID (D-44 à D-46) ; zéro rétention tranchée (D-89) | Preuve produite |

## E3 : exposition, intégration et industrialisation du modèle (15 à 20 pages, 20 min dont démo)

| Code | Compétence (résumé)                                            | Phase | Preuve prévue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Statut          |
| ---- | -------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| C9   | API REST exposant un modèle d'IA                               | 2, 4  | Contrat de l'API d'extraction et DossierDraft 1.1 (phase 2) ; API en phase 4 ; route `POST /llm/essai` du squelette (sprint 2) ; API de l'agent `POST /v1/extract/text` et `POST /v1/demo/runs`, format d'erreur du contrat, Swagger, écran « Agent » (sprint 4, étape 8) ; route de revue `POST /v1/demo/runs/{draft_id}/review` (sprint 5, étape 2)                                                                                                                                                                                                                                                                                                                  | Preuve produite |
| C10  | Intégrer l'API d'IA dans une application accessible            | 5     | Interface de démonstration, audit d'accessibilité ; console d'essai du LLM (sprint 2) ; correction et validation dans l'écran « Agent », accessibilité contrôlée (sprint 5, étape 2) ; écran « Démonstration » (appel joué à deux voix), relu WCAG 2.2 AA, quatre non-conformités corrigées avec tests de non-régression (sprint 5, étape 6)                                                                                                                                                                                                                                                                                                                           | En cours        |
| C11  | Monitorer un modèle d'IA (métriques, alertes, restitution)     | 2, 4  | Observabilité du modèle : métriques, dérive, 25 alertes (phase 2) ; mise en place en phase 4 ; Traces Langfuse sans contenu en production, coût et jetons par appel (sprint 4, étape 10, vérifié le 21 octobre) ; traces OpenTelemetry vers Application Insights vérifiées sur Azure, écran « Qualité » et trois règles d'alerte calculées par l'application, historique des alertes, classeur Azure Monitor (sprint 5, étapes 3 et 4, 23 octobre) ; dérive simulée : AL-01 allumée à l'écran (sprint 5, étape 5) ; AL-04 reçue par courriel lors de la panne simulée (étape 8) ; CA-8 mesuré trois fois en production, limite de la transcription documentée (INC-09) | Preuve produite |
| C12  | Tests automatisés du modèle (données, préparation, évaluation) | 2, 4  | Cas VE-01 à VE-30, seuils de blocage (phase 1) ; tests en phase 4 ; Jeu V-08 figé et relu, harnais (Wilson, base sans outils, cas bloquants), campagne de référence 119/120 (sprint 4, étape 9 ; 118 à 119/120 sur trois campagnes du même paquet, base sans outils 117 à 118) ; critères vérifiés en production, contrat personnel (étapes 11, 12)                                                                                                                                                                                                                                                                                                                    | Preuve produite |
| C13  | Livraison continue du modèle (approche MLOps)                  | 2, 4  | Chaîne LLMOps et AgentOps conçue (phase 2) ; workflows en phase 4 ; Évaluation en CI déclenchée par l'empreinte, bloquante ; CA-6 démontré (PR dégradée bloquée, D-79) ; reprise de la livraison sur erreur passagère d'Azure, testée (INC-05) ; nouvelle révision relue et vérifiée avant bascule dans les quatre scripts de livraison (INC-07) ; reprise sur ServerTimeout (INC-08) et sur révision dite invalide, limite des tests élargie (INC-10) ; schémas de la chaîne de livraison relus à la source                                                                                                                                                           | Preuve produite |

## E4 : conception et développement de l'application (15 à 20 pages, 20 min)

| Code | Compétence (résumé)                                                    | Phase | Preuve prévue                                                                                                                                                                                                                                                              | Statut          |
| ---- | ---------------------------------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| C14  | Analyse du besoin, spécifications fonctionnelles, accessibilité        | 0     | User stories, flux, accessibilité (phase 0a faite) ; modélisation à compléter en phase 1                                                                                                                                                                                   | Preuve produite |
| C15  | Cadre technique : architecture, outils, méthodes                       | 2     | Architecture technique, 17 ADR, coûts (phase 2)                                                                                                                                                                                                                            | Preuve produite |
| C16  | Coordination agile en contexte MLOps                                   | 2 à 7 | Méthode agile, backlog et itérations (phase 2) ; application du 15 octobre au 12 novembre ; compte rendu du sprint 4 ; sprint 5 clos par son rituel, compte rendu et démo de 10 minutes écrits (26 octobre)                                                                | En cours        |
| C17  | Développer composants et interfaces (accessibilité, sécurité, données) | 3 à 5 | Code, revues, tests ; squelette API et console, 17 tests (sprint 2) ; schéma `app`, rôle dédié, données personnelles hors de la base (sprint 5) ; écran « Qualité » accessible WCAG 2.2 AA dans tous ses états, relu par un non-développeur (simulé) et corrigé (sprint 5) | Preuve produite |
| C18  | Intégration continue des tests                                         | 2, 5  | Intégration continue conçue : contrôle requis, tests, évaluation (phase 2)                                                                                                                                                                                                 | Preuve produite |
| C19  | Livraison continue de l'application                                    | 2, 5  | Livraison continue conçue : staging, étiquette, canari, retour arrière (phase 2) ; livraisons du sprint 5 suivies jusqu'au verdict, 29 réussies, reprises durcies (INC-08, INC-10) ; révision de test par PR sur une application dédiée (D-90)                             | Preuve produite |

## E5 : surveillance et résolution d'incidents (2 à 5 pages, 10 min)

| Code | Compétence (résumé)                                                | Phase | Preuve prévue                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Statut          |
| ---- | ------------------------------------------------------------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| C20  | Surveiller l'application (journalisation conforme RGPD, détection) | 2, 6  | Journalisation sans DP, alertes et ouverture d'incident conçues (phase 2) ; journaux du LLM sans contenu échangé, testés (sprint 2) ; classeur des anomalies et des révisions, journaux de l'exportateur assainis (23 % des octets en moins), traces sans contenu (sprint 5) ; vigie de l'application : écran « Qualité », alertes AL-01, AL-16 et AL-04, journaux et traces sans contenu (sprint 5) ; workflow `vigie` qui lit les alertes Azure (2 novembre) | En cours        |
| C21  | Résoudre et documenter des incidents techniques                    | 6     | Fiches d'incident et correctifs ; INC-05 et INC-06 (sprint 4), correctif et non-régression ; INC-07 (sprint 5), correctif, non-régression et essai de mutation ; INC-08, INC-09 (limite assumée, sans ajustement au test) et INC-10 (sprint 5, 26 octobre)                                                                                                                                                                                                     | Preuve produite |

## Preuves, case par case

**Cases cochées : 56 sur 61** (au 2 novembre 2026). Plan et checklist des sept cases restantes :
`docs/suivi/reste-a-faire.md`.

Une case n'est cochée que si la preuve existe dans le dépôt. Source des preuves attendues :
`docs/v1/couverture-competences.md`. Une compétence passe à « Preuve produite » quand toutes
ses cases sont cochées, puis à « Validée » sur décision du porteur.

### E1 : données (premier oral, 29 octobre)

**C1** (3 sur 3)

- [x] Sources inventoriées et vérifiées : `docs/conception/sources_de_donnees/03-sources-de-donnees.md`
- [x] Scripts d'extraction : service web (API Géo), page web (Wiktionnaire), fichiers (COG, codes postaux), base de données (Wikidata, SPARQL) : `src/muninn/ingestion/`, `muninn-ingestion tout` (sprint 3, PR n° 30 à 33)
- [x] Extraction big data Sirene par DuckDB, tâche planifiée : `src/muninn/ingestion/sirene.py` (PR n° 34) ; tâche Container Apps planifiée le 3 de chaque mois (D-60, PR n° 43)

**C2** (3 sur 3)

- [x] Règles d'extraction SQL et big data conçues : `docs/conception/architecture_de_donnees/02-modele-de-donnees.md`
- [x] Requêtes SQL sur PostgreSQL : contrôles des chargements et lectures paramétrées de l'API (`src/muninn/ingestion/`, `src/muninn/referentiels/depot.py`, PR n° 30 à 35)
- [x] Requêtes SQL DuckDB sur Parquet : `src/muninn/ingestion/requetes/sirene_etablissements.sql` (PR n° 34)

**C3** (2 sur 2)

- [x] Défauts des sources et cas VD : `docs/conception/architecture_de_donnees/04-verification-exactitude.md`
- [x] Script de nettoyage et d'homogénéisation, rejets motivés : COG, codes postaux, API Géo, lexique ; contrôles VD (PR n° 30 à 33)

**C4** (3 sur 3)

- [x] Modèles conceptuel et physique : `docs/conception/architecture_de_donnees/02-modele-de-donnees.md`
- [x] Registre RGPD : `docs/conception/architecture_de_donnees/05-registre-rgpd.md`
- [x] Base PostgreSQL et import programmé : schémas, rôles et import en production par la tâche des données, planifiée chaque mois, rejouable en une commande (PR n° 29 à 43 ; `docs/v1/sprints/sprint-3/preuves/etape-10-production.md`)

**C5** (2 sur 2)

- [x] Contrat de l'API : `docs/conception/industrialisation/04-contrat-api.md`
- [x] API des référentiels déployée et chargée en production : sources citées, refus motivés, 10 questions de démonstration sur 10 (PR n° 35 à 43)

### E2 : veille, benchmark, paramétrage (oral du 12 novembre)

**C6** (0 sur 2)

- [ ] Dispositif de veille : sources, collecte, partage (31 octobre)
- [ ] Synthèses et recommandations (31 octobre)

**C7** (2 sur 3)

- [x] Comparatif des services big data : `docs/conception/architecture_de_donnees/06-big-data-externalise.md`
- [x] Banc d'essai des modèles LLM (T-06) : protocole commité avant la mesure, 48 extractions, recommandation et décision D-61 (`docs/v1/banc-essai-t06/`)
- [ ] Benchmark complet : transcription, synthèse vocale, téléphonie (1er novembre)

**C8** (4 sur 4)

- [x] Modèles déployés en zone UE, authentification Entra ID, choix documentés : `docs/decisions.md` (D-44 à D-46)
- [x] Interface de fournisseur et faux fournisseur : `src/muninn/llm/fournisseur.py` (sprint 2)
- [x] Sortie structurée et appel d'outils : `src/muninn/llm/fournisseur.py` (`response_format` en schéma JSON, `tools`, appels séquentiels) (sprint 4, PR n° 124)
- [x] Zéro rétention tranchée et tracée : D-89 dans `docs/decisions.md`, non demandée en V1 (exemption réservée aux clients suivis par Microsoft ; absence de `ContentLogging` vérifiée le 2 novembre), remplace D-32 sur ce point (ferme l'issue n° 99)

### E3 : modèle, intégration, monitoring, tests, livraison (premier oral, 29 octobre)

**C9** (3 sur 3)

- [x] Contrat `DossierDraft` 1.1 : `docs/conception/industrialisation/04-contrat-api.md`
- [x] Route d'appel au LLM du squelette : `POST /llm/essai` (sprint 2)
- [x] API d'extraction et OpenAPI : `src/muninn/api/agent.py`, contrat servi sous `/openapi.json` et `/docs` (sprint 4, PR n° 141 ; revue, sprint 5, PR n° 175)

**C10** (3 sur 4)

- [x] Exigences d'accessibilité : `docs/conception/sources_de_donnees/04-accessibilite-utilisabilite.md`
- [x] Console qui appelle l'API, testée par le porteur : `docs/v1/sprints/sprint-2/preuves/`
- [x] Contrôle axe-core automatisé en CI, WCAG 2.2 AA, sans manquement : `tests/test_accessibilite.py`, `.github/workflows/ci.yml` (sprint 2)
- [ ] Audit RGAA manuel (V1.1)

**C11** (3 sur 3)

- [x] Observabilité conçue : `docs/conception/industrialisation/03-observabilite.md`
- [x] Métriques, écran Qualité, alertes AL-01 et AL-16 : `src/muninn/traitements/metriques.py`, `docs/v1/sprints/sprint-5/preuves/etape-4-ecran-qualite-production.png`, `etape-5-derive.json` (sprint 5, PR n° 177 à 189)
- [x] OpenTelemetry vers Application Insights, alerte Azure Monitor AL-04 par courriel : `src/muninn/telemetrie.py`, `infra/azure/alertes/al04.kql`, `etape-3-traces.json`, `etape-5-al04.json`, `etape-8-exercice-panne.json` (sprint 5, PR n° 177 à 191) ; une semaine de production relue le 29 octobre

**C12** (3 sur 3)

- [x] Cas de vérification et seuils de blocage : `docs/conception/architecture_de_donnees/04-verification-exactitude.md`, `docs/conception/industrialisation/02-plan-de-tests.md`
- [x] 20 scénarios et 5 cas de conformité, jeu figé et validé en CI : `eval/v08/jeu.json`, `tests/test_jeu_v08.py` (sprint 4, PR n° 145)
- [x] Évaluation bloquante en CI, déclenchée par l'empreinte : job `evaluation` de `.github/workflows/ci.yml` ; PR n° 147 bloquée (D-79, PR n° 148)

**C13** (3 sur 3)

- [x] Chaîne LLMOps conçue : `docs/conception/industrialisation/05-chaine-llmops.md`
- [x] Validation, tests et évaluation automatisés en CI : lint, secrets, tests, build, evaluation et verdict dans `.github/workflows/ci.yml` (sprint 2, PR n° 1 ; sprint 4, PR n° 145)
- [x] Déploiement automatisé par la CI, sur fusion dans `main`, contrôlé avant bascule : `.github/workflows/ci.yml`, `infra/azure/deployer.sh` (fin du sprint 2)

### E4 : conception et réalisation (oral du 12 novembre)

**C14** (2 sur 2)

- [x] User stories, flux, accessibilité : `docs/conception/sources_de_donnees/`
- [x] Dossier V1, section 1 : `docs/v1/dossier-conception-v1.md`

**C15** (2 sur 2)

- [x] Architecture technique et 17 ADR : `docs/conception/industrialisation/06-architecture-technique.md`
- [x] Dossier V1, sections 4 et 5 : `docs/v1/dossier-conception-v1.md`

**C16** (4 sur 4)

- [x] Méthode agile : `docs/conception/industrialisation/07-methode-agile.md`
- [x] Journal des décisions et checklist du sprint 2 : `docs/decisions.md`, `docs/v1/sprints/sprint-2/checklist.md`
- [x] Tableau GitHub Projects « Muninn V1 » relié aux PR, 62 cartes, automatismes vérifiés de bout en bout : <https://github.com/users/Bealph/projects/4> (PR n° 109 ; à tenir à chaque sprint)
- [x] Comptes rendus de sprint : `docs/v1/sprints/sprint-2/compte-rendu.md` (à poursuivre à chaque sprint)

**C17** (2 sur 2)

- [x] Squelette API et console, 17 tests : `src/muninn/`, `tests/` (sprint 2)
- [x] Composants V-01 à V-10 livrés en production : `src/muninn/` (sprints 2 à 5 ; détail dans `docs/suivi/taches.md`)

**C18** (3 sur 3)

- [x] Intégration continue conçue : `docs/conception/industrialisation/02-plan-de-tests.md`
- [x] Tests (dont accessibilité), ruff et mypy automatisés en local : `pyproject.toml`, `tests/` (sprint 2)
- [x] Contrôle requis `verdict` sur chaque PR, protection de `main` : `.github/workflows/ci.yml` (fin du sprint 2)

**C19** (4 sur 4)

- [x] Livraison continue conçue : `docs/conception/industrialisation/05-chaine-llmops.md`
- [x] Déploiement automatisé en préproduction puis en production : exécution 38535838557 (fin du sprint 2)
- [x] Rollback en une opération, répété et mesuré : `docs/v1/sprints/sprint-2/preuves/etape-8-retour-arriere.md` (fin du sprint 2)
- [x] Environnement de test : révision de test par PR sur l'application dédiée `ca-muninn-api-test`, sans base ni secret, exigée par le verdict hors de `main` (D-90) ; job `test` de `.github/workflows/ci.yml`, `infra/azure/15-test.sh`, `infra/azure/tester-pr.sh` ; réussie sur les PR n° 204, 205 et 206 (PR n° 204, correctif de la livraison PR n° 205)

### E5 : surveillance et incidents (oral du 12 novembre)

**C20** (3 sur 4)

- [x] Journalisation sans donnée personnelle et alertes conçues : `docs/conception/industrialisation/03-observabilite.md`
- [x] Journaux du LLM sans contenu échangé, testés : `tests/test_llm.py` (sprint 2)
- [x] Alerte et boucle de rétroaction : champs corrigés par l'artisan comptés dans l'écran Qualité, alertes AL-01, AL-16 et AL-04 (sprint 5, PR n° 175, 176, 183 à 189)
- [ ] Détection automatique d'incident : workflow `vigie` en service toutes les 15 minutes, qui ouvre une issue « Incident » par alerte déclenchée (PR n° 203) ; visibilité prouvée le 2 novembre, 1 alerte lue sur 30 jours comme le compte propriétaire (PR n° 206). Reste : une issue ouverte par une alerte réelle, au prochain exercice de panne (renfort de C21)

**C21** (2 sur 2)

- [x] Fiche par incident réel : cause, correctif, PR, test de non-régression ; fiches `docs/v1/sprints/sprint-2/incidents/INC-01-creation-postgresql.md`, `INC-02-connexion-oidc.md` et `INC-03-livraison-en-double.md`, puis INC-04 à INC-10 dans `docs/v1/sprints/sprint-3/` à `sprint-5/incidents/` (à poursuivre au fil des sprints)
- [x] Incident provoqué, résolu et documenté : exercice de panne du 26 octobre 2026 en production (révision `0000095`, 20 appels, 20 brouillons de secours, AL-04 par courriel, réparation par la révision `0000096`) ; `docs/v1/sprints/sprint-5/checklist.md` (étape 8), `preuves/etape-8-exercice-panne.json` (PR n° 190, 191). Compté par décision du porteur du 29 octobre ; renfort prévu dans `docs/suivi/reste-a-faire.md`
