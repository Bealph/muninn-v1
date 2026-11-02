# INC-12 : exercice de panne du 2 novembre, de l'alerte jusqu'à l'issue « Incident »

| Champ                  | Valeur                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| Nature                 | Incident provoqué (exercice), en production, sur trafic synthétique                                    |
| Date                   | 2 novembre 2026, de 13:23:31 à 14:04 UTC                                                               |
| Environnement          | Production, API `ca-muninn-api-prod`, commit `11f5321`                                                 |
| Gravité                | Moyenne : 20 dossiers en brouillon de secours, aucun appel perdu, aucune donnée touchée, 0 € de modèle |
| Durée                  | 23 min 34 s de panne servie (13:24:52 à 13:48:26), puis réparation de la configuration à 13:55:14      |
| Détection              | Automatique : écran « Qualité », alerte AL-04 ; issue #210 ouverte par la vigie, lancée à la main      |
| Statut                 | Résolu : retour arrière, puis révision réparée `0000117`, SC-01 conforme ; AL-04 résolue à 15:04:43    |
| Compétences illustrées | C21 (résoudre et documenter un incident), C20 (détection automatique d'incident), C19 (retour arrière) |

## Objectif et attentes fixées d'avance

Prouver la chaîne complète, de la panne jusqu'à l'issue « Incident » ouverte par la vigie (C20), et
rejouer la résolution (C21). Le protocole et les attentes ont été écrits avant l'exercice, avec la
référence de l'exercice du 26 octobre (`../checklist.md`, étape 8).

| Repère | Attendu                                                                     | Mesuré                                                                             | Verdict        |
| ------ | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------- |
| H1     | Une nouvelle révision reçoit 100 % du trafic, avec le mauvais point d'accès | `0000116`, 100 %, `https://panne-simulee.invalid`                                  | tenu           |
| H2     | 20 appels, 20 brouillons de secours, aucun appel perdu                      | 20 dossiers, 20 « à vérifier », 0 échec, 0 € ; écran « Qualité » en alerte         | tenu           |
| H3     | AL-04 déclenchée au plus 20 minutes après la fin de la rafale               | 3 min 52 s (26 octobre : courriel après 5 min 21 s)                                | tenu           |
| H4     | La vigie ouvre une seule issue, et une relance n'en ouvre aucune autre      | issue #210 ouverte ; relance : « Issues à ouvrir : 0 »                             | tenu           |
| H5     | Retour arrière en moins de 2 min, SC-01 conforme, réparation réussie        | service vérifié en 110 s ; réparation réussie ; SC-01 conforme, mais sur `0000117` | tenu en partie |

## Chronologie (UTC)

| Heure    | Événement                                                                                                                   |
| -------- | --------------------------------------------------------------------------------------------------------------------------- |
| 13:21:12 | État initial relevé : révision `0000115` à 100 %, image `11f5321`, bon point d'accès ; 0 alerte sur 24 h ; 0 issue Incident |
| 13:23:31 | `12-panne.sh production --provoquer` lancé                                                                                  |
| 13:24:52 | Trafic à 100 % sur `0000116`, point d'accès `https://panne-simulee.invalid` (révision précédente conservée)                 |
| 13:27:11 | Rafale `rafale.py --profil nominal --nombre 20`                                                                             |
| 13:29:48 | Fin de la rafale : 20 dossiers « à vérifier », 0 échec ; état de la dernière heure : « Alerte » (brouillons de secours)     |
| 13:33:40 | AL-04 (`al04-muninn-modele`) à l'état « Déclenchée », gravité Sev2                                                          |
| 13:37:36 | Vigie lancée à la main en mode réel (`essai=false`) : 1 alerte déclenchée lue                                               |
| 13:38:05 | Issue #210 « Incident · al04-muninn-modele · 2026-11-02T13:33:40.6127406Z » créée, étiquette `incident`                     |
| 13:40:28 | Vigie relancée : 1 alerte lue, 0 issue à ouvrir (doublon évité)                                                             |
| 13:46:54 | Workflow `retour-arriere` lancé sur la production, sans SHA                                                                 |
| 13:48:26 | API à 100 % sur `0000115` (bascule du trafic en 82 s)                                                                       |
| 13:49:10 | Retour arrière vérifié : l'adresse publique sert `11f5321` (110 s après le début du script)                                 |
| 13:53:44 | `12-panne.sh production --reparer` lancé                                                                                    |
| 13:55:14 | `0000117` contrôlée (santé, appel réel au modèle), puis à 100 % ; modèle de l'application réparé                            |
| 14:04    | SC-01 dans la console de production : « conforme à l'attendu », confiance du modèle 0,99, dossier sans alerte               |
| 15:04:43 | AL-04 passe à « Résolue », 91 min après son déclenchement (26 octobre : 90 min)                                             |
| 15:04:44 | Groupe d'actions `ag-muninn` exécuté ; courriel « Resolved » reçu à 15:04 dans la boîte de réception                        |

## Ce que chaque outil a vu

- **Écran « Qualité »** (état rendu par la rafale) : alerte sur la dernière heure, « brouillons de
  secours » et « dossiers à vérifier ». La première est la cause, la seconde sa conséquence.
- **Azure Monitor** : AL-04 déclenchée 3 min 52 s après la fin de la rafale, sur les journaux de
  l'API de production. Courriel « Fired:Sev2 » reçu par le porteur à 13:33 UTC, d'après l'heure
  affichée par la messagerie (capture gardée hors du dépôt : boîte personnelle).
- **Vigie** : l'alerte déclenchée est lue et transformée en issue au format INC, avec la règle,
  l'heure, la gravité et la ressource. L'identifiant de l'alerte, écrit dans l'issue, empêche le
  doublon.
- **Retour arrière** : la révision fautive est une révision de configuration (même image) ; le
  script revient à la révision créée juste avant, saine, et vérifie le commit servi.
- **Classeur d'exploitation** : non consulté pendant cet exercice ; la cause était connue
  d'avance (panne provoquée).

## Cause

Panne provoquée : le point d'accès du modèle (`AZURE_AI_ENDPOINT`) est remplacé par une adresse
invalide sur une nouvelle révision, qui reçoit le trafic. Chaque appel au modèle échoue ; Muninn
rend des brouillons de secours, sans perdre d'appel.

## Résolution

1. Rétablir : retour arrière sur la révision précédente (`0000115`), 110 s jusqu'au service
   vérifié.
2. Réparer la configuration : `--reparer` remet le bon point d'accès sur une nouvelle révision
   (`0000117`), contrôlée par un appel réel au modèle avant la bascule. Le modèle de l'application
   porte de nouveau le bon point d'accès : la livraison suivante n'héritera pas de la panne.
3. Vérifier : SC-01 conforme dans la console (preuve : `../preuves/exercice-2-novembre-sc01.png`).

## Écarts au protocole

1. **SC-01 contrôlé après la réparation, et non après le retour arrière.** La réparation a été
   lancée avant le contrôle prévu. Entre 13:49:10 et 13:55:14, `0000115` a servi le bon commit
   (vérifié par le retour arrière), sans appel SC-01. La mesure « SC-01 conforme après le retour
   arrière » n'est pas faite ce jour ; elle avait donné 2 min 33 s le 26 octobre.
2. **Vigie lancée à la main.** Le workflow planifié de la vigie n'a déclenché aucune exécution
   automatique depuis son ajout le 2 novembre à 09:07 UTC, malgré une nouvelle expression de
   planification (PR n° 208). Le chemin de l'alerte à l'issue est prouvé, son lancement
   automatique ne l'est pas.
3. **Retour arrière plus lent.** 110 s jusqu'au service vérifié, contre 89 s le 26 octobre, sous le
   seuil de 2 minutes. Une mesure isolée : pas de conclusion sur une tendance.

## Suites données

- Planification de la vigie : vérification le 3 novembre au matin ; sans exécution automatique,
  déclencheur Azure (option B de `docs/suivi/reste-a-faire.md`).
- Issue #210 : complétée au format INC, fermée avec la PR de cette fiche.
- Courriel de résolution d'AL-04, question ouverte depuis le 29 octobre : élucidée. L'historique de
  l'alerte du 26 octobre montre la résolution à 11:03:42 UTC et le groupe d'actions exécuté une
  seconde plus tard ; le courriel « Resolved » a bien été reçu à 11:03 UTC, puis s'est retrouvé
  dans la corbeille de la messagerie, supprimé à la main par mégarde (aucun filtre de tri en cause, vérifié par le porteur). Ni la règle, ni le
  groupe d'actions, ni Azure ne sont en cause : aucun silence des actions, aucune règle de
  traitement des alertes, destinataire actif. Ce jour, le courriel « Resolved » est arrivé dans la boîte de
  réception à 15:04 UTC, une seconde après la résolution : la notification fonctionne de bout en
  bout, au déclenchement comme à la résolution.
- L'issue porte l'identifiant de l'abonnement Azure dans son marqueur caché : sans risque dans un
  dépôt privé, à revoir si le dépôt devient public.

## Ce qui change dans la façon de travailler

Un exercice s'écrit avant d'être joué : attentes chiffrées, référence de l'exercice précédent,
ordre des étapes. Les écarts se voient alors, et se disent, au lieu d'être rattrapés.
