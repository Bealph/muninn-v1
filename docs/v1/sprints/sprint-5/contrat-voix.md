# Sprint 5, étape 6 : contrat de la voix simulée

Contrat entre l'API, la console et les tests, figé avant le travail des agents spécialistes
(organisation en trois couches, validée par le porteur le 26 octobre 2026). Code partagé :
`src/muninn/voix/contrat.py` et les réglages `VOIX_FOURNISSEUR`, `SPEECH_REGION`,
`SPEECH_ENDPOINT`, `SPEECH_RESOURCE_ID` de `src/muninn/core/config.py`. Décisions : D-50, D-74,
D-88 ; exigences : V-12, CA-8.

## 1. Le parcours

1. La console demande la synthèse d'un scénario ; l'API rend un extrait MP3 par tour.
2. La console joue la sonnerie (15 s, D-68), puis les extraits, bulle par bulle.
3. À la fin de l'appel joué, la console renvoie l'enregistrement (extraits mis bout à bout).
4. L'API transcrit (séparation des locuteurs), recompose « Agent : … / Appelant : … », traite comme
   `POST /v1/demo/runs`, et rend le résultat, ses étapes (la transcription en tête) et ce qu'elle a
   entendu. CA-8 : de la fin de l'appel joué à la réponse, 45 s au plus (D-74).

## 2. Les routes de l'API

| Route                                   | Entrée                                                                 | Sortie                                                                             | Erreurs                                                                                                                  |
| --------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `POST /v1/demo/voice/synthesis`         | JSON `DemandeSynthese` : `scenario_id`                                 | `ReponseSynthese` : voix, et un `TourSynthetise` par tour (texte, MP3 en base64)   | 404 `scenario_not_found` ; 422 `validation_failed` ; 429 (limite de débit) ; 503 `voice_unavailable`                     |
| `POST /v1/demo/voice/call?scenario_id=` | Corps brut `audio/mpeg`, 1,5 Mo au plus, reçu en 20 s au plus, mémoire | `ReponseDemo` (comme `/v1/demo/runs`), plus `transcription` : `TranscriptionAppel` | 404 ; 408 `request_timeout` ; 413 `audio_too_large` ; 415 `unsupported_media_type` ; 422 ; 429 ; 503 `voice_unavailable` |

- Les deux routes passent par la limite de débit des appels au modèle (`reserver`), après les
  contrôles : une demande refusée (404, 408, 413, 415, 422) ne consomme rien.
- `/synthesis` : la synthèse d'un scénario est gardée en mémoire après la première demande ; les
  suivantes ne réservent ni ne synthétisent rien.
- `/call` : quatre appels au plus en même temps, lecture du corps comprise ; au-delà, 429 immédiat.
- Une configuration de voix incomplète, ou le faux fournisseur hors de l'environnement local,
  rend 503 `voice_unavailable`.
- `scenario_id` doit exister dans le jeu synthétique ; le modèle simulé (`P4-perimetre`) n'a pas de
  dialogue et est refusé (404).
- `/call` : la transcription est une étape `transcription` (niveau 1) au début de `steps`, avec sa
  durée ; le reste est le traitement réel de `/v1/demo/runs`, avec `conformity` contre l'attendu
  du scénario. L'enregistrement en base (`app.traitements`) se fait comme pour un scénario.
- Le contenu n'est tenu pour synthétique (stocké, corrigeable) que si la transcription reprend le
  dialogue du scénario, et rien d'autre (`voix/fidelite.py`) : sinon, mesures seules, comme un
  texte libre ; `transcription.matches_scenario` le dit.
- Aucun audio sur disque : corps lu par morceaux (`request.stream()`), borné en taille et en
  temps ; jamais `UploadFile`. Aucun texte ni audio
  dans les journaux ni dans les traces ; la trace porte seulement des nombres (octets, tours,
  durée).

## 3. Les routes de la console

| Route                                    | Rôle                                                              |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `GET /demonstration`                     | L'écran, d'après la maquette V0 (`demo-officielle/v0/index.html`) |
| `POST /demonstration/synthese`           | Relais JSON vers `/v1/demo/voice/synthesis`                       |
| `POST /demonstration/appel?scenario_id=` | Relais du corps brut `audio/mpeg` vers `/v1/demo/voice/call`      |

La console ne parle qu'à l'API (ADR-09). Quatre scénarios, comme la V0 : SC-Q4, SC-04, SC-Q1,
SC-10. L'écran « Agent » est gardé.

## 4. Répartition du travail

| Couche | Rôle                                                                    | Fichiers                                                                                                                                                                                                                          |
| ------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3      | A1 : voix et API                                                        | `src/muninn/voix/` (sauf `contrat.py`), `src/muninn/api/voix.py`, `src/muninn/api/main.py` (inclusion), `src/muninn/api/agent.py` (traitement partagé avec `/v1/demo/runs`), tests `tests/test_voix.py`, `tests/test_api_voix.py` |
| 3      | A2 : écran « Démonstration »                                            | `src/muninn/console/` (route et gabarit), `tests/test_console_demonstration.py`, accessibilité                                                                                                                                    |
| 3      | A3 : livraison et preuves                                               | `infra/azure/13-voix.sh`, `eval/production/verifier_ca8.py`, `docs/exploitation.md`                                                                                                                                               |
| 2      | Relecture du code, sécurité des données et de l'audio, accessibilité    | Lecture des branches de la couche 3                                                                                                                                                                                               |
| 1      | Orchestrateur : contrat, intégration, tests en conteneur, PR, livraison | Tout, après la couche 2                                                                                                                                                                                                           |

Personne ne modifie `src/muninn/voix/contrat.py` sans passer par l'orchestrateur.
