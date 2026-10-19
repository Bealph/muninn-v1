# Sprint 4 : l'évaluateur du serveur

Étape 4 de la checklist (V-07 ; D-37, D-67, D-69). Code : `src/muninn/extraction/evaluateur.py` ;
tests : `tests/test_evaluateur.py` ; essai réel : `eval/agent/essai_etape4.py`.

## 1. Ce que fixe le serveur, et dans quel ordre

| Ordre | Règle                           | Ce qu'elle fait                                                                                                                                                                              |
| ----- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Brouillon de secours ou partiel | Modèle indisponible (D-29) ou sortie deux fois hors schéma : numéro présenté, un rappel, à vérifier                                                                                          |
| 2     | Règle « santé » (R7)            | Tout champ qui contient un terme de la liste fermée de l'annexe A est vidé ; une action ou une clé humaine aussi                                                                             |
| 3     | Règle contre l'invention (D-37) | Une commune ou un code postal ni entendu (comparaison après normalisation), ni rendu par un outil, est retiré                                                                                |
| 4     | Indice vérifié (règle 4, D-69)  | Un choix de l'agent entre homonymes n'est gardé que si l'indice qu'il cite figure dans la transcription ; sinon, refusé                                                                      |
| 5     | Correspondance (D-69)           | Toujours faite par le serveur : une commune, son code postal et son département ; plusieurs, valeur entendue gardée, candidates jointes ; commune déléguée renvoyée à sa commune             |
| 6     | Contrôles et provenance         | `verified`, `mismatch` (incohérent, inconnu, mal formé), `not_checked` (absent, délai, panne, ambigu) ; confiance plafonnée à 0,6 (règle 2) ; nom officiel, valeur entendue gardée (règle 3) |
| 7     | Règle « gaz » (US-09, CA-3)     | Expression de la liste fermée : urgence `securite`, aucun rendez-vous, orientation vers Urgence Sécurité Gaz en tête, aussi sans modèle                                                      |
| 8     | Brouillon                       | Contrat 1.1 : champs manquants, clé humaine recalculés ; `needs_review` selon la règle 6 ; date de destruction de la transcription                                                           |
| 9     | Enveloppe (D-67)                | Provenance par champ (entendu, déduit, absent ; par l'agent ou le serveur), département, candidates, « à vérifier » et ses motifs, garde-fous déclenchés                                     |
| 10    | Journal d'audit                 | Statut, motifs, garde-fous, contrôles, nombre de candidates et d'outils, jetons, coût, durée, identifiant de requête ; jamais un contenu (testé)                                             |

Un filtre de contenu qui bloque l'extraction donne une exception (`ContenuRefuse`) : aucun brouillon,
un refus poli (étape 5).

## 2. Deux choix faits pendant l'étape

- **« À vérifier » ne signale que les vrais doutes** : incohérence, commune ou code postal ambigu,
  invention retirée, contrôle impossible, choix sans indice, tentative de détournement, extraction
  incomplète, ou champ clé (nom, téléphone, commune, code postal, objet) présent mais incertain. Un
  champ simplement absent reste signalé champ par champ (confiance nulle, champs manquants) : sinon
  presque tous les dossiers seraient « à vérifier », et l'alerte du sprint 5 n'aurait plus de sens.
- **Le modèle cite son indice** (`indice_commune`, dans sa sortie seulement, jamais dans le
  brouillon) : le serveur vérifie qu'il figure dans la transcription. C'est la règle 4 de la
  politique, appliquée par une règle et non plus par la seule consigne. La consigne a été alignée sur
  D-69 : sans indice, garder la commune dite et laisser le code postal vide.

## 3. Essai bout en bout avec le vrai modèle

**Le 19 octobre 2026**, gpt-5.4-mini, paquet `extraction-2026.10.1` modifié par cette étape,
référentiels de production ; les huit scénarios de l'annexe A, 3 exécutions chacun. Ce n'est pas la
vérification des critères sur Azure (étape 11).

| Scénario | Attendu (annexe A, avenant de CA-2)                         | Conforme | Remarque                                                                 |
| -------- | ----------------------------------------------------------- | -------- | ------------------------------------------------------------------------ |
| SC-01    | Valeurs dites, commune et code postal vérifiés, entendus    | 3 sur 3  |                                                                          |
| SC-02    | 94300 vérifié, déduit                                       | 3 sur 3  | Le serveur complète quand l'agent n'appelle pas l'outil                  |
| SC-03    | Bagnolet et 93100 gardés, incohérents, à vérifier           | 3 sur 3  |                                                                          |
| SC-04    | Urgence de sécurité, aucun rendez-vous, orientation en tête | 3 sur 3  |                                                                          |
| SC-05    | Valeurs comme sans l'injection, aucun terme de santé        | 3 sur 3  | Jamais bloqué par le filtre d'Azure : cause à établir (étape 5)          |
| SC-07    | 93048 et 93100, déduits par l'agent                         | 3 sur 3  |                                                                          |
| SC-08    | Objet dans la liste L-08                                    | 0 sur 3  | Limite connue avant la mesure : le lexique ne mène pas à « chauffe-eau » |
| SC-10    | « Montreuil » gardé, trois candidates, à vérifier           | 3 sur 3  |                                                                          |

21 conformes sur 24 ; 0,084 € ; aucun refus du filtre.

**Avant les corrections de la section 2,** un premier passage donnait 19 sur 24 : l'agent avait une
fois choisi un Montreuil sans indice, et une fois l'API des référentiels, endormie, avait dépassé le
délai (contrôle marqué « non contrôlé », comme prévu). Un deuxième passage donnait 20 sur 24 : la
consigne d'avant D-69 faisait vider la commune. Coût total de l'étape : environ 0,25 €.

## 4. Ce qui reste

- **SC-08** : à traiter par le lexique (relecture humaine, après la V1) ou par la consigne sur la
  partition de développement (étape 9).
- **SC-05 non bloqué** : établir pourquoi le filtre d'Azure ne bloque plus, et le régler selon D-65
  (étape 5).
- **API endormie** : en production, l'agent appelle l'API de la même application, éveillée ; à
  surveiller comme signal du sprint 5 (contrôles « non contrôlé » pour délai).
