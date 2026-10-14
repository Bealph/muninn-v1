# Couverture des compétences par la V1

**Version :** 1.2
**Date :** 14 octobre 2026
**Objet :** dire, compétence par compétence, ce que la V1 (dossier de conception V1, v1.3)
prouve, ce que la conception déjà produite prouve, et ce qui manque avant chaque oral. La
comparaison se fait contre l'énoncé exact du référentiel (21 compétences, livrables E1 à E5).

La V1 est une découpe temporaire pour la soutenance ; elle ne redéfinit pas le périmètre de
Muninn (D-42).

## 1. Verdict

**Couverture visée : 21 compétences sur 21, prouvées avant le 12 novembre (D-41).** La V1 est
livrée en incréments, tous déployés sur Azure, et accompagnée de documents versionnés dans le
dépôt. Les six jours de développement des sprints 2 à 5 n'en prouvent que 13 à eux seuls : c'est
pourquoi la V1 se poursuit par des incréments.

| Incrément ou document                                                                         | Date                                  | Compétences prouvées                            |
| --------------------------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| V1.0, sprints 2 à 5                                                                           | 14 au 19 octobre                      | C1 à C5, C8, C9, C10, C12, C17, C18             |
| V1.0 complète : outils de monitoring (le déploiement automatisé est livré au sprint 2)        | 22 octobre (D-52)                     | C11, C20 en partie ; C13 et C19 dès le sprint 2 |
| Dossier V1 et conception (phases 0 à 2), traces des sprints                                   | déjà versionnés, puis au fil de l'eau | C14, C15, C16                                   |
| Veille et benchmark (documents du dossier V1)                                                 | 31 octobre, 1er novembre              | C6, C7                                          |
| V1.1 : environnement de test, détection automatique d'incident, incidents résolus, audit RGAA | 2 et 3 novembre                       | C19, C20, C21 ; C10 renforcée                   |

**Au premier oral (29 octobre)**, E1 (C1 à C5) et E3 (C9 à C13) sont entièrement prouvés par la
V1.0 complète. **Au second oral (12 novembre)**, les 21 compétences le sont.

## 2. Détail, compétence par compétence

Légende des colonnes : « Preuve V1 » renvoie aux éléments V-xx du dossier V1 ; « Preuve hors
V1 » renvoie à la conception (`docs/conception/`), au déroulé du projet ou aux livrables.

### E1 : données (premier oral, 29 octobre)

| Code | Ce que l'énoncé exige                                                                                                                                    | Preuve V1                                                                                                                                                                 | Preuve hors V1                                         | Prouvée par | Manque, et quand |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ----------- | ---------------- |
| C1   | Extraction automatisée depuis un service web, une page web, un fichier, une base de données et un système big data ; scripts qui pérennisent la collecte | V-04 : API Géo (service web), Wiktionnaire (page web), codes postaux et COG (fichiers), Wikidata (base de données) ; V-06 : Sirene par DuckDB (big data), tâche planifiée | Phase 0, document 03 (inventaire des sources)          | V1.0        | Rien             |
| C2   | Requêtes SQL d'extraction depuis un SGBD et depuis un système big data                                                                                   | V-04 (SQL sur PostgreSQL), V-06 (SQL DuckDB sur Parquet)                                                                                                                  | Phase 1, document 02                                   | V1.0        | Rien             |
| C3   | Agrégation de sources différentes, suppression des entrées corrompues, homogénéisation des formats                                                       | V-04 : nettoyage, rejets motivés, codes typés en texte, UTF-8                                                                                                             | Phase 1, document 04 (cas VD)                          | V1.0        | Rien             |
| C4   | Base conforme au RGPD, modèles conceptuel et physique, import programmé                                                                                  | V-04 : schéma `ref`, import Alembic ; V-06 : schéma `market`                                                                                                              | Phase 1 : documents 02 (modèles) et 05 (registre RGPD) | V1.0        | Rien             |
| C5   | API REST de mise à disposition du jeu de données                                                                                                         | V-05 : API des référentiels ; agrégats Sirene lus par l'API                                                                                                               | Phase 2, document 04 (contrat)                         | V1.0        | Rien             |

### E2 : veille, benchmark, paramétrage (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                         | Preuve V1                                                                                                     | Preuve hors V1                                                                  | Prouvée par                            | Manque, et quand                                                                     |
| ---- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------ |
| C6   | Veille technique et réglementaire organisée et animée : sélection des sources, collecte, traitement, partage, recommandations | Aucune                                                                                                        | Vérifications de sources déjà faites et datées (phases 0 à 2), matière première | Veille, 31 octobre                     | Dispositif de veille, synthèses et recommandations : après le 30 octobre             |
| C7   | Benchmark de services d'IA existants et recommandation argumentée                                                             | T-06 : comparaison des modèles LLM, avant le sprint 4                                                         | Phase 1, document 06 (services big data comparés)                               | T-06 (V1.0) et benchmark, 1er novembre | Benchmark complet (transcription, synthèse vocale, téléphonie) : après le 30 octobre |
| C8   | Paramétrer un service d'IA selon sa documentation, connecteurs intégrés                                                       | V-07 : fournisseur LLM paramétré (point UE, sortie structurée, appel d'outils), interface et faux fournisseur | Phase 2, ADR-03                                                                 | V1.0                                   | Demande de zéro rétention à tracer (D-32)                                            |

### E3 : modèle, intégration, monitoring, tests, livraison (premier oral, 29 octobre)

| Code | Ce que l'énoncé exige                                                                                                                      | Preuve V1                                                                                                     | Preuve hors V1                                                         | Prouvée par                      | Manque, et quand                                                                                                         |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| C9   | API REST exposant un modèle d'IA                                                                                                           | V-07 : API d'extraction, contrat `DossierDraft` 1.1, OpenAPI                                                  | Phase 2, document 04                                                   | V1.0                             | Rien                                                                                                                     |
| C10  | Intégrer l'API d'IA dans une application, normes d'accessibilité respectées                                                                | V-09 : console qui appelle l'API ; contrôle axe-core en CI                                                    | Phase 0, document 04 (exigences d'accessibilité)                       | V1.0 ; audit RGAA en V1.1        | Audit RGAA manuel avant le 12 novembre, pour renforcer la preuve                                                         |
| C11  | Monitorer un modèle avec des métriques courantes et propres au projet, en **intégrant des outils** de collecte, d'alerte et de restitution | V-10 : métriques, écran Qualité, alerte calculée par l'application                                            | Phase 2, document 03                                                   | V1.0 complète, 22 octobre (D-52) | Outillage standard (OpenTelemetry vers Application Insights, alerte Azure Monitor) : **avant le 29 octobre**, recommandé |
| C12  | Tests automatisés du modèle : validation des données, préparation, évaluation, validation, intégration continue                            | V-08 : 20 scénarios, 5 cas de conformité, base sans outils, évaluation bloquante en CI                        | Phase 1, document 04 ; phase 2, document 02 ; précision du jury (D-03) | V1.0                             | Rien                                                                                                                     |
| C13  | Chaîne de livraison continue du modèle, approche MLOps : **automatiser** validation, test, packaging et **déploiement**                    | V-08 et V-03 : validation, tests et évaluation automatisés ; image construite ; déploiement par script manuel | Phase 2, document 05 (chaîne LLMOps complète)                          | V1.0 complète, 20 octobre        | Déploiement automatisé par la CI : **obligatoire avant le 29 octobre**                                                   |

### E4 : conception et réalisation de l'application (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                                       | Preuve V1                                              | Preuve hors V1                                                     | Prouvée par                                                | Manque, et quand                                                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| C14  | Analyse du besoin, spécifications fonctionnelles, modélisation, utilisabilité et accessibilité                                              | Dossier V1, section 1                                  | Phase 0 : documents 01 (54 stories), 02 (flux), 04 (accessibilité) | Dossier V1 et phase 0                                      | Rien                                                                                                                         |
| C15  | Cadre technique : architecture technique et applicative, outils et méthodes préconisés                                                      | Dossier V1, sections 4 et 5                            | Phase 2, document 06 (17 ADR)                                      | Dossier V1 et phase 2                                      | Rien                                                                                                                         |
| C16  | Coordination agile en contexte MLOps, temps de collaboration facilités                                                                      | Sprints 1 à 5                                          | Phase 2, document 07 ; journal des décisions                       | Dossier V1 et traces des sprints                           | Traces du déroulé réel : tableau GitHub Projects, PR et revues, comptes rendus de sprint, au fil des sprints                 |
| C17  | Composants et interfaces développés selon les spécifications et les normes d'accessibilité, de sécurité et de données                       | V-01 à V-10                                            | Phase 1, document 03 (sécurité)                                    | V1.0                                                       | Rien                                                                                                                         |
| C18  | Tests du code automatisés à chaque versionnement, par une CI                                                                                | V-03 : contrôle requis `verdict` sur chaque PR         | Phase 2, document 02                                               | V1.0                                                       | Rien                                                                                                                         |
| C19  | Livraison continue de l'application sur une chaîne d'intégration continue, outils d'automatisation **et environnements de test** paramétrés | V-03 : CI ; déploiement manuel ; une seule application | Phase 2, document 05 (préproduction, canari)                       | V1.0 complète (20 octobre) et V1.1 (environnement de test) | Déploiement automatisé (même travail que C13) et un environnement de test (révision de préproduction) : avant le 12 novembre |

### E5 : surveillance et incidents (oral du 12 novembre)

| Code | Ce que l'énoncé exige                                                                                                 | Preuve V1                                                                                      | Preuve hors V1                                          | Prouvée par                                                      | Manque, et quand                                                                                                                                                                |
| ---- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C20  | Surveillance par monitorage et journalisation conformes au RGPD, feedback loop, **détection automatique d'incidents** | V-01 : journaux à liste blanche ; V-10 : corrections par champ (boucle de rétroaction), alerte | Phase 2, document 03 (24 alertes, ouverture d'incident) | V1.0 complète (22 octobre, D-52) et V1.1 (détection automatique) | Détection automatique d'incident (alerte qui ouvre une fiche) : avant le 12 novembre                                                                                            |
| C21  | Résoudre des incidents en modifiant le code, et documenter les solutions                                              | Aucune                                                                                         | Aucune                                                  | Fiches au fil des sprints et V1.1                                | Fiche par incident réel pendant les sprints (cause, correctif, PR, test de non-régression), plus un incident provoqué et résolu : au fil des sprints, puis avant le 12 novembre |

## 3. Ce que chaque incrément ajoute

Le calendrier de ces actions est dans `roadmap-v1.md`.

| Priorité | Action                                                                                                           | Compétences   | Échéance                               | Charge [H]                     |
| -------- | ---------------------------------------------------------------------------------------------------------------- | ------------- | -------------------------------------- | ------------------------------ |
| 1        | Déploiement automatisé par la CI (OIDC), révision étiquetée par le SHA                                           | C13, C19      | **Fait au sprint 2** (D-43)            | 0,75 j, prises sur le sprint 2 |
| 2        | OpenTelemetry vers Application Insights, alerte Azure Monitor                                                    | C11, C20      | Avant le 29 octobre (22 octobre, D-52) | 0,5 j                          |
| 3        | Fiche d'incident ouverte dès le sprint 2, pour chaque incident réel                                              | C21, C16      | Dès le 14 octobre, au fil de l'eau     | Quelques minutes par incident  |
| 4        | Comptes rendus de sprint et tableau GitHub Projects                                                              | C16           | Dès le 14 octobre, au fil de l'eau     | 15 min par sprint              |
| 5        | Dispositif de veille, synthèses, recommandations                                                                 | C6            | sam. 31 octobre                        | 1 j                            |
| 6        | Benchmark complet des services d'IA                                                                              | C7            | dim. 1er novembre                      | 1 j                            |
| 7        | Environnement de test (révision de préproduction), ouverture automatique d'incident, incident provoqué et résolu | C19, C20, C21 | lun. 2 et mar. 3 novembre              | 1 j                            |
| 8        | Audit RGAA manuel de la console                                                                                  | C10, C14      | lun. 2 et mar. 3 novembre              | 0,5 j                          |

La priorité 1 est livrée au sprint 2 ; la priorité 2 prend 0,5 jour, le 22 octobre (D-52). Les éléments « si temps » du dossier V1 passent après elle.

## 4. Apports de la v1.5 du dossier V1 (D-48 à D-51)

| Compétence | Apport                                                                                                                                       | Élément    |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| C7         | Comparaison documentée des services de transcription (Azure AI Speech retenu, modèles OpenAI écartés faute de zone UE), matière du benchmark | D-50       |
| C8         | Second service d'IA paramétré selon sa documentation : synthèse et transcription vocales, authentification Entra, essai réel                 | V-12       |
| C9         | Qualification des appels exposée par l'API, sortie structurée validée par schéma                                                             | V-11       |
| C11        | Traces des appels au LLM dans Langfuse (métadonnées), en complément d'Application Insights                                                   | V-13       |
| C12        | Jeu étiqueté de qualification, cas à tolérance nulle bloquants ; expériences d'évaluation dans Langfuse                                      | V-11, V-13 |
| C13        | Échec de la CI en cas de régression mesurée par une expérience Langfuse                                                                      | V-13       |
| C17        | Lecteur audio et transcription affichée dans la console (alternative textuelle à l'audio, WCAG 1.2.1)                                        | V-12       |

Ces apports renforcent des compétences déjà couvertes ; aucune compétence ne dépend d'eux seuls.
