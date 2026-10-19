# Sprint 4 : la composante agentique et les garde-fous

**Objectif (consigne) :** construire la composante agentique choisie et gelée à la phase de
conception de la V1, au niveau travaillé en formation, et la protéger par des garde-fous d'entrée
et de sortie sérieux. À la fin du sprint, le contrat personnel du sprint 1 est en passe d'être
tenu : les critères fonctionnels propres au projet se vérifient en production.
**Périmètre :** V1 (`docs/v1/dossier-conception-v1.md`), éléments V-07, V-08, V-11 et V-13
(3,5 jours estimés). Rien hors V1. Les sprints sont reliés : l'agent interroge l'API des
référentiels du sprint 3 et est livré par la chaîne du sprint 2 ; le sprint 5 (V-09, V-10, V-12)
s'appuie sur ce que ce sprint livre.
**Méthode :** pas à pas. Chaque étape est validée par le porteur avant la suivante. Une case n'est
cochée qu'avec sa preuve (fichier, capture, exécution de la chaîne ou de la commande).
**Début :** vendredi 16 octobre 2026, avancé par le porteur. Point de décision Langfuse le lundi
19 au soir (dossier V1, § 7.1).

## Ce que veut dire la consigne pour Muninn

| Consigne                   | Pour Muninn (V1)                                                                                                                                                                                                                                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Composante agentique gelée | Agent outillé et ancré (dossier V1, § 3, D-37) : il lit une transcription d'appel manqué, produit un `DossierDraft` 1.1 et décide seul d'appeler deux outils en lecture seule (`chercher_communes`, `chercher_terme_metier`) qui passent par l'API des référentiels ; boucle bornée écrite dans le projet, sans framework |
| Qualification (V-11)       | Avant l'agent, un appel est classé dans une catégorie fermée ; seuls `demande_service` et `indetermine` deviennent un dossier, les autres un message (`MessageRecu`) ; règle d'asymétrie du serveur (D-48)                                                                                                                |
| Garde-fous d'entrée        | Trois couches, sans appel au LLM en plus (D-63) : règles déterministes (taille, caractères, motifs d'injection connus), modération par le filtre de contenu d'Azure, hors-périmètre par la qualification ; transcription toujours traitée comme une donnée, jamais comme une consigne                                     |
| Garde-fous de sortie       | Schéma 1.1 fermé, une relance puis brouillon partiel ; règles « gaz », « santé », contre l'invention ; contrôles rejoués par le serveur, seul à écrire statuts et provenance ; aucune fuite (consignes, secrets, valeurs hors transcription) ; refus poli à texte fixe, journalisé sans contenu                           |
| Si la composante agit      | L'agent n'a aucune action d'écriture : deux outils en lecture seule, en liste fermée, via l'API (rôle de base en lecture seule). Périmètre d'accès appliqué par le code et journalisé ; la seule action qui change un état, la validation du dossier, est humaine (CA-5, sprint 5)                                        |
| Contrat personnel          | CA-1 à CA-6 (dossier V1, § 6, annexe A), CA-7 et CA-8 en complément : état critère par critère, tenu, en cours ou avenant, versionné                                                                                                                                                                                      |
| Préparer le sprint 5       | Signaux à surveiller (latence, coût, taux de refus, erreurs de la composante), tirés de la phase 2 (`industrialisation/03-observabilite.md`) et des mesures du sprint                                                                                                                                                     |

## Critères d'évaluation par le pair, et étapes qui les prouvent

| N°  | Critère du pair                                                                    | Étapes      | Preuve attendue                                                                                                                        |
| --- | ---------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | La composante fait ce qui était annoncé : l'évaluateur relit le dossier et compare | 1 à 4, 7    | Table de conformité « annoncé / livré / preuve », ligne par ligne du dossier V1 (§ 3) ; écarts motivés                                 |
| P2  | Les garde-fous bloquent : l'évaluateur tire ses propres prompts hostiles en live   | 5, 6, 8, 11 | Écran « Agent » en production : texte libre de l'évaluateur, garde-fou déclenché, refus poli, événement journalisé sans contenu        |
| P3  | Les faux positifs sont contenus : les usages légitimes passent                     | 5, 9        | Taux de faux positifs des garde-fous d'entrée mesuré sur les scénarios légitimes, avec son intervalle ; démonstration en live          |
| P4  | Si la composante agit : confirmation sur action sensible démontrée                 | 0, 4, 8     | Non-applicabilité argumentée (aucune action d'écriture) ; périmètre d'accès appliqué et journalisé, démontré (outil hors liste refusé) |
| P5  | Le contrat personnel est en passe d'être tenu, écarts documentés                   | 11, 12      | `contrat-personnel.md` : CA-1 à CA-8, statut, preuve, écart ou avenant                                                                 |
| P6  | Journal des retours tenu                                                           | 0, 14       | `retours.md` du sprint, à jour (D-59)                                                                                                  |

## Étapes

### Étape 0 : cadrage du sprint

- [x] Checklist rédigée et versionnée (ce fichier).
- [x] Décision D-62 : écran minimal « Agent » dans la console dès ce sprint (scénario ou texte libre, dossier, garde-fous déclenchés, appels d'outils, liste « Messages ») ; le sprint 5 l'enrichit (provenance, correction, validation). Preuve : `docs/decisions.md`.
- [x] Décision D-63 : garde-fous d'entrée en trois couches, sans appel au LLM en plus (règles, modération par le filtre d'Azure, hors-périmètre par la qualification). Preuve : `docs/decisions.md`.
- [x] Décision D-64 : évaluation en CI plafonnée à 1 € par campagne et 10 € pour le sprint ; dépassement : verdict « non mesuré », bloquant ; accès au modèle par OIDC dans un environnement GitHub protégé, sans clé stockée. Preuve : `docs/decisions.md`.
- [x] Décision D-65 : filtre de contenu personnalisé, détection des détournements en annotation seule, catégories de nocivité bloquantes ; possible sans approbation de Microsoft (vérifié le 16 octobre 2026 dans Microsoft Learn par l'agent `verificateur-sources`). Créé par le porteur à l'étape 5 (R10) ; CA-4 reste tel qu'écrit. Preuve : `docs/decisions.md`.
- [x] Journal des retours du sprint (D-59) : `retours.md`.
- [x] Écarts entre la conception de la phase 2 et les décisions postérieures, relevés et tranchés par la décision la plus récente : extraction sans outil (remplacée par D-37), Langfuse « non retenu » dans le document d'observabilité (remplacé par D-49), modèle Mistral et graine dans la chaîne LLMOps (remplacés par D-44 et D-61). Preuve : `ecarts-conception.md`.

### Étape 1 : le contrat et le paquet d'extraction (V-07, C9)

- [x] Modèles Pydantic du `DossierDraft` 1.1, sous-ensemble utile à la V1, `extra="forbid"` partout ; frontière modèle / serveur respectée : le schéma demandé au LLM ne contient aucun champ du serveur. Écarts au contrat de la phase 2 motivés ; provenance par champ, candidates et « à vérifier » prévus dans une enveloppe du serveur, à côté du brouillon. Preuve : `src/muninn/extraction/contrat.py`, `contrat-dossier.md`.
- [x] Validateur applicatif des règles que le schéma n'exprime pas (règles 1, 2, 4 et 5 ; `needs_review` lié au statut par le modèle) ; `champs_manquants` recalculé par le serveur. Preuve : `src/muninn/extraction/regles.py`.
- [x] Paquet d'extraction versionné (`extraction-2026.10.1`) : consigne système (politique D-37, jeton témoin), gabarit du bloc de données (balises imitées retirées), schéma strict, définitions des deux outils, paramètres ; empreinte SHA-256 sur une liste fermée de chemins (paquet, extraction, fournisseur, `uv.lock`), fins de ligne normalisées. Preuve : `src/muninn/extraction/paquet_fichiers/`, `paquet.py`.
- [x] Tests : 30 tests (champs du serveur refusés dans la sortie du modèle, règles croisées, schéma du modèle aligné sur le contrat et compatible avec le mode strict, outils en liste fermée, bloc de données, empreinte stable, sensible au paquet, graphe des imports couvert) ; 123 tests au total. Preuve : `tests/test_extraction_contrat.py`.

### Étape 2 : le fournisseur LLM (C8)

- [ ] Interface du fournisseur étendue : messages multi-tours, appel d'outils (`parallel_tool_calls` désactivé), sortie structurée par schéma, délai par appel, jetons et coût par appel, refus du filtre de contenu distingué d'une panne.
- [ ] Faux fournisseur scriptable (appels d'outils et sorties programmés), pour les tests et la CI sans clé.
- [ ] Paramétrage documenté selon la documentation officielle (sortie structurée, appel d'outils), avec ses sources.

### Étape 3 : l'agent et sa boucle bornée (V-07, C8, C9)

- [ ] Deux outils en lecture seule, en liste fermée, qui appellent l'API des référentiels (rien d'autre ne part vers l'outil que le nom de commune, le code postal, le mot et le métier) ; outil inconnu refusé.
- [ ] Boucle : six appels d'outils au plus, délai par appel, une relance unique en cas de sortie hors schéma, puis brouillon partiel « à vérifier » ; LLM indisponible : brouillon de secours (D-29).
- [ ] Scénarios de l'annexe A en local avec le vrai modèle : SC-02, SC-07, SC-08, SC-10 appellent l'outil attendu ; consigne renforcée si besoin sur la partition de développement seulement (écarts SC-02, SC-07, SC-10 du banc T-06).

### Étape 4 : l'évaluateur du serveur (V-07)

- [ ] Contrôles de la commune et du code postal rejoués par le serveur ; statuts `verified`, `mismatch`, `not_checked` et provenance écrits par le serveur seul.
- [ ] Règle contre l'invention ; règle « gaz » (liste fermée de l'annexe A, action d'orientation insérée en tête) ; règle « santé » (liste fermée de l'annexe A) ; `needs_review`, champs manquants.
- [ ] Transcription détruite après extraction (`transcript_destroyed_at`, posé dans un `finally`) ; aucune transcription dans les journaux ni les métriques.
- [ ] Journal d'audit de l'agent, sans contenu : outils appelés, nombre d'appels, garde-fous déclenchés, statut, jetons, coût, latence, `request_id`.
- [ ] Enveloppe du serveur à côté du brouillon (D-67) : provenance par champ de la commune et du code postal, communes candidates, motifs « à vérifier » ; aucune valeur du client, ni stockée ni journalisée (test).

### Étape 5 : les garde-fous d'entrée (D-63)

- [ ] Règles déterministes : taille maximale, caractères de contrôle, motifs d'injection connus (liste fermée et versionnée, figée avant la mesure) ; une détection marque le dossier « à vérifier » et journalise l'événement, sans bloquer un client légitime.
- [ ] Modération : filtre personnalisé de D-65, créé par le porteur dans le portail Foundry et associé au déploiement ; vérifié par lecture du déploiement et par un appel réel (annotation `jailbreak.detected`, forme de l'erreur 400 `content_filter` constatée). Détournement annoté : garde-fou journalisé, dossier « à vérifier » ; contenu nocif bloqué : refus poli à texte fixe (`content_refused`), journalisé sans contenu.
- [ ] Hors-périmètre : par la qualification (étape 6) ; une entrée vide ou sans contenu exploitable donne un refus motivé.
- [ ] Jeu de prompts hostiles et légitimes (injection, extraction de consignes, hors-périmètre, contenu hostile ; demandes réelles proches) ; taux de blocage et de faux positifs mesurés, avec leur intervalle.

### Étape 6 : la qualification des appels (V-11, C9, C12)

- [ ] Liste des expressions de besoin figée et versionnée avant l'écriture des dialogues (garde-fou de complaisance).
- [ ] Dialogues de SC-Q1 à SC-Q8 écrits selon la trame (D-51), relus par le porteur avant la première exécution, puis figés.
- [ ] Classification par le LLM, schéma fermé, sans outil ; seuil 0,7 vers `indetermine` ; rétrogradation de `personnel` et `autre` par la règle du serveur ; `fournisseur` jamais rétrogradé ; règle « gaz » dans toutes les catégories.
- [ ] `MessageRecu` pour `fournisseur`, `personnel` et `autre` ; le `DossierDraft` n'est pas modifié.
- [ ] CA-7 en local : 8 scénarios ; SC-Q3, SC-Q4 et SC-Q7, 3 fois sur 3.

### Étape 7 : les garde-fous de sortie

- [ ] Fuite : aucune valeur absente de la transcription et non rendue par un outil (règle contre l'invention) ; jeton témoin dans la consigne, jamais dans une sortie ; recherche de secrets et de motifs de clé dans toute sortie.
- [ ] Hors rôle : sortie limitée au schéma fermé ; texte échappé à l'affichage, sans Markdown ni lien.
- [ ] Refus poli à texte fixe, jamais un fragment de l'entrée ; chaque refus et chaque garde-fou déclenché journalisés (code, `request_id`, garde-fou), sans contenu.
- [ ] Table de conformité « annoncé / livré / preuve » du dossier V1 (§ 3.1 à 3.4) : `conformite-conception.md` (critère P1).

### Étape 8 : l'API et l'écran « Agent » (C9, D-62)

- [ ] `POST /v1/extract/text` et `POST /v1/demo/runs` (scénario ou transcription) ; format d'erreur du contrat, `Cache-Control: no-store` ; limite de débit ; OpenAPI dans Swagger.
- [ ] Écran « Agent » : choisir un scénario ou coller un texte, voir la qualification, le dossier, les statuts et la provenance, les appels d'outils, les garde-fous déclenchés, le refus et son motif ; liste « Messages ».
- [ ] Périmètre d'accès démontré : outil hors liste refusé, appel au-delà de la borne arrêté, événement journalisé (critère P4).
- [ ] Contrôle d'accessibilité axe-core (WCAG 2.2 AA) sur les états de l'écran, en CI.

### Étape 9 : l'évaluation (V-08, C12, C13)

- [ ] Jeu versionné : 20 scénarios de test (composition de la phase 1), partition de développement distincte, 5 cas de conformité à tolérance nulle, 3 cas de qualification ; oracles figés avant la première exécution.
- [ ] Harnais : exactitude par champ avec intervalles de Wilson, base sans outils sur les mêmes scénarios, métriques de trajectoire (borne d'appels bloquante), latence p50 et p95, coût, part à vérifier ; rapport horodaté.
- [ ] Job d'évaluation en CI, déclenché par un changement d'empreinte, plafond D-64, bloquant pour `verdict` ; sans accès au modèle : « non mesuré », bloquant.
- [ ] Démonstration : une PR qui livre le paquet avec les outils désactivés est bloquée (CA-6, première partie).

### Étape 10 : Langfuse (V-13, détachable)

- [ ] Compte Langfuse Cloud UE créé par le porteur (palier gratuit, R10) ; clés dans les secrets.
- [ ] Traces des appels au LLM sans contenu en production (métadonnées seulement), testé ; contenu visible sur les évaluations synthétiques seulement.
- [ ] Jeux de données et expériences d'évaluation ; échec de la CI en cas de régression.
- [ ] Point de décision du lundi 19 au soir : si le sprint a plus d'un quart de journée de retard, Langfuse est retiré par décision écrite.

### Étape 11 : la production

- [ ] Modèle accessible en production par l'identité de l'application (OIDC, sans clé) ; livré par la chaîne du sprint 2.
- [ ] CA-2, CA-3, CA-4 et CA-7 vérifiés sur la révision active d'Azure, 3 exécutions sur 3. Preuve : `preuves/`.
- [ ] Prompts hostiles tirés en production depuis l'écran « Agent » : bloqués ou neutralisés, journalisés ; usages légitimes acceptés.

### Étape 12 : le contrat personnel

- [ ] `contrat-personnel.md` : CA-1 à CA-8, statut (tenu, en cours, avenant), preuve, écart documenté ; avenants par décision écrite.

### Étape 13 : préparer le sprint 5

- [ ] Signaux à surveiller, avec leur source, leur seuil et leur alerte : latence (extraction, démo), coût (par extraction, budget), taux de refus (filtre, règles, qualification), erreurs de la composante (fournisseur, validation, relance, borne d'outils, référentiels indisponibles), part à vérifier. Valeurs de référence mesurées pendant ce sprint. Preuve : `signaux-sprint-5.md`.

### Étape 14 : clôture (rituel de fin de sprint)

- [ ] Checklist close ; compte rendu de sprint (C16) ; fiches d'incident s'il y en a (C21).
- [ ] Déroulé de démonstration, avec le jeu de prompts hostiles et légitimes de l'évaluateur ; journal des retours.
- [ ] Section « Sprint 4 » des deux infographies, rendus régénérés.
- [ ] Suivi des tâches et des compétences à jour ; journal de session (local).
