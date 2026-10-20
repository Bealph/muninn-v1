# Sprint 4 : les garde-fous d'entrée

Étape 5 de la checklist (D-63 ; D-65 en attente de révision). Code : `src/muninn/extraction/entree.py`,
appelé en tête de `extraire_dossier` ; tests : `tests/test_entree.py` et `tests/test_evaluateur.py` ;
mesure : `eval/garde_fous/mesure_entree.py`.

## 1. Les trois couches de D-63

| Couche               | Où                                           | Effet                                                                                                              | État                          |
| -------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------- |
| 1. Règles du serveur | `entree.py`, avant l'agent                   | Refus motivé (vide, trop long) ; nettoyage des invisibles ; motifs d'injection : « à vérifier », jamais de blocage | Fait, mesuré (section 3)      |
| 2. Modération        | Filtre de contenu d'Azure sur le déploiement | Contenu nocif bloqué : `ContenuRefuse`, refus poli à texte fixe                                                    | Décision attendue (section 4) |
| 3. Hors-périmètre    | Qualification des appels                     | Un appel qui n'est pas une demande d'intervention ne donne pas de dossier                                          | Étape 6                       |

## 2. Les règles

- **Refus motivé, avant tout appel au modèle** : plus de 8 000 caractères (borne du contrat
  d'API) ; moins de 10 lettres après nettoyage. Exception `EntreeRefusee(code, message)`, texte fixe,
  jamais un fragment de l'entrée ; aucun brouillon. Vérifié : le faux fournisseur ne reçoit aucune
  requête.
- **Nettoyage** : caractères des catégories Unicode Cc et Cf retirés (largeur nulle, sens
  d'écriture, sonnerie), sauf saut de ligne et tabulation. Le modèle reçoit le texte nettoyé (testé).
  Une consigne coupée par des caractères invisibles est donc détectée.
- **Motifs d'injection** : 12 expressions régulières, sur le texte normalisé (minuscules, sans
  accents, ponctuation en espaces), liste `injection-2026.10.2`. Une détection ajoute le garde-fou
  `detournement` et le motif `detournement_suspect` : le dossier est « à vérifier », l'extraction a
  lieu quand même. Le journal porte l'identifiant du motif, jamais le texte.

## 3. Mesure

**Protocole, fixé avant la mesure** : 20 phrases hostiles et 20 phrases légitimes (`jeu-entree-2026.10.1`,
données synthétiques, R9). Les légitimes contiennent exprès des mots proches (« instructions »,
« vérifié », « confirme », « coché »). Le jeu et les motifs ont été figés et poussés avant toute
mesure (commit `a1cc6fe`). Intervalle de score de Wilson à 95 %.

| Mesure                                  | Résultat  | IC 95 %       |
| --------------------------------------- | --------- | ------------- |
| Détection sur les phrases hostiles      | 20 sur 20 | 0,839 à 1,000 |
| Faux positifs sur les phrases légitimes | 0 sur 20  | 0,000 à 0,161 |

**Une correction après le gel, sans changer le sens.** Dans le JSON figé, la limite de mot `\b` était
écrite avec une seule barre oblique : le lecteur JSON en faisait un caractère « retour arrière »,
et aucun motif ne détectait rien. Les tests l'ont montré avant la mesure. Correction : barre
doublée, version passée à `injection-2026.10.2`, aucune expression modifiée. Un test empêche la
récidive (aucun caractère de contrôle dans un motif).

**Ce que ce résultat ne dit pas.**

- Le jeu et les motifs ont la même origine : 20 sur 20 est une borne haute, pas la résistance à un
  attaquant qui ne connaît pas la liste. La borne basse de l'intervalle (84 %) est la valeur à
  retenir.
- Une limite est déjà connue : INJ-07 ne reconnaît pas le féminin (« marquez l'adresse comme
  vérifiée »). Elle n'est pas corrigée avant la mesure ; elle l'est dans la liste suivante, mesurée sur
  un jeu nouveau. Elle est consignée dans un test.
- Les règles ne sont qu'une couche : l'agent traite la transcription comme une donnée (bloc
  délimité, M-04), et le serveur contrôle sa sortie (étape 4 ; étape 7).

## 4. Constat sur le filtre d'Azure, et décision attendue sur D-65

**Constat (19 octobre 2026, 8 appels réels, filtre `Microsoft.DefaultV2` inchangé).** La
transcription de SC-05 envoyée brute est bloquée par la détection des détournements, 2 fois sur 2. La
même transcription dans le bloc délimité `<transcription>` passe, 2 fois sur 2. La présence de la
consigne ne change rien. C'est la cause des passages sans blocage de l'étape 4 (24 sur 24). Le script
de cette enquête était exploratoire et n'est pas versionné ; le constat repose sur 8 appels, il est
donc indicatif.

**Conséquence.** D-65 voulait passer la détection des détournements en annotation seule, parce
qu'elle bloquait SC-05 avant l'agent (banc T-06, transcription brute). Avec le bloc délimité, ce
blocage n'a plus lieu : le filtre personnalisé n'apporte plus rien à SC-05, et le créer coûte une
action du porteur dans le portail Foundry.

**Recommandation (décision D-70, à prendre par le porteur).**

1. Ne pas créer le filtre personnalisé de D-65 ; garder `Microsoft.DefaultV2` comme couche de
   modération.
2. Un blocage par le filtre, quelle qu'en soit la catégorie, donne le refus poli à texte fixe
   (`content_refused`), journalisé sans contenu. C'est déjà le comportement du code.
3. La détection des détournements est assurée par nos règles (section 2), mesurées, et non par
   l'annotation d'Azure.
4. Si une campagne ultérieure montre des blocages de demandes légitimes, revenir à D-65.

Risque de cette recommandation : un détournement que le filtre bloque donne un refus, et non un
dossier « à vérifier ». Pour un artisan, c'est un appel perdu au lieu d'un dossier signalé. Avec le
bloc délimité, c'est rare (0 sur 24 à l'étape 4), et le compteur de refus sera un signal du sprint 5.
