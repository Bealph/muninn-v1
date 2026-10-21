# Compte rendu du sprint 4 : la composante agentique et les garde-fous

**Période :** 16 au 21 octobre 2026 (prévu du 16 au 20 octobre, premier quart)
**Périmètre :** V1, éléments V-07, V-08, V-11 et V-13 (`docs/v1/dossier-conception-v1.md`),
décisions D-62 à D-80
**Compétences servies :** C8, C9, C11, C12, C13, C16, C17, C18, C21 ; C10 en partie

## 1. Objectif et résultat

**Objectif (consigne) :** construire la composante agentique gelée à la conception de la V1, et
la protéger par des garde-fous d'entrée et de sortie sérieux. À la fin du sprint, le contrat
personnel est en passe d'être tenu : les critères propres au projet se vérifient en production.

**Résultat : atteint, sauf le journal des retours du pair (en attente).** En production, l'écran
« Agent »
(<https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/agent>)
qualifie un appel, fait travailler l'agent et ses deux outils, contrôle le dossier par le serveur,
et applique les garde-fous ; chaque garde-fou déclenché est journalisé sans contenu. Livrable
d'entrée : `livrable-composante-agentique.md`.

**Ce que la consigne devient pour Muninn :** un agent outillé et ancré (D-37), qui lit la
transcription d'un appel manqué, produit un `DossierDraft` 1.1 et décide seul d'appeler deux
outils en lecture seule ; une architecture hybride, où le serveur fait ce qu'une règle sait faire
(D-69, D-77, D-78, D-80) et l'agent ce qu'une règle comprend mal.

## 2. Critères de l'évaluation par le pair

| N° | Critère                                                          | Statut     | Preuve                                                                                                     |
| -- | ---------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------- |
| P1 | La composante fait ce qui était annoncé                          | Prouvé     | `conformite-conception.md` (annoncé, livré, preuve) ; écarts motivés par décision                          |
| P2 | Les garde-fous bloquent des prompts hostiles tirés en direct     | Prouvé     | Écran « Agent » en production : 11 sur 11 tenus, journalisés sans contenu (`production.md`)                |
| P3 | Les faux positifs sont contenus                                  | Prouvé     | 0 sur 20 phrases légitimes, IC 95 % 0 à 16,1 % (`garde-fous-entree.md`) ; légitimes acceptés en production |
| P4 | Si la composante agit : confirmation sur action sensible         | Prouvé     | Non-applicabilité argumentée (aucune écriture) ; `P4-perimetre` en production : outil refusé, borne        |
| P5 | Le contrat personnel est en passe d'être tenu, écarts documentés | Prouvé     | `contrat-personnel.md` : CA-1 à CA-4 et CA-7 tenus sur Azure ; CA-5, CA-6 (partie 2), CA-8 au sprint 5     |
| P6 | Journal des retours tenu                                         | En attente | `retours.md` créé ; retours du pair à recevoir                                                             |

## 3. Ce qui a été livré

| Étape | Livrable                                                                                                                   | PR            |
| ----- | -------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 0     | Checklist, décisions D-62 à D-65, écarts entre la phase 2 et les décisions postérieures                                    | 112           |
| 1     | Contrat `DossierDraft` 1.1, paquet d'extraction versionné et son empreinte                                                 | 114           |
| 2     | Fournisseur LLM : outils, sortie structurée, coût, refus du filtre, annotation de détournement                             | 124           |
| 3     | Agent outillé, boucle bornée (6 appels), relance unique, brouillon de secours                                              | 126           |
| 4     | Évaluateur du serveur : correspondance (D-69), contrôles, règles gaz, santé, contre l'invention ; enveloppe (D-67)         | 130           |
| 5     | Garde-fous d'entrée par règles, mesurés (20 sur 20 hostiles, 0 sur 20 légitimes) ; filtre personnalisé (D-75)              | 132, 143      |
| 6     | Qualification des appels (V-11), dialogues SC-Q1 à SC-Q8 relus et figés                                                    | 136           |
| 7     | Garde-fous de sortie (fuite, invention, hors rôle), table de conformité                                                    | 139           |
| 8     | API de l'agent et écran « Agent » (D-62), refus du filtre en dossier « à vérifier » (D-73)                                 | 141           |
| 9     | Évaluation V-08 : jeu figé et relu, harnais, job de CI, identité dédiée ; vigie démontrée (D-79) ; apport de l'agent cadré | 145, 148, 149 |
| 10    | Langfuse (V-13) : traces sans contenu en production, dataset et expériences dans un projet séparé                          | 151 à 153     |
| 11    | Production : modèle sans clé, critères vérifiés sur Azure, prompts hostiles depuis l'écran                                 | 155           |
| 12    | Contrat personnel, livrable du sprint ; cases des étapes 3 et 5 traitées                                                   | 157           |
| 12    | Règle du serveur « urgence dite » (D-80) : CA-1 tenu                                                                       | 159           |
| 13    | Signaux à surveiller au sprint 5, reprises du sprint 5                                                                     | 161           |
| 14    | Incidents INC-05 et INC-06, reprise de la livraison sur erreur passagère d'Azure ; clôture                                 | 163, celle-ci |

## 4. Mesures

| Mesure                                                   | Valeur                                                                     | Source                                 |
| -------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------- |
| Exactitude du dossier, V-08 (20 scénarios × 3, test)     | 117/120 = 97,5 %, IC 95 % 92,9 à 99,1 % ; verdict `reussite`               | `evaluation.md` ; CI de la PR 159      |
| Agent comparé à la même chaîne sans outils               | 117/120 dans les deux cas : pas de gain mesurable des outils sur ce jeu    | `evaluation.md`, § 4 sexies            |
| Détection des phrases hostiles (règles d'entrée)         | 20 sur 20, IC 95 % 83,9 à 100 %                                            | `garde-fous-entree.md`                 |
| Faux positifs sur phrases légitimes                      | 0 sur 20, IC 95 % 0 à 16,1 %                                               | `garde-fous-entree.md`                 |
| Prompts hostiles et légitimes depuis l'écran, production | 11 sur 11 tenus, aucune fuite                                              | `production.md`, § 4                   |
| Critères du contrat sur Azure                            | CA-1 3/3 (après D-80), CA-2 24/24, CA-3 3/3, CA-4 15/15, CA-7 24/24        | `contrat-personnel.md`                 |
| Outil attendu appelé (annexe A, local)                   | 12 sur 12, consigne `extraction-2026.10.3` (9 sur 12 le 19 octobre)        | `agent.md`, § 4                        |
| Latence de l'extraction en production                    | p50 2,7 s ; p95 3,4 s (102 extractions)                                    | `signaux-sprint-5.md`                  |
| Coût d'une extraction en production                      | 0,0037 € en moyenne (plafond 0,01 €)                                       | `signaux-sprint-5.md`                  |
| Coût des campagnes V-08 conservées                       | 1,04 € pour 5 rapports ; environ 2 € pour l'étape 9 en tout ; plafond 10 € | `eval/v08/rapports/` ; `evaluation.md` |
| Tests                                                    | 368 ; 4 ignorés sur le poste sans base locale, joués en CI                 | `pytest`                               |
| CI sur une PR (51 réussies depuis le 16 octobre)         | 126 à 2 807 s, médiane 153 s (les longues comprennent une campagne V-08)   | Historique GitHub Actions              |
| Livraisons sur `main` (depuis le 16 octobre)             | 34 réussies, 4 en échec (INC-05, INC-06) ; médiane 10,5 min                | Historique GitHub Actions              |

Ces mesures portent sur peu d'exécutions : 3 exécutions sur 3 prouvent la stabilité, pas un taux.
Le coût total exact des campagnes du sprint, toutes poussées comprises, n'a pas été additionné ;
il se lit dans l'analyse des coûts d'Azure.

## 5. Incidents

| Fiche  | Incident                                                                      | Cause racine                                                       | Non-régression                                 |
| ------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| INC-05 | Livraison de la console interrompue par Azure (429, 503), trois fois          | Aucune reprise sur les erreurs passagères d'Azure Resource Manager | `az_tenace` ; `tests/test_livraison.py`        |
| INC-06 | Livraison bloquée par le contrôle des secrets, sur une branche encore ouverte | Clés de test factices au format réel, écrites en clair             | Clés de test assemblées à l'exécution (PR 139) |

Les deux incidents ont été trouvés à la clôture, en relisant l'historique des livraisons, et non au
moment des faits. Depuis, chaque livraison est suivie jusqu'à son verdict.

Défauts trouvés et corrigés avant toute livraison, sans incident : limite de mot `\b` lue comme un
caractère de contrôle dans les motifs d'injection, nom de l'artisan pris pour celui du client,
filtre de contenu qui bloquait la qualification de SC-05, campagnes d'évaluation en erreur 429,
traces Langfuse sans projet séparé pour l'évaluation, vérification de production qui ne contrôlait
pas tout le texte des critères (relevée à l'étape 12).

## 6. Décisions du sprint

D-62 (écran « Agent »), D-63 (garde-fous d'entrée en trois couches), D-64 (plafonds de
l'évaluation), D-65, D-70 puis D-75 (filtre de contenu personnalisé), D-67 (enveloppe du serveur),
D-69, D-77, D-78 (correspondance et départage par le serveur), D-71, D-72 (trame de l'agent vocal),
D-73 (refus du filtre en dossier « à vérifier »), D-74 (avenant de CA-8), D-79 (avenant de CA-6),
D-80 (urgence dite). D-66, D-68 et D-76 portent sur le projet global, hors V1. Détail dans
`docs/decisions.md`.

## 7. Dettes et risques ouverts

| Sujet                                                                 | Risque                                                        | Traitement proposé                                                              |
| --------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Outils de l'agent sans gain mesurable sur le jeu V-08                 | Question du jury sur l'apport de l'agent                      | Cadrage écrit (`evaluation.md`, § 4 sexies) ; jeu plus riche après la V1        |
| Prompts hostiles de la même origine que les motifs                    | Résistance réelle à une attaque nouvelle non mesurée          | Borne basse (84 %) retenue ; jeu nouveau dans la liste suivante                 |
| Prompt Shields faible en français                                     | Détournement non annoté                                       | Motifs du serveur et neutralisation du dossier ; à revoir                       |
| Rôle `Foundry User` plus large que l'inférence (D-77)                 | Identité de l'application plus puissante que nécessaire       | Rôle restreint, sprint 5                                                        |
| Contrôles du texte des critères absents de la vérification du serveur | L'écran « Agent » montre « conforme » sur un critère partiel  | Reporter dans `muninn.demo.verification`, sprint 5 (décidé le 21)               |
| SC-08 : objet attendu non atteint (lexique)                           | Une décision de l'agent sur cinq non démontrée                | Lexique à enrichir après la V1                                                  |
| Campagne V-08 rejouée à chaque poussée qui touche le paquet           | Coût et temps de CI                                           | Comparer l'empreinte à celle de `main`                                          |
| Calendrier : sprint 5 prévu les 20 et 21 octobre                      | Sprint 5 lourd (CA-5, voix, vigie, alerte) avant le gel du 28 | Périmètre et dates fixés au cadrage du sprint 5 (accord du porteur, 21 octobre) |
| Journal des retours du pair                                           | Critère P6 non prouvé                                         | Retours à recevoir et à consigner dans `retours.md`                             |
