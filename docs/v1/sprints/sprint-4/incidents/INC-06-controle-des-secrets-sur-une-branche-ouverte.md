# INC-06 : livraison bloquée par le contrôle des secrets, sur une branche encore ouverte

| Champ                  | Valeur                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| Date                   | 20 octobre 2026, 09:26 UTC                                                                 |
| Environnement          | CI sur `main`, job `secrets` (gitleaks 8.21.2), exécution 39400630835, fusion de la PR 136 |
| Gravité                | Faible : la livraison de la qualification (V-11) a attendu la fusion suivante              |
| Durée                  | 24 min, jusqu'à la livraison de la PR 139 (09:52 UTC)                                      |
| Détection              | À la clôture du sprint 4, en relisant l'historique des livraisons                          |
| Statut                 | Résolu ; aucun secret réel en cause                                                        |
| Compétences illustrées | C21 (résoudre et documenter un incident), C18 (contrôles en CI), C17 (sécurité)            |

## Symptôme

À la fusion de la PR 136 sur `main`, le job `secrets` rend « leaks found: 3 » après avoir lu
101 commits. Le verdict est rouge : rien n'est livré.

## Diagnostic

1. À ce commit, `main` ne comptait que 83 commits (`git rev-list --count 9ad7ef3`) : le contrôle
   en a lu 18 de plus.
2. Le job récupère tout l'historique (`fetch-depth: 0`) et gitleaks lit par défaut toutes les
   références récupérées, branches ouvertes comprises.
3. La branche `feat/garde-fous-sortie` (PR 138), ouverte à 09:20 UTC, contenait des clés de test
   factices écrites en clair dans les tests des garde-fous de sortie. Elle a été fermée à 09:34
   UTC, puis remplacée par la PR 139, où les clés de test sont assemblées à l'exécution.
4. Les livraisons suivantes, qui relisent tout l'historique, sont passées : aucune de ces clés
   n'est dans `main`.

## Cause racine

Des clés de test factices au format réel, écrites en clair, dans une branche poussée. Le contrôle a
fait son travail ; il a seulement bloqué une autre livraison que celle de la branche fautive.

## Correctif

PR 139 (20 octobre) : les clés de test sont assemblées à l'exécution ; aucune chaîne au format d'un
secret n'est versionnée. Pas de changement du contrôle : lire toutes les branches poussées est plus
strict, et c'est voulu.

## Vérification

Toutes les livraisons sur `main` depuis la PR 139 ont un job `secrets` réussi, sur l'historique
complet ; la dernière, celle de la PR 161, aussi.

## Ce qui change dans la façon de travailler

Une donnée de test qui imite un secret est assemblée à l'exécution, jamais écrite en clair, même
dans une branche de travail.
