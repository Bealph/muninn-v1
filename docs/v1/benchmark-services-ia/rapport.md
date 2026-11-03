# Benchmark C7 : transcription, synthèse vocale et téléphonie, rapport

**Date :** 3 novembre 2026. **Protocole :** `protocole.md`, commité le 3 novembre 2026 à 11:24 UTC
(commit `dadf77f`, PR n° 217), avant la mesure (11:41 UTC) et avant la lecture des offres
concurrentes ; seuls les prix d'Azure, service en place, y étaient lus pour fixer le plafond.
**Preuves :** `mesures/azure-speech-2026-11-03-1141.json` (mesure) et `releves/` (une fiche par
candidat, chaque valeur liée à sa source et à sa date de lecture).

## 1. Réponse courte

| Catégorie     | Recommandation                                            | Condition principale                                                                           |
| ------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Transcription | Garder Azure AI Speech, transcription rapide (D-50)       | Rendre déterministe le refus d'un numéro français mal formé (section 3)                        |
| Synthèse      | Garder Azure AI Speech, voix neuronales et SSML (D-50)    | Revoir si Voxtral TTS de Mistral passe en disponibilité générale dans l'UE                     |
| Téléphonie    | Aucun service ne passe la grille ; aucun n'est recommandé | Décision du porteur : l'éliminatoire « entraînement » devient-il une condition contractuelle ? |

## 2. Règles d'application de la grille

- **Un éliminatoire n'est satisfait que s'il est établi par une source officielle.** Une valeur
  « non trouvée », « contradictoire » ou seulement connue par un extrait de moteur de recherche
  vaut « non établi », donc non satisfait : le service est écarté. Une valeur documentée avec une
  réserve écrite (transferts possibles, exclusion à configurer) vaut « établi sous réserve » : le
  service reste, la réserve est rapportée. Une fonction documentée sans restriction de langue vaut
  pour le français quand le français est listé. Règles appliquées aux trois catégories.
- **Les critères « rapportés » (authentification, maturité, rétention, documentation) ne pèsent pas
  sur le choix** (protocole, section 3) : ils sont notés, jamais utilisés pour classer.
- **Le coût ne départage qu'à égalité** sur les critères principaux. Les prix restent dans leur
  devise d'origine, sans conversion.

## 3. Mesure du service en place : Azure AI Speech

Mesure faite le 3 novembre 2026 à 11:41 UTC, selon la section 5 du protocole, sur l'API de
production (version `ce8ca4b`, celle que `/version` annonçait pendant la mesure) : 16 scénarios,
3 passages, 48 transcriptions, aucune erreur. Coût estimé 0,64 € (prévu 0,70 €, plafond 2 €).

| Besoin    | Mesure                                         | Résultat                          | Verdict                                                                    |
| --------- | ---------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------- |
| T1        | Rappel des mots, médiane et minimum            | 0,983 ; 0,938                     | Tenu : seuil de 0,90 atteint par les 48 appels                             |
| T1        | Précision des mots, médiane et minimum         | 0,986 ; 0,929                     | Non tenu sur SC-08 (forme : « 94 300 ») ; tenu sur les 15 autres scénarios |
| T2        | Mots alignés attribués au bon locuteur         | 100 % sur les 48 appels           | Tenu                                                                       |
| T3        | Groupes de chiffres rendus à l'identique       | 69 sur 75 (92 %)                  | **Non tenu sur SC-02** : un chiffre inventé, aux 3 passages                |
| T3        | Groupes de chiffres entendus en trop           | 6 (SC-02 et SC-Q5, 3 fois chacun) | SC-02 : chiffre inventé ; SC-Q5 : « quinze » écrit « 15 »                  |
| T4        | Délai de la transcription, médiane et maximum  | 1,35 s ; 2,56 s                   | Tenu, loin des 30 s                                                        |
| Stabilité | Transcription identique d'un passage à l'autre | 16 scénarios sur 16               | Même audio, même texte : écarts reproductibles                             |

Lecture des écarts :

- **SC-02.** « 06 99 00 00 02 » est entendu « 06 99 00 000 02 » aux trois passages : un zéro
  ajouté, le défaut d'INC-09. Le numéro a onze chiffres, donc il est invalide. Vérification faite
  après la mesure, par un appel de plus (3 novembre 2026, requête
  `692d5d8c-8913-402c-aedf-7c5e9dd73b92`) : le dossier ne retient aucun numéro (`telephone.value`
  nul) et reste conforme à l'attendu. **Ce refus vient du modèle, pas d'une règle :** le contrat
  accepte tout numéro international de 8 à 15 chiffres (`MOTIF_TELEPHONE`,
  `extraction/contrat.py`), et le contrôle du serveur (`extraction/evaluateur.py`) garde un numéro
  dont les chiffres ont été dits. « +336990000002 » passerait les deux. Une règle propre aux
  numéros français (« +33 » suivi de 9 chiffres) rendrait ce refus déterministe : dette à traiter
  dans la V1. La mesure ne permet pas non plus de dire si le zéro vient de la synthèse ou de la
  transcription : S2 et T3 ne sont pas séparables par l'aller-retour.
- **SC-01.** Son numéro, mal rendu cinq fois sur six le 26 octobre (INC-09), est rendu à
  l'identique aux trois passages. Cause non établie ; un numéro qui contient « 00 00 » reste exposé,
  comme SC-02 le montre.
- **Écarts de forme, sans erreur de sens :** « quinze minutes » écrit « 15 » (SC-Q5) ; « 94300 »
  coupé en « 94 300 » (SC-08, d'où sa précision de 0,929) ; « le 9-3 » rendu « 9a3 » (SC-07).
- **Contrôle de fidélité de l'API (`voix/fidelite.py`) :** 30 appels sur 48 acceptés. Il accepte
  SC-02, seul vrai défaut de chiffres, parce qu'il tolère par conception un chiffre répété une fois
  par appel, et cinq mots en trop au plus (`fidelite.py`, `MOTS_EN_TROP_MAX`). Il refuse six
  scénarios aux trois passages pour des écarts sans effet sur le sens : une forme de chiffres
  (« 0000 » pour « 00 00 » sur SC-01, « 0800 » sur SC-Q7, « 9a3 » sur SC-07, « 15 » pour « quinze »
  sur SC-Q5), une coupure (SC-08) ou plus de cinq mots en trop (SC-Q4, aucun écart de chiffres).
  Ce contrôle est donc à la fois trop permissif sur le cas qui compte et trop strict sur la forme :
  constat à traiter dans la V1, au-delà de C7.

**Mesures ajoutées au protocole :** la durée de l'appel complet, extraction comprise, mesurée côté
client (médiane 4,2 s, maximum 6,7 s, sous les 45 s de CA-8).

**Synthèse vocale :** les 16 dialogues synthétisés à deux voix sont transcrits avec les résultats
ci-dessus, les deux voix bien séparées (S1, voix distinctes). Le caractère naturel des voix (S1)
n'est pas mesuré ; aucune voix n'a été écoutée pour ce rapport.

## 4. Transcription

Détail et sources : `releves/transcription.md`.

| Critère                                | Azure (en place)                                             | OVHcloud AI Endpoints                                                | Speechmatics                                                                                                          | Gladia                                            | Mistral Voxtral 3                   |
| -------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------------- |
| Pays d'établissement                   | États-Unis                                                   | France                                                               | Royaume-Uni, hors UE                                                                                                  | France                                            | France, siège non relu ce jour      |
| UE (éliminatoire)                      | Établi : West Europe                                         | Établi : « en UE », pays non précisé                                 | Établi sous réserve : région EU1 ; transferts hors EEE et Royaume-Uni possibles selon la politique de confidentialité | Non établi pour le mode fichier                   | Non établi pour l'audio             |
| Entraînement (éliminatoire)            | Établi : non, par écrit                                      | Établi : non, par écrit                                              | Établi : non par défaut                                                                                               | Contradictoire (prix : activé ; conformité : non) | Autorisé en préversion (art. 4.2 d) |
| Français et 2 locuteurs (éliminatoire) | Établi                                                       | Établi : français listé, séparation sans restriction de langue       | Établi : français listé, séparation sans restriction de langue                                                        | Établi (Solaria-3)                                | Français non listé en v3            |
| Intégration (principal)                | REST synchrone, SDK Python, déjà intégré                     | REST de type OpenAI ; séparation des locuteurs hors du client OpenAI | REST asynchrone, SDK Python                                                                                           | REST asynchrone, SDK Python                       | SDK Python, limites non trouvées    |
| Qualité sur nos dialogues (principal)  | Mesurée (section 3)                                          | Non mesurable (R10)                                                  | Non mesurable (R10)                                                                                                   | Non mesurable (R10)                               | Non mesurable (R10)                 |
| Délai d'un fichier (principal)         | Mesuré : 1,35 s                                              | Non publié                                                           | Non publié                                                                                                            | Non publié                                        | Non publié                          |
| Coût par heure (départage)             | 0,32 €, ou 0,59 € si la séparation est facturée              | 0,15 €                                                               | 0,45 $ à 0,75 $                                                                                                       | 0,16 € à 0,27 €                                   | 0,21 $ à 0,24 $                     |
| Mode continu (rapporté)                | Oui                                                          | Non                                                                  | Oui                                                                                                                   | Non confirmé en français                          | Non confirmé en français            |
| Maturité (rapporté)                    | Disponibilité générale d'après un billet, non relu en entier | Statut non trouvé                                                    | Statut non trouvé                                                                                                     | Disponibilité générale, date non trouvée          | Préversion (20 octobre 2026)        |
| Verdict                                | 1er                                                          | 3e                                                                   | 2e, sous réserve (UE)                                                                                                 | Écarté (UE, entraînement)                         | Écarté (UE, entraînement, français) |

Classement des trois candidats admis :

1. **Azure.** Seul candidat mesurable sur nos dialogues (qualité et délai, deux critères
   principaux) ; il est premier par construction, puisque R10 interdit de mesurer les autres.
2. **Speechmatics**, sous réserve sur l'UE (transferts hors EEE et Royaume-Uni possibles selon sa
   politique de confidentialité ; portée sur les données transcrites non vérifiée). Devant
   OVHcloud au critère principal d'intégration : SDK Python (`speechmatics-batch`), quand la
   séparation des
   locuteurs d'OVHcloud passe hors du client OpenAI.
3. **OVHcloud.** Le moins cher ; le coût ne départage pas ici, faute d'égalité sur l'intégration.

Une réserve sur un éliminatoire ne départage qu'à égalité sur les critères principaux : ici,
l'intégration tranche avant, d'où Speechmatics devant OVHcloud malgré sa réserve.

**Recommandation : garder Azure**, malgré T3 non tenu sur SC-02. On ignore si ce défaut est propre à
Azure : aucun concurrent n'est mesurable sans compte. La défense reste dans Muninn : le numéro
invalide de SC-02 n'a pas été retenu lors d'un appel de vérification, par le modèle ; une règle
déterministe est à ajouter
(section 3), et l'agent en direct de la cible devra relire le numéro à l'appelant.

**Ce qui ferait changer :** une mesure d'un concurrent sur le même jeu, avec un compte ouvert après
la V1 ; Mistral, s'il documente le français et le traitement de l'audio dans l'UE, hors préversion ;
Gladia, s'il documente la région du mode fichier et lève la contradiction sur l'entraînement.

## 5. Synthèse vocale

Détail et sources : `releves/synthese-vocale.md`.

| Critère                                    | Azure (en place)                 | Amazon Polly                                                                  | Google Cloud TTS                                                                             | Mistral Voxtral TTS 3     | ElevenLabs                                   |
| ------------------------------------------ | -------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------- |
| UE (éliminatoire)                          | Établi                           | Établi sous réserve : une part du contenu peut être stockée hors de la région | Établi sous réserve : point d'accès UE, voix disponibles ambiguës                            | Non établi                | Non établi, Enterprise compris               |
| Entraînement (éliminatoire)                | Établi : non, par écrit          | Établi sous réserve : politique d'exclusion à poser                           | Établi : non, par écrit (art. 18)                                                            | Autorisé en préversion    | Établi sous réserve : exclusion à configurer |
| Voix françaises (éliminatoire)             | Établi : 23                      | Établi : 6                                                                    | Établi : 42 au catalogue ; 2 seulement si le point d'accès UE se limite à Neural2            | 4                         | Bibliothèque partagée                        |
| Lecture des numéros (principal)            | `say-as` documenté en français   | `say-as telephone` documenté en français                                      | `say-as telephone` sans restriction de langue (option « zero-as-zero » en anglais seulement) | Pas de SSML               | Pas de SSML                                  |
| Intégration (principal)                    | REST et SDK Python, déjà intégré | SDK, flux bidirectionnel                                                      | REST, SDK Python, flux                                                                       | REST, SDK, flux           | REST, SDK                                    |
| Coût par million de caractères (départage) | 13,47 €                          | 16 $ (neuronal)                                                               | 16 $ (Neural2)                                                                               | 13 $                      | 40 $ à 80 $                                  |
| Authentification (rapporté)                | Entra, sans clé                  | IAM AWS                                                                       | OAuth Google                                                                                 | Clé d'API                 | Clé d'API                                    |
| Verdict                                    | 1er                              | 3e, sous réserve (exclusion, région)                                          | 2e, sous réserve (voix sur le point d'accès UE)                                              | Écarté (UE, entraînement) | Écarté (UE)                                  |

Sur les critères principaux, Azure, Google et Polly sont à égalité : lecture des numéros (S2)
documentée (`say-as telephone` sans restriction de langue chez Google, règle de la section 2),
intégration comparable (SDK et flux). Le coût ne peut pas les départager sans conversion de
devise. L'ordre retenu est hors grille, déclaré en section 7 : Azure, dont les éliminatoires sont
établis sans réserve ; Google, une réserve (les voix françaises disponibles sur le point d'accès UE
sont ambiguës) ; Polly, deux réserves (politique d'exclusion à poser, région non garantie pour
tout le contenu). Chez Google, l'option qui lit « zéro » chaque zéro d'un numéro ne vaut qu'en
anglais (<https://docs.cloud.google.com/text-to-speech/docs/ssml>, lu le 3 novembre 2026).

**Recommandation : garder Azure.** Le seul fournisseur établi dans l'UE examiné, Mistral, ne passe
pas la grille ; ReadSpeaker n'a pas été examiné.

**Point de vigilance pour la cible :** chez Azure comme chez Google, le SSML n'est pas accepté
quand le texte arrive en flux. Un agent qui répond en direct devra écrire les numéros sous leur
forme parlée avant la synthèse.

**Ce qui ferait changer :** Voxtral TTS en disponibilité générale sur le point d'accès de l'UE, avec
une lecture des numéros documentée.

## 6. Téléphonie

Détail et sources : `releves/telephonie.md`. Rien n'a été essayé (R10).

| Critère                              | Twilio                                                       | Sinch                                                           | Vonage                        | OVHcloud                    | Azure Communication Services        |
| ------------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------- | --------------------------- | ----------------------------------- |
| Entité contractante                  | Twilio Ireland Limited                                       | Sinch Sweden AB                                                 | Non trouvée (pages en 403)    | OVH, France (extrait)       | Non relevée                         |
| UE (éliminatoire)                    | Établi sous réserve : région IE1, sans garantie de résidence | Non établi (extrait) : point d'accès UE, sous-traitants hors UE | Régions Dublin et Francfort   | Non trouvé                  | Non examiné                         |
| Entraînement (éliminatoire)          | Non tenu : texte contraire                                   | Non établi                                                      | Non établi                    | Non établi                  | Non examiné                         |
| Numéro français (éliminatoire)       | Établi : Kbis et adresse                                     | Non trouvé                                                      | Extrait seulement             | Établi                      | Fermé aux nouveaux clients          |
| Flux audio temps réel (éliminatoire) | Établi : 8 kHz                                               | Préversion                                                      | Établi : jusqu'à 24 kHz       | Non trouvé                  | Préversion                          |
| Origine et renvoi (principal)        | `From` et `ForwardedFrom`                                    | `cli` et `rdnis`                                                | `from` seul                   | Non trouvé                  | Non examiné                         |
| SMS depuis le numéro (rapporté)      | Mobile, SMS automatisé interdit                              | Non trouvé                                                      | Non trouvé                    | Non trouvé                  | Expéditeur alphanumérique seulement |
| Verdict                              | Écarté (entraînement)                                        | Écarté (entraînement, numéro)                                   | Écarté (entraînement, numéro) | Écarté (flux, entraînement) | Écarté (numéro)                     |

Constats :

- **Aucun service ne passe la grille.** L'avis de confidentialité de Twilio (9 avril 2026) compte le
  contenu client (« Customer Content ») parmi les données de la finalité qui entraîne ses modèles
  de lutte contre la fraude (relu dans le texte complet) ; les autres ne publient aucun engagement.
  Le protocole n'est pas modifié :
  aucun service n'est recommandé.
- **Azure Communication Services n'est plus une option.** Microsoft a annoncé le 23 septembre 2026
  le retrait d'ACS comme offre autonome au 30 septembre 2028 ; un client sans ressource ACS créée
  avant le 23 octobre 2026 ne peut plus acquérir de numéro
(<https://learn.microsoft.com/en-us/azure/communication-services/acs-retirement-and-breaking-changes-guide>,
  mise à jour du 29 octobre 2026, lue le 3 novembre 2026). Muninn n'a aucune ressource ACS
  (recherche du dépôt, 3 novembre 2026).
- **Les inconnues de la conception restent ouvertes.** I2 (le numéro d'origine arrive-t-il lors
  d'un renvoi) dépend des opérateurs : la documentation nomme les champs, pas leur remplissage
  (« Not all carriers support passing this information », Twilio). I7 (flux bidirectionnel chez un
  fournisseur établi dans l'UE) : aucun en disponibilité générale ; Sinch s'en approche, en
  préversion.

**Classement indicatif, hors protocole**, sous l'hypothèse où le porteur ferait de l'éliminatoire
« entraînement » une condition contractuelle à obtenir par écrit avant tout achat : Twilio (seul à
documenter les deux champs de P2, prix français publics : 1,35 $ par mois pour un numéro local,
0,01 $ la minute entrante, flux non chiffré), puis Sinch, puis Vonage. Twilio porte un texte
contraire : la clause devrait déroger à son avis de confidentialité. P6 : un numéro local et
300 minutes entrantes par mois (hypothèse) font environ 4,35 $, hors flux, compatible avec le budget
de 60 € par mois.

**Décisions attendues du porteur :** l'éliminatoire « entraînement » vaut-il exclusion, ou condition
contractuelle ? D-20 se lit-elle « entité contractante dans l'UE » ou « traitement garanti dans
l'UE » ? Dans le second cas, aucun service n'est prêt aujourd'hui.

**Décision du porteur, 3 novembre 2026 (D-93) :** l'absence d'entraînement sur le contenu
des appels devient une clause écrite obligatoire avant tout achat ; D-20 se lit « traitement
garanti dans l'UE ». Aucun fournisseur ne remplit aujourd'hui ces deux conditions sur pièces
publiques : le choix se fera après la V1, contrat à l'appui.

## 7. Écarts au protocole

- **Candidats non listés dans ce rapport avant la notation (section 4) :** ils l'ont été en tête de
  chaque relevé, avant les fiches.
- **Motif d'inclusion hors de la section 4 :** Speechmatics, Google, Amazon Polly, ElevenLabs et
  Vonage ont été inclus comme acteurs majeurs, motif que la règle ne prévoit pas.
- **Inclusion contraire à la section 4 :** Voxtral Transcribe 3 a été inclus alors que sa
  documentation ne liste pas le français ; il est écarté à la notation.
- **Preuve en un seul fichier** au lieu d'un fichier par passage (section 5) ; les trois passages y
  sont distingués ligne par ligne.
- **Mesure ajoutée :** la durée de l'appel complet, extraction comprise.
- **Règles d'application** posées dans ce rapport (section 2) : « non établi = non satisfait »,
  « établi sous réserve », fonction sans restriction de langue valable pour le français. Le
  protocole ne dit pas comment traiter une valeur non trouvée ou assortie d'une réserve.
- **Classement indicatif de la téléphonie** donné hors grille, à la demande de décision du porteur.
- **Ordre Azure, Google, Polly en synthèse vocale** fixé sur le nombre de réserves des
  éliminatoires, critère que la grille ne prévoit pas pour classer.
- **Vérification ajoutée après la mesure :** un appel sur SC-02 pour lire le téléphone du dossier
  (`mesures/verification-sc02-2026-11-03.json`, archive partielle).

## 8. Limites

- **Hors d'Azure, la comparaison est documentaire**, donc déclarative : aucun concurrent n'a été
  essayé (R10).
- **Lecture des sources par un outil qui résume les pages :** les citations des relevés sont
  celles que l'outil a rendues. Certaines valeurs ne sont connues que par l'extrait d'un moteur de
  recherche (pages refusées en HTTP 403) : Vonage, Sinch (UE et entraînement), l'entité et les
  justificatifs de numéro d'OVHcloud, Telnyx, une page d'ElevenLabs. Les citations qui fondent un
  verdict ont été relues le 3 novembre 2026 dans le texte complet de la page officielle, et
  confirmées :
  - l'avis de confidentialité de Twilio (la finalité « Platform Security & Fraud Prevention », qui
    entraîne des modèles, traite le « Customer Content ») et sa page des régions (« Twilio does not
    guarantee that all data will remain within your selected Region », mise à jour du 9 mars 2026) ;
  - l'avenant IA de Sinch, lu en entier : il ne dit rien de l'entraînement, d'où « non établi » ;
  - la page de création d'une transcription par fichier de Gladia : aucune région documentée,
    d'où l'UE « non établie » pour ce mode ;
  - la page des langues de Mistral : « 50 languages » pour Voxtral Transcribe 3, sans liste ; le
    français n'y est nommé que pour la synthèse vocale ;
  - la page de résidence des données d'ElevenLabs (« Data residency is an Enterprise feature » ;
    « processing may nevertheless occur outside of the selected location ») ;
  - les articles 4.2 d et 4.3 des conditions commerciales de Mistral ;
  - la phrase d'Azure « Microsoft does not use customer data to improve its Speech models »
    (`speech-encryption-of-data-at-rest`), avec l'absence de conservation pour la transcription
    rapide et la synthèse en temps réel (pages de confidentialité du service Speech) ;
  - l'article 18 des conditions de Google Cloud (« Google will not use Customer Data to train or
    fine-tune any AI/ML models […] »), Text-to-Speech figurant parmi les services d'IA visés ;
  - la page d'OVHcloud AI Endpoints (« hébergés et opérés en Union Européenne », « Vos données ne
    servent jamais à entraîner nos modèles ») et sa documentation de `diarize` ;
  - la page de diarisation de Speechmatics et la page SSML de Google (aucune restriction de langue,
    sauf l'option « zero-as-zero », en anglais seulement) ;
  - la FAQ d'Amazon Polly (« Some portion of content processed by Amazon Polly may be stored in
    another AWS region », exclusion par une politique AWS Organizations) et la page de ces
    politiques (« AWS AI services may use and store customer content for […] model training »).

  Les autres valeurs n'ont pas été relues ; une relecture est nécessaire avant toute décision
  d'achat.
- **Jeu synthétique :** voix de synthèse, sans bruit, accent ni coupure. L'audio mesuré est celui
  de la V1 (`FORMAT_SYNTHESE = "audio-24khz-48kbitrate-mono-mp3"`, `voix/contrat.py`), pas la bande
  téléphonique à 8 kHz d'un vrai appel. La
  mesure borne la qualité par le haut.
- **Latence de la synthèse non interprétable :** l'API garde la synthèse en mémoire depuis son
  démarrage ; les durées relevées (0,4 à 2,1 s) peuvent venir de cette mémoire.
- **Facturation de la séparation des locuteurs par Azure non établie**, comptée par prudence.
- **Services non examinés en transcription,** faute de place sous le plafond de cinq candidats :
  Google Speech-to-Text (relevé en annexe seulement), AWS Transcribe, Deepgram, AssemblyAI,
  Scaleway. Aucun jugement n'est porté sur eux.
- **Dates des valeurs :** lues le 3 novembre 2026, sauf l'exclusion des modèles d'OpenAI et la
  première mesure d'Azure, reprises de D-50 (14 octobre 2026).
