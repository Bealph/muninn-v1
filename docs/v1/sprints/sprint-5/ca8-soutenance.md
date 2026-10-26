# CA-8 devant le jury : la voix, non atteint sur le téléphone

Fiche de présentation du critère CA-8 pour la soutenance. Elle s'appuie sur trois mesures faites en
production le 26 octobre 2026 et sur l'incident INC-09. La planche à projeter est `ca8/ca8.png`
(source `ca8/ca8.svg`, produite par `ca8/generer.py`).

## 1. Le critère

> **CA-8. La voix.** Étant donné le dialogue de SC-01, quand je clique sur « Jouer et traiter »,
> alors le serveur synthétise l'appel, le navigateur le joue, la transcription affichée distingue
> l'agent et l'appelant, et le dossier satisfait les valeurs attendues de CA-1 en 45 secondes au
> plus, comptées depuis le clic. Après traitement, aucun octet audio ne subsiste côté serveur : ni
> en base, ni en fichier, ni dans les journaux (TC-10).

Source : `docs/v1/dossier-conception-v1.md`. L'avenant D-74 (`docs/decisions.md`) fait compter les
45 secondes depuis la fin de l'appel joué, et non depuis le clic.

## 2. Le résultat en une phrase

CA-8 est **non atteint sur le téléphone** : tout le reste du critère est tenu, mais la transcription
d'Azure entend le numéro dicté de SC-01 avec un zéro de trop, si bien que le dossier n'a pas de
téléphone. La limite est mesurée, expliquée et assumée.

## 3. Élément par élément

| Exigence de CA-8                                | Mesure                                                                                    | Résultat     |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------ |
| Le serveur synthétise l'appel                   | 21 parcours sur la production, deux voix neuronales (Denise, Henri)                       | Tenu         |
| Le navigateur le joue                           | Parcours de l'écran « Démonstration » joué dans Chromium par les tests, sans sortie son   | Tenu (tests) |
| La transcription distingue agent et appelant    | 21 parcours sur 21, même suite de locuteurs que le dialogue                               | Tenu         |
| 45 s au plus après l'appel (D-74)               | De 3,9 à 17,4 s sur les 21 parcours                                                       | Tenu         |
| Le dossier de SC-01 satisfait l'attendu de CA-1 | Issue « dossier » 9 fois sur 9 ; un seul champ en écart, `telephone`, 9 fois sur 9        | Non atteint  |
| Aucun audio côté serveur (TC-10)                | Tests de l'API et de la console : aucun fichier temporaire ouvert, rien dans les journaux | Tenu (tests) |

Les quatre scénarios de la démonstration (SC-Q4, SC-04, SC-Q1, SC-10) sont conformes à leur attendu
à la troisième mesure : **4 sur 4**.

## 4. Pourquoi le téléphone manque

1. L'appelant de SC-01 dicte « 06 99 00 00 01 », un numéro de la tranche fictive (R9).
2. La transcription rapide d'Azure rend « 06 99 00 000 01 » à chaque passage : onze chiffres, donc
   un numéro invalide, que l'extraction ne retient pas.
3. Trois façons de faire lire le numéro à la voix ont été essayées, deux fois chacune (texte brut,
   pauses entre les paires, balise « téléphone » du SSML) : la même erreur revient. La réponse
   d'Azure ne contient pas de forme en mots qui permettrait de recompter les zéros.
4. Le dossier reste sûr : il n'a pas de numéro dicté, et aucun numéro n'est inventé.

Détail et preuves : `incidents/INC-09-numero-dicte-mal-transcrit.md`,
`preuves/etape-6-ca8-premiere-mesure.json`, `preuves/etape-6-ca8-deuxieme-mesure.json`,
`preuves/etape-6-ca8.json`.

## 5. Ce qui a été écarté, et pourquoi

Trois moyens auraient fait réussir la mesure sans rendre Muninn meilleur :

- réécrire « 000 » en « 00 » pour ce numéro : la règle ne vaudrait que pour le test ;
- donner le numéro à la transcription, par une liste de phrases : ce serait lui souffler la réponse ;
- changer le numéro : impossible, il doit rester dans la tranche fictive (R9).

Décision du porteur, le 26 octobre 2026 : constater et documenter, sans ajuster le système au test.

## 6. Ce que la mesure a corrigé ailleurs

Les deux premières mesures ont aussi montré un défaut réel : le contrôle de fidélité, qui décide si
un appel joué est bien le dialogue synthétique, refusait des transcriptions presque exactes
(« 8h » ou « 8h00 » pour « 8 heures », homophones). Il a été assoupli, avec l'accord du porteur,
puis resserré après une revue de sécurité. La démonstration est passée de 2 sur 4 à 4 sur 4.

## 7. Déroulé oral (environ 90 secondes)

1. **Le critère** (15 s) : « CA-8 demande qu'un appel joué à voix haute donne le même dossier que
   le texte, en 45 secondes. »
2. **Ce qui marche** (20 s) : « Sur 21 appels joués en production, les deux voix sont toujours
   séparées et le dossier arrive en 4 à 17 secondes. Les quatre scénarios de la démonstration sont
   conformes. »
3. **Ce qui ne marche pas** (25 s) : montrer la colonne centrale de la planche. « Le numéro dicté,
   06 99 00 00 01, est entendu avec un zéro de trop. Le numéro est invalide, le dossier n'en a pas.
   J'ai essayé trois lectures : le défaut est dans la transcription. »
4. **Le choix** (20 s) : « J'aurais pu corriger ce numéro-là dans le code. Le test serait passé,
   Muninn n'aurait pas été meilleur. J'ai préféré noter CA-8 non atteint, avec la preuve. »
5. **La suite** (10 s) : « Comparer d'autres services de transcription sur les numéros dictés : c'est
   au programme du benchmark. »

## 8. Questions probables du jury

| Question                                        | Réponse                                                                                                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Pourquoi ne pas avoir corrigé le numéro ?       | Une correction propre à ce numéro ferait réussir le test sans améliorer le système ; sur un vrai appel, un autre numéro aurait la même faiblesse.      |
| Un vrai client perdrait-il son numéro ?         | Le dossier n'aurait pas le numéro dicté ; il n'en invente aucun. Le comportement d'un vrai appel n'a pas été mesuré : la téléphonie est simulée (R10). |
| Le défaut vient-il de la voix ou de l'écoute ?  | Trois lectures différentes donnent la même erreur ; l'audio n'a pas été écouté, seul le texte transcrit est mesuré.                                    |
| Comment savez-vous que ce n'est pas un hasard ? | Trois mesures, trois passages de SC-01 chacune : 9 fois sur 9 le même écart, et seulement celui-là.                                                    |
| Que coûte une mesure ?                          | Environ 0,10 € pour sept parcours (synthèse, transcription et modèle de langage), selon les estimations du script de mesure.                           |

## 9. Sources

- Critère : `docs/v1/dossier-conception-v1.md` (CA-8) ; avenant : `docs/decisions.md` (D-74).
- Mesures : `preuves/etape-6-ca8-premiere-mesure.json` (production `5c3874b`),
  `preuves/etape-6-ca8-deuxieme-mesure.json` (`a714586`), `preuves/etape-6-ca8.json` (`74b1e55`).
- Script de mesure : `eval/production/verifier_ca8.py`.
- Incident : `incidents/INC-09-numero-dicte-mal-transcrit.md`.
- Tests TC-10 : `tests/test_api_voix.py` (`test_l_audio_ne_touche_pas_le_disque`),
  `tests/test_console_demonstration.py`.
