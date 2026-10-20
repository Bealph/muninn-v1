# Sprint 4 : les garde-fous de sortie

Étape 7 de la checklist. Code : `src/muninn/extraction/sortie.py`, appelé par l'évaluateur (dossier)
et par la qualification (message) ; tests : `tests/test_sortie.py`, `tests/test_evaluateur.py`,
`tests/test_qualification.py`. Table de conformité : `conformite-conception.md`.

## 1. Ce que vérifie le serveur sur toute sortie du modèle

| Garde-fou | Règle                                                                                                                                                                             | Effet                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Fuite     | Jeton témoin des consignes (un par paquet : extraction, qualification) ou motif de secret (9 motifs : clés d'API, JWT, clé privée, `AccountKey=`, mot de passe, clé hexadécimale) | Texte vidé ; dossier « à vérifier » (`fuite_retiree`) ; message remplacé par un texte fixe         |
| Invention | Commune et code postal (D-37), et depuis l'étape 7 : nom, prénom, rue, téléphone dit ; une valeur absente de la transcription est retirée                                         | Valeur retirée ; repli sur le numéro présenté pour le téléphone ; « à vérifier »                   |
| Hors rôle | Sortie limitée au schéma fermé (sortie structurée stricte) ; dans les textes libres, liens, liens Markdown, balises et caractères de balisage retirés                             | Texte nettoyé ; garde-fou `hors_role` journalisé                                                   |
| Refus     | Filtre de contenu : texte fixe (`MESSAGE_REFUS_CONTENU`), jamais un fragment de l'entrée ; entrée vide ou trop longue : texte fixe (étape 5)                                      | Aucun brouillon ; `extraction.refus` ou `qualification.refus` journalisé avec `request_id` et code |

Chaque garde-fou déclenché est journalisé par son code, avec le `request_id`, sans contenu
(`extraction.fin`, `qualification.fin`). L'échappement à l'affichage revient à l'écran « Agent »
(étape 8).

## 2. Vérification avec le vrai modèle

Les deux essais ont été rejoués le 20 octobre 2026 avec ces garde-fous, 3 exécutions par scénario.

| Essai                          | Avant l'étape 7 | Après l'étape 7 | Garde-fous de sortie déclenchés |
| ------------------------------ | --------------- | --------------- | ------------------------------- |
| Extraction, annexe A (étape 4) | 21 sur 24       | 20 sur 24       | Aucun                           |
| Qualification, CA-7 (étape 6)  | 24 sur 24       | 24 sur 24       | Non enregistré par l'essai      |

L'écart de l'extraction n'est pas dû à l'étape 7 : SC-01, première exécution, a vu l'API des
référentiels en veille dépasser le délai (« non contrôlé »), limite déjà notée à l'étape 4 ; SC-08
reste à 0 sur 3. SC-05 porte désormais le motif « détournement suspect », effet attendu des règles
d'entrée de l'étape 5. Aucune valeur dite n'a été retirée par la règle d'identité étendue. L'essai
de qualification n'enregistrait pas les garde-fous du message ; le champ est ajouté au script. Coût des
deux essais : 0,145 €.

## 3. Limites

- Les motifs de secret sont une liste fermée : un secret d'une autre forme n'est pas vu. Le jeton
  témoin ne détecte que la recopie littérale des consignes, pas une paraphrase.
- La règle d'identité compare après normalisation : un nom mal transcrit puis corrigé par le modèle
  serait retiré. Aucun cas sur l'annexe A ; à suivre sur la partition de développement (étape 9).
- Un code de porte dit sous la forme « code secret : 1234 » serait vidé comme un secret.
