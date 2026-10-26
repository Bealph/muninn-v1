# Compte rendu du sprint 5 : la vigie et la démo

**Période :** 22 au 26 octobre 2026 (prévu du 22 au 25 octobre au matin, D-81)
**Périmètre :** V1, éléments V-09, V-10 et V-12, plus la « V1.0 complète » : traces vers Application
Insights et alerte Azure Monitor (`docs/v1/dossier-conception-v1.md`, § 2.4) ; décisions D-81 à
D-88
**Compétences servies :** C10, C11, C13, C16, C19, C20, C21

## 1. Objectif et résultat

**Objectif (consigne) :** rendre le système pilotable et reprenable : métriques et traces, tableau
de bord lisible par un non-développeur, alertes à seuils argumentés chacune liée à une action,
documentation d'exploitation qu'un tiers peut suivre seul. Le sprint se termine par la répétition
de la démonstration finale.

**Résultat : atteint, avec trois réserves écrites.** En production, l'écran « Qualité » dit la
santé du service en mots et en couleurs ; trois alertes ont chacune un seuil argumenté et une action
dans `docs/exploitation.md`, dont AL-04, envoyée par courriel par Azure Monitor ; le guide
d'exploitation a été suivi seul par le porteur pour une panne réelle et son retour arrière ; l'écran
« Démonstration » joue un appel manqué à deux voix et la vraie chaîne. Le contrat personnel est
tenu, 6 sur 6, sur la révision active.

Réserves : CA-8 non atteint sur le téléphone (limite de la transcription, INC-09) ; répétitions
orales de la démo à faire par la personne qui présente ; deux reprises du sprint 4 reportées après
le premier oral (dialogues de l'annexe A, rôle restreint de l'identité), par décision écrite.

## 2. Critères de l'évaluation par le pair

| N° | Critère                                                                     | Statut            | Preuve                                                                                                                                       |
| -- | --------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| P1 | Une dérive simulée déclenche l'alerte prévue, et l'action documentée existe | Prouvé            | Dérive en production, AL-01 affichée (`preuves/etape-5-derive*.png/json`) ; AL-04 par courriel en 5 min 21 s (`etape-8-exercice-panne.json`) |
| P2 | Le tableau de bord est compris sans explication orale                       | Prêt, à constater | Écran « Qualité » en production ; questions de compréhension prévues (`demonstration.md`, § 3) ; réponses à consigner                        |
| P3 | Le test de la doc : déployer, diagnostiquer, retour arrière, seul           | Prouvé            | Relecture par un évaluateur simulé (12 constats traités) ; exercice réel du porteur, seul avec le guide, sans blocage                        |
| P4 | La démo répétée tient en 10 minutes et montre du réel                       | Partiel           | `demonstration.md` ; deux répétitions techniques en production ; répétitions orales à faire                                                  |
| P5 | Grille de retours tenue sur l'ensemble de la série                          | Prouvé            | `../retours-serie.md`, sprints 2 à 5 ; aucun retour du pair reçu à ce jour                                                                   |

## 3. Ce qui a été livré

| Étape     | Livrable                                                                                                                             | PR             |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| 0         | Checklist, calendrier et décisions D-81 à D-84, grille des retours                                                                   | 171            |
| 1         | Traitements enregistrés dans le schéma `app`, rôle dédié (D-82, D-85)                                                                | 173            |
| 2         | Correction et validation par l'artisan (V-09, D-86) ; CA-5 vérifié en production                                                     | 175, 176       |
| 3         | Métriques tirées de la base, étapes d'un appel, traces vers Application Insights (D-87) ; INC-07                                     | 179 à 182      |
| 4         | Écran « Qualité » (deux versions), AL-16, classeur Azure Monitor                                                                     | 183 à 188      |
| 5         | Alerte Azure Monitor AL-04 par courriel, dérive simulée constatée, guide des alertes                                                 | 189            |
| 8         | Guide d'exploitation, panne type simulable, retour arrière corrigé ; exercice réussi ; INC-08                                        | 190, 191       |
| 6         | Voix simulée (D-88) et écran « Démonstration » ; relectures code, sécurité, accessibilité ; CA-8 mesuré quatre fois ; INC-09, INC-10 | 193, 195 à 198 |
| —         | Schémas de la chaîne de livraison ; style commun des diagrammes et des infographies ; suivi                                          | 192, 194, 199  |
| 9         | Contrat personnel sur la révision active : 6 sur 6                                                                                   | 200            |
| 7, 10, 11 | Contrôles des critères dans la vérification du serveur ; rôle de l'identité étudié ; démo écrite et répétée ; clôture                | celle-ci       |

## 4. Mesures

| Mesure                                     | Valeur                                                                                                       | Source                                          |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------- |
| Contrat sur la révision active (`9dee403`) | CA-1 3/3, CA-2 6/6, CA-3 3/3, CA-4 3/3, CA-5 3/3, CA-7 24/24 ; CA-6 partie 2 : SC-01 en 2 min 33 s           | `contrat-personnel.md`                          |
| CA-8, appel joué à deux voix               | 21 parcours en trois mesures : locuteurs séparés 21 sur 21, 3,9 à 17,4 s ; téléphone de SC-01 absent 9 sur 9 | `preuves/etape-6-ca8*.json`, `etape-9-ca8.json` |
| Démonstration jouée à l'écran, production  | 33,9 à 36,3 s du clic au résultat ; dossier 4,4 à 4,9 s après la fin de l'appel                              | `preuves/etape-10-repetition-*.json`            |
| AL-04, délai du courriel                   | 5 min 21 s après la fin de la rafale                                                                         | `preuves/etape-8-exercice-panne.json`           |
| Retour arrière                             | Trafic basculé en 61 s, service vérifié en 89 s                                                              | `preuves/etape-8-exercice-panne.json`           |
| Coût d'une mesure de CA-8 (7 parcours)     | Environ 0,10 € (estimation du script)                                                                        | `eval/production/verifier_ca8.py`               |
| Livraisons sur `main` depuis le 22 octobre | 29 réussies, dont 3 après relance (INC-08, INC-10) ; médiane 16,4 min                                        | Historique GitHub Actions                       |
| Tests                                      | 700 en conteneur, base de test comprise                                                                      | `make tests-conteneur`                          |

## 5. Incidents

| Fiche  | Incident                                                             | Cause racine                                                        | Non-régression                                     |
| ------ | -------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------- |
| INC-07 | Trafic resté sur l'ancienne révision après une mise à jour           | Nom de révision pris dans une réponse périmée d'Azure               | `nouvelle_revision` relue ; tests                  |
| INC-08 | Livraison interrompue par `ServerTimeout`                            | Erreur passagère absente de la reprise d'`az_tenace`                | Motif ajouté ; `tests/test_livraison.py`           |
| INC-09 | Numéro dicté transcrit avec un zéro de trop ; CA-8 non atteint       | Limite de la transcription d'Azure sur « 00 00 »                    | Limite documentée, sans correction ajustée au test |
| INC-10 | Livraisons interrompues (miroir Ubuntu lent, révision dite invalide) | Limite de 15 min trop juste ; réponse incohérente passagère d'Azure | Limite à 30 min ; motif repris ; test              |

Défauts trouvés et corrigés avant livraison, sans incident : contenu marqué synthétique sans
preuve (revue de sécurité de la voix), contrôle de fidélité trop strict puis trop large, quatre
non-conformités d'accessibilité de l'écran « Démonstration », schéma de déploiement en partie tiré
de mémoire puis refait à la source.

## 6. Décisions du sprint

D-81 (calendrier), D-82 (traitements enregistrés), D-83 (trois alertes), D-84 (dérive simulée),
D-85 (rôle d'écriture dédié), D-86 (correction et validation en une requête), D-87 (traces vers
Application Insights), D-88 (voie A de la voix). Décisions du porteur du 26 octobre, consignées dans
les fiches : CA-8 constaté et assumé (INC-09) ; contrôle de fidélité assoupli (INC-09). Décisions
prises sous délégation, réversibles : reports de l'étape 7 (checklist, étape 7).

## 7. Dettes et risques ouverts

| Sujet                                                            | Risque                                                           | Traitement proposé                                         |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------- |
| CA-8 : numéro dicté mal transcrit                                | Dossier sans numéro dicté                                        | Benchmark des services de transcription (carte #92)        |
| Tolérance de fidélité (5 mots), calée sur trois mesures          | Une transcription plus bruitée refusée, ou un nom glissé accepté | Remesurer à chaque mesure de CA-8                          |
| Rôle Foundry User plus large que l'inférence                     | Identité de l'application capable de lire les clés               | Plan en quatre temps (`role-identite.md`), après l'oral    |
| Dialogues de l'annexe A antérieurs à la trame v1.2               | Consigne de sécurité non dite par Muninn dans SC-04              | Réécriture relue par le porteur, après l'oral              |
| Répétitions orales de la démo                                    | Démo hors des 10 minutes                                         | Deux répétitions chronométrées avant le 29 octobre         |
| AL-04 ne surveille que l'API de production                       | Panne en préproduction sans courriel                             | Assumé (`docs/exploitation.md`, § 1.2)                     |
| Migrations faites par la tâche des données, pas par la livraison | Nouvelle version sur l'ancien schéma jusqu'au 3 du mois          | Lancer `donnees` après une livraison qui migre (carte #95) |
| Dépendances du navigateur de la CI sans cache                    | Lenteur du miroir Ubuntu                                         | Limite à 30 min ; cache à étudier                          |
| Journal des retours du pair                                      | Critères P5 et P6 sans retour réel                               | Retours à consigner le jour de l'évaluation                |
