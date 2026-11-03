# V-2026-11-03-05 : `pull_request_target` bloqué par défaut le 2 décembre

| Champ                         | Valeur                                                                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Date de lecture               | 2026-11-03                                                                                                                                                                |
| Source                        | S09, « pull_request_target blocked by default December 2 », 2 novembre 2026, <https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2> |
| Thème                         | Chaîne de livraison                                                                                                                                                       |
| Vérifiée à la source primaire | Oui : billet du changelog de GitHub lu le 3 novembre                                                                                                                      |

## Résumé

À partir du 2 décembre 2026, GitHub Actions bloque par défaut l'événement `pull_request_target`
dans les dépôts publics, sauf autorisation explicite par une politique d'événements. Deux coupures
d'essai ont lieu les 9 et 16 novembre, de 16:00 à 18:00 UTC. Les dépôts privés ne sont pas
concernés.

## Impact sur Muninn

Aucun. Le dépôt est privé (`gh repo view` : `PRIVATE`), et aucun workflow de `.github/workflows/` n'utilise
`pull_request_target` (recherche du 3 novembre) ; le job `test` de C19 tourne sur `pull_request`.

## Suite

Rien. À relire si le dépôt devenait public.
