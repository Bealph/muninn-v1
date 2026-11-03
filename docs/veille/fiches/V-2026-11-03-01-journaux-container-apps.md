# V-2026-11-03-01 : la destination de journaux Log Analytics de Container Apps devient héritée

| Champ                         | Valeur                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Date de lecture               | 2026-11-03                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Source                        | S01, « Announcing: Migrate Azure Container Apps logging destination from Log Analytics to Azure Monitor », 28 octobre 2026, <https://azure.microsoft.com/updates?id=577689>                                                                                                                                                                                                                                                                                                          |
| Entrée de collecte            | <https://azure.microsoft.com/updates?id=577689>                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Thème                         | Modèles et services d'IA (hébergement)                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Vérifiée à la source primaire | Oui, trois pages lues le 3 novembre : l'annonce (texte complet par l'API d'Azure Updates) ; [G1] « Change Container Apps logging from Log Analytics to Azure Monitor », mise à jour le 14 août 2026, <https://learn.microsoft.com/azure/container-apps/migrate-logs-azure-monitor> ; [G2] « Migrate from the HTTP Data Collector API to the Logs ingestion API », mise à jour le 29 septembre 2026, <https://learn.microsoft.com/en-us/azure/azure-monitor/logs/custom-logs-migrate> |

## En clair

Azure déclasse l'ancienne façon de ranger les journaux des applications de Muninn ; elle devient une
option « héritée ». Elle fonctionne encore, sans date d'arrêt annoncée, mais au changement de
destination les alertes branchées dessus ne reçoivent plus de données. Muninn est directement
concerné : l'alerte AL-04 et le classeur d'exploitation lisent l'ancien emplacement.

## Résumé

La destination « Log Analytics » des journaux de Container Apps est désormais une option héritée
(annonce). Elle repose sur l'API HTTP Data Collector, dont le support a pris fin le 14 septembre
2026, « although ingestion continues to function » pour les clients en TLS 1.2 ou plus récent
([G2], introduction). Aucune date d'arrêt de l'ingestion n'est annoncée dans ces pages. Microsoft
recommande la destination « Azure Monitor », qui écrit dans `ContainerAppConsoleLogs` au lieu de
`ContainerAppConsoleLogs_CL`, avec `Log` au lieu de `Log_s` et `ContainerAppName` au lieu de
`ContainerAppName_s` ([G1], « Update queries and alerts »).

## Impact sur Muninn

Direct. L'environnement `cae-muninn` utilise la destination Log Analytics (`az containerapp env
show … --query properties.appLogsConfiguration.destination`, le 3 novembre : `log-analytics`).
Deux éléments en service lisent `ContainerAppConsoleLogs_CL` (recherche dans le dépôt le 3
novembre) : la règle AL-04 (`infra/azure/alertes/al04.kql`) et le classeur d'exploitation
(`infra/azure/classeur/requetes.kql`). D'après [G1] (« Plan for the monitoring transition ») :
les alertes qui lisent les tables `_CL` ne reçoivent plus de nouvelles données dès le changement
de destination, et le nouveau routage peut mettre jusqu'à 90 minutes à s'activer.

## Suite

Recommandation R1 de la synthèse S-2026-11-03.
