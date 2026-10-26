# Contrat personnel : état critère par critère, fin du sprint 5

Étape 9 de la checklist du sprint 5. État au **26 octobre 2026**, révision active de production
`git_sha` 9dee403 (API et console), modèle retenu gpt-5.4-mini. Il remplace l'état du sprint 4
(`../sprint-4/contrat-personnel.md`, 21 octobre), gardé tel quel pour l'historique.
Critères : dossier V1, § 6 (CA-1 à CA-6, le contrat) et critères complémentaires de la v1.5
(CA-7, CA-8, hors contrat).

Statuts : **tenu** (vérifié sur la révision active dans sa forme en vigueur, chaque série à 3 sur
3) ; **non atteint** (mesuré, écart constaté et documenté) ; **avenant** (forme modifiée par une
décision écrite, indiquée à côté du statut).

## 1. Synthèse

| Critère | Intitulé                        | Statut      | Avenant    | Preuve sur la révision active                                   |
| ------- | ------------------------------- | ----------- | ---------- | --------------------------------------------------------------- |
| CA-1    | Le parcours promis              | Tenu        | Aucun      | 3/3, `preuves/etape-9-criteres.json`                            |
| CA-2    | Les décisions de l'agent        | Tenu        | D-69, D-78 | 6/6 (SC-07, SC-10), `preuves/etape-9-criteres.json`             |
| CA-3    | Le garde-fou de sécurité        | Tenu        | Aucun      | 3/3 (SC-04), `preuves/etape-9-criteres.json`                    |
| CA-4    | La résistance à la manipulation | Tenu        | Aucun      | 3/3 (SC-05), `preuves/etape-9-criteres.json`                    |
| CA-5    | La correction et la validation  | Tenu        | Aucun      | 3/3, `preuves/etape-9-ca5.json` ; « 93170 » absent des journaux |
| CA-6    | La vigie                        | Tenu        | D-79       | Partie 1 : PR n° 147 bloquée ; partie 2 : SC-01 en 2 min 33 s   |
| CA-7    | La qualification des appels     | Tenu        | Aucun      | 24/24 (SC-Q1 à SC-Q8), `preuves/etape-9-criteres.json`          |
| CA-8    | La voix                         | Non atteint | D-74       | SC-01 0/3, téléphone seul en écart (INC-09) ; démonstration 4/4 |

Bilan du contrat (CA-1 à CA-6) : **6 tenus sur 6**, dont deux avec avenant (CA-2, CA-6).
Critères complémentaires : CA-7 tenu ; CA-8 non atteint sur le téléphone, limite de la
transcription mesurée et assumée (`ca8-soutenance.md`).

## 2. Mesures du 26 octobre sur la révision 9dee403

| Heure (UTC) | Script                                 | Critères                     | Résultat                  |
| ----------- | -------------------------------------- | ---------------------------- | ------------------------- |
| 16:43       | `eval/production/verifier_criteres.py` | CA-1, CA-2, CA-3, CA-4, CA-7 | 3/3, 6/6, 3/3, 3/3, 24/24 |
| 16:45       | `eval/production/verifier_ca5.py`      | CA-5                         | 3/3                       |
| 16:47       | `eval/production/verifier_ca8.py`      | CA-8                         | 0/3 ; démonstration 4/4   |

Le verdict de chaque exécution vient du serveur (`conformity`), complété par les contrôles du
texte des critères que le serveur ne fait pas encore (`complements` du script : nom de SC-01,
objet et statuts de SC-05, statuts de SC-07, code postal et département des candidates de
SC-10). CA-1 exige aussi le dossier en 30 s au plus, mesurées côté client.

## 3. Détail des critères qui ont changé depuis le sprint 4

### CA-5. La correction et la validation

- **Forme en vigueur** : dossier V1, § 6, sans changement. Livré au sprint 5, étape 2 (V-09,
  D-86) : `validation.md`.
- **Preuve** : `preuves/etape-9-ca5.json`, 3/3 : SC-03 joué, code postal corrigé en « 93170 »,
  dossier validé en une requête ; commune et code postal « vérifié », dossier « validé », champ
  corrigé cité.
- **Valeur jamais gardée** : requêtes Log Analytics du 26 octobre, sur les deux heures qui couvrent
  les trois corrections : 1 133 lignes de journaux des applications (dont 3 `revue.fin`) et 330
  traces d'Application Insights, aucune ne contient « 93170 ». La table `app.corrections` ne garde
  que le chemin et la date, jamais la valeur (conception, et `tests/test_revue_base.py`) ; son
  comptage a été vérifié à l'étape 2 (`consulter-base.sh --traitements`, lancé par le porteur).

### CA-6. La vigie

- **Partie 1, avenant D-79** : inchangée depuis le sprint 4 : PR n° 147 (consigne dégradée)
  bloquée par l'évaluation, `verdict` rouge, fusion refusée.
- **Partie 2, tenue** : exercice du 26 octobre (`preuves/etape-8-exercice-panne.json`), mené par
  le porteur avec le seul guide d'exploitation : version dégradée en production (révision
  `0000095`, point d'accès du modèle invalide), retour arrière lancé à 09:41:50 UTC (workflow
  `retour-arriere`), SC-01 conforme à CA-1 à 09:44:23 UTC, soit **2 min 33 s** après le lancement,
  pour moins de 5 minutes exigées.
- **Écart de forme, assumé** : le critère parle de « cette même version » que celle de la partie 1.
  Elle n'a jamais pu être déployée, puisque la CI l'a bloquée : c'est ce que la partie 1 prouve. La
  version dégradée de la partie 2 est donc la panne type de l'étape 8, déployée par un script.

### CA-8. La voix

- **Avenant D-74** : 45 secondes comptées depuis la fin de l'appel joué.
- **Mesure** : quatre mesures le 26 octobre (`preuves/etape-6-ca8-premiere-mesure.json`,
  `etape-6-ca8-deuxieme-mesure.json`, `etape-6-ca8.json`, `etape-9-ca8.json`) ; à la dernière,
  sur 9dee403 : SC-01 de 5,1 à 6,6 s, locuteurs séparés, transcription jugée fidèle, issue
  « dossier », un seul écart à l'attendu de CA-1 : `telephone`. Démonstration 4 sur 4.
- **Statut** : non atteint sur le téléphone. La transcription d'Azure entend « 06 99 00 00 01 »
  avec un zéro de trop ; aucune correction ajustée au test (décision du porteur, INC-09).

## 4. Avenants en vigueur

Inchangés depuis le sprint 4 : D-69 et D-78 (CA-2), D-79 (CA-6, partie 1), D-74 (CA-8). Voir
`../sprint-4/contrat-personnel.md`, § 3, et `docs/decisions.md`.

## 5. Limites

- 3 exécutions sur 3 prouvent la stabilité sur la révision servie, pas un taux. Les taux, avec
  leurs intervalles, sont ceux de l'évaluation V-08 (`../sprint-4/evaluation.md`).
- Les vérifications passent par l'API (`POST /v1/demo/runs`, `/review`, `/voice/*`), celle qu'appelle
  la console, et non par un clic dans l'écran : le chemin côté serveur est le même ; le parcours à
  l'écran est montré dans la démonstration (étape 10).
- Les contrôles `complements` du texte des critères restent dans le script de production ; leur
  report dans `muninn.demo.verification` est l'objet de l'étape 7.
