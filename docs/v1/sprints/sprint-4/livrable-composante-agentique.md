# Livrable du sprint 4 : la composante agentique en production, garde-fous actifs

Document d'entrée du livrable. État au **21 octobre 2026**, révision de production
`ca-muninn-api-prod--0000066` (`git_sha` 4151621). Chaque ligne renvoie à sa preuve ; le détail
est dans les notes du sprint (`docs/v1/sprints/sprint-4/`).

## 1. Ce qui tourne en production

| Élément                   | Ce qu'il fait                                                                                                                      | Note                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| Qualification (V-11)      | Classe l'appel dans une catégorie fermée ; `demande_service` et `indetermine` deviennent un dossier, les autres un message (D-48)  | `qualification.md`   |
| Agent d'extraction (V-07) | Lit la transcription, produit un `DossierDraft` 1.1, décide seul d'appeler deux outils en lecture seule ; boucle bornée (6 appels) | `agent.md`           |
| Évaluateur du serveur     | Rejoue les contrôles sur les référentiels, seul à écrire statuts et provenance ; règles D-69, D-77, D-78                           | `evaluateur.md`      |
| Écran « Agent »           | Scénario ou texte libre ; dossier, garde-fous déclenchés, appels d'outils, liste « Messages » (D-62)                               | `api-ecran-agent.md` |
| Évaluation (V-08)         | Harnais et job de CI `evaluation` ; une PR qui dégrade l'agent est bloquée (D-79)                                                  | `evaluation.md`      |
| Observabilité (V-13)      | Traces Langfuse sans contenu en production ; journaux Log Analytics sans contenu                                                   | `langfuse.md`        |

Modèle : gpt-5.4-mini sur Azure AI Foundry, appelé par l'identité de l'application
(`id-muninn-execution`, rôle `Foundry User`) ; aucune clé d'API dans l'application de production.

**Où l'essayer** : console de production, écran « Agent »
(`https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/agent`),
mode « texte libre » : l'évaluateur y colle ses propres prompts hostiles (critère du pair P2).

## 2. Garde-fous actifs, et leur preuve en production

| Moment | Garde-fou                                                                                                     | Preuve en production (21 octobre 2026)                                                                                           |
| ------ | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Entrée | Règles déterministes : taille (8 000 caractères), caractères, motifs d'injection connus (D-63)                | Entrée trop longue refusée (HTTP 422) ; 34 lignes `entree.controle` `INJ-…`                                                      |
| Entrée | Filtre de contenu personnalisé `muninn-annotation-injection` : détournement annoté, nocivité bloquante (D-75) | 7/7 cas hostiles : garde-fou « détournement » (motif du serveur ou annotation du filtre, non distingués), dossier « à vérifier » |
| Entrée | Hors périmètre par la qualification ; dans le doute, un dossier (D-73)                                        | CA-7 : 24/24                                                                                                                     |
| Sortie | Schéma fermé, une relance puis brouillon partiel                                                              | Aucune valeur injectée (montants) dans les dossiers hostiles                                                                     |
| Sortie | Règles « gaz » et « santé » ; règle contre l'invention                                                        | CA-3 : 3/3 ; CA-4 : 12/12 (aucun terme de santé)                                                                                 |
| Sortie | Fuite : jeton témoin des consignes, 9 motifs de secret                                                        | Aucune fuite sur 11 cas (marqueurs, extraits de consigne, montants injectés)                                                     |
| Sortie | Refus poli à texte fixe, jamais un fragment de l'entrée                                                       | Non déclenché le 21 en production (aucun blocage du filtre) ; démontré à l'étape 8 (`api-ecran-agent.md`)                        |
| Action | Deux outils en lecture seule, liste fermée, par l'API des référentiels ; aucune écriture                      | Démontré par test (`P4-perimetre`), non rejouable en production sans modèle simulé                                               |
| Trace  | Garde-fou journalisé par son code et le `request_id`, sans contenu                                            | 0 ligne de journal sur 1 509 contenant une donnée d'appel                                                                        |

Sources : `production.md` (§ 2 à 5), `preuves/etape-11-criteres.json`,
`preuves/etape-11-hostiles.json`, `preuves/etape-12-ca-1-2-4.json`.

## 3. Mesures

| Mesure                                             | Résultat                   | Intervalle à 95 % (Wilson) | Source                 |
| -------------------------------------------------- | -------------------------- | -------------------------- | ---------------------- |
| Détection des phrases hostiles (règles d'entrée)   | 20/20                      | 83,9 à 100 %               | `garde-fous-entree.md` |
| Faux positifs sur phrases légitimes                | 0/20                       | 0 à 16,1 %                 | `garde-fous-entree.md` |
| Exactitude globale du dossier, V-08 (campagne 2)   | 117/120 = 97,5 %           | 92,9 à 99,1 %              | `evaluation.md`        |
| Coût de la campagne V-08                           | 0,18 €                     | sans objet                 | `evaluation.md`        |
| Prompts hostiles et légitimes depuis l'écran       | 11/11 tenus                | non calculé (11 cas)       | `production.md`, § 4   |
| Durée du parcours SC-01 en production, côté client | 2,7 à 12,1 s (limite 30 s) | sans objet                 | `contrat-personnel.md` |

## 4. État du contrat personnel

Détail critère par critère : `contrat-personnel.md`. En bref : CA-2 (avec avenants D-69, D-78),
CA-3, CA-4 et CA-7 tenus sur Azure ; CA-1 en cours, un écart d'urgence sur 12 exécutions ;
CA-5, CA-6 (partie 2) et CA-8 (avenant D-74) au sprint 5.

## 5. Limites

- Les phrases hostiles jouées en production viennent du jeu de l'étape 5, connu du code : elles
  prouvent que la production se comporte comme les essais, pas la résistance à une attaque
  nouvelle. La borne basse de détection (84 %) est la valeur à retenir.
- Prompt Shields reconnaît mal le français ; la défense repose aussi sur les motifs du serveur et
  la neutralisation du dossier.
- Sur ce jeu, les outils de l'agent n'apportent pas de gain mesurable (PR n° 146) ; l'apport de
  l'agent est cadré dans `evaluation.md`, § 4 sexies.
- Le rôle `Foundry User` est plus large que l'inférence (dette, D-77).
