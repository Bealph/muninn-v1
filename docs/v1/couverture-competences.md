# Couverture des compétences par la V1

**Version :** 1.0
**Date :** 12 octobre 2026
**Objet :** dire, compétence par compétence, ce que la V1 (dossier de conception V1, v1.3)
prouve, ce que la conception déjà produite prouve, et ce qui manque avant chaque oral. La
comparaison se fait contre l'énoncé exact du référentiel (21 compétences, livrables E1 à E5).

## 1. Verdict

La V1, à elle seule, ne couvre pas tout le référentiel. Ce n'est pas son rôle : c'est la démo.
Une partie des compétences se prouve par la conception déjà versionnée (phases 0 à 2), par le
déroulé du projet (sprints, revues, incidents) et par la rédaction des livrables.

| Statut                                                | Nombre | Compétences                                              |
| ----------------------------------------------------- | ------ | -------------------------------------------------------- |
| Couverte par la V1 ou par la conception déjà produite | 13     | C1, C2, C3, C4, C5, C8, C9, C10, C12, C14, C15, C17, C18 |
| Partielle : un élément exigé par l'énoncé manque      | 6      | C7, C11, C13, C16, C19, C20                              |
| Non couverte par la V1 : à produire hors V1           | 2      | C6, C21                                                  |

**Écart le plus grave.** C13, évaluée au premier oral (29 octobre), exige d'« automatiser les
étapes de validation, de test, de packaging et de déploiement du modèle ». La V1 automatise la
validation, les tests et l'évaluation, mais **déploie par un script lancé à la main** (coupe faite
pour tenir six jours). Sans correction, C13 est partielle devant le jury. La feuille de route V1
rend donc obligatoire, avant le 29 octobre, le déploiement automatisé, qui était le premier
élément « si temps ».

## 2. Détail, compétence par compétence

Légende des colonnes : « Preuve V1 » renvoie aux éléments V-xx du dossier V1 ; « Preuve hors
V1 » renvoie à la conception (`docs/conception/`), au déroulé du projet ou aux livrables.

### E1 : données (premier oral, 29 octobre)

| Code | Ce que l'énoncé exige                                                                                                                                    | Preuve V1                                                                                                                                                                 | Preuve hors V1                                         | Statut   | Manque, et quand |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------- | ---------------- |
| C1   | Extraction automatisée depuis un service web, une page web, un fichier, une base de données et un système big data ; scripts qui pérennisent la collecte | V-04 : API Géo (service web), Wiktionnaire (page web), codes postaux et COG (fichiers), Wikidata (base de données) ; V-06 : Sirene par DuckDB (big data), tâche planifiée | Phase 0, document 03 (inventaire des sources)          | Couverte | Rien             |
| C2   | Requêtes SQL d'extraction depuis un SGBD et depuis un système big data                                                                                   | V-04 (SQL sur PostgreSQL), V-06 (SQL DuckDB sur Parquet)                                                                                                                  | Phase 1, document 02                                   | Couverte | Rien             |
| C3   | Agrégation de sources différentes, suppression des entrées corrompues, homogénéisation des formats                                                       | V-04 : nettoyage, rejets motivés, codes typés en texte, UTF-8                                                                                                             | Phase 1, document 04 (cas VD)                          | Couverte | Rien             |
| C4   | Base conforme au RGPD, modèles conceptuel et physique, import programmé                                                                                  | V-04 : schéma `ref`, import Alembic ; V-06 : schéma `market`                                                                                                              | Phase 1 : documents 02 (modèles) et 05 (registre RGPD) | Couverte | Rien             |
| C5   | API REST de mise à disposition du jeu de données                                                                                                         | V-05 : API des référentiels ; agrégats Sirene lus par l'API                                                                                                               | Phase 2, document 04 (contrat)                         | Couverte | Rien             |

### E2 : veille, benchmark, paramétrage (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                         | Preuve V1                                                                                                     | Preuve hors V1                                                                  | Statut       | Manque, et quand                                                                     |
| ---- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------ |
| C6   | Veille technique et réglementaire organisée et animée : sélection des sources, collecte, traitement, partage, recommandations | Aucune                                                                                                        | Vérifications de sources déjà faites et datées (phases 0 à 2), matière première | Non couverte | Dispositif de veille, synthèses et recommandations : après le 30 octobre             |
| C7   | Benchmark de services d'IA existants et recommandation argumentée                                                             | T-06 : comparaison des modèles LLM, avant le sprint 4                                                         | Phase 1, document 06 (services big data comparés)                               | Partielle    | Benchmark complet (transcription, synthèse vocale, téléphonie) : après le 30 octobre |
| C8   | Paramétrer un service d'IA selon sa documentation, connecteurs intégrés                                                       | V-07 : fournisseur LLM paramétré (point UE, sortie structurée, appel d'outils), interface et faux fournisseur | Phase 2, ADR-03                                                                 | Couverte     | Demande de zéro rétention à tracer (D-32)                                            |

### E3 : modèle, intégration, monitoring, tests, livraison (premier oral, 29 octobre)

| Code | Ce que l'énoncé exige                                                                                                                      | Preuve V1                                                                                                     | Preuve hors V1                                                         | Statut    | Manque, et quand                                                                                                         |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------ |
| C9   | API REST exposant un modèle d'IA                                                                                                           | V-07 : API d'extraction, contrat `DossierDraft` 1.1, OpenAPI                                                  | Phase 2, document 04                                                   | Couverte  | Rien                                                                                                                     |
| C10  | Intégrer l'API d'IA dans une application, normes d'accessibilité respectées                                                                | V-09 : console qui appelle l'API ; contrôle axe-core en CI                                                    | Phase 0, document 04 (exigences d'accessibilité)                       | Couverte  | Audit RGAA manuel avant le 12 novembre, pour renforcer la preuve                                                         |
| C11  | Monitorer un modèle avec des métriques courantes et propres au projet, en **intégrant des outils** de collecte, d'alerte et de restitution | V-10 : métriques, écran Qualité, alerte calculée par l'application                                            | Phase 2, document 03                                                   | Partielle | Outillage standard (OpenTelemetry vers Application Insights, alerte Azure Monitor) : **avant le 29 octobre**, recommandé |
| C12  | Tests automatisés du modèle : validation des données, préparation, évaluation, validation, intégration continue                            | V-08 : 20 scénarios, 5 cas de conformité, base sans outils, évaluation bloquante en CI                        | Phase 1, document 04 ; phase 2, document 02 ; précision du jury (D-03) | Couverte  | Rien                                                                                                                     |
| C13  | Chaîne de livraison continue du modèle, approche MLOps : **automatiser** validation, test, packaging et **déploiement**                    | V-08 et V-03 : validation, tests et évaluation automatisés ; image construite ; déploiement par script manuel | Phase 2, document 05 (chaîne LLMOps complète)                          | Partielle | Déploiement automatisé par la CI : **obligatoire avant le 29 octobre**                                                   |

### E4 : conception et réalisation de l'application (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                                       | Preuve V1                                              | Preuve hors V1                                                     | Statut    | Manque, et quand                                                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------ | --------- | ---------------------------------------------------------------------------------------------------------------------------- |
| C14  | Analyse du besoin, spécifications fonctionnelles, modélisation, utilisabilité et accessibilité                                              | Dossier V1, section 1                                  | Phase 0 : documents 01 (54 stories), 02 (flux), 04 (accessibilité) | Couverte  | Rien                                                                                                                         |
| C15  | Cadre technique : architecture technique et applicative, outils et méthodes préconisés                                                      | Dossier V1, sections 4 et 5                            | Phase 2, document 06 (17 ADR)                                      | Couverte  | Rien                                                                                                                         |
| C16  | Coordination agile en contexte MLOps, temps de collaboration facilités                                                                      | Sprints 1 à 5                                          | Phase 2, document 07 ; journal des décisions                       | Partielle | Traces du déroulé réel : tableau GitHub Projects, PR et revues, comptes rendus de sprint, au fil des sprints                 |
| C17  | Composants et interfaces développés selon les spécifications et les normes d'accessibilité, de sécurité et de données                       | V-01 à V-10                                            | Phase 1, document 03 (sécurité)                                    | Couverte  | Rien                                                                                                                         |
| C18  | Tests du code automatisés à chaque versionnement, par une CI                                                                                | V-03 : contrôle requis `verdict` sur chaque PR         | Phase 2, document 02                                               | Couverte  | Rien                                                                                                                         |
| C19  | Livraison continue de l'application sur une chaîne d'intégration continue, outils d'automatisation **et environnements de test** paramétrés | V-03 : CI ; déploiement manuel ; une seule application | Phase 2, document 05 (préproduction, canari)                       | Partielle | Déploiement automatisé (même travail que C13) et un environnement de test (révision de préproduction) : avant le 12 novembre |

### E5 : surveillance et incidents (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                 | Preuve V1                                                                                      | Preuve hors V1                                          | Statut       | Manque, et quand                                                                                                                                                                |
| ---- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C20  | Surveillance par monitorage et journalisation conformes au RGPD, feedback loop, **détection automatique d'incidents** | V-01 : journaux à liste blanche ; V-10 : corrections par champ (boucle de rétroaction), alerte | Phase 2, document 03 (24 alertes, ouverture d'incident) | Partielle    | Détection automatique d'incident (alerte qui ouvre une fiche) : avant le 12 novembre                                                                                            |
| C21  | Résoudre des incidents en modifiant le code, et documenter les solutions                                              | Aucune                                                                                         | Aucune                                                  | Non couverte | Fiche par incident réel pendant les sprints (cause, correctif, PR, test de non-régression), plus un incident provoqué et résolu : au fil des sprints, puis avant le 12 novembre |

## 3. Conséquences pour le plan

Le calendrier de ces actions est dans `roadmap-v1.md`.

| Priorité | Action                                                                                                           | Compétences   | Échéance                                  | Charge [H]                    |
| -------- | ---------------------------------------------------------------------------------------------------------------- | ------------- | ----------------------------------------- | ----------------------------- |
| 1        | Déploiement automatisé par la CI (OIDC), révision étiquetée                                                      | C13, C19      | Avant le 29 octobre (réserve, 20 octobre) | 0,75 j                        |
| 2        | OpenTelemetry vers Application Insights, alerte Azure Monitor                                                    | C11, C20      | Avant le 29 octobre (réserve, 21 octobre) | 0,5 j                         |
| 3        | Fiche d'incident ouverte dès le sprint 2, pour chaque incident réel                                              | C21, C16      | Dès le 14 octobre, au fil de l'eau        | Quelques minutes par incident |
| 4        | Comptes rendus de sprint et tableau GitHub Projects                                                              | C16           | Dès le 14 octobre, au fil de l'eau        | 15 min par sprint             |
| 5        | Dispositif de veille, synthèses, recommandations                                                                 | C6            | sam. 31 octobre                           | 1 j                           |
| 6        | Benchmark complet des services d'IA                                                                              | C7            | dim. 1er novembre                         | 1 j                           |
| 7        | Environnement de test (révision de préproduction), ouverture automatique d'incident, incident provoqué et résolu | C19, C20, C21 | lun. 2 et mar. 3 novembre                 | 1 j                           |
| 8        | Audit RGAA manuel de la console                                                                                  | C10, C14      | lun. 2 et mar. 3 novembre                 | 0,5 j                         |

Les priorités 1 et 2 consomment 1,25 jour de la réserve du 20 au 24 octobre. Les éléments « si
temps » du dossier V1 passent après elles.
