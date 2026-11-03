# V-2026-11-03-02 : le SDK Python de Langfuse passe en version 5

| Champ                         | Valeur                                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Date de lecture               | 2026-11-03                                                                                                                                 |
| Source                        | S04, versions du SDK Python : v5.0.1 le 14 octobre 2026, v5.1.0 le 30 octobre 2026, <https://github.com/langfuse/langfuse-python/releases> |
| Entrée de collecte            | <https://github.com/langfuse/langfuse-python/releases/tag/v5.1.0>                                                                          |
| Thème                         | Évaluation et observabilité                                                                                                                |
| Vérifiée à la source primaire | Oui : notes de version (API GitHub) et guide de migration, <https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5>      |

## En clair

Langfuse, l'outil qu'utilise Muninn pour observer et évaluer son modèle d'IA, sort la version 5 de
son SDK Python, qui retire plusieurs fonctions. Muninn reste fixé sur la version 4.15.6 et n'utilise
aucune des fonctions retirées : l'impact est faible. Le guide ne dit pas jusqu'à quand la version 4
recevra des correctifs.

## Résumé

La version 5 du SDK retire plusieurs API : les accesseurs `set_current_trace_io()` et
`span.set_trace_io()`, `blocked_instrumentation_scopes`, les méthodes dépréciées `api.trace.get`,
`api.sessions` et `api.legacy.*`, les assistants des « dataset runs » (remplacés par l'API des
expériences). `api.scores.create` prend désormais une liste. La version 5 demande Python 3.11 ou
plus. Le guide ne dit pas jusqu'à quand la version 4 reçoit des correctifs.

## Impact sur Muninn

Faible. Muninn épingle `langfuse==4.15.6` (D-49), parue le 24 septembre 2026. Recherche dans
`src/`, `eval/` et `tests/` le 3 novembre : aucune des API retirées n'est utilisée ; le harnais
d'évaluation appelle déjà `run_experiment`, la voie recommandée. Python 3.12 convient
(`requires-python = ">=3.12,<3.13"` dans `pyproject.toml`).

## Suite

Recommandation R2 de la synthèse S-2026-11-03.
