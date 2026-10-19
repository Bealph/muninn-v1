# Sprint 4 : le fournisseur LLM et son paramétrage

Étape 2 de la checklist (C8 : paramétrer un service d'IA selon sa documentation). Code :
`src/muninn/llm/fournisseur.py` ; tests : `tests/test_llm_completer.py`.

## 1. Ce que fait le fournisseur

| Fonction                 | Ce qu'elle fait                                                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `completer(RequeteChat)` | Une étape de conversation : messages à plusieurs tours, outils, sortie structurée par schéma, délai propre à l'étape             |
| `ReponseChat`            | Contenu ou appels d'outils, raison de fin, jetons d'entrée et de sortie, coût en millionièmes d'euro, détournement annoté (D-65) |
| `message_outil`          | La réponse d'un outil à remettre dans la conversation, à la forme du schéma de référence                                         |
| Trois échecs distincts   | `RefusContenu` (filtre de contenu, entrée ou sortie), `DelaiDepasse`, `ErreurFournisseur` (panne, réponse illisible)             |
| `FauxFournisseur`        | Sans réseau ; scénario programmable (réponses, appels d'outils, exceptions) ; garde les requêtes reçues pour les tests           |
| Journaux                 | Modèle, durée, jetons, coût, raison de fin, nombre d'appels d'outils, détournement ; jamais un contenu (R4, testé)               |

La méthode `repondre` de l'écran d'essai de la console (sprint 2) est inchangée.

## 2. Paramétrage, selon la documentation officielle

Lu le 19 octobre 2026 sur Microsoft Learn (agent `verificateur-sources`) :
[sortie structurée](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/structured-outputs),
[modèles de raisonnement](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reasoning),
[appel d'outils](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling),
[référence REST v1](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat).

| Paramètre                 | Réglage retenu                                                                                                 | Raison documentée                                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `response_format`         | `json_schema`, `strict: true`                                                                                  | Sortie structurée prise en charge par gpt-5.4-mini (page des modèles de raisonnement)                                  |
| Schéma                    | Sans `pattern`, `format`, bornes de longueur, de nombre ni de taille de tableau                                | Mots-clés non pris en charge par Azure en mode strict ; contraintes vérifiées par Pydantic côté serveur                |
| Schéma                    | 100 propriétés et 5 niveaux d'imbrication au plus ; `enum` sans `null`, avec `type: ["string","null"]`         | Limites et forme documentées par Azure (testées)                                                                       |
| `tools[].function.strict` | `true`                                                                                                         | Sortie structurée appliquée aux arguments des outils                                                                   |
| `parallel_tool_calls`     | `false`                                                                                                        | Obligatoire avec la sortie structurée ; la page des modèles ne prête pas d'appels parallèles à gpt-5.4-mini            |
| `max_completion_tokens`   | 4 000                                                                                                          | Seul paramètre de longueur des modèles de raisonnement ; il compte aussi les jetons de raisonnement                    |
| `temperature`, `top_p`    | Non envoyés                                                                                                    | Non pris en charge par les modèles de raisonnement GPT-5                                                               |
| `seed`                    | Non envoyé                                                                                                     | Déprécié, en bêta, déterminisme non garanti : la reproductibilité se mesure par les répétitions de l'évaluation (EC-3) |
| Message d'outil           | `role`, `tool_call_id`, `content`, sans `name`                                                                 | Schéma de référence REST ; le banc T-06 envoyait `name`, toléré dans un exemple mais hors du schéma                    |
| `message.refusal`         | Lu et rapporté (`refus_modele`)                                                                                | Le modèle peut refuser en sortie structurée ; à tester avant de lire le contenu                                        |
| Filtre de contenu         | 400 `content_filter` ou `finish_reason: content_filter` : `RefusContenu` ; annotation `jailbreak.detected` lue | Formes documentées (vérification de D-65)                                                                              |

## 3. Correction du paquet d'extraction

Le schéma du paquet (`extraction-2026.10.1`, jamais évalué ni publié) contenait `pattern`,
`minimum`, `maximum`, `maxItems` et une `enum` avec `null` : ils sont retirés. Les mêmes contraintes
restent vérifiées par les modèles Pydantic du contrat (`SortieLLM`). L'empreinte du paquet change
en conséquence.

## 4. Ce qui reste à constater par un appel réel (étape 3)

- Une requête qui combine `tools` et `response_format` : non traitée par la documentation, mais
  constatée en pratique par le banc T-06 sur gpt-5.4-mini (21 sorties conformes sur 21 hors SC-05).
- Le rapport entre `completion_tokens` et les jetons de raisonnement (champ
  `completion_tokens_details.reasoning_tokens`), pour le calcul du coût.
- La valeur par défaut de `reasoning_effort` pour gpt-5.4-mini, non documentée.
- La forme exacte de l'erreur 400 du filtre et de l'annotation, après la création du filtre de D-65.
