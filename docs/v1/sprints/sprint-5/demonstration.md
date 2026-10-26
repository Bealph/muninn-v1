# Démonstration de la V1 en 10 minutes

Étape 10 de la checklist du sprint 5. **Public :** jury du premier oral, et évaluateur pair.
**Durée :** 10 minutes. **Contenu :** le parcours principal en voix, la correction par l'artisan,
une alerte déclenchée, une livraison automatique et le critère CA-8 assumé. Le texte entre
guillemets est à dire ; le reste est pour toi. Débit visé : environ 140 mots par minute, comme le
pitch (`docs/v1/pitch/pitch-3-minutes.md`).

**Adresses de production :**

- console : <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io>
  (écrans « Démonstration », « Agent », « Qualité ») ;
- livraisons : <https://github.com/Bealph/Muninn/actions/workflows/ci.yml>.

## 1. Préparation

| Quand        | Geste                                                                                                                                                                  | Pourquoi                                                                   |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 30 min avant | `uv run python eval/production/rafale.py --profil derive --nombre 24` (environ 3 min, environ 0,12 €)                                                                  | La dérive simulée (D-84) allume AL-01 sur l'écran « Qualité » pour 1 heure |
| 20 min avant | Fusionner une PR prête et sans risque (une ligne de documentation)                                                                                                     | La livraison automatique sera en cours ou juste finie pendant la démo      |
| 10 min avant | Ouvrir les trois écrans de la console et la page des livraisons ; jouer une fois SC-10 sur « Démonstration »                                                           | Hors trafic, l'application s'endort ; le premier appel est plus lent       |
| 5 min avant  | Ouvrir les secours : `preuves/etape-10-repetition-2-SC-04.png`, `preuves/etape-5-derive-ecran.png`, `ca8/ca8.png`, `infra/azure/schemas/png/1-chaine-de-livraison.png` | Plan B de chaque séquence                                                  |

Le son de l'ordinateur doit être audible de la salle : la conversation est jouée à deux voix.

## 2. Déroulé

| Séquence | Début | Durée    | Écran                    | Ce qui se montre                                            |
| -------- | ----- | -------- | ------------------------ | ----------------------------------------------------------- |
| 1        | 0:00  | 1 min    | Aucun                    | Le problème et la promesse                                  |
| 2        | 1:00  | 2 min 30 | « Démonstration », SC-04 | Un appel manqué joué à deux voix, l'urgence gaz, le dossier |
| 3        | 3:30  | 1 min 30 | « Agent », SC-03         | La correction et la validation par l'artisan (CA-5)         |
| 4        | 5:00  | 1 min 30 | « Qualité »              | Une alerte déclenchée par une dérive simulée                |
| 5        | 6:30  | 2 min    | GitHub Actions           | La livraison automatique, et le retour arrière              |
| 6        | 8:30  | 1 min    | Planche `ca8/ca8.png`    | CA-8 non atteint sur le téléphone, assumé                   |
| 7        | 9:30  | 30 s     | Aucun                    | Conclusion                                                  |

### Séquence 1 · 0:00 · Le problème et la promesse (1 min)

« Un artisan qui travaille seul a les mains prises toute la journée : il manque des appels, et une
demande oubliée, c'est un chantier perdu. Muninn prend l'appel quand il ne décroche pas, annonce
qu'il est une intelligence artificielle, et prépare un dossier vérifié que l'artisan valide d'un
geste. Il parle, Muninn se souvient. Je vous montre la V1, en production, sur des données
synthétiques. »

### Séquence 2 · 1:00 · Un appel joué à deux voix (2 min 30)

- **Je fais :** écran « Démonstration », carte SC-04 « Odeur de gaz », « Lancer l'appel ». La
  sonnerie dure 15 s, la conversation environ 15 s, puis le dossier arrive en moins de 7 s
  (répétitions techniques : 33,9 à 36,3 s du clic au résultat ; 4,4 à 4,9 s après la fin de
  l'appel).
- **Pendant la sonnerie :** « Karim ne décroche pas. Au bout de 15 secondes, l'appel est renvoyé
  vers Muninn. Les deux voix sont des voix de synthèse d'Azure ; tout ce qui s'affiche ensuite vient
  de la vraie chaîne en production. »
- **Au résultat :** montrer le téléphone de Karim. « Le serveur a reconnu le gaz : urgence de
  sécurité, orientation vers Urgence Sécurité Gaz en tête, et aucun rendez-vous proposé. La commune
  et le code postal sont vérifiés dans les référentiels publics. » Puis la chaîne : « Chaque étape
  avec sa durée mesurée : transcription, contrôle d'entrée, qualification, agent, contrôles du
  serveur. L'audio n'est jamais conservé. »
- **Secours :** `preuves/etape-10-repetition-2-SC-04.png` (même écran, joué en production le
  26 octobre).

### Séquence 3 · 3:30 · L'artisan corrige et valide (1 min 30)

- **Je fais :** écran « Agent », scénario SC-03 ; le code postal est « incohérent » avec Bagnolet.
  Dans « Corriger et valider », je remplace le code postal par 93170, puis « Valider le dossier ».
- **À dire :** « Muninn ne maquille rien : la paire commune et code postal est incohérente, il le
  signale. L'artisan corrige, le serveur rejoue le contrôle : les deux passent à vérifié, le
  dossier est validé. La valeur corrigée n'est gardée nulle part, ni en base, ni dans les
  journaux : seule la trace du champ corrigé reste. »
- **Secours :** `preuves/etape-9-ca5.json` (3 sur 3 sur la révision active) et `validation.md`.

### Séquence 4 · 5:00 · Une alerte déclenchée (1 min 30)

- **Je fais :** écran « Qualité ». La rafale de la préparation a joué 24 fois SC-10, une commune
  ambiguë sans indice : chaque dossier finit « à vérifier ».
- **À dire :** « Voici la vigie. Plus de 20 % des dossiers de la dernière heure sont à vérifier,
  sur au moins 20 : l'alerte AL-01 s'allume. C'est une dérive simulée, mais le calcul est celui de
  la production. Une panne du modèle, elle, déclenche AL-04, qui envoie un courriel : nous l'avons
  provoquée lors de l'exercice d'exploitation, le courriel est arrivé 5 minutes et 21 secondes après
  la fin de la rafale. »
- **Secours :** `preuves/etape-5-derive-ecran.png` (alerte AL-01) ; `preuves/etape-8-exercice-panne.json`
  (AL-04).

### Séquence 5 · 6:30 · La livraison automatique (2 min)

- **Je fais :** page des livraisons, le run de la PR fusionnée pendant la préparation : lint,
  tests, build, secrets, évaluation, verdict, puis préproduction et production.
- **À dire :** « Une fusion dans main suffit. La CI vérifie tout, évalue l'agent si le paquet
  d'extraction a changé, puis livre en préproduction et en production. Chaque nouvelle révision est
  contrôlée à sa propre adresse, avec un appel réel au modèle, avant de recevoir le trafic. Si un
  contrôle échoue, rien ne bascule. Et si une version passe mais se dégrade, le retour arrière tient
  en une commande : lors de l'exercice, le service était rétabli en 89 secondes, et SC-01 conforme
  2 minutes 33 après. »
- **Secours :** `infra/azure/schemas/png/1-chaine-de-livraison.png` et le run 40353051573 (PR 198,
  réussi de bout en bout).

### Séquence 6 · 8:30 · CA-8, assumé (1 min)

- **Je fais :** projeter `ca8/ca8.png`.
- **À dire :** le déroulé de `ca8-soutenance.md`, § 7, en version courte : « Sur 21 appels joués, les
  voix sont toujours séparées et le dossier arrive en moins de 18 secondes. Mais le numéro dicté,
  06 99 00 00 01, est entendu avec un zéro de trop : le dossier n'a pas de téléphone. J'aurais pu
  corriger ce numéro-là dans le code ; le test serait passé, Muninn n'aurait pas été meilleur. CA-8
  est donc noté non atteint, avec le diagnostic. »

### Séquence 7 · 9:30 · Conclusion (30 s)

« Le contrat est tenu : six critères sur six, dont cinq mesurés aujourd'hui sur la révision en
production, et la vigie prouvée par la CI et par l'exercice de panne.
Les données sont synthétiques, la téléphonie est simulée : la suite, c'est un opérateur partenaire
et un vrai renvoi d'appel. Merci. »

## 3. Les critères de l'évaluation par le pair

| Critère | Ce que l'évaluateur constate lui-même                                                                                                                                                | En direct                                            | Secours                                                     | Statut                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------ |
| P1      | La dérive simulée allume AL-01 sur l'écran « Qualité » ; il ouvre `docs/exploitation.md`, § 1.3, et suit l'action prévue pour AL-01                                                  | Séquence 4                                           | `preuves/etape-5-derive-ecran.png`, `etape-5-derive.json`   | Prêt                                 |
| P2      | Il lit l'écran « Qualité » sans explication, puis répond à trois questions : le service va-t-il bien ? quelle part des dossiers est à vérifier ? que faire si l'alerte reste rouge ? | Séquence 4 ; réponses consignées dans `retours.md`   | `preuves/etape-4-ecran-qualite-production.png`              | Prêt                                 |
| P3      | Il suit `docs/exploitation.md` seul : déployer, diagnostiquer la panne simulée, faire le retour arrière ; chaque blocage est consigné comme trou de la doc                           | Hors des 10 minutes, sur sa demande (environ 15 min) | `preuves/etape-8-exercice-panne.json` (exercice du porteur) | Prêt                                 |
| P4      | La démo tient en 10 minutes et ne montre que du réel, en production                                                                                                                  | Les sept séquences                                   | Section 5 (répétitions)                                     | Partiel : répétitions orales à faire |
| P5      | La grille de la série (sprints 2 à 5) recense chaque retour, sa décision et son lien                                                                                                 | `../retours-serie.md`                                | Même fichier                                                | Prêt                                 |

## 4. Plan B général

Si la console ne répond pas : les captures de la section 1, dans l'ordre des séquences, puis
`contrat-personnel.md` § 1. Si GitHub ne répond pas : la planche de la chaîne de livraison.

## 5. Répétitions

| N° | Date            | Nature                                            | Résultat                                                                                      | Preuve                               |
| -- | --------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------ |
| 1  | 26 octobre 2026 | Technique, production, sans discours              | SC-04 : 35,9 s, dossier 4,4 s après l'appel ; SC-10 : 34,2 s, 4,9 s ; CA-8 respecté à l'écran | `preuves/etape-10-repetition-1.json` |
| 2  | 26 octobre 2026 | Technique, production, sans discours              | SC-04 : 36,3 s, 4,7 s ; SC-10 : 33,9 s, 4,5 s ; CA-8 respecté à l'écran                       | `preuves/etape-10-repetition-2.json` |
| 3  | À faire         | Orale, chronométrée, par la personne qui présente | Non disponible                                                                                | Durées à consigner ici               |
| 4  | À faire         | Orale, chronométrée, par la personne qui présente | Non disponible                                                                                | Durées à consigner ici               |

Les répétitions techniques (`eval/production/repetition_demo.py`) jouent l'écran
« Démonstration » de production dans Chromium et mesurent ce que la production met à répondre.
Elles ne mesurent pas le discours : le minutage de la section 2 repose sur le débit visé
(140 mots par minute) et reste à confirmer par deux répétitions orales chronométrées.
