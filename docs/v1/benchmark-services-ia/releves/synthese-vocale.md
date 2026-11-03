# C7, synthèse vocale : notes documentaires (3 novembre 2026)

Grille appliquée sans modification : `docs/v1/benchmark-services-ia/protocole.md`, sections 3.1 et
3.2 ; besoins S1 à S5 (section 2.2) ; choix des candidats selon la section 4. Notation
documentaire seulement (R10) : aucune inscription, aucun compte, pages publiques. Toutes les
pages ont été lues le **3 novembre 2026**. « Non trouvé » = absent des pages lues, pas
« inexistant ».

## 1. Candidats

| Candidat                          | Inclus | Raison                                                                                                                   |
| --------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| Azure AI Speech (voix neuronales) | Oui    | Service en place (D-50), obligatoire (section 4)                                                                         |
| Mistral AI, Voxtral TTS 3         | Oui    | Seul fournisseur établi dans l'UE trouvé avec une synthèse française documentée ; source S03 de la veille                |
| Google Cloud Text-to-Speech       | Oui    | Acteur majeur, point d'accès UE documenté, voix fr-FR nombreuses                                                         |
| Amazon Polly                      | Oui    | Acteur majeur, régions UE, `say-as telephone` documenté pour fr-FR                                                       |
| ElevenLabs                        | Oui    | Acteur de référence de la synthèse « conversationnelle », souvent cité face à Voxtral                                    |
| OVHcloud AI Endpoints             | Non    | Catalogue TTS : `nvr-tts-de-de`, `-en-us`, `-es-es`, `-it-it` ; pas de français (règle section 4)                        |
| Scaleway Generative APIs          | Non    | Page des modèles pris en charge : audio = `whisper-large-v3`, `voxtral-small-24b-2507` (transcription) ; pas de synthèse |
| Acapela Group                     | Non    | Pas de documentation d'API ni de prix publics sur le site ; notation documentaire impossible                             |
| ReadSpeaker                       | Non    | Non examiné faute de temps ; à vérifier si un second fournisseur UE est exigé                                            |

Sources des exclusions :

- OVHcloud : <https://www.ovhcloud.com/fr/public-cloud/ai-endpoints/catalog/> (HTML téléchargé,
  modèles `nvr-tts-*` comptés).
- Scaleway : <https://www.scaleway.com/en/docs/generative-apis/reference-content/supported-models/>
  (HTML téléchargé, recherche « tts », « speech », « voxtral », « whisper »).
- Acapela : <https://www.acapela-group.com/> (« Cloud API for streaming » cité, pas de lien de
  documentation, prix sur demande).

## 2. Azure AI Speech (en place)

| Critère (nature)                   | Valeur relevée                                                                                                                                                                                                                                             | Source |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| UE (éliminatoire)                  | Points d'accès de synthèse temps réel en West Europe, France Central, Germany West Central, North Europe, Sweden Central, Italy North… Production Muninn : West Europe (D-50)                                                                              | A1     |
| Entraînement (éliminatoire)        | « Microsoft **does not** use customer data to improve its Speech models. » ; « if endpoint logging is disabled and no customizations are used, then no customer data is stored »                                                                           | A2     |
| Rétention (rapporté)               | Voix préconstruites : « Neither input text nor output audio content is stored in Microsoft logs » ; « Microsoft doesn't retain or store the text that you provide with the real-time synthesis » (API Long Audio : stockage jusqu'à suppression)           | A3     |
| Coût (départage)                   | 13,4656 € par million de caractères (« S1 Neural Text To Speech Characters », West Europe) ; voix Neural HD 19,7495 € par million                                                                                                                          | A4     |
| Intégration (principal)            | API REST `cognitiveservices/v1` (corps SSML), SDK Python `azure-cognitiveservices-speech`, exemples ; quotas sur une page dédiée (valeurs non relevées) ; audio limité à 10 min par requête ; sorties 8 kHz µ-law/A-law pour la téléphonie                 | A5     |
| Authentification (rapporté)        | Clé, jeton STS de 10 min, ou **Microsoft Entra** (`aad#<resourceId>#<jeton>`), donc identité managée sans clé (mode en place, D-50)                                                                                                                        | A5     |
| Maturité (rapporté)                | Voix Denise et Henri : type « Standard » neuronal, GA (liste des voix) ; engagement de service : non vérifié aujourd'hui                                                                                                                                   | A6     |
| Documentation (rapporté)           | Microsoft Learn, en anglais (traductions), datée (`updated_at` 2026-06-05 à 2026-11-01 selon la page)                                                                                                                                                      | A1–A6  |
| Voix françaises S1 (éliminatoire)  | 23 voix fr-FR, dont DeniseNeural (F) et HenriNeural (M), plus HD (Vivienne, Remy, Marc, Soleil) et multilingues                                                                                                                                            | A6     |
| Contrôle de lecture S2 (principal) | SSML complet : `say-as` (`telephone`, `number_digit`, `cardinal`, `characters`…) pris en charge pour **tous les paramètres régionaux du français** ; `phoneme` (jeu SAPI défini pour fr-FR) ; lexique personnalisé ; `sub`                                 | A7     |
| Latence et flux S3 (rapporté)      | Pas de chiffre publié ; méthode de mesure (latence du premier octet, propriété `SynthesisFirstByteLatencyMs`) ; sortie en flux ; entrée de texte en flux (websocket v2) **sans SSML** (« doesn't support SSML »). Mesure interne D-50 : deux voix en 1,4 s | A8     |
| Droit d'usage commercial (S4)      | Pas de clause trouvée restreignant l'usage commercial des voix préconstruites ; le code de conduite impose de **signaler la nature synthétique de la voix** (exigence 3), ce qui rejoint D-04 et S5                                                        | A9     |

Sources :

- A1 <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech>
  (ms.date 2026-05-21)
- A2
  <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-encryption-of-data-at-rest>
  (updated 2026-06-05)
- A3
  <https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/text-to-speech/data-privacy-security>
  (updated 2026-08-26)
- A4 <https://prices.azure.com/api/retail/prices> filtre `productName eq 'Azure Speech' and
  armRegionName eq 'westeurope'`, EUR (interrogé le 3 novembre)
- A5 = A1
- A6 <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts>
  (updated 2026-11-01)
- A7
  <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-pronunciation>
  (updated 2026-06-05)
- A8
  <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-lower-speech-synthesis-latency>
  (updated 2026-06-05)
- A9 <https://learn.microsoft.com/en-us/legal/ai-code-of-conduct> (version 4.0, 2026-05-01)

## 3. Mistral AI, Voxtral TTS 3 (`voxtral-mini-tts-3-0`)

| Critère (nature)                   | Valeur relevée                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Source     |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| UE (éliminatoire)                  | Hébergement par défaut dans l'UE (centre d'aide) ; point d'accès `api.eu.mistral.ai` (UE et AELE, +10 %) ; le point d'accès global « no specific inference location is committed » ; **disponibilité de la synthèse sur le point d'accès UE non documentée** (« Regional endpoints only serve models hosted in that region »)                                                                                                                                                    | M1, M2     |
| Entraînement (éliminatoire)        | Conditions commerciales, art. 4.2 : pas d'entraînement sauf exceptions, dont « (d) when Customer uses Labs or Preview Models » ; art. 4.3 : « the opt-out preferences you selected… (including through zero data retention) does not apply to Labs or Preview Models ». Or **Voxtral TTS 3 est en « Public Preview »** (journal des modifications, 20 octobre 2026 : « All four models are in Public Preview » ; fiche du modèle : badge « Public Preview ») → **non satisfait** | M3, M4, M5 |
| Rétention (rapporté)               | Durée par défaut : non trouvée ; rétention nulle (ZDR) sur demande motivée, au paiement à l'usage, couvre « audio speech » — mais sans effet sur l'entraînement des modèles en préversion (M3)                                                                                                                                                                                                                                                                                   | M6         |
| Coût (départage)                   | « $13 /M Chars » (fiche du modèle) ; +10 % sur le point d'accès UE ; page des prix générale : aucun montant TTS                                                                                                                                                                                                                                                                                                                                                                  | M5, M7     |
| Intégration (principal)            | REST `POST /v1/audio/speech`, SDK Python et TypeScript (`client.audio.speech.complete`), quickstart ; flux SSE (`speech.audio.delta`) ; limites de débit : non trouvées                                                                                                                                                                                                                                                                                                          | M8, M9     |
| Authentification (rapporté)        | Clé d'API ; mode sans clé (identité managée) : non trouvé                                                                                                                                                                                                                                                                                                                                                                                                                        | M8         |
| Maturité (rapporté)                | Public Preview depuis le 20 octobre 2026 ; prédécesseur `voxtral-mini-tts-2603` déprécié le 31/10/2026, retrait le 30/04/2027 ; engagement de service : non trouvé                                                                                                                                                                                                                                                                                                               | M4, M10    |
| Documentation (rapporté)           | Publique, en anglais ; pages non datées (sauf centre d'aide)                                                                                                                                                                                                                                                                                                                                                                                                                     | M8         |
| Voix françaises S1 (éliminatoire)  | Voxtral 3 : 4 voix fr (Marie, Manon, Lea, Camille), genre non indiqué ; Voxtral 2 : Marie seule (variantes d'émotion). Satisfait pour Voxtral 3 sur le nombre ; distinction des voix non vérifiable sans écoute                                                                                                                                                                                                                                                                  | M11        |
| Contrôle de lecture S2 (principal) | Pas de SSML ; lecture des nombres non documentée ; `phoneme_hints` par mot, mais le jeu de phonèmes exclut « the French ʁ or nasal vowels » ; balises d'émotion (34) et de débit (2)                                                                                                                                                                                                                                                                                             | M12, M13   |
| Latence et flux S3 (rapporté)      | « ~90 ms time-to-first-audio » (fiche du modèle) ; flux SSE ; modèle temps réel cité (`voxtral-mini-tts-realtime-3-0`) mais absent de la liste des modèles                                                                                                                                                                                                                                                                                                                       | M5, M9     |
| Droit d'usage commercial (S4)      | Art. 3.1 : le client « owns all Output » ; droits sur les voix préréglées et consentement du clonage : non trouvés                                                                                                                                                                                                                                                                                                                                                               | M3         |

Sources :

- M1
  <https://help.mistral.ai/en/articles/347629-where-do-you-store-my-data-or-my-organization-s-data>
- M2 <https://docs.mistral.ai/inference/regional-inference> (non datée)
- M3 <https://legal.mistral.ai/terms/commercial-terms-of-service/> (en vigueur le 25 septembre 2026)
- M4 <https://docs.mistral.ai/getting-started/changelog/>
- M5 <https://docs.mistral.ai/models/voxtral-mini-tts-3-0>
- M6 <https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr> (12 août
  2026) ;
  <https://help.mistral.ai/en/articles/455207-can-i-opt-out-of-my-input-or-output-data-being-used-for-training>
  (3 septembre 2026)
- M7 <https://mistral.ai/pricing>
- M8 <https://docs.mistral.ai/studio/audio/overview.md>
- M9 <https://docs.mistral.ai/studio/audio/text-to-speech/stream-speech>
- M10 <https://docs.mistral.ai/getting-started/models/>
- M11 <https://docs.mistral.ai/studio/audio/text-to-speech/voices> ;
  <https://docs.mistral.ai/studio/audio/specs-and-limits/languages> (35 langues TTS, fr avec 4 voix)
- M12 <https://docs.mistral.ai/studio/audio/text-to-speech/overview>
- M13 <https://docs.mistral.ai/studio/audio/text-to-speech/custom-pronunciation>

## 4. Google Cloud Text-to-Speech

| Critère (nature)                   | Valeur relevée                                                                                                                                                                                                                                                                                                                                                          | Source |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| UE (éliminatoire)                  | Point d'accès `eu-texttospeech.googleapis.com` : « your data at-rest and in-use stay within the regional or continental boundaries of Europe » ; Chirp 3: HD disponible en multirégion EU (GA) et europe-west2. Ambiguïté : la mention « Only Neural2 voices are available from these endpoints » suit le tableau EU/US ; Neural2 n'apparaît pas dans le tableau Europe | G1, G2 |
| Entraînement (éliminatoire)        | Service Specific Terms, art. 18 « Training Restriction » : « Google will not use Customer Data to train or fine-tune any AI/ML models without Customer's prior permission or instruction » ; Text-to-Speech classé parmi les « AI/ML Services »                                                                                                                         | G3, G4 |
| Rétention (rapporté)               | « Cloud Text-to-Speech is both stateless and resourceless… Google does not log any customer Cloud TTS text or audio data »                                                                                                                                                                                                                                              | G5     |
| Coût (départage)                   | Chirp 3: HD 30 $/M caractères ; Neural2 16 $/M ; WaveNet et Standard 4 $/M ; Studio 160 $/M (au-delà des franchises)                                                                                                                                                                                                                                                    | G6     |
| Intégration (principal)            | REST `v1/text:synthesize`, bibliothèque Python (exemple `streaming_synthesize`), exemples ; limites de débit : non relevées                                                                                                                                                                                                                                             | G1, G2 |
| Authentification (rapporté)        | Jeton OAuth (exemple officiel `gcloud auth print-access-token`) ; fédération depuis une identité Azure : non vérifiée                                                                                                                                                                                                                                                   | G1     |
| Maturité (rapporté)                | Chirp 3: HD GA dans la zone `eu` ; SSML et contrôles de voix de Chirp 3: HD en préversion ; SLA Text-to-Speech ≥ 99,9 %                                                                                                                                                                                                                                                 | G2, G7 |
| Documentation (rapporté)           | Publique, datée (« Last updated 2026-10-26 UTC »), en anglais et en français                                                                                                                                                                                                                                                                                            | G1, G2 |
| Voix françaises S1 (éliminatoire)  | 42 voix fr-FR, dont 30 Chirp3-HD (14 F, 16 M), 2 Neural2 (F, M), 2 Studio, 2 WaveNet, 2 Standard                                                                                                                                                                                                                                                                        | G8     |
| Contrôle de lecture S2 (principal) | SSML général : `say-as` avec `telephone`, `cardinal`, `characters`… (exemples en anglais ; français non précisé) ; Chirp 3: HD : SSML **en préversion**, `say-as`, `phoneme`, `sub`, `break` en requête synchrone, « SSML tags are not currently supported for streaming requests » ; balises de pause dans le champ `markup`                                           | G2, G9 |
| Latence et flux S3 (rapporté)      | Synthèse en flux bidirectionnelle (`StreamingSynthesize`) pour Chirp 3: HD ; latence chiffrée : non trouvée                                                                                                                                                                                                                                                             | G2     |
| Droit d'usage commercial (S4)      | Non trouvé                                                                                                                                                                                                                                                                                                                                                              | —      |

Sources :

- G1 <https://docs.cloud.google.com/text-to-speech/docs/endpoints> (2026-10-26 ; tableau lu dans le
  HTML : icônes « Supported »)
- G2 <https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd> (2026-10-26)
- G3 <https://cloud.google.com/terms/service-terms> (modifié le 30 octobre 2026)
- G4 <https://cloud.google.com/terms/services>
- G5 <https://docs.cloud.google.com/text-to-speech/docs/data-logging> (2026-10-26)
- G6 <https://cloud.google.com/text-to-speech/pricing>
- G7 <https://cloud.google.com/text-to-speech/sla>
- G8 <https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types>
- G9 <https://docs.cloud.google.com/text-to-speech/docs/ssml>

## 5. Amazon Polly

| Critère (nature)                   | Valeur relevée                                                                                                                                                                                                                                                                                                                                        | Source |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| UE (éliminatoire)                  | Moteur génératif en Europe (Frankfurt) eu-central-1, Londres, Zurich (Londres et Zurich : seulement Florian et Ambre en fr-FR) ; voix neuronales notamment en EU (Ireland). Mais « Some portion of content processed by Amazon Polly may be stored in another AWS region » pour l'amélioration du service, sauf exclusion                             | P1, P2 |
| Entraînement (éliminatoire)        | Par défaut, usage possible : « AWS AI services may use and store customer content for service improvement… model training » ; exclusion par une politique AWS Organizations ; FAQ : « You may opt out of having your content used to improve and develop the quality of Amazon Polly ». **Satisfait seulement sous condition d'exclusion configurée** | P2, P3 |
| Rétention (rapporté)               | « may store and use text inputs processed by the service solely to provide and maintain the service » ; durée : non trouvée ; l'exclusion supprime les copies conservées pour l'amélioration                                                                                                                                                          | P2, P3 |
| Coût (départage)                   | Standard 4 $/M ; Neural 16 $/M ; Generative 30 $/M ; Long-Form 100 $/M caractères                                                                                                                                                                                                                                                                     | P4     |
| Intégration (principal)            | API AWS (SDK boto3), API de flux bidirectionnelle `StartSpeechSynthesisStream` (Frankfurt) ; sorties 8, 16, 22, 24 kHz, PCM ; limites : non relevées                                                                                                                                                                                                  | P1     |
| Authentification (rapporté)        | IAM AWS (recommandation de la page de protection des données) ; fédération depuis une identité Azure : non vérifiée                                                                                                                                                                                                                                   | P5     |
| Maturité (rapporté)                | Service établi ; voix génératives fr-FR disponibles ; avertissement d'AWS sur de possibles « hallucinations » du moteur génératif (mot coupé) ; SLA : non trouvé                                                                                                                                                                                      | P1     |
| Documentation (rapporté)           | Publique, en anglais, non datée                                                                                                                                                                                                                                                                                                                       | P1     |
| Voix françaises S1 (éliminatoire)  | fr-FR : Ambre (F), Céline (F), Florian (M), Léa (F), Mathieu (M), Rémi (M) ; génératif : 5 ; neuronal : Léa, Rémi                                                                                                                                                                                                                                     | P6     |
| Contrôle de lecture S2 (principal) | `say-as` disponible pour le moteur génératif (« Full availability »), partiel en neuronal ; `interpret-as="telephone"` **explicitement disponible pour fr-FR** ; `digits`, `cardinal` ; `phoneme` partiel en génératif                                                                                                                                | P7, P8 |
| Latence et flux S3 (rapporté)      | Flux d'entrée et de sortie simultanés (génératif) ; latence chiffrée : non trouvée (« low latency » dans la FAQ) ; SSML en mode flux : non trouvé                                                                                                                                                                                                     | P1, P2 |
| Droit d'usage commercial (S4)      | « As between you and AWS, your Polly output belongs to you » ; réutilisation d'invites statiques : « The service does not restrict this »                                                                                                                                                                                                             | P2     |

Sources :

- P1 <https://docs.aws.amazon.com/polly/latest/dg/generative-voices.html>
- P2 <https://aws.amazon.com/polly/faqs/>
- P3
  <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ai-opt-out.html>
- P4 <https://aws.amazon.com/polly/pricing/>
- P5 <https://docs.aws.amazon.com/polly/latest/dg/data-protection.html>
- P6 <https://docs.aws.amazon.com/polly/latest/dg/available-voices.html>
- P7 <https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html>
- P8 <https://docs.aws.amazon.com/polly/latest/dg/say-as-tag.html>

## 6. ElevenLabs

| Critère (nature)                   | Valeur relevée                                                                                                                                                                                                                                                                                                                                 | Source |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| UE (éliminatoire)                  | Résidence UE « exclusive feature available to ElevenLabs' Enterprise customers » (`api.eu.residency.elevenlabs.io`) ; « While storage will take place in the selected location, processing may nevertheless occur outside of the selected location » → **non satisfait** (traitement hors UE possible, hors offre Enterprise aucune résidence) | E1     |
| Entraînement (éliminatoire)        | Conditions d'utilisation (9 octobre 2026) : licence d'usage du contenu « to improve the Services » ; exclusion possible par le menu « Data use » ; rétention nulle (Enterprise)                                                                                                                                                                | E2, E3 |
| Rétention (rapporté)               | Zero Retention Mode réservé à des clients Enterprise choisis, `enable_logging=false` par requête                                                                                                                                                                                                                                               | E3     |
| Coût (départage)                   | Flash/Turbo 0,04 $ par millier de caractères (40 $/M) ; Multilingual v2 et v3 0,08 $ (80 $/M)                                                                                                                                                                                                                                                  | E4     |
| Intégration (principal)            | API REST, SDK ; non approfondi (éliminé)                                                                                                                                                                                                                                                                                                       | E5     |
| Authentification (rapporté)        | Clé d'API (clé distincte pour l'environnement UE)                                                                                                                                                                                                                                                                                              | E1     |
| Maturité (rapporté)                | Modèles GA cités ; SLA : non trouvé                                                                                                                                                                                                                                                                                                            | E5     |
| Documentation (rapporté)           | Publique, en anglais, non datée                                                                                                                                                                                                                                                                                                                | E1, E5 |
| Voix françaises S1 (éliminatoire)  | Français pris en charge par v3, v4 Turbo, Multilingual v2, Flash v2.5 ; voix françaises via la bibliothèque (clones partagés) ; liste officielle de voix françaises préconstruites : non trouvée                                                                                                                                               | E5     |
| Contrôle de lecture S2 (principal) | Pas de SSML documenté sur la page des modèles ; normalisation des nombres désactivée par défaut sur Flash v2.5 (activable en Enterprise), « phone numbers may be read in a way that isn't clear » ; Multilingual v2 recommandé pour les numéros                                                                                                | E5     |
| Latence et flux S3 (rapporté)      | Médiane ~100 ms (v4 Turbo, Flash v2.5), hors réseau                                                                                                                                                                                                                                                                                            | E5     |
| Droit d'usage commercial (S4)      | Commercial seulement en abonnement payant ; gratuit = non commercial                                                                                                                                                                                                                                                                           | E2     |

Sources :

- E1 <https://elevenlabs.io/docs/overview/administration/data-residency>
- E2 <https://elevenlabs.io/terms-of-use> (« Last Updated: 09 October 2026 »)
- E3 <https://elevenlabs.io/docs/eleven-api/resources/zero-retention-mode> (via résultat de
  recherche, non ouvert)
- E4 <https://elevenlabs.io/pricing/api>
- E5 <https://elevenlabs.io/docs/overview/models>

## 7. Éliminatoires

| Candidat         | UE                                                           | Entraînement                                                       | Voix FR (S1)       | Verdict               |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------ | --------------------- |
| Azure AI Speech  | Oui (West Europe, France Central…)                           | Oui (engagement écrit)                                             | Oui (23)           | Retenu                |
| Google Cloud TTS | Oui, par `eu-texttospeech`                                   | Oui (Service Specific Terms, art. 18)                              | Oui (42)           | Retenu                |
| Amazon Polly     | Oui (Frankfurt), sous exclusion                              | Sous condition d'exclusion configurée                              | Oui (6)            | Retenu sous condition |
| Mistral Voxtral  | Point d'accès UE ; TTS non confirmé                          | **Non** (préversion : entraînement possible, exclusion inopérante) | Oui (4)            | **Écarté**            |
| ElevenLabs       | **Non** (Enterprise seulement ; traitement hors UE possible) | Exclusion possible                                                 | Oui (bibliothèque) | **Écarté**            |

## 8. Classement des retenus (critères principaux : intégration, contrôle de lecture)

> Classement provisoire du relevé, remplacé par `rapport.md`, section 5 : la page SSML de Google,
> relue le 3/11, ne restreint `say-as telephone` à aucune langue (seule l'option « zero-as-zero »
> est limitée à l'anglais) ; Azure, Google et Polly sont donc à égalité sur les critères
> principaux, et l'ordre Azure, Google, Polly est fixé hors grille sur les réserves.

1. **Azure AI Speech.** Contrôle de lecture le plus complet et documenté pour le français
   (`say-as telephone`/`number_digit`, phonèmes SAPI fr-FR, lexique) ; REST et SDK Python ;
   seule authentification sans clé déjà en place (Entra, identité managée) ; aucune migration.
   Départage favorable : 13,47 € par million (le moins cher des voix neuronales).
2. **Amazon Polly.** `say-as telephone` explicitement documenté pour fr-FR et complet en
   génératif ; flux bidirectionnel à Frankfurt. Mais entraînement par défaut (exclusion
   AWS Organizations à poser), authentification IAM étrangère à Azure, coût 16 à 30 $/M.
3. **Google Cloud TTS.** Voix nombreuses et datation de la doc exemplaire, mais SSML de
   Chirp 3: HD en préversion et absent du flux ; prise en charge du `say-as telephone` en
   français non précisée ; voix disponibles sur le point d'accès UE ambiguës (Neural2).

Ce qui pourrait changer le classement :

- Voxtral TTS 3 en disponibilité générale, présent sur `api.eu.mistral.ai`, avec une lecture
  des nombres documentée : il redeviendrait éligible (seul fournisseur établi dans l'UE).
- Une mesure aller-retour (section 5 du protocole) montrant que la synthèse Azure lit mal
  les paires de chiffres : S2 devient alors discriminant à mesurer chez les autres.
- Le passage à la cible S3 (agent en direct) : chez Azure et Google, le SSML disparaît en
  entrée de texte en flux ; le contrôle des nombres doit alors se faire en amont (texte
  normalisé), ce qui réduit l'avantage SSML d'Azure.

## 9. Non trouvé (à signaler dans le rapport)

- Latence du premier son chiffrée : Azure, Google, Polly (seuls Mistral ~90 ms et ElevenLabs ~100 ms
  publient un chiffre).
- Engagement de service : Azure (non vérifié aujourd'hui), Polly, Mistral, ElevenLabs. Google : ≥
  99,9 %.
- Limites de débit : Mistral (non trouvées) ; Azure, Google, Polly (pages existantes, valeurs non
  relevées).
- Rétention par défaut de Mistral ; durée de rétention de Polly.
- Disponibilité de Voxtral TTS sur le point d'accès UE de Mistral.
- Droit d'usage commercial explicite des voix préconstruites : Azure, Google ; voix préréglées
  Mistral.
- `say-as telephone` en français chez Google ; SSML en mode flux chez Polly.
- Authentification sans clé depuis une identité Azure pour Google et AWS (fédération non vérifiée).

## 10. Limites de cette note

- Plusieurs valeurs viennent d'un résumé automatique de page (WebFetch) ; les citations clés
  (Mistral 4.2/4.3 et statut Preview, Azure « does not use customer data », Google art. 18,
  tableau EU de Google, prix Azure) ont été relues dans le texte source ou le HTML téléchargé.
- ElevenLabs E3 n'a été lu qu'à travers un résultat de recherche.
- La qualité des voix n'est pas jugée : aucune écoute (R10 hors service en place).
