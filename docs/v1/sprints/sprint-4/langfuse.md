# Sprint 4 : Langfuse (V-13)

Étape 10 de la checklist (D-49 ; gardé, non négociable, décision du porteur du 19 octobre 2026).
Code : `src/muninn/observabilite.py` ; tests : `tests/test_observabilite.py`,
`tests/test_evaluation.py` ; clés : `infra/azure/07-langfuse.sh`.

## 1. Ce qui est tracé

| Observation     | Type Langfuse | Métadonnées envoyées en production                                                    |
| --------------- | ------------- | ------------------------------------------------------------------------------------- |
| `appel`         | span (racine) | Issue (dossier, message, trace), garde-fous du message ; `request_id`, environnement  |
| `qualification` | chain         | Catégorie, proposition du modèle, confiance, règle du serveur, sécurité               |
| `extraction`    | span          | Statut, « à vérifier », motifs, garde-fous, statuts des contrôles                     |
| `agent`         | agent         | Statut, tentatives, étapes, outils appelés, borne, coût                               |
| outil           | tool          | Nom (ou `outil_inconnu`), statut, durée, nombre de communes rendues                   |
| `llm`           | generation    | Modèle, jetons d'entrée et de sortie, coût, durée, raison de fin, détournement annoté |

**Jamais en production** : le texte de l'appel, les messages au modèle, sa réponse, les valeurs du
dossier, les arguments des outils (R3, R4). Le contenu n'est envoyé que par le harnais d'évaluation,
sur données synthétiques (R9). Testé : en production, ni le nom, ni la rue, ni le numéro n'apparaissent
dans les traces exportées ; une panne de Langfuse ne fait jamais échouer un appel.

## 2. Choix techniques

- SDK `langfuse` **4.15.6** (24 septembre 2026), épinglé (D-49 : branche 4.x, publiée depuis plus de
  deux semaines). La 4.17.0 est écartée par la règle `exclude-newer` du projet ; la 5.x par D-49.
  API vérifiée sur la bibliothèque installée : `start_as_current_observation`,
  `propagate_attributes`, `run_experiment`, `score_current_trace` (la v4 n'a plus
  `start_as_current_span` ni `update_current_trace`).
- **Sans clés, aucun client** : ni trace ni erreur ; tests et CI ordinaire inchangés.
- **Traceur OpenTelemetry isolé**, jamais enregistré comme fournisseur global.
- **Décorateur typé** (`tracer`, `ParamSpec`) : les fonctions tracées gardent leur signature,
  vérifiée par mypy.
- Région UE, `https://cloud.langfuse.com` ; palier gratuit Hobby : 50 000 unités par mois, 30 jours
  d'accès aux données (pas une durée de conservation, Langfuse, page des prix).

## 3. Jeux de données et expériences

Quand les clés sont présentes, le harnais V-08 publie les 20 scénarios de test dans le dataset
`muninn-v08-test` (identifiants stables : mise à jour, pas de doublon), puis joue le passage de
l'agent comme une expérience Langfuse « V-08 agent », un score `exact_<champ>` par champ, une
exécution à la fois (limite de débit d'Azure). Le verdict reste celui du harnais : la CI échoue en
cas de régression (cas bloquants, seuil global), avec ou sans Langfuse. Si Langfuse échoue en route,
le harnais joue lui-même ce qui manque.

## 4. Ce qui reste à faire par le porteur, puis à vérifier

1. Compte Langfuse Cloud UE et **deux projets** (R10) : `muninn` (traces de production) et
   `muninn-evaluation` (CI) ; une paire de clés par projet. Le job d'évaluation exécute le code d'une
   PR : il ne reçoit jamais les clés de production (revue de sécurité du 20 octobre 2026).
2. Clés dans `.env`, jamais dans le dépôt : `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` (production),
   `LANGFUSE_EVAL_PUBLIC_KEY`, `LANGFUSE_EVAL_SECRET_KEY` (évaluation) ; puis
   `bash infra/azure/07-langfuse.sh`.
3. Vérification : une campagne locale (dataset et expérience visibles dans le projet d'évaluation) et
   un appel de l'écran « Agent » en production (trace sans contenu dans le projet de production).

**Projet visé.** L'API vise le projet `muninn` (`LANGFUSE_*`). Le harnais d'évaluation vise
`muninn-evaluation` dès que `LANGFUSE_EVAL_*` est défini (en local, `.env` porte les deux paires) ;
en CI, l'environnement `evaluation` ne reçoit que les clés d'évaluation. Une exécution locale de
l'API envoie ses traces au projet de production, étiquetées `environment=local`.

**Revue de sécurité** : le nom d'un outil demandé par le modèle n'est jamais tracé hors de la liste
fermée (`outil_inconnu`), testé.
