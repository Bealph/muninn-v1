# Benchmark C7 : transcription, synthèse vocale et téléphonie, protocole

**Statut :** protocole écrit et versionné le 3 novembre 2026, **avant toute mesure et avant toute
lecture d'offre**. Les candidats, les résultats et la recommandation iront dans `rapport.md`, sans
modifier ce protocole ; un écart au protocole y sera signalé comme tel.
**Références :** D-20 (téléphonie dans l'UE), D-50 (voix simulée, Azure AI Speech), D-68
(raccordement), R5 (traitement dans l'UE), R10 (pas de compte fournisseur ni d'achat) ;
`docs/conception/appels-et-voix/03-raccordement-telephonique.md` ; INC-09 ; veille de C6.

## 1. Question

Pour chacun des trois services dont Muninn a besoin autour de l'appel, quel service existant
recommander, et à quelles conditions : la **transcription** de l'appel, la **synthèse vocale** de
l'agent, la **téléphonie** qui reçoit l'appel renvoyé ?

Le banc d'essai T-06 a déjà tranché le modèle de langage (D-61) ; il n'est pas repris ici.

## 2. Expression de besoin

Les besoins viennent de la conception et de la V1, pas des offres.

### 2.1 Transcription

| N°  | Besoin                                                                                                         | Origine            |
| --- | -------------------------------------------------------------------------------------------------------------- | ------------------ |
| T1  | Français de France, parole téléphonique, vocabulaire des métiers de l'artisanat                                | Concept, D-50      |
| T2  | Deux locuteurs séparés (l'appelant et l'agent), attribués au bon tour                                          | D-50               |
| T3  | Chiffres exacts : numéro de téléphone, code postal, numéro de rue ; mieux vaut un chiffre manquant qu'inventé  | CA-1, INC-09       |
| T4  | Transcription d'un appel terminé en moins de 30 s, dans le budget de 45 s du dossier                           | CA-8, D-74         |
| T5  | Traitement et stockage dans l'UE ; aucun entraînement sur les appels ; rétention nulle ou bornée et documentée | R5, D-32           |
| T6  | API utilisable sans SDK imposé, authentification sans clé de préférence (identité managée)                     | D-50, sécurité     |
| T7  | Cible, hors V1 : transcription en continu pendant l'appel, pour un agent qui répond en direct                  | Conception (cible) |

### 2.2 Synthèse vocale

| N°  | Besoin                                                                                                      | Origine            |
| --- | ----------------------------------------------------------------------------------------------------------- | ------------------ |
| S1  | Deux voix françaises distinctes et naturelles : l'agent et, pour la démonstration, l'appelant               | D-50, D-51         |
| S2  | Lecture correcte des numéros dictés (paires de chiffres) ; réglage par SSML ou équivalent                   | INC-09             |
| S3  | Cible, hors V1 : synthèse en flux, pour un agent qui répond en direct ; aucun seuil fixé à ce jour          | Conception (cible) |
| S4  | Traitement dans l'UE ; aucun entraînement sur les textes ; droit d'usage commercial de la voix              | R5                 |
| S5  | Annonce de l'agent automatique dès la première phrase, avec une voix qui ne se fait pas passer pour humaine | D-04               |

### 2.3 Téléphonie

| N°  | Besoin                                                                                                      | Origine                                     |
| --- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| P1  | Numéro français géographique ou mobile, attribuable à une entreprise, conforme aux règles de l'ARCEP        | D-68, guide de l'ARCEP cité au raccordement |
| P2  | Reçoit les appels renvoyés par le mobile de l'artisan (renvoi conditionnel) et transmet le numéro d'origine | D-68, F8, I2                                |
| P3  | Appel entrant signalé à un service web, et flux audio bidirectionnel temps réel vers Muninn                 | F5, I7                                      |
| P4  | Traitement dans l'UE ; fournisseur établi dans l'UE ou garanties équivalentes                               | D-20, R5                                    |
| P5  | Envoi de SMS depuis le numéro (message à l'appelant, code de vérification de la ligne)                      | Cartographie E7, raccordement               |
| P6  | Coût par minute entrante et par numéro compatible avec le budget de 60 € par mois                           | SLO-16                                      |

## 3. Grille

Fixée avant de lire les offres. Un critère **éliminatoire** non satisfait écarte le service ; un
critère **principal** classe les restants ; un critère de **départage** n'intervient qu'à égalité ;
un critère **rapporté** est noté sans peser sur le choix.

### 3.1 Critères communs aux trois catégories

| Critère                          | Nature       | Ce qui est lu ou mesuré                                                                |
| -------------------------------- | ------------ | -------------------------------------------------------------------------------------- |
| Traitement et stockage dans l'UE | Éliminatoire | Région UE disponible pour le service, conditions de traitement lues                    |
| Entraînement sur les données     | Éliminatoire | Engagement écrit de ne pas entraîner sur les données du client                         |
| Rétention                        | Rapporté     | Durée de conservation par défaut ; possibilité de rétention nulle                      |
| Coût à l'usage                   | Départage    | Prix public, ramené à l'unité de Muninn (heure d'audio, million de caractères, minute) |
| Intégration                      | Principal    | API REST documentée ; SDK Python ; exemples ; limites de débit publiées                |
| Authentification                 | Rapporté     | Clé seule, ou identité managée et jetons à durée courte                                |
| Maturité                         | Rapporté     | Disponibilité générale ou préversion ; date de lancement ; engagement de service       |
| Documentation                    | Rapporté     | Publique, datée, en français ou en anglais                                             |

### 3.2 Critères propres

| Catégorie     | Critère                               | Nature       | Ce qui est lu ou mesuré                                                     |
| ------------- | ------------------------------------- | ------------ | --------------------------------------------------------------------------- |
| Transcription | Français et séparation de 2 locuteurs | Éliminatoire | Langue et séparation documentées pour le mode d'appel utilisé               |
| Transcription | Qualité sur nos dialogues             | Principal    | Mesurée pour le service en place (section 5) ; documentaire pour les autres |
| Transcription | Délai d'un appel terminé              | Principal    | Mode asynchrone ou rapide ; mesuré pour le service en place                 |
| Transcription | Mode en continu (T7)                  | Rapporté     | Disponibilité en français                                                   |
| Synthèse      | Voix françaises (S1)                  | Éliminatoire | Au moins deux voix françaises distinctes                                    |
| Synthèse      | Contrôle de la lecture (S2)           | Principal    | SSML ou équivalent ; lecture des nombres                                    |
| Synthèse      | Latence du premier son (S3)           | Rapporté     | Documentée ; diffusion en flux possible                                     |
| Téléphonie    | Numéro français (P1)                  | Éliminatoire | Numéros français proposés aux entreprises, justificatifs demandés           |
| Téléphonie    | Flux audio temps réel (P3)            | Éliminatoire | Webhook d'appel entrant et flux bidirectionnel documentés                   |
| Téléphonie    | Numéro d'origine transmis (P2)        | Principal    | Champ documenté de l'appelant et du renvoi                                  |
| Téléphonie    | SMS (P5)                              | Rapporté     | Envoi de SMS depuis un numéro français                                      |

## 4. Choix des candidats

De trois à cinq services par catégorie, listés dans `rapport.md` avant toute notation :

- le service en place quand il existe (Azure AI Speech, D-50) ;
- au moins un service d'un fournisseur établi dans l'UE ;
- les services cités par les sources de la veille (`docs/veille/sources.md`) ou par la conception ;
- inclusion seulement si la documentation publique couvre le français ; une préversion est
  admise et signalée.

Aucun compte n'est ouvert, aucun achat n'est fait (R10) : hors du service en place, la notation est
documentaire, chaque valeur liée à sa source et à sa date de lecture.

## 5. Mesure du service en place

Seul Azure AI Speech peut être mesuré sans nouveau compte : il sert déjà la production.

- **Chemin :** l'API de production, `POST /v1/demo/voice/synthesis` puis
  `POST /v1/demo/voice/call`, sans clé (routes publiques de démonstration). La synthèse d'un
  scénario est faite une fois puis gardée en mémoire par l'API : les répétitions envoient le même
  audio à la transcription.
- **Jeu :** les 16 scénarios du jeu synthétique qui ont un dialogue (`P4-perimetre` n'en a pas),
  noms et numéros fictifs (R9). Aucun appel réel.
- **Répétitions :** 3 passages par scénario, soit 48 transcriptions ; un appel toutes les 10 s au
  moins, jamais en parallèle, pour rester sous la limite de débit de la production.
- **Mesures :**
  - fidélité des mots : rappel et précision de `voix/fidelite.py`, par appel ;
  - chiffres : part des groupes de chiffres du dialogue rendus à l'identique, et nombre de
    chiffres en trop (T3) ;
  - locuteurs : part des mots alignés attribués au bon locuteur (T2) ;
  - délai : `transcription_ms`, médiane et maximum (T4) ;
  - stabilité : écarts de transcription d'un passage à l'autre sur un même audio ;
  - synthèse : aller-retour, c'est-à-dire la fidélité de la transcription d'un audio synthétisé (S1, S2).
- **Seuils de lecture**, repris de la V1 : rappel 0,90 et précision 0,95 au moins (seuils de
  `fidelite.py`) ; délai sous 30 s (T4).
- **Plafond de coût :** 2 € (section 6). Le programme cumule le coût estimé de chaque appel et
  s'arrête avant de dépasser le plafond.
- **Preuve :** un fichier JSON par passage dans `docs/v1/benchmark-services-ia/mesures/`, sans
  audio ; le programme de mesure est versionné avec le protocole.

## 6. Coût prévu

Prix publics d'Azure, West Europe, en euros, lus le 3 novembre 2026 dans l'API officielle des prix
(<https://prices.azure.com/api/retail/prices>, produit « Azure Speech ») :

| Usage                                        | Prix                                              | Quantité prévue                                  | Coût prévu |
| -------------------------------------------- | ------------------------------------------------- | ------------------------------------------------ | ---------- |
| Synthèse neuronale standard                  | 13,4656 € par million de caractères               | 16 dialogues une fois, environ 10 500 caractères | 0,14 €     |
| Transcription rapide                         | 0,3232 € par heure d'audio                        | 48 appels, environ 35 min d'audio                | 0,19 €     |
| Séparation des locuteurs, si facturée à part | 0,2693 € par heure (non vérifié pour ce mode)     | les mêmes 35 min                                 | 0,16 €     |
| Extraction par le modèle A                   | environ 0,0045 € par appel (mesure du 29 octobre) | 48 dossiers                                      | 0,22 €     |
| **Total**                                    |                                                   |                                                  | **0,70 €** |

La durée d'audio suppose un débit de parole de 15 caractères par seconde ; le programme compte la
durée réelle. Le tarif promotionnel de transcription (0,0898 € par heure jusqu'au 31 décembre 2026)
n'est pas retenu : son application à la transcription rapide n'est pas établie. Plafond fixé à
2 €, près de trois fois le coût prévu (0,70 €).

## 7. Limites assumées

- Hors du service en place, aucune mesure : la comparaison de qualité entre services reste
  documentaire, donc déclarative.
- Le jeu est synthétique : une voix de synthèse transcrite n'a ni bruit, ni accent, ni coupure de
  réseau. La mesure borne la qualité par le haut.
- La téléphonie n'est ni essayée ni mesurée (R10).
- Les prix et les conditions changent : chaque valeur porte sa date de lecture.
