# V-2026-11-03-06 : conventions sémantiques OpenTelemetry 1.45.0, rien pour l'IA générative

| Champ                         | Valeur                                                                                                               |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Date de lecture               | 2026-11-03                                                                                                           |
| Source                        | S05, version v1.45.0, 2 novembre 2026, <https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.45.0> |
| Thème                         | Évaluation et observabilité                                                                                          |
| Vérifiée à la source primaire | Oui : notes de la version v1.45.0 lues le 3 novembre, aucune entrée `gen_ai`                                         |

## Résumé

La version 1.45.0 des conventions sémantiques ne contient aucun changement des attributs, spans,
métriques ou événements `gen_ai.*`.

## Impact sur Muninn

Aucun. Les traces de Muninn passent par une liste blanche d'attributs (OB-2,
`docs/conception/industrialisation/03-observabilite.md`) ; rien ne change pour elles.

## Suite

Rien.
