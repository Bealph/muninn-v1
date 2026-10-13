# Contrat d'API de Muninn

**Version :** 1.0
**Date :** 12 octobre 2026
**Historique :** première version. Elle fixe le contrat `DossierDraft` 1.1 (D-24) et ajoute au
contrat les points d'accès relevés par P-09 et P-10.
**Phase :** 2 (industrialisation)
**Statut :** proposition, à valider par le porteur
**Compétences servies :** C5 (API REST de mise à disposition des données), C9 (API exposant le
modèle d'IA) ; préparation de C10 (intégration), C12 (tests de contrat) et C17 (composants)
**Documents liés :** `../sources_de_donnees/01-user-stories.md`, `../sources_de_donnees/02-flux-de-donnees.md`,
`../architecture_de_donnees/02-modele-de-donnees.md`, `../architecture_de_donnees/03-acces-et-exposition.md`,
`../architecture_de_donnees/04-verification-exactitude.md`, `../architecture_de_donnees/05-registre-rgpd.md`,
`../../decisions.md`

## 1. Objet, sources et conventions de lecture

Ce document est le contrat des interfaces HTTP de Muninn : l'API produit, appelée par
l'application mobile et par les fournisseurs, l'API d'extraction (C9) et l'API des référentiels
(C5). Il ne contient aucune ligne de code applicatif. Les exemples JSON et les extraits de JSON
Schema font partie du contrat : chacun a été validé contre son schéma (section 9.4).

Sources : la table d'API de la passation back-end (section 8), son contrat `DossierDraft` 1.0
(section 6) et ses règles R1 à R10 ; les décisions D-01 à D-26 ; les points P-01 à P-18 du
document 02 de la phase 0 ; les documents 02, 03 et 04 de la phase 1.

Conventions :

- **[H]** marque une hypothèse : valeur de départ, à confirmer par une mesure ou une décision.
- **Démo** : « oui » si le point d'accès sert la démo du 29 octobre 2026 (document 01, section 8).
- **Lot** : lot de livraison de la passation (0 à 6). L'API des référentiels, absente de la
  passation, est rattachée au lot 1, car l'extraction de la démo l'appelle.
- **Écart P-03** : marque les seules réponses qui contiennent un brouillon en clair hors d'une
  enveloppe chiffrée pour un appareil. Elles n'existent que dans la configuration de démo
  (D-07).
- Les noms de champs, de chemins et de codes sont en anglais, en `snake_case`. Les champs
  historiques du contrat `DossierDraft` (`nom`, `commune`, `objet_court`, etc.) restent en
  français (section 3.1).

## 2. Conventions communes

### 2.1 Services et URL de base

| Service              | URL de base (proposée)           | Joignable depuis          | Document OpenAPI exporté       |
| -------------------- | -------------------------------- | ------------------------- | ------------------------------ |
| api                  | `https://api.muninn.example/v1`  | Internet (TLS)            | `docs/openapi.json`            |
| voice-gateway        | `wss://voice.muninn.example/v1`  | Internet, CPaaS seulement | sans objet (WebSocket)         |
| extraction           | `https://extraction.internal/v1` | Réseau interne            | `docs/openapi-extraction.json` |
| API des référentiels | `https://refdata.internal/v1`    | Réseau interne            | `docs/openapi-refdata.json`    |
| relay                | `https://relay.internal/v1`      | Réseau interne            | `docs/openapi-relay.json`      |

Les noms de domaine sont des exemples (`.example`, `.internal`) [H : fixés par ADR-06]. Les
points de supervision `/health` et `/ready` sont à la racine de chaque service, hors préfixe de
version, car ils décrivent le processus et non le contrat.

### 2.2 Versionnage

- **Version majeure dans le chemin** : `/v1`. Une rupture de contrat ouvre `/v2`, servi en
  parallèle de `/v1` pendant la transition.
- **Évolutions mineures sans changement de chemin** : ajout d'un point d'accès, d'un champ de
  réponse facultatif, d'un paramètre de requête facultatif. Le client ignore les champs de
  réponse qu'il ne connaît pas (lecteur tolérant).
- **Sont des ruptures** : suppression ou renommage d'un champ, changement de type, ajout d'un
  champ de requête obligatoire, ajout d'une valeur à une énumération de réponse, changement de
  sens d'un code d'erreur.
- **Retrait annoncé** : un point d'accès en fin de vie porte l'en-tête `Deprecation` (RFC 9745,
  valeur de la forme `@<secondes depuis l'epoch>`) et l'en-tête `Sunset` (RFC 8594, valeur
  HTTP-date). Délai minimal entre `Deprecation` et `Sunset` : 90 jours [H], pour laisser les
  artisans mettre à jour l'application.
- **Version du contrat `DossierDraft`** : portée par `schema_version` dans le brouillon, et
  indépendante de la version de l'API (section 3.6).

### 2.3 Formats

| Élément                      | Règle                                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Corps                        | `application/json`, UTF-8 ; `multipart/form-data` pour l'audio et l'image ; `application/octet-stream` pour les blobs chiffrés |
| Instants                     | RFC 3339 avec décalage. Le serveur rend ses horodatages en UTC (`Z`). Un rendez-vous garde le décalage local de l'artisan      |
| Dates                        | `AAAA-MM-JJ`                                                                                                                   |
| Identifiants exposés         | UUID aléatoires (document 02 de la phase 1, principe 4)                                                                        |
| Binaire dans un JSON         | Base64 standard avec remplissage (RFC 4648, section 4)                                                                         |
| Numéros de téléphone         | E.164 (`+33…`)                                                                                                                 |
| Taille d'un corps JSON       | 64 Kio au plus, sauf mention contraire                                                                                         |
| Langue des messages d'erreur | Français, texte fixe par code d'erreur                                                                                         |

### 2.4 Authentification par point d'accès

| Schéma                 | Porteur                                                                                        | Mécanisme                                                                                                                                                                            | Refus                                                                       |
| ---------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| `device_token`         | Application mobile                                                                             | `Authorization: Bearer mdt_…` ; jeton aléatoire de 256 bits rendu une fois par `POST /v1/auth/otp/verify` ; le serveur n'en garde que l'empreinte SHA-256 (document 03, section 5.3) | 401 `unauthenticated`, `device_revoked`, `token_expired`                    |
| `device_token_pending` | Appareil en attente d'approbation (D-22)                                                       | Même jeton, de portée réduite à cinq points (section 6.3) ; aucune enveloppe                                                                                                         | 403 `device_pending_approval` sur tout autre point                          |
| `service_token`        | Composant interne (api, voice-gateway, extraction, console, harnais d'évaluation, serveur MCP) | `Authorization: Bearer mst_…` ; un jeton par couple appelant-appelé, avec une liste de portées ; TLS mutuel si l'hébergeur le permet [H : ADR-06]                                    | 401 `unauthenticated` ; 403 `scope_denied`                                  |
| `webhook_signature`    | CPaaS, fournisseur SMS, paiement                                                               | Signature du fournisseur : `X-Twilio-Signature` ou `telnyx-signature-ed25519` et `telnyx-timestamp` (ADR-02) ; mécanisme du fournisseur SMS (ADR-05) ; `Stripe-Signature`            | 401 `invalid_signature` ; 409 `duplicate_event` rendu en 200 (section 6.12) |
| `media_token`          | CPaaS, à l'ouverture du flux média                                                             | Jeton à usage unique lié à la session d'appel, valable 30 secondes [H], placé par l'api dans la réponse au webhook d'appel entrant                                                   | Connexion refusée                                                           |
| `none`                 | Tout appelant                                                                                  | Aucun ; protégé par la limitation de débit                                                                                                                                           | sans objet                                                                  |

Règles communes :

- l'api déduit `account_id` et `device_id` du jeton. Un identifiant de compte placé dans le corps
  ou l'URL est ignoré (TA-18) ;
- un appareil révoqué reçoit 401 `device_revoked` à sa requête suivante (TA-17) ;
- l'accès à la ressource d'un autre compte rend 404 `not_found`, jamais 403, pour ne pas révéler
  son existence (TA-16) ;
- l'exploitant ne s'authentifie jamais directement auprès de l'api. Il se connecte à la console
  (compte nominatif, second facteur), dont le serveur appelle l'api avec un `service_token` de
  portée `demo` (section 4.9).

Portées des jetons de service :

| Appelant      | Appelé               | Portées                                                            |
| ------------- | -------------------- | ------------------------------------------------------------------ |
| api           | extraction           | `extract:text`, `extract:audio`, `extract:image`, `transcribe`     |
| voice-gateway | extraction           | `extract:text`                                                     |
| harnais (CI)  | extraction           | `extract:text`, `extract:audio`, `extract:image`                   |
| extraction    | API des référentiels | `checks`, `postal_codes`, `lexicons`, `versions`                   |
| voice-gateway | API des référentiels | `lexicons`, `holidays`, `versions`                                 |
| api           | API des référentiels | `forwarding_codes`, `naf_trades`, `holidays`, `versions`           |
| console       | API des référentiels | `versions`, `lexicons`                                             |
| serveur MCP   | API des référentiels | `versions`, `lexicons`, `postal_codes` (D-21, après le 29 octobre) |
| voice-gateway | relay                | `relay:draft`                                                      |
| api           | relay                | `notify:device`                                                    |
| api           | voice-gateway        | `sessions`                                                         |
| console       | api                  | `demo`                                                             |

### 2.5 Idempotence

- **En-tête `Idempotency-Key`** : UUID v4 choisi par le client. Le mécanisme suit le brouillon
  IETF `draft-ietf-httpapi-idempotency-key-header` (version 07 du 15 octobre 2025, expirée, sans
  numéro de RFC). Il est donc une convention de Muninn inspirée de ce brouillon, pas une norme.
- **Portée** : la clé est propre au compte (ou au jeton de service) et au chemin. Elle est gardée
  24 heures [H].
- **Rejeu** : même clé et même corps : le serveur rend la réponse d'origine, avec l'en-tête
  `Idempotent-Replayed: true`. Même clé et corps différent : 422 `idempotency_key_mismatch`.
  Même clé pendant le traitement : 409 `request_in_progress`.
- **Ce que le serveur garde** : la clé, une empreinte HMAC du corps (poivre serveur) et la
  réponse, **seulement si la réponse ne contient aucune donnée personnelle**. C'est le cas des
  réponses de `POST /v1/sms` (identifiant et statut), de l'archive et du paiement.
- **Pas d'idempotence pour l'extraction.** Rejouer une extraction exigerait de garder le
  brouillon en clair pour le rendre une seconde fois, ce que R1 interdit. Une extraction relancée
  est une nouvelle extraction, avec un nouveau `draft_id`. Le coût d'une relance est borné par
  les quotas (section 2.7). Ce choix est dit, pas subi.
- **Requis** sur `POST /v1/sms`, `POST /v1/archive/blobs`, `POST /v1/billing/checkout`,
  `POST /v1/erasures` ; **accepté** sur `POST /v1/envelopes/{envelope_id}/ack` et
  `POST /v1/drafts/{draft_id}/review`. Les `PUT` sont idempotents par nature.
- **Webhooks** : l'idempotence repose sur l'identifiant d'événement du fournisseur
  (`app.processed_webhooks`). Pour le paiement, la documentation du prestataire indique qu'un
  même événement peut être livré plusieurs fois et que deux événements distincts peuvent
  décrire le même changement : le dédoublonnage se fait sur `event.id`, puis sur le couple
  identifiant de l'objet et type d'événement (section 13).

### 2.6 Pagination

Pagination par curseur opaque, sur les seules listes qui peuvent croître :
`GET /v1/envelopes`, `GET /v1/archive/blobs`.

- Paramètres : `limit` (1 à 100, défaut 50) et `cursor` (valeur rendue par la page précédente).
- Réponse : `{"items": [...], "next_cursor": "…" | null}`.
- Le curseur encode une position (horodatage et identifiant), jamais une donnée personnelle. Un
  curseur invalide ou expiré rend 400 `invalid_cursor`.

### 2.7 Limitation de débit et quotas

- Les limites reprennent le document 03 de la phase 1 (section 5.4) et les complètent pour les
  nouveaux points (inventaire de la section 7). Toutes sont des valeurs de départ [H].
- **Dépassement** : 429 `rate_limited` (fenêtre courte) ou `quota_exceeded` (quota journalier),
  avec l'en-tête `Retry-After` en secondes (RFC 9110, section 10.2.3 ; code 429 : RFC 6585).
- **En-têtes d'information** : `RateLimit-Policy` et `RateLimit`, selon le brouillon IETF
  `draft-ietf-httpapi-ratelimit-headers` (version 11 du 23 mai 2026, actif, sans numéro de RFC).
  Exemple : `RateLimit-Policy: "device-hour";q=60;w=3600` et `RateLimit: "device-hour";r=12;t=1800`.
  La syntaxe a changé d'une version du brouillon à l'autre : elle est figée à la version 11 et
  testée (section 9) [H : à revoir à la publication de la RFC].
- **Budget des fournisseurs épuisé** (alerte à 50 % et 80 %, arrêt à 100 %, document 03) : les
  points d'extraction rendent 503 `capacity_exhausted` avec `Retry-After`.

### 2.8 Format d'erreur unique

Toute réponse 4xx ou 5xx a ce corps, quel que soit le service (US-39, US-50).

<!-- contract:schema Error -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/error/1",
  "title": "Error",
  "type": "object",
  "additionalProperties": false,
  "required": ["code", "message", "request_id"],
  "properties": {
    "code": { "type": "string", "pattern": "^[a-z][a-z0-9_]{2,63}$" },
    "message": { "type": "string", "minLength": 1, "maxLength": 300 },
    "request_id": { "type": "string", "format": "uuid" },
    "details": {
      "type": "array",
      "maxItems": 50,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["field", "issue"],
        "properties": {
          "field": { "type": "string", "maxLength": 200 },
          "issue": { "type": "string", "pattern": "^[a-z][a-z0-9_]{2,63}$" }
        }
      }
    },
    "retry_after_s": { "type": "integer", "minimum": 1 }
  }
}
```

<!-- contract:example Error -->
```json
{
  "code": "validation_failed",
  "message": "La requête ne respecte pas le contrat.",
  "request_id": "0b6f6f2e-4f1d-4c51-9a53-2f0d8f1c7a10",
  "details": [{ "field": "body.text", "issue": "too_long" }]
}
```

Règles :

- `request_id` est généré par le serveur et rendu aussi dans l'en-tête `X-Request-Id` de toute
  réponse, réussie ou non. Il relie toutes les lignes de journal de la requête (US-39, critère 2)
  et se propage aux composants internes par le même en-tête.
- `message` est un texte fixe associé au code. **Il ne contient jamais un fragment de l'entrée**
  (TA-38) : ni valeur, ni nom, ni extrait de transcription.
- `details[].field` donne le chemin du champ fautif (`body.client.nom`), jamais sa valeur.
  `details[].issue` est un code fermé (`required`, `too_long`, `bad_format`, `out_of_range`,
  `unknown_field`, `not_allowed`).
- Muninn n'utilise pas le format « Problem Details » de la RFC 9457 (qui rend obsolète la
  RFC 7807) : le format à trois champs vient de la passation et de US-50. Une réponse
  `application/problem+json` pourra être ajoutée en évolution mineure si un consommateur
  externe la demande.

**Catalogue des codes d'erreur.**

| HTTP | Code                            | Sens                                                                                         | Points concernés                            |
| ---- | ------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 400  | `malformed_request`             | Corps illisible (JSON invalide, multipart incomplet)                                         | Tous                                        |
| 400  | `invalid_cursor`                | Curseur de pagination invalide ou expiré                                                     | Listes paginées                             |
| 401  | `unauthenticated`               | Jeton absent ou inconnu                                                                      | Tous sauf `none`                            |
| 401  | `token_expired`                 | Jeton d'appareil inutilisé depuis 90 jours [H]                                               | Points `device_token`                       |
| 401  | `device_revoked`                | Appareil révoqué                                                                             | Points `device_token`                       |
| 401  | `invalid_signature`             | Signature de webhook absente, fausse ou hors fenêtre de temps                                | Webhooks                                    |
| 403  | `scope_denied`                  | Jeton de service hors portée                                                                 | Services internes                           |
| 403  | `device_pending_approval`       | Appareil pas encore approuvé (D-22)                                                          | Points `device_token`                       |
| 403  | `account_not_active`            | Compte en attente d'acceptation du contrat, suspendu ou fermé                                | Points `device_token`                       |
| 404  | `not_found`                     | Ressource absente ou d'un autre compte                                                       | Tous                                        |
| 404  | `feature_disabled`              | Point de démo appelé hors configuration de démo (TA-24)                                      | `/v1/demo/*`                                |
| 409  | `request_in_progress`           | Même `Idempotency-Key` en cours de traitement                                                | Points idempotents                          |
| 409  | `conflict`                      | État incompatible (test de renvoi déjà ouvert, brouillon déjà revu, appareil non en attente) | Selon le point                              |
| 409  | `public_key_already_registered` | Clé publique déjà connue                                                                     | `POST /v1/auth/otp/verify`                  |
| 410  | `otp_expired`                   | Code expiré (10 minutes)                                                                     | `POST /v1/auth/otp/verify`                  |
| 412  | `precondition_failed`           | `If-Match` ne correspond plus à la sauvegarde en place                                       | `PUT /v1/backup/blob`                       |
| 413  | `payload_too_large`             | Corps au-delà de la limite du point                                                          | Selon le point                              |
| 415  | `unsupported_media_type`        | Type de contenu non accepté                                                                  | Audio, image, blobs                         |
| 422  | `validation_failed`             | Contrat de requête non respecté (détail dans `details`)                                      | Tous                                        |
| 422  | `idempotency_key_mismatch`      | Même clé, corps différent                                                                    | Points idempotents                          |
| 422  | `otp_invalid`                   | Code faux ; essais restants dans `details`                                                   | `POST /v1/auth/otp/verify`                  |
| 422  | `approval_code_invalid`         | Code d'approbation faux                                                                      | `POST /v1/devices/{device_id}/approve`      |
| 422  | `audio_too_long`                | Audio au-delà de la durée permise                                                            | Points audio                                |
| 422  | `content_unprocessable`         | Entrée sans contenu exploitable : aucun mot reconnu, image qui n'est pas un ticket           | Extraction, transcription                   |
| 422  | `content_refused`               | Le fournisseur LLM a refusé de traiter l'entrée (filtre de contenu)                          | Extraction                                  |
| 422  | `sms_too_long`                  | Texte au-delà de 160 caractères GSM 7 bits ou 70 caractères UCS-2                            | `POST /v1/sms`                              |
| 422  | `recipient_not_mobile`          | Destinataire hors des tranches mobiles                                                       | `POST /v1/sms`                              |
| 422  | `greeting_rejected`             | Partie libre de l'accueil refusée (longueur, prétention d'être un humain ou l'artisan)       | `PUT /v1/lines/me`                          |
| 422  | `not_a_public_holiday`          | Date déclarée travaillée qui n'est pas un jour férié de la zone                              | `PUT /v1/lines/me/worked-holidays`          |
| 422  | `recovery_signature_invalid`    | Signature du défi de récupération fausse [H : en attente de décision du porteur]             | `POST /v1/devices/me/recovery-approval`     |
| 423  | `otp_locked`                    | 5 codes faux : nouveau code nécessaire (US-01, critère 3)                                    | `POST /v1/auth/otp/verify`                  |
| 423  | `recovery_locked`               | 5 signatures fausses dans la journée [H : en attente de décision du porteur]                 | `POST /v1/devices/me/recovery-approval`     |
| 429  | `rate_limited`                  | Limite de débit franchie                                                                     | Tous                                        |
| 429  | `quota_exceeded`                | Quota journalier atteint                                                                     | Selon le point                              |
| 500  | `internal_error`                | Erreur non prévue ; le `request_id` permet le diagnostic                                     | Tous                                        |
| 502  | `upstream_error`                | Réponse invalide d'un fournisseur (hors LLM et STT)                                          | SMS, paiement                               |
| 503  | `llm_unavailable`               | Fournisseur LLM indisponible ou en erreur après les essais                                   | Extraction                                  |
| 503  | `stt_unavailable`               | Fournisseur de transcription indisponible                                                    | Extraction audio, transcription             |
| 503  | `sms_provider_unavailable`      | Fournisseur SMS indisponible                                                                 | `POST /v1/sms`, `POST /v1/auth/otp/request` |
| 503  | `capacity_exhausted`            | Budget mensuel des fournisseurs atteint                                                      | Extraction, transcription                   |
| 503  | `service_unavailable`           | Dépendance interne indisponible (base, file)                                                 | Tous                                        |
| 504  | `upstream_timeout`              | Traitement au-delà du délai maximal du point (30 s pour l'extraction [H])                    | Extraction, transcription                   |

L'indisponibilité de l'API des référentiels n'est **pas** une erreur de l'extraction : elle
produit le mode dégradé de US-51 (critère 4), dans une réponse 200 (section 4.2).

### 2.9 En-têtes de confidentialité

- `Cache-Control: no-store` sur toute réponse qui porte une donnée personnelle, un jeton ou un
  brouillon (TA-38), et sur toute réponse d'erreur.
- `Strict-Transport-Security` sur le domaine public.
- **Aucune donnée personnelle dans une URL** (P-05) : identifiants, numéros, communes, codes
  postaux, textes et SIREN passent dans le corps. Seuls des identifiants opaques (UUID), des
  énumérations (`operator`, `trade`, `zone`) et des années apparaissent dans un chemin ou une
  chaîne de requête.
- Corps de requête et de réponse jamais journalisés (document 03, section 5.5).

## 3. Contrat `DossierDraft` 1.1

### 3.1 Ce qui change depuis la version 1.0

Le contrat 1.0 est celui de la passation (section 6). La version 1.1 répond à D-24 et à P-10.

| Changement                                 | Champ                                                                                                               | Raison                                                                                                                          |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Identifiant du brouillon                   | `draft_id`                                                                                                          | Égal à `app.extraction_runs.id` ; l'appareil le cite pour signaler ses corrections (US-17)                                      |
| Date de production                         | `created_at`                                                                                                        | Historique daté du dossier (US-20, critère 2)                                                                                   |
| Versions et mode de production             | `provenance`                                                                                                        | US-40 (critère 2), VE-29 : versions du prompt, du modèle, du lexique ; mode d'entrée ; statut de l'extraction                   |
| Dates de destruction                       | `destruction`                                                                                                       | US-31 : audio, transcription (ou texte saisi) et image                                                                          |
| Résultat du contrôle par champ             | `checks`                                                                                                            | US-51 : `verified`, `mismatch`, `not_checked`, motif, version du référentiel, valeur entendue, type de ligne                    |
| Issue de l'appel                           | `call_outcome`                                                                                                      | US-10 (critère 3) et US-09 : « refus de l'assistant : rappeler » ne se déduit pas d'un brouillon vide                           |
| Base du montant d'une dépense              | `depense.amount_basis`                                                                                              | US-22 (critère 3) : montant dicté sans HT ni TTC, aucun taux de TVA supposé                                                     |
| Appelant distinct de la personne concernée | `contact` (facultatif) et `checks["contact.telephone"]`                                                             | D-25 : appel pour un tiers ; le client est la personne concernée, l'appelant est le contact (règle 12)                          |
| Chemins de `champs_manquants`              | Chemins complets depuis la racine (`client.adresse.rue`)                                                            | L'exemple 1.0 écrivait `adresse.rue` ; la liste fermée du modèle de données (`app.field_corrections`) utilise le chemin complet |
| Règles rendues vérifiables par le schéma   | Confiance nulle si `value` est nulle ; `needs_review` lié au statut ; cohérence `source`, `depense`, `call_outcome` | VE-03, VE-04 : ce que le texte de 1.0 disait devient une contrainte du schéma                                                   |

**Points tranchés par D-24.** Plusieurs documents antérieurs laissaient au conditionnel le
résultat du contrôle par champ, faute de contrat 1.1. D-24 le tranche : le contrat 1.1 porte le
résultat par champ, et la baisse de confiance seule n'est plus l'option retenue.

| Point resté au conditionnel                                                  | Ce que fixe le contrat 1.1                                                                                  |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| P-10 (phase 0, document 02) : « version 1.1, ou baisse de confiance seule »  | Version 1.1 : `draft_id`, `destruction`, `checks` ; la baisse de confiance s'y ajoute (règle 2)             |
| US-51, critère 4 : « non contrôlé » si le contrat passe en 1.1               | Statut `not_checked`, motif `service_unavailable` ou `timeout`, par champ (exemple 3)                       |
| US-31, critère 1 : horodatage « à ajouter à l'enveloppe »                    | `destruction.audio_destroyed_at`, `transcript_destroyed_at`, `image_destroyed_at`, dans le brouillon scellé |
| VE-24 (phase 1, document 04) : statut vérifié « si le contrat passe en 1.1 » | Vérifié : `checks[…].status` vaut `not_checked` en plus de la confiance sous 0,7                            |
| VE-25 (c) : numéro fixe « non mesurable jusqu'au contrat 1.1 »               | Mesurable : `checks["client.telephone"].line_type` et `sms_capable` (exemple 5)                             |
| US-51, critère 2 : valeur entendue consultable [H]                           | `checks["client.adresse.commune"].heard_value`                                                              |

Ce qui ne change pas : la structure `client`, `demande`, `cle_humaine`, `actions`, `depense`,
les valeurs à confiance `{"value", "confidence"}`, les énumérations `source`, `metier`,
`urgence`, `actions[].type`, `telephone.origin`, et la règle « ne jamais inventer ».

**Pourquoi les noms français restent.** Les champs `nom`, `prenom`, `telephone`, `adresse`,
`rue`, `code_postal`, `commune`, `demande`, `objet_court`, `description`, `metier`, `urgence`,
`disponibilites_client`, `rdv_propose`, `accepte_par_client`, `cle_humaine`, `actions`,
`libelle`, `depense`, `fournisseur`, `montant_ht`, `montant_ttc`, `tva`,
`dossier_cle_humaine_mentionnee`, `needs_review` et `champs_manquants` sont gardés tels quels :
le prompt d'extraction, la vérité terrain du jeu synthétique, les métriques par champ
(`app.field_corrections`, liste fermée), les cas VE-01 à VE-30 et la base locale de l'appareil
les citent. Les renommer casserait la comparaison des rapports d'évaluation d'une version à
l'autre (US-37, critère 2) sans rien apporter. Les champs **ajoutés** en 1.1 sont en anglais,
comme le reste de l'API.

### 3.2 Ce que produit le modèle, ce qu'ajoute le serveur

Le brouillon a deux origines, et la frontière est une mesure de sécurité.

| Partie                           | Produite par                          | Champs                                                                                                                                                           |
| -------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Contenu extrait                  | LLM, puis validation et normalisation | `client`, `demande`, `cle_humaine`, `actions`, `depense`, `champs_manquants`, confiances brutes                                                                  |
| Métadonnées, contrôle et preuves | Serveur, après validation             | `schema_version`, `draft_id`, `created_at`, `source`, `call_outcome`, `provenance`, `destruction`, `checks`, `needs_review`, confiances ajustées par le contrôle |

Le schéma de sortie demandé au LLM ne contient **aucun** champ serveur. Une transcription qui
dicte « contrôle vérifié » ou une fausse date de destruction (M-04, VE-22) ne peut donc pas
remplir ces champs : la validation stricte refuse tout champ inconnu dans la sortie du modèle
(M-05), et le serveur écrit ces champs lui-même.

### 3.3 Règles

1. **Confiance.** Nombre entre 0 et 1. Une valeur nulle a une confiance de 0. Un champ est
   « à vérifier » si sa confiance est inférieure à 0,7 ou s'il figure dans `champs_manquants`
   (US-17, critère 1) [H : seuil recalibré par ADR-08].
2. **Effet du contrôle sur la confiance.** Un champ `mismatch` ou `not_checked` a sa confiance
   ramenée à 0,6 au plus [H : ADR-08]. Il est donc toujours « à vérifier », ce qui garde le
   comportement attendu par un lecteur qui ne lirait que la confiance. Aucune valeur n'est
   remplacée en silence (US-51, critère 1).
3. **Nom officiel.** Quand le contrôle reconnaît une commune sous une autre graphie, `value`
   prend le nom officiel du COG et `checks["client.adresse.commune"].heard_value` garde la valeur
   entendue (US-51, critère 2).
4. **Contrôles.** Les trois entrées de `checks` sont toujours présentes. Un champ sans valeur est
   `not_checked` avec le motif `no_value`. Un brouillon de dépense a ses trois contrôles
   `not_checked` avec le motif `not_applicable`. Le téléphone est contrôlé par son préfixe de
   7 chiffres, quelle que soit son origine ; un numéro hors plan français (`+32…`) est
   `not_checked`, motif `not_applicable`.
5. **`champs_manquants`.** Liste les chemins des champs à confiance dont `value` est nulle, et,
   pour une dépense, les champs `depense.*` nuls. Exception : pour une source `expense_voice` ou
   `receipt_scan`, les champs de `client` et de `demande` sont nuls et **ne sont pas** listés.
   `rdv_propose`, `actions` et `cle_humaine` n'y figurent jamais (document 04, section 3.1).
6. **`needs_review`.** Vrai si et seulement si `provenance.extraction_status` n'est pas
   `complete` : brouillon partiel après une relance échouée (`partial_after_retry`), ou brouillon
   de secours construit sans LLM (`fallback_no_llm`, section 4.2).
7. **Destruction.** Une date est nulle si l'élément n'a jamais existé (pas d'audio pour une
   entrée écrite). Si l'élément a existé, la date est renseignée **après** sa destruction dans un
   bloc `finally` (F-02, T7). Pour une entrée écrite, `transcript_destroyed_at` date la
   destruction du texte reçu. La date est une assertion du serveur, adossée aux tests de
   conformité ; elle ne prouve pas l'effacement physique de la mémoire (document 05, section 8).
8. **`call_outcome`.** Renseigné pour `missed_call` seulement : `completed`, `caller_refused`
   (US-10 : le brouillon ne contient que le numéro et l'action `rappeler`), `safety_redirect`
   (US-09), `abandoned`.
9. **Dépense.** `depense` est un objet si `source` vaut `expense_voice` ou `receipt_scan`, nul
   sinon (VE-04). Si `amount_basis` vaut `unstated`, le montant entendu est porté par
   `montant_ttc`, `montant_ht` et `tva` restent nuls, et l'application affiche le montant
   « à vérifier, HT ou TTC non précisé ».
10. **Clé humaine.** Format « Nom, Commune, objet court » ; nulle pour une dépense et pour un
    brouillon de secours.
11. **Aucune donnée médicale** (R7) : aucun champ ne la porte ; le contrôle est un test
    (VE-13), pas une contrainte du schéma.
12. **Appel pour un tiers (D-25).** `client` décrit toujours la personne concernée par
    l'intervention : son nom, l'adresse du lieu d'intervention, son numéro s'il est donné. Quand
    l'appelant n'est pas cette personne (une fille qui appelle pour sa mère), il est décrit dans
    le bloc facultatif `contact` : `nom`, `prenom`, `telephone`, et `relation` (« fille »,
    « voisin », « gestionnaire »), avec les mêmes conventions `value` et `confidence`. Le numéro
    de l'appel (`origin: caller_id`) va alors dans `contact.telephone`, et
    `client.telephone` reste nul, listé dans `champs_manquants`, sauf si un numéro de la personne
    concernée est dicté. La clé humaine porte le nom du **client**, pas du contact. Le bloc est
    absent ou nul quand l'appelant est la personne concernée, ce qui reste le cas courant. Les
    chemins `contact.*` entrent dans `champs_manquants` seulement si le bloc est présent. Le
    téléphone du contact est contrôlé comme celui du client, dans `checks["contact.telephone"]`,
    présent si et seulement si `contact` l'est. Ces brouillons restent hors du KPI tant que leur
    test n'est pas écrit (D-25, document 04, section 3.1). Le rapprochement d'un dossier connu
    (US-20) se fait sur l'appareil, sur le numéro du client comme du contact.

### 3.4 JSON Schema

Dialecte JSON Schema 2020-12, celui dont le schéma d'OpenAPI 3.1 est un sur-ensemble. Les
contraintes croisées (`if`, `then`) expriment les règles 1, 5 (partiellement), 6, 7, 8, 9 et 12.

<!-- contract:schema DossierDraft -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/dossier-draft/1.1",
  "title": "DossierDraft",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "draft_id", "created_at", "source", "call_outcome", "provenance",
    "destruction", "client", "demande", "cle_humaine", "actions", "depense", "checks",
    "needs_review", "champs_manquants"
  ],
  "properties": {
    "schema_version": { "const": "1.1" },
    "draft_id": { "type": "string", "format": "uuid" },
    "created_at": { "type": "string", "format": "date-time" },
    "source": { "enum": ["missed_call", "debrief", "expense_voice", "receipt_scan"] },
    "call_outcome": { "enum": ["completed", "caller_refused", "safety_redirect", "abandoned", null] },
    "provenance": { "$ref": "#/$defs/Provenance" },
    "destruction": { "$ref": "#/$defs/Destruction" },
    "client": { "$ref": "#/$defs/Client" },
    "contact": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/Contact" }] },
    "demande": { "$ref": "#/$defs/Demande" },
    "cle_humaine": { "type": ["string", "null"], "minLength": 5, "maxLength": 160 },
    "actions": { "type": "array", "maxItems": 10, "items": { "$ref": "#/$defs/Action" } },
    "depense": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/Depense" }] },
    "checks": { "$ref": "#/$defs/Checks" },
    "needs_review": { "type": "boolean" },
    "champs_manquants": {
      "type": "array",
      "uniqueItems": true,
      "items": { "$ref": "#/$defs/FieldPath" }
    }
  },
  "allOf": [
    {
      "if": { "required": ["contact"], "properties": { "contact": { "type": "object" } } },
      "then": { "properties": { "checks": { "required": ["contact.telephone"] } } },
      "else": { "properties": { "checks": { "not": { "required": ["contact.telephone"] } } } }
    },
    {
      "if": { "properties": { "provenance": { "properties": { "extraction_status": { "const": "complete" } } } } },
      "then": { "properties": { "needs_review": { "const": false } } },
      "else": { "properties": { "needs_review": { "const": true } } }
    },
    {
      "if": { "properties": { "source": { "const": "missed_call" } } },
      "then": { "properties": { "call_outcome": { "enum": ["completed", "caller_refused", "safety_redirect", "abandoned"] } } },
      "else": { "properties": { "call_outcome": { "const": null } } }
    },
    {
      "if": { "properties": { "source": { "enum": ["expense_voice", "receipt_scan"] } } },
      "then": { "properties": { "depense": { "$ref": "#/$defs/Depense" } } },
      "else": { "properties": { "depense": { "const": null } } }
    },
    {
      "if": { "properties": { "provenance": { "properties": { "input_mode": { "const": "audio" } } } } },
      "then": {
        "properties": {
          "destruction": {
            "properties": {
              "audio_destroyed_at": { "type": "string" },
              "transcript_destroyed_at": { "type": "string" },
              "image_destroyed_at": { "const": null }
            }
          }
        }
      }
    },
    {
      "if": { "properties": { "provenance": { "properties": { "input_mode": { "enum": ["text", "simulated"] } } } } },
      "then": {
        "properties": {
          "destruction": {
            "properties": {
              "audio_destroyed_at": { "const": null },
              "transcript_destroyed_at": { "type": "string" },
              "image_destroyed_at": { "const": null }
            }
          }
        }
      }
    },
    {
      "if": { "properties": { "provenance": { "properties": { "input_mode": { "const": "image" } } } } },
      "then": {
        "properties": {
          "source": { "const": "receipt_scan" },
          "destruction": {
            "properties": {
              "audio_destroyed_at": { "const": null },
              "transcript_destroyed_at": { "const": null },
              "image_destroyed_at": { "type": "string" }
            }
          }
        }
      }
    }
  ],
  "$defs": {
    "Confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "ShortText": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "confidence"],
      "properties": {
        "value": { "type": ["string", "null"], "minLength": 1, "maxLength": 120 },
        "confidence": { "$ref": "#/$defs/Confidence" }
      },
      "if": { "properties": { "value": { "type": "null" } } },
      "then": { "properties": { "confidence": { "const": 0 } } }
    },
    "LongText": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "confidence"],
      "properties": {
        "value": { "type": ["string", "null"], "minLength": 1, "maxLength": 2000 },
        "confidence": { "$ref": "#/$defs/Confidence" }
      },
      "if": { "properties": { "value": { "type": "null" } } },
      "then": { "properties": { "confidence": { "const": 0 } } }
    },
    "Telephone": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "confidence", "origin"],
      "properties": {
        "value": { "type": ["string", "null"], "pattern": "^\\+[1-9][0-9]{7,14}$" },
        "confidence": { "$ref": "#/$defs/Confidence" },
        "origin": { "enum": ["caller_id", "spoken", null] }
      },
      "if": { "properties": { "value": { "type": "null" } } },
      "then": { "properties": { "confidence": { "const": 0 }, "origin": { "const": null } } },
      "else": { "properties": { "origin": { "enum": ["caller_id", "spoken"] } } }
    },
    "CodePostal": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "confidence"],
      "properties": {
        "value": { "type": ["string", "null"], "pattern": "^[0-9]{4,5}$" },
        "confidence": { "$ref": "#/$defs/Confidence" }
      },
      "allOf": [
        {
          "if": { "properties": { "value": { "type": "null" } } },
          "then": { "properties": { "confidence": { "const": 0 } } }
        },
        {
          "if": { "properties": { "value": { "type": "string", "pattern": "^[0-9]{4}$" } } },
          "then": { "properties": { "confidence": { "exclusiveMaximum": 0.7 } } }
        }
      ]
    },
    "Adresse": {
      "type": "object",
      "additionalProperties": false,
      "required": ["rue", "code_postal", "commune"],
      "properties": {
        "rue": { "$ref": "#/$defs/ShortText" },
        "code_postal": { "$ref": "#/$defs/CodePostal" },
        "commune": { "$ref": "#/$defs/ShortText" }
      }
    },
    "Client": {
      "type": "object",
      "additionalProperties": false,
      "required": ["nom", "prenom", "telephone", "adresse"],
      "properties": {
        "nom": { "$ref": "#/$defs/ShortText" },
        "prenom": { "$ref": "#/$defs/ShortText" },
        "telephone": { "$ref": "#/$defs/Telephone" },
        "adresse": { "$ref": "#/$defs/Adresse" }
      }
    },
    "Contact": {
      "type": "object",
      "additionalProperties": false,
      "required": ["nom", "prenom", "telephone", "relation"],
      "properties": {
        "nom": { "$ref": "#/$defs/ShortText" },
        "prenom": { "$ref": "#/$defs/ShortText" },
        "telephone": { "$ref": "#/$defs/Telephone" },
        "relation": { "$ref": "#/$defs/ShortText" }
      }
    },
    "RdvPropose": {
      "type": "object",
      "additionalProperties": false,
      "required": ["start", "end", "accepte_par_client"],
      "properties": {
        "start": { "type": "string", "format": "date-time" },
        "end": { "type": "string", "format": "date-time" },
        "accepte_par_client": { "type": "boolean" }
      }
    },
    "Demande": {
      "type": "object",
      "additionalProperties": false,
      "required": ["objet_court", "description", "metier", "urgence", "disponibilites_client", "rdv_propose"],
      "properties": {
        "objet_court": { "$ref": "#/$defs/ShortText" },
        "description": { "$ref": "#/$defs/LongText" },
        "metier": { "enum": ["plomberie", "chauffage", "electricite", "serrurerie", "autre"] },
        "urgence": { "enum": ["securite", "urgent", "normal", "non_precise"] },
        "disponibilites_client": { "type": "array", "maxItems": 5, "items": { "$ref": "#/$defs/ShortText" } },
        "rdv_propose": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/RdvPropose" }] }
      }
    },
    "Action": {
      "type": "object",
      "additionalProperties": false,
      "required": ["type", "libelle"],
      "properties": {
        "type": { "enum": ["rappeler", "envoyer_devis", "commander", "autre"] },
        "libelle": { "type": "string", "minLength": 1, "maxLength": 140 }
      }
    },
    "Amount": { "type": ["number", "null"], "minimum": 0, "maximum": 1000000 },
    "Depense": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "fournisseur", "date", "montant_ht", "montant_ttc", "tva", "libelle",
        "dossier_cle_humaine_mentionnee", "amount_basis"
      ],
      "properties": {
        "fournisseur": { "$ref": "#/$defs/ShortText" },
        "date": { "type": ["string", "null"], "format": "date" },
        "montant_ht": { "$ref": "#/$defs/Amount" },
        "montant_ttc": { "$ref": "#/$defs/Amount" },
        "tva": { "$ref": "#/$defs/Amount" },
        "libelle": { "type": ["string", "null"], "minLength": 1, "maxLength": 200 },
        "dossier_cle_humaine_mentionnee": { "type": ["string", "null"], "minLength": 1, "maxLength": 160 },
        "amount_basis": { "enum": ["ht", "ttc", "unstated", null] }
      },
      "if": { "properties": { "amount_basis": { "const": "unstated" } } },
      "then": { "properties": { "montant_ht": { "const": null }, "tva": { "const": null } } }
    },
    "Provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["input_mode", "prompt_version", "model_id", "lexicon", "extraction_status", "validation_attempts"],
      "properties": {
        "input_mode": { "enum": ["audio", "text", "image", "simulated"] },
        "prompt_version": { "type": ["string", "null"], "pattern": "^[a-z0-9][a-z0-9._-]{1,63}$" },
        "model_id": { "type": ["string", "null"], "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{1,99}$" },
        "lexicon": {
          "oneOf": [
            { "type": "null" },
            {
              "type": "object",
              "additionalProperties": false,
              "required": ["trade", "version"],
              "properties": {
                "trade": { "enum": ["plomberie", "chauffage", "electricite", "serrurerie", "autre"] },
                "version": { "type": "string", "pattern": "^[0-9]{4}\\.[0-9]{2}\\.[0-9]+$" }
              }
            }
          ]
        },
        "extraction_status": { "enum": ["complete", "partial_after_retry", "fallback_no_llm"] },
        "validation_attempts": { "type": "integer", "minimum": 0, "maximum": 2 }
      },
      "allOf": [
        {
          "if": { "properties": { "extraction_status": { "const": "fallback_no_llm" } } },
          "then": { "properties": { "validation_attempts": { "const": 0 }, "prompt_version": { "const": null }, "model_id": { "const": null } } },
          "else": { "properties": { "validation_attempts": { "minimum": 1 }, "prompt_version": { "type": "string" }, "model_id": { "type": "string" } } }
        },
        {
          "if": { "properties": { "extraction_status": { "const": "partial_after_retry" } } },
          "then": { "properties": { "validation_attempts": { "const": 2 } } }
        }
      ]
    },
    "Destruction": {
      "type": "object",
      "additionalProperties": false,
      "required": ["audio_destroyed_at", "transcript_destroyed_at", "image_destroyed_at"],
      "properties": {
        "audio_destroyed_at": { "type": ["string", "null"], "format": "date-time" },
        "transcript_destroyed_at": { "type": ["string", "null"], "format": "date-time" },
        "image_destroyed_at": { "type": ["string", "null"], "format": "date-time" }
      }
    },
    "ReferentialVersion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["dataset", "source_id", "source_date", "channel"],
      "properties": {
        "dataset": { "enum": ["communes", "postal_codes", "numbering_ranges"] },
        "source_id": { "enum": ["SRC-06", "SRC-07", "SRC-13"] },
        "source_date": { "type": "string", "format": "date" },
        "channel": { "enum": ["production", "test"] }
      }
    },
    "CheckStatus": { "enum": ["verified", "mismatch", "not_checked"] },
    "NotCheckedReason": { "enum": ["no_value", "service_unavailable", "timeout", "not_applicable"] },
    "PhoneCheck": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reason", "referential", "line_type", "sms_capable"],
      "properties": {
        "status": { "$ref": "#/$defs/CheckStatus" },
        "reason": { "enum": [null, "unassigned_range", "malformed", "no_value", "service_unavailable", "timeout", "not_applicable"] },
        "referential": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/ReferentialVersion" }] },
        "line_type": { "enum": ["mobile", "fixed", "non_geographic", "special", "unknown", null] },
        "sms_capable": { "type": ["boolean", "null"] }
      },
      "allOf": [
        {
          "if": { "properties": { "status": { "const": "verified" } } },
          "then": { "properties": { "reason": { "const": null }, "referential": { "type": "object" }, "line_type": { "type": "string" }, "sms_capable": { "type": "boolean" } } }
        },
        {
          "if": { "properties": { "status": { "const": "mismatch" } } },
          "then": { "properties": { "reason": { "enum": ["unassigned_range", "malformed"] }, "referential": { "type": "object" } } }
        },
        {
          "if": { "properties": { "status": { "const": "not_checked" } } },
          "then": { "properties": { "reason": { "$ref": "#/$defs/NotCheckedReason" }, "referential": { "const": null }, "line_type": { "const": null }, "sms_capable": { "const": null } } }
        }
      ]
    },
    "PostalCodeCheck": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reason", "referential"],
      "properties": {
        "status": { "$ref": "#/$defs/CheckStatus" },
        "reason": { "enum": [null, "inconsistent_pair", "unknown_postal_code", "malformed", "no_value", "service_unavailable", "timeout", "not_applicable"] },
        "referential": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/ReferentialVersion" }] }
      },
      "allOf": [
        {
          "if": { "properties": { "status": { "const": "verified" } } },
          "then": { "properties": { "reason": { "const": null }, "referential": { "type": "object" } } }
        },
        {
          "if": { "properties": { "status": { "const": "mismatch" } } },
          "then": { "properties": { "reason": { "enum": ["inconsistent_pair", "unknown_postal_code", "malformed"] }, "referential": { "type": "object" } } }
        },
        {
          "if": { "properties": { "status": { "const": "not_checked" } } },
          "then": { "properties": { "reason": { "$ref": "#/$defs/NotCheckedReason" }, "referential": { "const": null } } }
        }
      ]
    },
    "CommuneCheck": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reason", "referential", "insee_code", "match", "heard_value"],
      "properties": {
        "status": { "$ref": "#/$defs/CheckStatus" },
        "reason": { "enum": [null, "inconsistent_pair", "unknown_commune", "no_value", "service_unavailable", "timeout", "not_applicable"] },
        "referential": { "oneOf": [{ "type": "null" }, { "$ref": "#/$defs/ReferentialVersion" }] },
        "insee_code": { "type": ["string", "null"], "pattern": "^[0-9][0-9AB][0-9]{3}$" },
        "match": { "enum": ["exact", "normalized", "fuzzy", "delegated", null] },
        "heard_value": { "type": ["string", "null"], "minLength": 1, "maxLength": 120 }
      },
      "allOf": [
        {
          "if": { "properties": { "status": { "const": "verified" } } },
          "then": { "properties": { "reason": { "const": null }, "referential": { "type": "object" }, "insee_code": { "type": "string" }, "match": { "type": "string" } } }
        },
        {
          "if": { "properties": { "status": { "const": "mismatch" } } },
          "then": { "properties": { "reason": { "enum": ["inconsistent_pair", "unknown_commune"] }, "referential": { "type": "object" } } }
        },
        {
          "if": { "properties": { "status": { "const": "not_checked" } } },
          "then": { "properties": { "reason": { "$ref": "#/$defs/NotCheckedReason" }, "referential": { "const": null }, "insee_code": { "const": null }, "match": { "const": null }, "heard_value": { "const": null } } }
        }
      ]
    },
    "Checks": {
      "type": "object",
      "additionalProperties": false,
      "required": ["client.telephone", "client.adresse.code_postal", "client.adresse.commune"],
      "properties": {
        "client.telephone": { "$ref": "#/$defs/PhoneCheck" },
        "client.adresse.code_postal": { "$ref": "#/$defs/PostalCodeCheck" },
        "client.adresse.commune": { "$ref": "#/$defs/CommuneCheck" },
        "contact.telephone": { "$ref": "#/$defs/PhoneCheck" }
      }
    },
    "FieldPath": {
      "enum": [
        "client.nom", "client.prenom", "client.telephone", "client.adresse.rue",
        "client.adresse.code_postal", "client.adresse.commune", "demande.objet_court",
        "demande.description", "demande.metier", "demande.urgence",
        "demande.disponibilites_client", "demande.rdv_propose", "cle_humaine", "actions",
        "depense.fournisseur", "depense.date", "depense.montant_ht", "depense.montant_ttc",
        "depense.tva", "depense.libelle", "depense.dossier_cle_humaine_mentionnee",
        "contact.nom", "contact.prenom", "contact.telephone", "contact.relation"
      ]
    }
  }
}
```

Limites connues du schéma : la symétrie complète de la règle 5 (« valeur nulle si et seulement
si le chemin est listé ») et le plafond de 0,6 de la règle 2 portent sur deux branches du
document ; JSON Schema ne les exprime pas simplement. Elles sont vérifiées par le validateur
applicatif et par VE-04 (section 9.2). `FieldPath` reprend la liste fermée de
`app.field_corrections`, complétée des quatre chemins `contact.*` (section 11.1) : les deux
listes doivent rester la même source, testée par égalité.

### 3.5 Exemples

Toutes les données sont synthétiques (R9). Les numéros `+33 6 39 98 …` sont dans la plage
fictive déclarée valide par la seule version de test du référentiel de numérotation (VD-16),
d'où `channel: test` sur ce contrôle. Les versions de prompt, de modèle et de référentiel sont
des exemples.

**Exemple 1. Appel manqué nominal, Montreuil, entrée audio.**

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "3f6c1d2e-8a4b-4c7e-9f10-2b3c4d5e6f70",
  "created_at": "2026-10-12T07:42:18Z",
  "source": "missed_call",
  "call_outcome": "completed",
  "provenance": {
    "input_mode": "audio",
    "prompt_version": "extraction-2026.10.3",
    "model_id": "llm-ue-small-2026-09",
    "lexicon": { "trade": "plomberie", "version": "2026.10.1" },
    "extraction_status": "complete",
    "validation_attempts": 1
  },
  "destruction": {
    "audio_destroyed_at": "2026-10-12T07:42:09Z",
    "transcript_destroyed_at": "2026-10-12T07:42:17Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": "Dupont", "confidence": 0.97 },
    "prenom": { "value": "Marie", "confidence": 0.9 },
    "telephone": { "value": "+33639980047", "confidence": 0.99, "origin": "caller_id" },
    "adresse": {
      "rue": { "value": null, "confidence": 0 },
      "code_postal": { "value": "93100", "confidence": 0.8 },
      "commune": { "value": "Montreuil", "confidence": 0.95 }
    }
  },
  "demande": {
    "objet_court": { "value": "fuite évier", "confidence": 0.92 },
    "description": { "value": "Fuite sous l'évier de la cuisine depuis ce matin, eau coupée.", "confidence": 0.88 },
    "metier": "plomberie",
    "urgence": "urgent",
    "disponibilites_client": [{ "value": "demain matin", "confidence": 0.8 }],
    "rdv_propose": { "start": "2026-10-13T09:00:00+02:00", "end": "2026-10-13T10:00:00+02:00", "accepte_par_client": true }
  },
  "cle_humaine": "Dupont, Montreuil, fuite évier",
  "actions": [{ "type": "rappeler", "libelle": "Rappeler pour confirmer le créneau" }],
  "depense": null,
  "checks": {
    "client.telephone": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "numbering_ranges", "source_id": "SRC-13", "source_date": "2026-10-08", "channel": "test" },
      "line_type": "mobile", "sms_capable": true
    },
    "client.adresse.code_postal": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "postal_codes", "source_id": "SRC-06", "source_date": "2026-09-30", "channel": "production" }
    },
    "client.adresse.commune": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "communes", "source_id": "SRC-07", "source_date": "2026-01-01", "channel": "production" },
      "insee_code": "93048", "match": "exact", "heard_value": null
    }
  },
  "needs_review": false,
  "champs_manquants": ["client.adresse.rue"]
}
```

**Exemple 2. Scénario de démo « 93100 Bagnolet », transcription simulée, numéro dicté.** Le
couple est incohérent : les deux champs sont `mismatch`, leur confiance est ramenée à 0,6 et
leurs valeurs sont gardées (US-51, critère 1).

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d",
  "created_at": "2026-10-29T09:15:04Z",
  "source": "missed_call",
  "call_outcome": "completed",
  "provenance": {
    "input_mode": "simulated",
    "prompt_version": "extraction-2026.10.3",
    "model_id": "llm-ue-small-2026-09",
    "lexicon": { "trade": "plomberie", "version": "2026.10.1" },
    "extraction_status": "complete",
    "validation_attempts": 2
  },
  "destruction": {
    "audio_destroyed_at": null,
    "transcript_destroyed_at": "2026-10-29T09:15:03Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": "Martin", "confidence": 0.94 },
    "prenom": { "value": null, "confidence": 0 },
    "telephone": { "value": "+33639980012", "confidence": 0.93, "origin": "spoken" },
    "adresse": {
      "rue": { "value": "4 rue Sadi Carnot", "confidence": 0.78 },
      "code_postal": { "value": "93100", "confidence": 0.6 },
      "commune": { "value": "Bagnolet", "confidence": 0.6 }
    }
  },
  "demande": {
    "objet_court": { "value": "chauffe-eau en panne", "confidence": 0.9 },
    "description": { "value": "Plus d'eau chaude depuis hier soir.", "confidence": 0.86 },
    "metier": "plomberie",
    "urgence": "normal",
    "disponibilites_client": [],
    "rdv_propose": null
  },
  "cle_humaine": "Martin, Bagnolet, chauffe-eau en panne",
  "actions": [{ "type": "rappeler", "libelle": "Rappeler pour fixer un rendez-vous" }],
  "depense": null,
  "checks": {
    "client.telephone": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "numbering_ranges", "source_id": "SRC-13", "source_date": "2026-10-08", "channel": "test" },
      "line_type": "mobile", "sms_capable": true
    },
    "client.adresse.code_postal": {
      "status": "mismatch", "reason": "inconsistent_pair",
      "referential": { "dataset": "postal_codes", "source_id": "SRC-06", "source_date": "2026-09-30", "channel": "production" }
    },
    "client.adresse.commune": {
      "status": "mismatch", "reason": "inconsistent_pair",
      "referential": { "dataset": "communes", "source_id": "SRC-07", "source_date": "2026-01-01", "channel": "production" },
      "insee_code": "93006", "match": "exact", "heard_value": null
    }
  },
  "needs_review": false,
  "champs_manquants": ["client.prenom"]
}
```

**Exemple 3. Débrief écrit, API des référentiels indisponible (mode dégradé).** Les champs à
contrôler sont `not_checked`, motif `service_unavailable`, et leur confiance est ramenée à 0,6.

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "5e4d3c2b-1a09-4f8e-b7d6-c5b4a3928170",
  "created_at": "2026-10-14T16:20:41Z",
  "source": "debrief",
  "call_outcome": null,
  "provenance": {
    "input_mode": "text",
    "prompt_version": "extraction-2026.10.3",
    "model_id": "llm-ue-small-2026-09",
    "lexicon": { "trade": "electricite", "version": "2026.10.1" },
    "extraction_status": "complete",
    "validation_attempts": 1
  },
  "destruction": {
    "audio_destroyed_at": null,
    "transcript_destroyed_at": "2026-10-14T16:20:40Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": "Lefèvre", "confidence": 0.95 },
    "prenom": { "value": null, "confidence": 0 },
    "telephone": { "value": "+33639980031", "confidence": 0.6, "origin": "spoken" },
    "adresse": {
      "rue": { "value": null, "confidence": 0 },
      "code_postal": { "value": "69003", "confidence": 0.6 },
      "commune": { "value": "Lyon", "confidence": 0.6 }
    }
  },
  "demande": {
    "objet_court": { "value": "tableau électrique", "confidence": 0.9 },
    "description": { "value": "Remplacer le disjoncteur différentiel, devis à envoyer cette semaine.", "confidence": 0.87 },
    "metier": "electricite",
    "urgence": "normal",
    "disponibilites_client": [],
    "rdv_propose": null
  },
  "cle_humaine": "Lefèvre, Lyon, tableau électrique",
  "actions": [{ "type": "envoyer_devis", "libelle": "Envoyer le devis du disjoncteur différentiel" }],
  "depense": null,
  "checks": {
    "client.telephone": { "status": "not_checked", "reason": "service_unavailable", "referential": null, "line_type": null, "sms_capable": null },
    "client.adresse.code_postal": { "status": "not_checked", "reason": "service_unavailable", "referential": null },
    "client.adresse.commune": { "status": "not_checked", "reason": "service_unavailable", "referential": null, "insee_code": null, "match": null, "heard_value": null }
  },
  "needs_review": false,
  "champs_manquants": ["client.prenom", "client.adresse.rue"]
}
```

**Exemple 4. Dépense dictée sans précision HT ou TTC.** « 84 euros 20 chez Cedeo pour le Dupont
de Montreuil » (US-22).

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "c0ffee00-1234-4abc-8def-0123456789ab",
  "created_at": "2026-10-12T12:05:33Z",
  "source": "expense_voice",
  "call_outcome": null,
  "provenance": {
    "input_mode": "audio",
    "prompt_version": "extraction-2026.10.3",
    "model_id": "llm-ue-small-2026-09",
    "lexicon": { "trade": "plomberie", "version": "2026.10.1" },
    "extraction_status": "complete",
    "validation_attempts": 1
  },
  "destruction": {
    "audio_destroyed_at": "2026-10-12T12:05:30Z",
    "transcript_destroyed_at": "2026-10-12T12:05:33Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": null, "confidence": 0 },
    "prenom": { "value": null, "confidence": 0 },
    "telephone": { "value": null, "confidence": 0, "origin": null },
    "adresse": {
      "rue": { "value": null, "confidence": 0 },
      "code_postal": { "value": null, "confidence": 0 },
      "commune": { "value": null, "confidence": 0 }
    }
  },
  "demande": {
    "objet_court": { "value": null, "confidence": 0 },
    "description": { "value": null, "confidence": 0 },
    "metier": "plomberie",
    "urgence": "non_precise",
    "disponibilites_client": [],
    "rdv_propose": null
  },
  "cle_humaine": null,
  "actions": [],
  "depense": {
    "fournisseur": { "value": "Cedeo", "confidence": 0.95 },
    "date": "2026-10-12",
    "montant_ht": null,
    "montant_ttc": 84.2,
    "tva": null,
    "libelle": null,
    "dossier_cle_humaine_mentionnee": "Dupont, Montreuil",
    "amount_basis": "unstated"
  },
  "checks": {
    "client.telephone": { "status": "not_checked", "reason": "not_applicable", "referential": null, "line_type": null, "sms_capable": null },
    "client.adresse.code_postal": { "status": "not_checked", "reason": "not_applicable", "referential": null },
    "client.adresse.commune": { "status": "not_checked", "reason": "not_applicable", "referential": null, "insee_code": null, "match": null, "heard_value": null }
  },
  "needs_review": false,
  "champs_manquants": ["depense.montant_ht", "depense.tva", "depense.libelle"]
}
```

**Exemple 5. Brouillon de secours : LLM indisponible en fin d'appel.** Le serveur ne peut pas
garder la transcription pour réessayer plus tard (R3). Il construit sans LLM un brouillon qui
ne contient que ce qu'il sait déjà : le numéro appelant et l'action « rappeler ». Le contrôle du
préfixe signale une ligne fixe, incapable de recevoir un SMS (US-51, critère 3).

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "7b8c9d0e-1f2a-4b3c-9d4e-5f6a7b8c9d0e",
  "created_at": "2026-10-12T18:03:12Z",
  "source": "missed_call",
  "call_outcome": "completed",
  "provenance": {
    "input_mode": "audio",
    "prompt_version": null,
    "model_id": null,
    "lexicon": null,
    "extraction_status": "fallback_no_llm",
    "validation_attempts": 0
  },
  "destruction": {
    "audio_destroyed_at": "2026-10-12T18:02:58Z",
    "transcript_destroyed_at": "2026-10-12T18:03:11Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": null, "confidence": 0 },
    "prenom": { "value": null, "confidence": 0 },
    "telephone": { "value": "+33199001234", "confidence": 1, "origin": "caller_id" },
    "adresse": {
      "rue": { "value": null, "confidence": 0 },
      "code_postal": { "value": null, "confidence": 0 },
      "commune": { "value": null, "confidence": 0 }
    }
  },
  "demande": {
    "objet_court": { "value": null, "confidence": 0 },
    "description": { "value": null, "confidence": 0 },
    "metier": "chauffage",
    "urgence": "non_precise",
    "disponibilites_client": [],
    "rdv_propose": null
  },
  "cle_humaine": null,
  "actions": [{ "type": "rappeler", "libelle": "Demande non extraite : rappeler le client" }],
  "depense": null,
  "checks": {
    "client.telephone": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "numbering_ranges", "source_id": "SRC-13", "source_date": "2026-10-08", "channel": "test" },
      "line_type": "fixed", "sms_capable": false
    },
    "client.adresse.code_postal": { "status": "not_checked", "reason": "no_value", "referential": null },
    "client.adresse.commune": { "status": "not_checked", "reason": "no_value", "referential": null, "insee_code": null, "match": null, "heard_value": null }
  },
  "needs_review": true,
  "champs_manquants": [
    "client.nom", "client.prenom", "client.adresse.rue", "client.adresse.code_postal",
    "client.adresse.commune", "demande.objet_court", "demande.description"
  ]
}
```

**Exemple 6. Appel pour un tiers (D-25).** Une fille appelle pour sa mère, qui habite Vincennes.
Le client est la mère ; la fille est le contact, et le numéro de l'appel est le sien.

<!-- contract:example DossierDraft -->
```json
{
  "schema_version": "1.1",
  "draft_id": "e1d2c3b4-a596-4877-8a6b-5c4d3e2f1a0b",
  "created_at": "2026-10-12T10:11:45Z",
  "source": "missed_call",
  "call_outcome": "completed",
  "provenance": {
    "input_mode": "audio",
    "prompt_version": "extraction-2026.10.3",
    "model_id": "llm-ue-small-2026-09",
    "lexicon": { "trade": "serrurerie", "version": "2026.10.1" },
    "extraction_status": "complete",
    "validation_attempts": 1
  },
  "destruction": {
    "audio_destroyed_at": "2026-10-12T10:11:31Z",
    "transcript_destroyed_at": "2026-10-12T10:11:44Z",
    "image_destroyed_at": null
  },
  "client": {
    "nom": { "value": "Ollivro", "confidence": 0.88 },
    "prenom": { "value": "Jeanne", "confidence": 0.82 },
    "telephone": { "value": null, "confidence": 0, "origin": null },
    "adresse": {
      "rue": { "value": "9 avenue de Paris", "confidence": 0.81 },
      "code_postal": { "value": "94300", "confidence": 0.9 },
      "commune": { "value": "Vincennes", "confidence": 0.96 }
    }
  },
  "contact": {
    "nom": { "value": "Ollivro", "confidence": 0.85 },
    "prenom": { "value": "Claire", "confidence": 0.84 },
    "telephone": { "value": "+33639980058", "confidence": 0.99, "origin": "caller_id" },
    "relation": { "value": "fille", "confidence": 0.93 }
  },
  "demande": {
    "objet_court": { "value": "serrure bloquée", "confidence": 0.91 },
    "description": { "value": "La serrure de la porte d'entrée de sa mère ne tourne plus.", "confidence": 0.86 },
    "metier": "serrurerie",
    "urgence": "urgent",
    "disponibilites_client": [],
    "rdv_propose": null
  },
  "cle_humaine": "Ollivro, Vincennes, serrure bloquée",
  "actions": [{ "type": "rappeler", "libelle": "Rappeler la fille de la cliente pour fixer l'intervention" }],
  "depense": null,
  "checks": {
    "client.telephone": { "status": "not_checked", "reason": "no_value", "referential": null, "line_type": null, "sms_capable": null },
    "client.adresse.code_postal": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "postal_codes", "source_id": "SRC-06", "source_date": "2026-09-30", "channel": "production" }
    },
    "client.adresse.commune": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "communes", "source_id": "SRC-07", "source_date": "2026-01-01", "channel": "production" },
      "insee_code": "94080", "match": "exact", "heard_value": null
    },
    "contact.telephone": {
      "status": "verified", "reason": null,
      "referential": { "dataset": "numbering_ranges", "source_id": "SRC-13", "source_date": "2026-10-08", "channel": "test" },
      "line_type": "mobile", "sms_capable": true
    }
  },
  "needs_review": false,
  "champs_manquants": ["client.telephone"]
}
```

### 3.6 Règle de compatibilité

- **Numérotation `MAJEUR.MINEUR`**, propre au contrat et indépendante de `/v1`.
- **Version mineure** : ajout de champs ou d'objets, contraintes resserrées sur des valeurs que
  le serveur ne produisait pas. Un lecteur d'une version mineure antérieure lit le brouillon en
  ignorant les champs inconnus. Le serveur valide sa sortie **strictement** contre le schéma de
  la version qu'il déclare (`additionalProperties: false`, VE-01).
- **Version majeure** : suppression, renommage, changement de type, ajout d'une valeur à une
  énumération. Le serveur émet alors les deux versions pendant une période de transition [H :
  90 jours], et l'application déclare à l'enregistrement de l'appareil les versions qu'elle lit.
- **Application de la règle à 1.1.** La version 1.1 est additive pour la structure. Elle
  contient deux resserrements : les chemins complets de `champs_manquants` et le lien strict
  entre `needs_review` et `extraction_status`. Aucun lecteur 1.0 n'est en production : la 1.0 n'a
  existé que dans la passation et le harnais d'évaluation. Le passage est donc sans transition :
  **le serveur n'émet que la 1.1**. L'application sait lire 1.0 et 1.1 (document 02 de la phase 1,
  section 8.4), pour les jeux d'évaluation et les sauvegardes anciennes.
- **Versions dans le brouillon** : `schema_version` (contrat), `provenance.prompt_version`,
  `provenance.model_id`, `provenance.lexicon.version`, et la version de chaque référentiel dans
  `checks`. Le rapport d'évaluation ajoute la version du jeu de scénarios (VE-29).

## 4. API d'extraction (C9)

### 4.1 Vue d'ensemble

L'extraction a deux faces (document 03 de la phase 1, section 6.2) : des points publics de
l'api, appelés par l'appareil et par la console de démo, et des points internes du composant
extraction, sans état et sans accès à la base. L'api et voice-gateway écrivent
`app.extraction_runs` avant l'appel, et transmettent son identifiant comme `draft_id`.

| Point d'accès               | Service    | Consommateur                         | Entrée                                           | Sortie                                                       | Latence p95 visée [H] |
| --------------------------- | ---------- | ------------------------------------ | ------------------------------------------------ | ------------------------------------------------------------ | --------------------- |
| `POST /v1/extractions/text` | api        | Appareil (accessibilité)             | Texte, source, métier, lexique personnel         | `DossierDraft` (`debrief`, `expense_voice`)                  | 10 s                  |
| `POST /v1/debrief`          | api        | Appareil                             | Audio de 60 s au plus, métier, lexique personnel | `DossierDraft` (`debrief`)                                   | 15 s                  |
| `POST /v1/expenses/voice`   | api        | Appareil                             | Audio de 60 s au plus                            | `DossierDraft` (`expense_voice`)                             | 12 s                  |
| `POST /v1/receipts/scan`    | api        | Appareil                             | Image de 10 Mo au plus                           | `DossierDraft` (`receipt_scan`)                              | 15 s                  |
| `POST /v1/transcriptions`   | api        | Appareil (recherche et imprévu dits) | Audio de 15 s au plus                            | Texte                                                        | 3 s                   |
| `POST /v1/demo/runs`        | api        | Console de démo                      | Scénario synthétique ou transcription simulée    | `DossierDraft` en clair, vérité terrain, écarts (écart P-03) | 15 s                  |
| `POST /v1/extract/text`     | extraction | api, voice-gateway, harnais          | Transcription ou texte, contexte                 | `DossierDraft`, mesures d'exécution                          | 20 s (fin d'appel)    |
| `POST /v1/extract/audio`    | extraction | api, harnais                         | Audio, contexte                                  | `DossierDraft`, mesures d'exécution                          | 15 s                  |
| `POST /v1/extract/image`    | extraction | api, harnais                         | Image, contexte                                  | `DossierDraft`, mesures d'exécution                          | 15 s                  |
| `POST /v1/transcribe`       | extraction | api                                  | Audio court                                      | Texte                                                        | 3 s                   |

Les latences visées sont des hypothèses, à mesurer en phase 4 (US-37, critère 1). La cible de
20 s pour la fin d'appel laisse 10 s au relais et à la notification dans l'objectif de 30 s de
US-12. Délai maximal côté serveur : 30 s, puis 504 `upstream_timeout`.

**Ce qui n'est jamais stocké, quel que soit le point** (R1, R2, R3, D-11, D-12) : l'audio,
l'image, la transcription, le texte saisi, le lexique personnel, la sortie brute du modèle, le
brouillon, le numéro appelant en clair. Seules les métadonnées de `app.extraction_runs` restent
(statut, versions, latence, jetons, coût, horodatages de destruction). Rien de cela ne passe par
la file Redis : l'appel est synchrone, en mémoire (D-11).

### 4.2 Erreurs et modes dégradés de l'extraction

| Situation                                          | Réponse                                                                                                                                                     | Ce que fait le client                                                                    |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Sortie du modèle invalide, valide à la relance     | 200, `extraction_status: complete`, `validation_attempts: 2`                                                                                                | Affiche le brouillon                                                                     |
| Validation échouée après la relance                | 200, brouillon partiel, `extraction_status: partial_after_retry`, `needs_review: true` (passation, section 6)                                               | Affiche le brouillon partiel, champs manquants « à vérifier »                            |
| API des référentiels indisponible ou trop lente    | 200, contrôles `not_checked` (`service_unavailable` ou `timeout` au-delà de 200 ms [H]), confiances ramenées sous 0,7 ; événement compté (US-51, critère 4) | Affiche « non contrôlé »                                                                 |
| Contenu refusé par le fournisseur LLM              | 422 `content_refused` ; rien n'est stocké                                                                                                                   | Appareil : propose la saisie manuelle                                                    |
| Entrée sans contenu exploitable                    | 422 `content_unprocessable` (silence, aucun mot reconnu, image qui n'est pas un ticket)                                                                     | Appareil : propose de recommencer                                                        |
| Fournisseur LLM indisponible (point de l'appareil) | 503 `llm_unavailable`, `Retry-After`                                                                                                                        | Garde la soumission chiffrée sur le téléphone et la renvoie plus tard (US-13, critère 4) |
| Fournisseur LLM indisponible (fin d'appel)         | Le composant appelant (voice-gateway) construit le brouillon de secours `fallback_no_llm` (exemple 5) et le confie au relay                                 | L'artisan reçoit « rappeler » ; aucune demande n'est perdue en silence                   |
| Fournisseur de transcription indisponible          | 503 `stt_unavailable` ; en fin d'appel, sans objet (transcription en flux déjà faite)                                                                       | Comme pour le LLM                                                                        |
| Budget épuisé                                      | 503 `capacity_exhausted`                                                                                                                                    | Comme pour le LLM                                                                        |
| Information médicale dictée                        | 200 ; aucun champ ne la contient (R7, VE-13)                                                                                                                | Aucun                                                                                    |

Le brouillon de secours est la seule réponse au cas « LLM indisponible en fin d'appel » qui
respecte R3 : la transcription ne peut être ni gardée ni mise en file pour un nouvel essai.

### 4.3 `POST /v1/extractions/text` : extraction à partir d'un texte

Point d'extraction à partir de texte demandé par P-09, pour l'équivalent écrit du débrief et
de la dépense dictée (US-13, critère 3 ; US-22, critère 2 ; document 04 de la phase 0, EXA-16).

- **Rôle** : appareil. **Authentification** : `device_token`. **Lot** : 4. **Démo** : non (la
  démo passe par `POST /v1/demo/runs`).
- **Idempotence** : aucune (section 2.5). **Quota** : 60 par appareil et par heure, partagé avec
  `/v1/debrief` et `/v1/expenses/voice` [H].

<!-- contract:schema ExtractionTextRequest -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/extraction-text-request/1",
  "title": "ExtractionTextRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["source", "text", "trade"],
  "properties": {
    "source": { "enum": ["debrief", "expense_voice"] },
    "text": { "type": "string", "minLength": 1, "maxLength": 8000 },
    "trade": { "enum": ["plomberie", "chauffage", "electricite", "serrurerie", "autre"] },
    "personal_lexicon": {
      "type": "array",
      "maxItems": 500,
      "items": { "type": "string", "minLength": 1, "maxLength": 80 }
    }
  }
}
```

<!-- contract:example ExtractionTextRequest -->
```json
{
  "source": "debrief",
  "text": "Passé chez Lefèvre à Lyon 3e, 69003. Disjoncteur différentiel à remplacer, devis à envoyer cette semaine. Son portable : 06 39 98 00 31.",
  "trade": "electricite",
  "personal_lexicon": ["Lefèvre"]
}
```

- **Réponse 200** : `DossierDraft` 1.1 (exemple 3), `Cache-Control: no-store`.
- **Erreurs** : 400, 401, 403, 413, 422 (`validation_failed`, `content_refused`,
  `content_unprocessable`), 429, 503 (`llm_unavailable`, `capacity_exhausted`), 504.
- **Jamais stocké** : le texte, le lexique personnel, le brouillon.

### 4.4 `POST /v1/debrief` : débrief dicté

- **Rôle** : appareil. **Authentification** : `device_token`. **Lot** : 4. **Démo** : non.
- **Corps** : `multipart/form-data` avec trois parties : `audio` (`audio/ogg` Opus, `audio/mp4`
  AAC ou `audio/wav`, 60 s et 5 Mo au plus [H]), `trade` (paramètre `métier` de P-09) et
  `personal_lexicon` (JSON, même forme que ci-dessus, facultatif).
- **Réponse 200** : `DossierDraft` de source `debrief`, `input_mode: audio`.
- **Erreurs** : celles de 4.3, plus 413, 415, 422 `audio_too_long`, 503 `stt_unavailable`.
- **Idempotence** : aucune. **Quota** : partagé, 60 par appareil et par heure.
- **Jamais stocké** : l'audio (libéré dans un bloc `finally` après la transcription), la
  transcription, le lexique personnel (D-12 : il n'est utilisé que pendant cette requête).

### 4.5 `POST /v1/expenses/voice` : dépense dictée

- **Rôle** : appareil. **Authentification** : `device_token`. **Lot** : 4. **Démo** : non.
- **Corps** : `multipart/form-data` : `audio` (mêmes formats et limites que 4.4) et `trade`.
  La forme écrite passe par `POST /v1/extractions/text` avec `source: expense_voice`.
- **Réponse 200** : `DossierDraft` de source `expense_voice` (exemple 4). Un montant sans
  précision HT ou TTC donne `amount_basis: unstated` (règle 9).
- **Erreurs, idempotence, quota, jamais stocké** : comme 4.4.

### 4.6 `POST /v1/receipts/scan` : ticket photographié

- **Rôle** : appareil. **Authentification** : `device_token`. **Lot** : 4. **Démo** : non.
- **Corps** : `multipart/form-data` : `image` (`image/jpeg`, `image/png` ou `image/heic` [H],
  10 Mo au plus) et `trade`.
- **Réponse 200** : `DossierDraft` de source `receipt_scan`, `input_mode: image`,
  `image_destroyed_at` renseigné. Un montant illisible vaut `null` et figure dans
  `champs_manquants` (US-21, critère 2).
- **Erreurs** : 400, 401, 403, 413, 415, 422 (`content_unprocessable` si l'image n'est pas un
  ticket, `content_refused`), 429, 503, 504.
- **Idempotence** : aucune. **Quota** : 60 par appareil et par heure.
- **Jamais stocké** : l'image transmise pour le traitement (US-21, critère 3). Seule la copie
  chiffrée par l'appareil peut être archivée, par `POST /v1/archive/blobs`.

### 4.7 `POST /v1/transcriptions` : phrase dite

Transcription d'une recherche dite (US-18, critère 3), d'une réponse à la question de
désambiguïsation (US-19) et d'un imprévu dit (US-28, P-17). P-09 la relevait comme absente.

- **Rôle** : appareil. **Authentification** : `device_token`. **Lot** : 4. **Démo** : non.
- **Corps** : `multipart/form-data` : `audio` (15 s et 1 Mo au plus [H]).
- **Réponse 200** : `{"text": "le Dupont de Montreuil"}`. L'interprétation et la recherche se
  font sur l'appareil.
- **Erreurs** : 400, 401, 403, 413, 415, 422 (`audio_too_long`, `content_unprocessable`), 429,
  503 `stt_unavailable`, 504.
- **Idempotence** : aucune. **Quota** : 120 par appareil et par heure [H].
- **Jamais stocké** : l'audio et le texte (F-04, T2). L'api appelle `POST /v1/transcribe` du
  composant extraction, seul détenteur de la clé du fournisseur de transcription (document 03,
  section 5.6). Le flux F-04, qui fait appeler le STT par l'api, est à corriger en ce sens
  (section 11.2, CA-04).

### 4.8 Points internes du composant extraction

Authentification : `service_token`, portées de la section 2.4. Réseau interne seulement.

| Point                    | Corps                                                                                                                                                                                                                                    | Réponse 200                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `POST /v1/extract/text`  | JSON : `draft_id`, `source`, `input_mode` (`text` ou `simulated`), `text`, `trade`, `lexicon_version` (facultatif), `caller_number` (E.164, facultatif), `personal_lexicon`, `context` (`booking_enabled`, `timezone`, `reference_date`) | `{"draft": DossierDraft, "run": RunMetrics}` |
| `POST /v1/extract/audio` | `multipart/form-data` : partie `meta` (mêmes champs sauf `text`) et partie `audio`                                                                                                                                                       | Idem                                         |
| `POST /v1/extract/image` | `multipart/form-data` : partie `meta` et partie `image`                                                                                                                                                                                  | Idem                                         |
| `POST /v1/transcribe`    | `multipart/form-data` : `audio`                                                                                                                                                                                                          | `{"text": "…"}`                              |

`RunMetrics` : `status` (valeurs de `app.extraction_runs.status`), `validation_attempts`,
`latency_ms`, `input_tokens`, `output_tokens`, `cost_micro_eur`, `reference_check` (`ok`,
`flagged`, `unchecked`, `not_applicable`), `fields_to_review_count`. Le composant appelant écrit
ces mesures dans `app.extraction_runs` ; l'extraction n'a aucun accès à la base (TA-01).

`caller_number` est le numéro appelant d'une fin d'appel, utilisé pour `origin: caller_id`. Il
est oublié à la fin de la requête. `reference_date` donne la date du jour à l'artisan, pour
résoudre « demain matin » ou « aujourd'hui » sans supposer le fuseau.

Le harnais d'évaluation (US-37) appelle ces points avec le jeton du harnais, et pose
`is_synthetic` du côté de l'appelant. Erreurs : celles de la section 4.2, plus 403
`scope_denied`.

### 4.9 `POST /v1/demo/runs` : démo du 29 octobre

Point de la console de démo (US-36, F-12). Il n'existe que si la configuration de démo est
active ; sinon il rend 404 `feature_disabled` (TA-24).

- **Rôle** : console (exploitant dans le rôle de l'artisan). **Authentification** :
  `service_token` de portée `demo`, appelé par le serveur de la console après la connexion de
  l'exploitant (compte nominatif, second facteur). **Lot** : 1. **Démo** : **oui**.
- **Écart P-03 assumé (D-07)** : la réponse contient le brouillon **en clair**, sans enveloppe
  chiffrée, sur données synthétiques. Rien n'est stocké. Le relais chiffré (US-12) est prévu
  pour le 12 novembre. L'écart est dit au jury.
- **Corps** : soit `{"mode": "scenario", "scenario_id": "…"}` (scénario du jeu synthétique,
  avec vérité terrain), soit `{"mode": "transcript", "transcript": "…", "trade": "…",
  "caller_number": "+33639980…"}` (transcription simulée saisie, sans vérité terrain). Le
  numéro doit être dans la plage fictive, sinon 422 `validation_failed` (R9).
- **Traitement** : l'api appelle le simulateur, qui envoie au point
  `POST /v1/webhooks/telephony/fake/call-ended` un webhook factice signé ; la suite suit le même
  code que la production, puis `POST /v1/extract/text` avec `input_mode: simulated`.
- **Idempotence** : aucune. **Quota** : 30 par minute [H].

<!-- contract:schema DemoRunResponse -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/demo-run-response/1",
  "title": "DemoRunResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["draft", "ground_truth", "field_diffs", "latency_ms", "request_id", "plaintext_draft_notice"],
  "properties": {
    "draft": { "$ref": "https://muninn.example/schemas/dossier-draft/1.1" },
    "ground_truth": { "type": ["object", "null"] },
    "field_diffs": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["field", "outcome"],
        "properties": {
          "field": { "$ref": "https://muninn.example/schemas/dossier-draft/1.1#/$defs/FieldPath" },
          "outcome": { "enum": ["exact", "wrong", "missing", "invented", "not_counted"] }
        }
      }
    },
    "latency_ms": { "type": "integer", "minimum": 0 },
    "request_id": { "type": "string", "format": "uuid" },
    "plaintext_draft_notice": { "const": "P-03" }
  }
}
```

Le champ `plaintext_draft_notice` marque la réponse comme relevant de l'écart P-03 ; un test
vérifie qu'aucune réponse hors démo ne le porte. `ground_truth` suit le schéma de la vérité
terrain du jeu synthétique (document 04, section 4.1) ; il est nul en mode `transcript`.

**`POST /v1/demo/runs/{draft_id}/review`** : décision et noms des champs corrigés, même corps
que `POST /v1/drafts/{draft_id}/review` (section 6.9), même authentification que ci-dessus.
Réponse 204. **Lot** : 1. **Démo** : oui.

**`GET /v1/demo/scenarios`** : liste des scénarios de démonstration (`scenario_id`, titre,
catégorie). Aucune donnée personnelle réelle. **Lot** : 1. **Démo** : oui.

## 5. API des référentiels (C5)

### 5.1 Consommateurs, authentification et quotas

- **Service** : interne, jamais exposé sur Internet ni à l'application (US-50, critère 2).
- **Authentification** : `service_token` ; sans jeton 401, hors portée 403 (TA-22).
- **Quotas** : 100 requêtes par seconde et par jeton ; corps de 1 Ko au plus (document 03,
  section 5.4). Latence p95 inférieure à 50 ms (US-50, critère 4) [H].
- **Lecture seule** : aucune écriture ; seules les versions publiées sont servies.
- **Aucune valeur contrôlée dans l'URL** (P-05) : les contrôles sont des `POST`. Les valeurs
  reçues ne sont ni journalisées, ni stockées, ni renvoyées au-delà du résultat (TA-23).
- **Version citée** : chaque réponse cite la version du référentiel utilisé (source et date).

| Point d'accès                         | Consommateurs (portée)                               | Lot | Démo |
| ------------------------------------- | ---------------------------------------------------- | --- | ---- |
| `POST /v1/checks/postal-commune`      | extraction (`checks`)                                | 1   | oui  |
| `POST /v1/checks/phone-prefix`        | extraction (`checks`)                                | 1   | oui  |
| `POST /v1/postal-codes/communes`      | extraction, serveur MCP (`postal_codes`)             | 1   | non  |
| `GET /v1/versions`                    | tous (`versions`)                                    | 1   | oui  |
| `GET /v1/lexicons/{trade}`            | extraction, voice-gateway, console, MCP (`lexicons`) | 1   | non  |
| `GET /v1/holidays/{zone}/{year}`      | voice-gateway, api (`holidays`)                      | 2   | non  |
| `GET /v1/forwarding-codes/{operator}` | api (`forwarding_codes`)                             | 2   | non  |
| `GET /v1/naf-trades/{naf_code}`       | api (`naf_trades`)                                   | 3   | non  |
| `GET /health`, `GET /ready`           | supervision (`none`, réseau interne)                 | 0   | oui  |

Le lexique sert la démo de façon indirecte : l'extraction le lit, mais la démo ne montre pas le
point. Il est donc marqué « non ».

### 5.2 `POST /v1/checks/postal-commune`

Contrôle d'un couple code postal et commune extrait (US-51, critères 1 et 2).

<!-- contract:schema PostalCommuneCheckRequest -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/postal-commune-check-request/1",
  "title": "PostalCommuneCheckRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["postal_code", "commune"],
  "properties": {
    "postal_code": { "type": ["string", "null"], "pattern": "^[0-9]{4,5}$" },
    "commune": { "type": ["string", "null"], "minLength": 1, "maxLength": 120 }
  },
  "anyOf": [
    { "properties": { "postal_code": { "type": "string" } } },
    { "properties": { "commune": { "type": "string" } } }
  ]
}
```

<!-- contract:example PostalCommuneCheckRequest -->
```json
{ "postal_code": "93100", "commune": "Bagnolet" }
```

<!-- contract:schema PostalCommuneCheckResponse -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/postal-commune-check-response/1",
  "title": "PostalCommuneCheckResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["postal_code_status", "commune_status", "pair_status", "commune", "versions"],
  "properties": {
    "postal_code_status": { "enum": ["known", "unknown", "malformed", "absent"] },
    "commune_status": { "enum": ["known", "unknown", "absent"] },
    "pair_status": { "enum": ["consistent", "inconsistent", "not_evaluated"] },
    "commune": {
      "oneOf": [
        { "type": "null" },
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["official_name", "insee_code", "match", "similarity"],
          "properties": {
            "official_name": { "type": "string" },
            "insee_code": { "type": "string", "pattern": "^[0-9][0-9AB][0-9]{3}$" },
            "match": { "enum": ["exact", "normalized", "fuzzy", "delegated"] },
            "similarity": { "type": "number", "minimum": 0, "maximum": 1 }
          }
        }
      ]
    },
    "versions": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "https://muninn.example/schemas/dossier-draft/1.1#/$defs/ReferentialVersion" }
    }
  }
}
```

<!-- contract:example PostalCommuneCheckResponse -->
```json
{
  "postal_code_status": "known",
  "commune_status": "known",
  "pair_status": "inconsistent",
  "commune": { "official_name": "Bagnolet", "insee_code": "93006", "match": "exact", "similarity": 1 },
  "versions": [
    { "dataset": "postal_codes", "source_id": "SRC-06", "source_date": "2026-09-30", "channel": "production" },
    { "dataset": "communes", "source_id": "SRC-07", "source_date": "2026-01-01", "channel": "production" }
  ]
}
```

- `match` : `exact` (nom officiel), `normalized` (même nom après N1 à N3 et N5, par exemple
  « montreuil »), `fuzzy` (similarité trigramme au-dessus d'un seuil [H : 0,8]), `delegated`
  (commune déléguée rattachée à sa commune nouvelle).
- Correspondance avec le brouillon : `pair_status: inconsistent` donne `mismatch`,
  `inconsistent_pair` sur les deux champs ; `postal_code_status: unknown` donne
  `unknown_postal_code` ; `commune_status: unknown` donne `unknown_commune`.
- **Erreurs** : 401, 403, 413 (corps de plus de 1 Ko), 422 `validation_failed`, 429, 503.
- **Idempotence** : lecture pure. **Jamais stocké ni journalisé** : le code postal et la commune
  reçus.

### 5.3 `POST /v1/checks/phone-prefix`

Contrôle d'un numéro par son seul préfixe (US-50, critère 3 ; US-51, critère 3).

<!-- contract:schema PhonePrefixCheckRequest -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/phone-prefix-check-request/1",
  "title": "PhonePrefixCheckRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["prefix"],
  "properties": { "prefix": { "type": "string", "pattern": "^0[1-9][0-9]{5}$" } }
}
```

<!-- contract:example PhonePrefixCheckRequest -->
```json
{ "prefix": "0639980" }
```

<!-- contract:schema PhonePrefixCheckResponse -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/phone-prefix-check-response/1",
  "title": "PhonePrefixCheckResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "line_type", "sms_capable", "version"],
  "properties": {
    "status": { "enum": ["assigned", "unassigned"] },
    "line_type": { "enum": ["mobile", "fixed", "non_geographic", "special", "unknown", null] },
    "sms_capable": { "type": ["boolean", "null"] },
    "version": { "$ref": "https://muninn.example/schemas/dossier-draft/1.1#/$defs/ReferentialVersion" }
  }
}
```

<!-- contract:example PhonePrefixCheckResponse -->
```json
{
  "status": "assigned",
  "line_type": "mobile",
  "sms_capable": true,
  "version": { "dataset": "numbering_ranges", "source_id": "SRC-13", "source_date": "2026-10-08", "channel": "test" }
}
```

- Le préfixe est formé des 7 premiers chiffres du numéro au format national (`0` suivi de six
  chiffres) [H : granularité à confirmer sur MAJNUM]. L'extraction le calcule depuis la valeur
  E.164 ; le numéro complet ne quitte jamais l'extraction (document 03, section 6.1).
- `sms_capable` vaut vrai pour une tranche mobile seulement [H : règle mobile et fixe à
  confirmer dans le plan de numérotation, VD-15]. L'opérateur de la tranche n'est jamais rendu.
- En canal `production`, la plage fictive n'existe pas ; en canal `test`, elle est déclarée
  attribuée (VD-16).
- **Erreurs** : 401, 403, 413, 422, 429, 503. **Jamais stocké ni journalisé** : le préfixe.

### 5.4 Autres points des référentiels

| Point                                 | Requête                                                          | Réponse 200                                                                                                                                                 | Erreurs propres                                     |
| ------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `POST /v1/postal-codes/communes`      | `{"postal_code": "93100"}`                                       | `{"communes": [{"official_name", "insee_code", "line_5"}], "versions": [...]}`                                                                              | 422 si le code n'a pas 5 chiffres                   |
| `GET /v1/versions`                    | aucune                                                           | `{"datasets": [{"dataset", "source_id", "source_date", "channel", "published_at", "rows_loaded"}]}`                                                         | aucune                                              |
| `GET /v1/lexicons/{trade}`            | `trade` (énumération) ; `version` facultatif en requête          | `{"trade", "version", "published_at", "terms": [{"term", "category", "stt_rank", "source_id", "license"}], "sources": [...]}` ; termes `accepted` seulement | 404 si la version n'existe pas ou n'est pas publiée |
| `GET /v1/holidays/{zone}/{year}`      | `zone` (13 zones de SRC-08), `year` (année en cours ou suivante) | `{"zone", "year", "holidays": [{"date", "label"}], "version": {...}}`                                                                                       | 404 hors des années chargées                        |
| `GET /v1/forwarding-codes/{operator}` | `operator` (`orange`, `sfr`, `bouygues`, `free`)                 | `{"operator", "codes": [{"condition", "action", "code", "verified_on"}]}` ; `verified_on` nul signifie « non testé »                                        | 404 opérateur inconnu                               |
| `GET /v1/naf-trades/{naf_code}`       | `naf_code` (code NAF, donnée publique)                           | `{"naf_code", "naf_revision", "trade", "label"}`                                                                                                            | 404 code hors tête de pont                          |

Le lexique publié porte sa licence par terme (CC BY-SA 4.0, CC0, interne) et la liste des
sources (US-48, critère 4). `stt_rank` donne la sélection documentée des 100 termes injectés
dans la transcription (US-15, critère 4).

## 6. API produit

### 6.1 Reprise de la table de la passation

| Passation (section 8)                             | Contrat                                                                                                       | Changement et raison                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `POST /auth/otp/request`, `POST /auth/otp/verify` | `POST /v1/auth/otp/request`, `POST /v1/auth/otp/verify`                                                       | `verify` porte aussi la clé publique et la plateforme : la ligne `app.devices` exige jeton haché et clé publique ensemble |
| `POST /devices`                                   | Absorbé par `verify` ; ajout de `GET /v1/devices`, `PUT /v1/devices/me/push-token`, approbation et révocation | D-22 : approbation par un appareil existant, révocation                                                                   |
| `GET /envelopes`, `POST /envelopes/{id}/ack`      | Inchangés sous `/v1`, avec pagination                                                                         | Aucun                                                                                                                     |
| `PUT /lines/me`                                   | Inchangé, champs ajoutés : `slot_duration_min`, `holiday_zone`, `timezone`                                    | US-05 (critère 3), P-11, outre-mer                                                                                        |
| `GET /lines/me/forwarding-codes`                  | Inchangé ; l'opérateur passe en paramètre de requête                                                          | Aucun                                                                                                                     |
| `PUT /availability`                               | Inchangé sous `/v1`                                                                                           | Créneaux de l'agent non reçus gardés (US-05, critère 2)                                                                   |
| `POST /webhooks/telephony/*`                      | `POST /v1/webhooks/telephony/{provider}/{event}`                                                              | Fournisseur dans le chemin (ADR-02 ; `fake` en démo)                                                                      |
| `WS /voice/stream`                                | `WS /v1/voice/stream` sur voice-gateway                                                                       | Jeton à usage unique                                                                                                      |
| `POST /debrief`                                   | Inchangé, avec `trade`                                                                                        | P-09 : paramètre `métier`                                                                                                 |
| `POST /receipts/scan`, `POST /expenses/voice`     | Inchangés                                                                                                     | Aucun                                                                                                                     |
| `POST /sms`                                       | Inchangé, `Idempotency-Key` requis ; ajout de `GET /v1/sms/{sms_id}` et du webhook SMS                        | Un SMS ne doit jamais partir deux fois                                                                                    |
| `PUT /backup/blob`, `GET /backup/blob`            | Inchangés ; ajout de `HEAD`                                                                                   | Contrôle d'intégrité et de concurrence                                                                                    |
| `POST /archive/blobs`, `GET /archive/blobs`       | Inchangés ; ajout de `GET /v1/archive/blobs/{archive_id}`                                                     | Téléchargement d'une pièce                                                                                                |
| `POST /billing/checkout`, `POST /webhooks/stripe` | Inchangés sous `/v1` ; ajout de `POST /v1/billing/portal`                                                     | D-26 : l'artisan gère son abonnement chez le prestataire                                                                  |
| `GET /health`, `GET /ready`                       | Inchangés, hors préfixe                                                                                       | Aucun                                                                                                                     |
| Absent (P-09)                                     | `POST /v1/extractions/text`                                                                                   | Extraction à partir de texte                                                                                              |
| Absent (P-09)                                     | `POST /v1/transcriptions`                                                                                     | Transcription d'une recherche dite                                                                                        |
| Absent (P-09)                                     | `POST /v1/drafts/{draft_id}/review`                                                                           | Compteurs de correction                                                                                                   |
| Absent (P-09)                                     | `POST /v1/lines/me/forwarding-tests`, `GET /v1/lines/me/forwarding-tests/{test_id}`                           | Fenêtre de test du renvoi et son statut                                                                                   |
| Absent (P-09, P-16)                               | `POST /v1/onboarding/siren-lookup`                                                                            | Recherche par SIREN, en option tant qu'aucune story ne la porte                                                           |
| Absent (P-09, X-06)                               | `POST /v1/erasures`                                                                                           | Événement d'effacement et effacement des traces d'un numéro                                                               |
| Absent (P-09)                                     | API des référentiels (section 5)                                                                              | US-50                                                                                                                     |
| Absent (P-11)                                     | `PUT /v1/lines/me/worked-holidays`                                                                            | Jours fériés travaillés                                                                                                   |
| Absent (document 05, section 8.1)                 | `GET /v1/account/export`, `POST /v1/account/closure`, `GET /v1/account`, `POST /v1/account/dpa-acceptance`    | Droits d'accès, de portabilité et d'effacement de l'artisan ; preuve d'acceptation du contrat de sous-traitance           |
| Absent (F-12)                                     | `/v1/demo/*`                                                                                                  | Démo du 29 octobre                                                                                                        |

### 6.2 Comptes et codes à usage unique

**`POST /v1/auth/otp/request`** : demande d'un code (US-01).

- Authentification `none`. Lot 3. Démo : non.
- Corps : `{"login_kind": "phone" | "email", "login": "+33612345678" | "artisan@example.fr"}`.
- Réponse **202** : `{"challenge_id": "uuid", "expires_at": "…", "resend_after_s": 60}`. La
  réponse est la même que le compte existe ou non (pas d'énumération des comptes).
- Erreurs : 422 `validation_failed`, 429 `rate_limited`, 503 `sms_provider_unavailable`.
- Quota : 3 par identifiant et par 15 minutes ; 10 par adresse IP et par heure. Idempotence :
  sans objet ; une nouvelle demande invalide le code précédent.
- Jamais stocké : l'identifiant (seule son empreinte HMAC), le code (seule son empreinte).

**`POST /v1/auth/otp/verify`** : vérification du code et enregistrement de l'appareil.

<!-- contract:schema OtpVerifyRequest -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/otp-verify-request/1",
  "title": "OtpVerifyRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["challenge_id", "login", "code", "device"],
  "properties": {
    "challenge_id": { "type": "string", "format": "uuid" },
    "login": { "type": "string", "minLength": 3, "maxLength": 254 },
    "code": { "type": "string", "pattern": "^[0-9]{6}$" },
    "device": {
      "type": "object",
      "additionalProperties": false,
      "required": ["platform", "public_key", "app_version"],
      "properties": {
        "platform": { "enum": ["android", "ios"] },
        "public_key": { "type": "string", "contentEncoding": "base64", "pattern": "^[A-Za-z0-9+/]{43}=$" },
        "push_token": { "type": ["string", "null"], "maxLength": 4096 },
        "app_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
      }
    }
  }
}
```

<!-- contract:example OtpVerifyRequest -->
```json
{
  "challenge_id": "2d1e0f9a-8b7c-4d6e-9f5a-4b3c2d1e0f9a",
  "login": "+33639980047",
  "code": "482915",
  "device": {
    "platform": "android",
    "public_key": "x6Etgzrb5lZZsSLe1zK21dlfrlUt/tTVvqipJvNI6qk=",
    "push_token": null,
    "app_version": "1.0.0"
  }
}
```

<!-- contract:schema OtpVerifyResponse -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/otp-verify-response/1",
  "title": "OtpVerifyResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["device_id", "device_token", "device_status", "account_status", "approval"],
  "properties": {
    "device_id": { "type": "string", "format": "uuid" },
    "device_token": { "type": "string", "pattern": "^mdt_[A-Za-z0-9_-]{43}$" },
    "device_status": { "enum": ["active", "pending_approval"] },
    "account_status": { "enum": ["created", "existing"] },
    "approval": {
      "oneOf": [
        { "type": "null" },
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["approval_code", "expires_at"],
          "properties": {
            "approval_code": { "type": "string", "pattern": "^[0-9]{6}$" },
            "expires_at": { "type": "string", "format": "date-time" }
          }
        }
      ]
    }
  }
}
```

<!-- contract:example OtpVerifyResponse -->
```json
{
  "device_id": "6a7b8c9d-0e1f-4a2b-8c3d-4e5f6a7b8c9d",
  "device_token": "mdt_Q2hhbmdlTWVJblByb2R1Y3Rpb25fdGhpc19pc19mYWs",
  "device_status": "pending_approval",
  "account_status": "existing",
  "approval": { "approval_code": "730194", "expires_at": "2026-10-12T08:15:00Z" }
}
```

- Authentification `none`. Lot 3. Démo : non. Réponse 200, `Cache-Control: no-store`.
- Premier appareil d'un compte créé : `device_status: active`, `approval: null`. Appareil
  supplémentaire d'un compte existant : `pending_approval` (D-22, section 6.3).
- Erreurs : 409 `public_key_already_registered`, 410 `otp_expired`, 422 `otp_invalid` (avec
  `details: [{"field": "body.code", "issue": "attempts_remaining_4"}]` [H : forme du compteur]),
  423 `otp_locked`, 429.
- Quota : 5 essais par code (US-01, critère 3). Idempotence : sans objet, le code est à usage
  unique.
- Jamais transmis : la clé privée (test de US-01, critère 2). Jamais stocké : le jeton (seule
  son empreinte).

**`GET /v1/account`** : état du compte (`status`, `plan`, `trial_ends_at`, `dpa_version`,
`created_at`). `device_token`. Lot 3. Démo : non. Aucune donnée de client.

**`POST /v1/account/dpa-acceptance`** : `{"dpa_version": "2026-10"}` ; pose `dpa_accepted_at`
et passe le compte en `active` (document 05, section 5). Réponse 200 avec l'état du compte.
`device_token`. Lot 3. Idempotent par nature. Démo : non.

**`GET /v1/account/export`** : export JSON des données serveur du compte (compte, appareils,
ligne, créneaux, statuts de SMS, sessions d'appel sans `caller_hash`, extractions sans contenu,
événements d'audit), pour les droits d'accès et de portabilité de l'artisan (document 05,
section 8.1). Aucune donnée de client n'y figure : il n'y en a pas. `device_token`. Lot 6. Quota :
5 par compte et par jour. Démo : non.

**`POST /v1/account/closure`** : demande de fermeture du compte. Réponse 202 avec `purge_after`
(30 jours [H]). Rappel affiché par l'application : les archives légales restent selon D-23.
`device_token`, `Idempotency-Key` accepté. Lot 6. Démo : non. L'annulation pendant le délai de
grâce est une décision attendue (section 12).

**`POST /v1/onboarding/siren-lookup`** : `{"siren": "123456789"}` en corps (le SIREN d'un
entrepreneur individuel est une donnée personnelle). Réponse : `{"business_name",
"naf_code", "suggested_trade"}` ; le bloc `dirigeants` de SRC-02 est écarté sans stockage.
`device_token`. Lot 3, **option** : il n'est livré que si une story le porte (P-16). Démo : non.

### 6.3 Appareils, approbation et révocation (D-22, US-01 critère 5, US-54)

**Cycle de vie.**

1. **Demande.** `POST /v1/auth/otp/verify` enregistre l'appareil. Le premier appareil d'un compte
   est actif d'emblée (US-01, critère 5). Tout appareil suivant naît `pending_approval` : la
   vérification du code vaut demande d'approbation, sans point d'accès séparé.
2. **Aucune enveloppe pour un appareil en attente.** Le relay ne chiffre que pour les appareils
   approuvés et non révoqués (`approved_at` renseigné, `revoked_at` nul). Un appareil en attente
   ne reçoit donc aucune demande, même celles qui arrivent pendant l'attente ; il ne lit pas non
   plus les anciennes, chiffrées pour d'autres clés.
3. **Portée réduite.** Le jeton d'un appareil en attente n'ouvre que
   `GET /v1/devices/me/approval`, `PUT /v1/devices/me/push-token`,
   `POST /v1/devices/{device_id}/revoke` avec `me`, `POST /v1/devices/me/recovery-challenge` et
   `POST /v1/devices/me/recovery-approval`. Tout autre point rend 403 `device_pending_approval`.
4. **Notification.** Les appareils approuvés reçoivent une notification sans contenu, à texte
   fixe « Nouvel appareil à approuver », émise par le relay, seul détenteur des clés de
   notification (`POST /v1/notifications`, section 6.13).
5. **Approbation ou refus.** Sur un appareil approuvé, l'artisan ouvre la liste des appareils et
   saisit le code à 6 chiffres affiché par le nouvel appareil. Ce code est dérivé de la clé
   publique du nouvel appareil [H : 6 chiffres tirés de son empreinte SHA-256] : l'approbation
   lie l'appareil **et** sa clé, ce qui empêche de substituer une autre clé entre l'affichage et
   l'approbation. Le refus révoque l'appareil en attente.
6. **Révocation (US-54).** Depuis un autre appareil, en un geste suivi d'une confirmation dans
   l'application : empreinte du jeton et jeton push effacés, enveloppes en attente supprimées,
   `revoked_at` posé, événement d'audit `device_revoked` sans donnée personnelle (seulement
   `device_id`, identifiant opaque). La requête suivante de l'appareil révoqué rend 401
   `device_revoked`. Le relay ne chiffre plus pour lui.

| Point                                    | Rôle et règle                                                                                                                                                                                                                | Auth                                     | Réponse                                                      | Erreurs propres                                                                                                                 | Idempotence                           | Quota [H]                         |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | --------------------------------- |
| `GET /v1/devices`                        | Liste des appareils du compte : `device_id`, `platform`, `status` (`active`, `pending_approval`, `revoked`), `created_at`, `last_seen_at`, `approved_at`, `key_fingerprint` (12 caractères), `is_current` (US-54, critère 1) | `device_token`                           | 200                                                          | aucune                                                                                                                          | Lecture                               | 60 par appareil et par heure      |
| `PUT /v1/devices/me/push-token`          | Remplace le jeton push de l'appareil courant : `{"push_token": "…"}`                                                                                                                                                         | `device_token` ou `device_token_pending` | 204                                                          | 422                                                                                                                             | Par nature                            | 30 par appareil et par heure      |
| `GET /v1/devices/me/approval`            | Statut de la demande de l'appareil courant : `{"status", "approval_code", "expires_at"}`                                                                                                                                     | `device_token_pending`                   | 200                                                          | 409 `conflict` si l'appareil est déjà approuvé                                                                                  | Lecture                               | 120 par appareil et par heure     |
| `POST /v1/devices/{device_id}/approve`   | Un appareil approuvé approuve un appareil en attente : `{"approval_code": "730194"}` ; pose `approved_at` et `approved_by_device_id`                                                                                         | `device_token` (appareil approuvé)       | 200, appareil `active`                                       | 404 ; 409 `conflict` (pas en attente) ; 422 `approval_code_invalid` ; au troisième code faux, l'appareil en attente est révoqué | Accepte `Idempotency-Key`             | 3 essais par appareil en attente  |
| `POST /v1/devices/{device_id}/reject`    | Refus d'un appareil en attente : il est révoqué, avec les effets d'une révocation                                                                                                                                            | `device_token` (appareil approuvé)       | 200                                                          | 404 ; 409 `conflict` (pas en attente)                                                                                           | Oui : un second refus rend 200        | 20 par compte et par jour         |
| `POST /v1/devices/{device_id}/revoke`    | Révocation d'un appareil du compte, ou de l'appareil courant (`me`) ; effets du point 6 ci-dessus                                                                                                                            | `device_token` ; `me` aussi en attente   | 200 ; l'appareil révoqué reçoit ensuite 401 `device_revoked` | 404                                                                                                                             | Oui : une seconde révocation rend 200 | 20 par compte et par jour         |
| `PUT /v1/account/recovery-key`           | **[H : en attente de décision du porteur]** Enregistre la clé publique de vérification dérivée de la phrase de récupération (D-14) : `{"recovery_public_key": "…"}`                                                          | `device_token` (appareil approuvé)       | 204                                                          | 422                                                                                                                             | Par nature                            | 10 par compte et par jour         |
| `POST /v1/devices/me/recovery-challenge` | **[H : en attente de décision du porteur]** Défi à usage unique pour l'appareil en attente : `{"challenge", "expires_at"}`, valable 5 minutes                                                                                | `device_token_pending`                   | 200                                                          | 404 si aucune clé de récupération n'est enregistrée                                                                             | Non                                   | 5 par appareil et par jour        |
| `POST /v1/devices/me/recovery-approval`  | **[H : en attente de décision du porteur]** Approbation par la phrase de récupération : `{"challenge", "signature"}` ; pose `approved_at`, `approved_by_device_id` nul et la méthode `recovery_phrase`                       | `device_token_pending`                   | 200, appareil `active`                                       | 422 `recovery_signature_invalid` ; 423 `recovery_locked` après 5 échecs                                                         | Non                                   | 5 essais par appareil et par jour |

- Lot 3. Démo : non.
- Audit : `device_registered`, `device_revoked`, et trois types à ajouter :
  `device_approval_requested`, `device_approved`, `device_rejected` (section 11.1). Leur `meta`
  ne porte que des identifiants opaques et la méthode d'approbation.

**Artisan qui a perdu son seul appareil : recours par la phrase de récupération [H : en attente
de décision du porteur].** Aucun appareil ne peut approuver. La proposition soumise au porteur
réutilise la phrase de récupération de D-14, que l'artisan garde seul. À la création de la
sauvegarde, l'application dérive de la phrase une paire de clés de signature, par une fonction
de dérivation dont le contexte est distinct de celui de la clé de sauvegarde [H : choix de la
fonction en phase 3], et ne transmet que la clé publique (`PUT /v1/account/recovery-key`). Pour
être approuvé, le nouvel appareil, sur lequel l'artisan ressaisit sa phrase, signe un défi du
serveur.

- R1 et D-14 restent tenues : le serveur ne garde qu'une clé publique, qui ne permet ni de
  déchiffrer la sauvegarde ni de retrouver la phrase.
- Protection contre l'échange de carte SIM : la phrase n'est ni sur le téléphone détourné ni
  chez l'opérateur ; le code SMS seul ne suffit pas.
- Limite : un artisan qui a perdu la phrase **et** son seul téléphone n'a plus de recours en
  ligne. Il faut alors une procédure hors ligne (vérification d'identité par le support) ou une
  activation différée, à décider. Les trois points marqués [H] ne sont pas livrés avant la
  décision.

### 6.4 Ligne, renvoi et jours fériés

**`GET /v1/lines/me`**, **`PUT /v1/lines/me`** : configuration de la ligne (US-02).

<!-- contract:schema LineConfig -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/line-config/1",
  "title": "LineConfig",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "business_name", "first_name", "trade", "opening_hours", "greeting_custom",
    "booking_enabled", "slot_duration_min", "holiday_zone", "timezone"
  ],
  "properties": {
    "business_name": { "type": "string", "minLength": 1, "maxLength": 80 },
    "first_name": { "type": "string", "minLength": 1, "maxLength": 40 },
    "trade": { "enum": ["plomberie", "chauffage", "electricite", "serrurerie", "autre"] },
    "opening_hours": {
      "type": "object",
      "additionalProperties": false,
      "patternProperties": {
        "^(mon|tue|wed|thu|fri|sat|sun)$": {
          "type": "array",
          "maxItems": 4,
          "items": {
            "type": "array",
            "prefixItems": [
              { "type": "string", "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$" },
              { "type": "string", "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$" }
            ],
            "minItems": 2,
            "maxItems": 2
          }
        }
      }
    },
    "greeting_custom": { "type": "string", "maxLength": 300 },
    "booking_enabled": { "type": "boolean" },
    "slot_duration_min": { "type": "integer", "minimum": 15, "maximum": 480 },
    "holiday_zone": { "type": "string", "pattern": "^[a-z][a-z0-9-]{2,31}$" },
    "timezone": { "type": "string", "pattern": "^[A-Za-z_]+(/[A-Za-z_+-]+){0,2}$" }
  }
}
```

<!-- contract:example LineConfig -->
```json
{
  "business_name": "Plomberie Exemple",
  "first_name": "Karim",
  "trade": "plomberie",
  "opening_hours": { "mon": [["08:00", "12:00"], ["14:00", "18:00"]], "tue": [["08:00", "18:00"]] },
  "greeting_custom": "Pour une urgence, précisez-le dès le début.",
  "booking_enabled": true,
  "slot_duration_min": 60,
  "holiday_zone": "metropole",
  "timezone": "Europe/Paris"
}
```

- `device_token`. Lot 2. Démo : non (la démo utilise une configuration figée). Quota : 30 par
  compte et par heure [H].
- Réponse 200 de `PUT` et de `GET` : la configuration, plus `cpaas_number` (nul tant qu'aucun
  numéro n'est attribué : R10 interdit d'en acheter sans accord) et `greeting_preview`, texte
  complet prononcé. L'annonce de l'assistant automatique (D-04) est produite par le code et
  placée en premier : elle n'est pas un champ et ne peut pas être supprimée (US-02, critère 1).
- Erreurs : 422 `validation_failed`, 422 `greeting_rejected` (partie libre qui contredit
  l'annonce, par exemple « je suis Karim » [H : liste de motifs à écrire]).

**`PUT /v1/lines/me/worked-holidays`** : `{"dates": ["2026-11-11"]}` remplace la liste des jours
fériés déclarés travaillés (US-49, critère 4 ; P-11). Chaque date est contrôlée auprès de l'API
des référentiels pour la zone de la ligne : sinon 422 `not_a_public_holiday`. `device_token`.
Lot 2. Démo : non. Réponse 200 avec la liste.

**`GET /v1/lines/me/forwarding-codes?operator=orange`** : codes d'activation et de
désactivation des trois renvois, avec `verified_on` et l'avertissement sur la facturation du
renvoi (US-03). L'opérateur est une énumération, pas une donnée personnelle. `device_token`.
Lot 2. Démo : non. Erreurs : 422 opérateur inconnu.

**`POST /v1/lines/me/forwarding-tests`** : ouvre une fenêtre de test de 2 minutes (US-04).
Réponse 201 `{"test_id", "status": "pending", "expires_at"}`. 409 `conflict` si une fenêtre est
déjà ouverte (unicité partielle de `app.forwarding_tests`). `device_token`. Lot 2. Quota : 10 par
ligne et par heure [H]. Démo : non.

**`GET /v1/lines/me/forwarding-tests/{test_id}`** : `{"test_id", "status": "pending" |
"verified" | "expired", "resolved_at"}`. L'application affiche « renvoi vérifié » ou « renvoi
non détecté ». `device_token`. Lot 2. Démo : non.

### 6.5 Disponibilités

**`PUT /v1/availability`** : remplace les créneaux des 14 prochains jours (US-05).

<!-- contract:schema AvailabilityPut -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/availability-put/1",
  "title": "AvailabilityPut",
  "type": "object",
  "additionalProperties": false,
  "required": ["window_start", "window_end", "slots"],
  "properties": {
    "window_start": { "type": "string", "format": "date-time" },
    "window_end": { "type": "string", "format": "date-time" },
    "slots": {
      "type": "array",
      "maxItems": 500,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["starts_at", "ends_at", "kind"],
        "properties": {
          "starts_at": { "type": "string", "format": "date-time" },
          "ends_at": { "type": "string", "format": "date-time" },
          "kind": { "enum": ["free", "busy"] }
        }
      }
    }
  }
}
```

<!-- contract:example AvailabilityPut -->
```json
{
  "window_start": "2026-10-12T00:00:00+02:00",
  "window_end": "2026-10-26T00:00:00+01:00",
  "slots": [
    { "starts_at": "2026-10-13T08:00:00+02:00", "ends_at": "2026-10-13T12:00:00+02:00", "kind": "free" },
    { "starts_at": "2026-10-13T14:00:00+02:00", "ends_at": "2026-10-13T16:00:00+02:00", "kind": "busy" }
  ]
}
```

- **Sans nom par construction** : le schéma n'a aucun champ de libellé, de client ou de lieu
  (US-05, critère 1) ; un champ en plus est refusé (`unknown_field`).
- Règles : fenêtre de 14 jours au plus ; créneau de 24 heures au plus, fin après le début ;
  pas de chevauchement entre créneaux envoyés. Les créneaux `agent` non encore reçus par
  l'appareil sont gardés occupés (US-05, critère 2) et rendus dans la réponse.
- Réponse 200 : `{"stored": 2, "kept_agent_slots": [{"starts_at", "ends_at"}], "purged_past": 0}`.
- `device_token`. Lot 2. Idempotent par nature. Quota : 60 par appareil et par heure [H].
  Démo : non.

### 6.6 Enveloppes et accusé de réception

**`GET /v1/envelopes`** : enveloppes en attente pour l'appareil du jeton (US-12, TA-15).

Ordre de la liste : `created_at` croissant, puis `envelope_id` en cas d'égalité, pour que l'appareil
intègre les demandes dans l'ordre où elles sont arrivées (invariant I-4 du plan de tests).
Plusieurs appareils : chaque appareil approuvé reçoit sa propre enveloppe ; `device_received_at`
(créneau réservé par l'agent) est renseigné au premier accusé de réception, quel que soit
l'appareil. Ces deux règles ont été fixées à la consolidation de la phase 2.

<!-- contract:schema EnvelopeList -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/envelope-list/1",
  "title": "EnvelopeList",
  "type": "object",
  "additionalProperties": false,
  "required": ["items", "next_cursor"],
  "properties": {
    "items": {
      "type": "array",
      "maxItems": 100,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["envelope_id", "created_at", "expires_at", "ciphertext"],
        "properties": {
          "envelope_id": { "type": "string", "format": "uuid" },
          "created_at": { "type": "string", "format": "date-time" },
          "expires_at": { "type": "string", "format": "date-time" },
          "ciphertext": { "type": "string", "contentEncoding": "base64", "minLength": 68, "maxLength": 87384 }
        }
      }
    },
    "next_cursor": { "type": ["string", "null"], "maxLength": 200 }
  }
}
```

<!-- contract:example EnvelopeList -->
```json
{
  "items": [
    {
      "envelope_id": "1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      "created_at": "2026-10-12T07:42:21Z",
      "expires_at": "2026-10-19T07:42:21Z",
      "ciphertext": "H0D8ktokFpR1CXnubPWC8tXX0o4YM13gWrxU0FYOD1MChgxlK/CNVgJSql50IQVG82n7u86MEs/HlXsmUv6adT4j6BYAOVlKM4lPZWThsTSLvXoA"
    }
  ],
  "next_cursor": null
}
```

- Le contenu chiffré est un `DossierDraft` 1.1 scellé (`SealedBox` X25519) pour cet appareil ;
  le serveur ne peut pas le lire (US-12, critère 4). Bornes de taille : 49 octets à 64 Kio
  (document 02 de la phase 1).
- `device_token`. Lot 3. Pagination. Quota : 60 par appareil et par minute. Démo : non (prévu
  pour le 12 novembre).

**`POST /v1/envelopes/{envelope_id}/ack`** : accusé de réception. Le serveur supprime
l'enveloppe, renseigne `delivered_at` de l'extraction et `device_received_at` du créneau de
l'agent concerné. Réponse 204. L'enveloppe d'un autre appareil rend 404, sans indiquer qu'elle
existe (TA-16). Un second accusé sans `Idempotency-Key` rend aussi 404 : l'application traite 404
comme « déjà supprimée ». `device_token`. Lot 3. Démo : non.

### 6.7 Revue des brouillons et compteurs de correction

**`POST /v1/drafts/{draft_id}/review`** : décision de l'artisan et noms des champs corrigés,
sans valeur (US-17, critère 3 ; P-09).

<!-- contract:schema DraftReview -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/draft-review/1",
  "title": "DraftReview",
  "type": "object",
  "additionalProperties": false,
  "required": ["decision", "corrected_fields"],
  "properties": {
    "decision": { "enum": ["validated", "validated_with_corrections", "rejected"] },
    "corrected_fields": {
      "type": "array",
      "uniqueItems": true,
      "maxItems": 25,
      "items": { "$ref": "https://muninn.example/schemas/dossier-draft/1.1#/$defs/FieldPath" }
    }
  },
  "allOf": [
    {
      "if": { "properties": { "decision": { "const": "validated_with_corrections" } } },
      "then": { "properties": { "corrected_fields": { "minItems": 1 } } },
      "else": { "properties": { "corrected_fields": { "maxItems": 0 } } }
    }
  ]
}
```

<!-- contract:example DraftReview -->
```json
{ "decision": "validated_with_corrections", "corrected_fields": ["client.adresse.code_postal"] }
```

- Réponse 204. Écrit `review_decision`, `reviewed_at` et `app.field_corrections`. Le champ
  `corrected_fields` n'accepte que la liste fermée : aucune valeur ne peut y être glissée.
- Erreurs : 404 (brouillon d'un autre compte ou purgé), 409 `conflict` (déjà revu), 422.
- `device_token`. Lot 3. Accepte `Idempotency-Key`. Quota : 600 par appareil et par jour [H].
  Démo : non ; la démo utilise `POST /v1/demo/runs/{draft_id}/review` (section 4.9).

### 6.8 SMS

**`POST /v1/sms`** : envoi d'un SMS transactionnel dont le texte est composé par l'appareil
(US-27, US-28, US-29).

<!-- contract:schema SmsRequest -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://muninn.example/schemas/sms-request/1",
  "title": "SmsRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["kind", "to", "text"],
  "properties": {
    "kind": { "enum": ["reminder", "reschedule"] },
    "to": { "type": "string", "pattern": "^\\+[1-9][0-9]{7,14}$" },
    "text": { "type": "string", "minLength": 1, "maxLength": 160 }
  }
}
```

<!-- contract:example SmsRequest -->
```json
{
  "kind": "reschedule",
  "to": "+33639980047",
  "text": "Plomberie Exemple : votre RDV du 13/10 9h est deplace au 14/10 9h. Pour un autre creneau, appelez le 01 99 00 12 34."
}
```

- Réponse 200 : `{"sms_id": "uuid", "status": "queued" | "sent", "segments": 1}`.
- Envoi dans la requête, sans file Redis (P-01 étendu aux SMS) ; le texte et le numéro sont
  oubliés après l'envoi (US-27, critère 3 ; P-04).
- Erreurs : 422 `sms_too_long` (160 caractères GSM 7 bits ou 70 UCS-2), 422
  `recipient_not_mobile` (préfixe non mobile, contrôlé par l'API des référentiels), 429
  `quota_exceeded`, 502 `upstream_error`, 503 `sms_provider_unavailable`.
- `device_token`. Lot 5. **`Idempotency-Key` requis** : un SMS ne part jamais deux fois. Quota :
  100 par compte et par jour. En développement et en démo, fournisseur factice ; aucun SMS réel
  sans accord (R10). Démo : non.

**`GET /v1/sms/{sms_id}`** : `{"sms_id", "kind", "status", "segments", "updated_at"}`.
`device_token`. Lot 5. Démo : non.

### 6.9 Sauvegarde et archive

| Point                                | Requête                                                                                                                                           | Réponse                                                                                         | Erreurs propres                                        | Idempotence                  | Quota [H]                    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------- | ---------------------------- |
| `PUT /v1/backup/blob`                | `application/octet-stream`, 200 Mo au plus ; en-tête `Muninn-Ciphertext-SHA256` (base64) ; `If-Match` facultatif (ETag de la sauvegarde en place) | 200 `{"backup_id", "size_bytes", "created_at"}`, `ETag` ; l'ancien objet est supprimé (D-13)    | 412 `precondition_failed` ; 413 ; 422 empreinte fausse | Par nature                   | 24 par compte et par jour    |
| `HEAD /v1/backup/blob`               | aucune                                                                                                                                            | 200 avec `ETag`, `Content-Length`, `Muninn-Ciphertext-SHA256` ; 404 sans sauvegarde             | 404                                                    | Lecture                      | 60 par appareil et par heure |
| `GET /v1/backup/blob`                | aucune                                                                                                                                            | 200 `application/octet-stream`, mêmes en-têtes                                                  | 404                                                    | Lecture                      | 10 par compte et par jour    |
| `POST /v1/archive/blobs`             | `application/octet-stream`, 10 Mo au plus ; en-têtes `Muninn-Ciphertext-SHA256` et `Muninn-Retention-Until` (date)                                | 201 `{"archive_id", "size_bytes", "retention_until"}`                                           | 413 ; 422 date au-delà de 11 ans ou passée             | **`Idempotency-Key` requis** | 500 par compte et par jour   |
| `GET /v1/archive/blobs`              | `limit`, `cursor`                                                                                                                                 | 200 `{"items": [{"archive_id", "size_bytes", "retention_until", "created_at"}], "next_cursor"}` | 400 `invalid_cursor`                                   | Lecture                      | 60 par appareil et par heure |
| `GET /v1/archive/blobs/{archive_id}` | aucune                                                                                                                                            | 200 `application/octet-stream`                                                                  | 404                                                    | Lecture                      | 200 par compte et par jour   |

- `device_token`. Lot 6. Démo : non.
- Le contenu est chiffré sur l'appareil (XChaCha20-Poly1305, clé de l'artisan, D-14) ; le
  serveur ne peut pas le lire (US-33, critère 1). L'empreinte porte sur le contenu chiffré et
  sert le contrôle d'intégrité (`app.blobs.ciphertext_sha256`).
- Aucun point ne supprime une archive : l'api n'en a pas le droit (document 03, section 4.2) ;
  la purge à `retention_until` est faite par worker-maintenance.
- L'en-tête d'empreinte est propre à Muninn. Les champs d'empreinte normalisés par l'IETF n'ont
  pas été vérifiés pour ce document : à revoir en phase 3 [H].

### 6.10 Effacement à la demande

**`POST /v1/erasures`** : l'artisan a effacé sur l'appareil le dossier d'un client qui l'a
demandé (US-35 ; document 05, section 8.2 ; X-06).

- Corps : `{"archives_kept": 2, "caller_number": "+33639980047"}`. `caller_number` est
  facultatif : s'il est présent, l'api le normalise en E.164, calcule `caller_hash` avec chaque
  version active du poivre, supprime les sessions d'appel du compte qui portent cette empreinte,
  puis oublie le numéro. Il n'est ni journalisé ni stocké.
- Effet : un événement d'audit `case_erased` sans identifiant de dossier, avec le seul nombre de
  pièces restées en archive (US-35, critère 2).
- Réponse 200 : `{"call_sessions_deleted": 3, "archives_kept": 2}`.
- `device_token`. Lot 6. **`Idempotency-Key` requis**. Quota : 50 par compte et par jour [H].
  Démo : non.
- La sauvegarde suivante, sans le dossier, passe par `PUT /v1/backup/blob` (US-35, critère 1).

### 6.11 Abonnement

| Point                       | Rôle                                                                                   | Auth           | Réponse                | Idempotence                  | Lot | Démo |
| --------------------------- | -------------------------------------------------------------------------------------- | -------------- | ---------------------- | ---------------------------- | --- | ---- |
| `POST /v1/billing/checkout` | Crée une session de paiement chez le prestataire : `plan` vaut `monthly` ou `annual`   | `device_token` | 200 `{"checkout_url"}` | **`Idempotency-Key` requis** | 6   | non  |
| `POST /v1/billing/portal`   | Ouvre l'espace client du prestataire (moyen de paiement, factures, coordonnées) ; D-26 | `device_token` | 200 `{"portal_url"}`   | Aucune ; URL à courte durée  | 6   | non  |

Aucune donnée bancaire ne transite par Muninn. Quota : 10 par compte et par heure [H].

### 6.12 Webhooks des fournisseurs

| Point                                                  | Émetteur                         | Vérification                                                                   | Effet                                                                                                                                                                                                                           | Lot | Démo    |
| ------------------------------------------------------ | -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ------- |
| `POST /v1/webhooks/telephony/{provider}/call-incoming` | CPaaS                            | Signature du fournisseur, fenêtre de 5 minutes, liste d'adresses en complément | Crée la session d'appel (`caller_hash`), vérifie les plafonds de la ligne, rend l'instruction de connexion au flux média avec un `media_token` ; au-delà des plafonds ou du budget, instruction de message fixe et de raccroché | 2   | non     |
| `POST /v1/webhooks/telephony/{provider}/call-status`   | CPaaS                            | Idem                                                                           | Met à jour la session (durée, statut) ; la fin d'appel déclenche l'extraction côté voice-gateway                                                                                                                                | 2   | non     |
| `POST /v1/webhooks/telephony/fake/call-ended`          | Simulateur (démo, développement) | HMAC d'un secret de test ; absent en production (404)                          | Même code que `call-status`, avec une transcription écrite synthétique                                                                                                                                                          | 1   | **oui** |
| `POST /v1/webhooks/sms/{provider}`                     | Fournisseur SMS                  | Signature du fournisseur [H : ADR-05]                                          | Met à jour `app.sms_jobs.status`                                                                                                                                                                                                | 5   | non     |
| `POST /v1/webhooks/stripe`                             | Prestataire de paiement          | `Stripe-Signature`, tolérance de 5 minutes                                     | Met à jour le plan et l'essai ; rapproche par `billing_customer_ref`                                                                                                                                                            | 6   | non     |

- Réponses : 200 dès que l'événement est enregistré ; un événement déjà traité rend aussi 200
  sans effet (idempotence par `app.processed_webhooks`), pour que le fournisseur cesse de le
  renvoyer. Signature absente, fausse ou hors fenêtre : 401 `invalid_signature`, aucune écriture
  (TA-19).
- Le corps d'un webhook n'est jamais stocké ni journalisé. Le numéro appelant est haché dès la
  réception (F-02, T1).
- La forme exacte de l'instruction rendue au CPaaS dépend du fournisseur [H : ADR-02].
- Quota : 50 par seconde et par fournisseur.

### 6.13 Flux média et points internes de l'appel

| Point                    | Service       | Appelant      | Auth            | Rôle                                                                                                                                             | Lot |
| ------------------------ | ------------- | ------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --- |
| `WS /v1/voice/stream`    | voice-gateway | CPaaS         | `media_token`   | Flux audio de l'appel. Jeton à usage unique, 30 s, lié à la session ; refus sans jeton, avec un jeton expiré ou rejoué (TA-21)                   | 2   |
| `POST /v1/sessions`      | voice-gateway | api           | `service_token` | Ouvre la session de l'agent : `call_session_id`, `line_id`, mode (`normal`, `test`, `simulated`), numéro appelant en mémoire                     | 2   |
| `POST /v1/drafts`        | relay         | voice-gateway | `service_token` | Remet le brouillon de l'appel, en mémoire, pour chiffrement par appareil et notification ; le brouillon en clair est libéré après le chiffrement | 3   |
| `POST /v1/notifications` | relay         | api           | `service_token` | Notification sans contenu à texte fixe (`new_device_pending`) vers les appareils actifs du compte                                                | 3   |

Le jeton du flux média circule dans l'URL de connexion ou dans le premier message du flux, selon
ce que permet le CPaaS [H : ADR-02]. Il n'est pas une donnée personnelle, et le proxy ne garde
pas la chaîne de requête (document 03, section 5.5).

### 6.14 Santé

| Point         | Service | Auth                   | Réponse                                                                                                                                            | Lot | Démo |
| ------------- | ------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ---- |
| `GET /health` | Chacun  | `none`                 | 200 `{"status": "ok"}` si le processus répond ; aucune dépendance testée                                                                           | 0   | oui  |
| `GET /ready`  | Chacun  | `none`, réseau interne | 200 ou 503 ; `status` vaut `ready` ou `not_ready` ; `checks` donne l'état de chaque dépendance (`postgres`, `redis`, `refdata`) (US-41, critère 1) | 0   | oui  |

`/ready` n'est pas joignable depuis Internet : le détail des dépendances n'est donné qu'au réseau
interne. La démo l'utilise pour la vérification de déploiement de la chaîne de livraison.

## 7. Inventaire des points d'accès

« Auth » : schéma de la section 2.4. « Idem. » : idempotence (« req. » pour `Idempotency-Key`
requis, « acc. » pour accepté, « nat. » pour un `PUT` ou une lecture, « non » sinon). Les quotas
détaillés sont dans les fiches ; [H] partout sauf ceux repris du document 03.

| Méthode et chemin                                      | Service       | Rôle                                         | Auth                      | Idem. | Quota principal                   | Lot | Démo |
| ------------------------------------------------------ | ------------- | -------------------------------------------- | ------------------------- | ----- | --------------------------------- | --- | ---- |
| `GET /health`                                          | tous          | Vivacité                                     | `none`                    | nat.  | aucun                             | 0   | oui  |
| `GET /ready`                                           | tous          | Disponibilité des dépendances                | `none` (interne)          | nat.  | aucun                             | 0   | oui  |
| `POST /v1/extract/text`                                | extraction    | Extraction d'une transcription ou d'un texte | `service_token`           | non   | Plafond de jetons LLM par appel   | 1   | oui  |
| `POST /v1/extract/audio`                               | extraction    | Extraction d'un audio                        | `service_token`           | non   | Idem                              | 4   | non  |
| `POST /v1/extract/image`                               | extraction    | Extraction d'une image                       | `service_token`           | non   | Idem                              | 4   | non  |
| `POST /v1/transcribe`                                  | extraction    | Transcription d'une phrase                   | `service_token`           | non   | Idem                              | 4   | non  |
| `POST /v1/checks/postal-commune`                       | refdata       | Contrôle code postal et commune              | `service_token`           | nat.  | 100 par seconde et par jeton      | 1   | oui  |
| `POST /v1/checks/phone-prefix`                         | refdata       | Contrôle du préfixe                          | `service_token`           | nat.  | Idem                              | 1   | oui  |
| `POST /v1/postal-codes/communes`                       | refdata       | Communes d'un code postal                    | `service_token`           | nat.  | Idem                              | 1   | non  |
| `GET /v1/versions`                                     | refdata       | Versions servies                             | `service_token`           | nat.  | Idem                              | 1   | oui  |
| `GET /v1/lexicons/{trade}`                             | refdata       | Lexique d'un métier                          | `service_token`           | nat.  | Idem                              | 1   | non  |
| `GET /v1/holidays/{zone}/{year}`                       | refdata       | Jours fériés                                 | `service_token`           | nat.  | Idem                              | 2   | non  |
| `GET /v1/forwarding-codes/{operator}`                  | refdata       | Codes de renvoi                              | `service_token`           | nat.  | Idem                              | 2   | non  |
| `GET /v1/naf-trades/{naf_code}`                        | refdata       | Correspondance NAF et métier                 | `service_token`           | nat.  | Idem                              | 3   | non  |
| `GET /v1/demo/scenarios`                               | api           | Scénarios de démonstration                   | `service_token` `demo`    | nat.  | 30 par minute                     | 1   | oui  |
| `POST /v1/demo/runs`                                   | api           | Lancement d'un scénario (écart P-03)         | `service_token` `demo`    | non   | 30 par minute                     | 1   | oui  |
| `POST /v1/demo/runs/{draft_id}/review`                 | api           | Revue d'un brouillon de démo                 | `service_token` `demo`    | acc.  | 30 par minute                     | 1   | oui  |
| `POST /v1/webhooks/telephony/fake/call-ended`          | api           | Fin d'appel simulée                          | HMAC de test              | nat.  | 50 par seconde                    | 1   | oui  |
| `PUT /v1/lines/me`                                     | api           | Configuration de la ligne                    | `device_token`            | nat.  | 30 par compte et par heure        | 2   | non  |
| `GET /v1/lines/me`                                     | api           | Lecture de la configuration                  | `device_token`            | nat.  | 600 par appareil et par heure     | 2   | non  |
| `PUT /v1/lines/me/worked-holidays`                     | api           | Jours fériés travaillés                      | `device_token`            | nat.  | 30 par compte et par heure        | 2   | non  |
| `GET /v1/lines/me/forwarding-codes`                    | api           | Codes de renvoi                              | `device_token`            | nat.  | 600 par appareil et par heure     | 2   | non  |
| `POST /v1/lines/me/forwarding-tests`                   | api           | Ouverture d'un test de renvoi                | `device_token`            | non   | 10 par ligne et par heure         | 2   | non  |
| `GET /v1/lines/me/forwarding-tests/{test_id}`          | api           | Statut du test                               | `device_token`            | nat.  | 600 par appareil et par heure     | 2   | non  |
| `PUT /v1/availability`                                 | api           | Créneaux sans nom                            | `device_token`            | nat.  | 60 par appareil et par heure      | 2   | non  |
| `POST /v1/webhooks/telephony/{provider}/call-incoming` | api           | Appel entrant                                | `webhook_signature`       | nat.  | 50 par seconde                    | 2   | non  |
| `POST /v1/webhooks/telephony/{provider}/call-status`   | api           | Statut et fin d'appel                        | `webhook_signature`       | nat.  | 50 par seconde                    | 2   | non  |
| `WS /v1/voice/stream`                                  | voice-gateway | Flux média                                   | `media_token`             | non   | 2 appels simultanés par ligne     | 2   | non  |
| `POST /v1/sessions`                                    | voice-gateway | Ouverture de session de l'agent              | `service_token`           | non   | 50 appels par ligne et par jour   | 2   | non  |
| `POST /v1/auth/otp/request`                            | api           | Demande de code                              | `none`                    | non   | 3 par identifiant et par 15 min   | 3   | non  |
| `POST /v1/auth/otp/verify`                             | api           | Vérification et enregistrement de l'appareil | `none`                    | non   | 5 essais par code                 | 3   | non  |
| `GET /v1/account`                                      | api           | État du compte                               | `device_token`            | nat.  | 600 par appareil et par heure     | 3   | non  |
| `POST /v1/account/dpa-acceptance`                      | api           | Acceptation du contrat de sous-traitance     | `device_token`            | nat.  | 10 par compte et par jour         | 3   | non  |
| `POST /v1/onboarding/siren-lookup`                     | api           | Préremplissage par SIREN (option)            | `device_token`            | non   | 10 par compte et par jour         | 3   | non  |
| `GET /v1/devices`                                      | api           | Appareils du compte                          | `device_token`            | nat.  | 60 par appareil et par heure      | 3   | non  |
| `PUT /v1/devices/me/push-token`                        | api           | Jeton push                                   | `device_token` ou pending | nat.  | 30 par appareil et par heure      | 3   | non  |
| `GET /v1/devices/me/approval`                          | api           | Statut d'approbation                         | `device_token_pending`    | nat.  | 120 par appareil et par heure     | 3   | non  |
| `POST /v1/devices/{device_id}/approve`                 | api           | Approbation d'un appareil                    | `device_token`            | acc.  | 3 essais par appareil en attente  | 3   | non  |
| `POST /v1/devices/{device_id}/reject`                  | api           | Refus d'un appareil en attente               | `device_token`            | nat.  | 20 par compte et par jour         | 3   | non  |
| `POST /v1/devices/{device_id}/revoke`                  | api           | Révocation (US-54)                           | `device_token`            | nat.  | 20 par compte et par jour         | 3   | non  |
| `PUT /v1/account/recovery-key`                         | api           | Clé publique de récupération [H : décision]  | `device_token`            | nat.  | 10 par compte et par jour         | 3   | non  |
| `POST /v1/devices/me/recovery-challenge`               | api           | Défi de récupération [H : décision]          | `device_token_pending`    | non   | 5 par appareil et par jour        | 3   | non  |
| `POST /v1/devices/me/recovery-approval`                | api           | Approbation par phrase [H : décision]        | `device_token_pending`    | non   | 5 essais par appareil et par jour | 3   | non  |
| `GET /v1/envelopes`                                    | api           | Enveloppes en attente                        | `device_token`            | nat.  | 60 par appareil et par minute     | 3   | non  |
| `POST /v1/envelopes/{envelope_id}/ack`                 | api           | Accusé de réception                          | `device_token`            | acc.  | 600 par appareil et par heure     | 3   | non  |
| `POST /v1/drafts/{draft_id}/review`                    | api           | Décision et champs corrigés                  | `device_token`            | acc.  | 600 par appareil et par jour      | 3   | non  |
| `POST /v1/drafts`                                      | relay         | Remise du brouillon de l'appel               | `service_token`           | non   | aucun                             | 3   | non  |
| `POST /v1/notifications`                               | relay         | Notification de nouvel appareil              | `service_token`           | non   | aucun                             | 3   | non  |
| `POST /v1/extractions/text`                            | api           | Extraction d'un texte (accessibilité)        | `device_token`            | non   | 60 par appareil et par heure      | 4   | non  |
| `POST /v1/debrief`                                     | api           | Débrief dicté                                | `device_token`            | non   | 60 par appareil et par heure      | 4   | non  |
| `POST /v1/expenses/voice`                              | api           | Dépense dictée                               | `device_token`            | non   | 60 par appareil et par heure      | 4   | non  |
| `POST /v1/receipts/scan`                               | api           | Ticket photographié                          | `device_token`            | non   | 60 par appareil et par heure      | 4   | non  |
| `POST /v1/transcriptions`                              | api           | Transcription d'une phrase dite              | `device_token`            | non   | 120 par appareil et par heure     | 4   | non  |
| `POST /v1/sms`                                         | api           | Envoi d'un SMS                               | `device_token`            | req.  | 100 par compte et par jour        | 5   | non  |
| `GET /v1/sms/{sms_id}`                                 | api           | Statut d'un SMS                              | `device_token`            | nat.  | 600 par appareil et par heure     | 5   | non  |
| `POST /v1/webhooks/sms/{provider}`                     | api           | Statut d'envoi                               | `webhook_signature`       | nat.  | 50 par seconde                    | 5   | non  |
| `PUT /v1/backup/blob`                                  | api           | Sauvegarde chiffrée                          | `device_token`            | nat.  | 24 par compte et par jour         | 6   | non  |
| `HEAD /v1/backup/blob`                                 | api           | Métadonnées de la sauvegarde                 | `device_token`            | nat.  | 60 par appareil et par heure      | 6   | non  |
| `GET /v1/backup/blob`                                  | api           | Restauration                                 | `device_token`            | nat.  | 10 par compte et par jour         | 6   | non  |
| `POST /v1/archive/blobs`                               | api           | Archive d'une pièce                          | `device_token`            | req.  | 500 par compte et par jour        | 6   | non  |
| `GET /v1/archive/blobs`                                | api           | Liste des archives                           | `device_token`            | nat.  | 60 par appareil et par heure      | 6   | non  |
| `GET /v1/archive/blobs/{archive_id}`                   | api           | Téléchargement d'une archive                 | `device_token`            | nat.  | 200 par compte et par jour        | 6   | non  |
| `POST /v1/erasures`                                    | api           | Effacement à la demande                      | `device_token`            | req.  | 50 par compte et par jour         | 6   | non  |
| `GET /v1/account/export`                               | api           | Export des données du compte                 | `device_token`            | nat.  | 5 par compte et par jour          | 6   | non  |
| `POST /v1/account/closure`                             | api           | Fermeture du compte                          | `device_token`            | acc.  | 5 par compte et par jour          | 6   | non  |
| `POST /v1/billing/checkout`                            | api           | Session de paiement                          | `device_token`            | req.  | 10 par compte et par heure        | 6   | non  |
| `POST /v1/billing/portal`                              | api           | Espace client du prestataire                 | `device_token`            | non   | 10 par compte et par heure        | 6   | non  |
| `POST /v1/webhooks/stripe`                             | api           | Événements de paiement                       | `webhook_signature`       | nat.  | 50 par seconde                    | 6   | non  |

Décompte : 68 points d'accès, dont 10 servent la démo du 29 octobre. Trois points de
récupération sont marqués [H] et ne seront livrés qu'après décision du porteur.

## 8. Points d'accès de la démo du 29 octobre

| Point                                           | Rôle dans le scénario (document 01, section 8.1)                              | Clair hors enveloppe       |
| ----------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------- |
| `GET /v1/demo/scenarios`                        | Étape 1 : choix du scénario                                                   | non                        |
| `POST /v1/demo/runs`                            | Étapes 1 à 4 : lancement, brouillon, champs à vérifier, preuve de destruction | **oui, écart P-03**        |
| `POST /v1/webhooks/telephony/fake/call-ended`   | Étape 2 : fin d'appel factice, même code que la production                    | non (synthétique, interne) |
| `POST /v1/extract/text`                         | Étape 2 : extraction réelle, relance, `needs_review`, refus médical (étape 8) | non (interne, en mémoire)  |
| `POST /v1/checks/postal-commune`                | Étape 3 : nom officiel, couple « 93100 Bagnolet »                             | non                        |
| `POST /v1/checks/phone-prefix`                  | Étape 3 : numéro dicté confronté aux tranches (version de test)               | non                        |
| `GET /v1/versions`                              | Étape 3 : version du référentiel affichée                                     | non                        |
| `POST /v1/demo/runs/{draft_id}/review`          | Étapes 5 et 6 : correction, validation, compteur de correction                | non                        |
| `GET /health`, `GET /ready` (4 services utiles) | Étape 7 : vérification de déploiement dans la chaîne de livraison             | non                        |

Le décompte de 10 de la section 7 compte `/health` et `/ready` une fois chacun, pour l'ensemble
des services. Le
tableau de bord (étape 6) et le journal par `request_id` sont servis par la console, qui lit les
agrégats horaires avec son propre rôle de base (document 03, section 4.1) ; ils ne sont pas des
points de l'api.

**Écart P-03, dit explicitement.** Seule la réponse de `POST /v1/demo/runs` contient un brouillon
en clair hors d'une enveloppe chiffrée pour un appareil. Elle porte `plaintext_draft_notice:
"P-03"`, ne sert que des données synthétiques, n'existe que dans la configuration de démo, et
rien n'en est stocké. Les réponses de `POST /v1/extractions/text`, `/v1/debrief`,
`/v1/expenses/voice` et `/v1/receipts/scan` rendent aussi un brouillon en clair, mais à
l'appareil authentifié qui l'a demandé, dans la réponse HTTPS : c'est le contrat de la passation
et ce n'est pas l'écart P-03 (F-03).

## 9. Vérifier que le code respecte ce contrat

FastAPI génère par défaut un document OpenAPI 3.1.0 (depuis la version 0.99.0), servi à
`/openapi.json`. Chaque service FastAPI exporte le sien dans `docs/` (section 2.1). La version
d'OpenAPI se règle par l'attribut `openapi_version` de l'application, pas par un argument du
constructeur : il n'y a pas lieu d'y toucher.

### 9.1 Sources de vérité et dérive

- **Ce document** est la référence de conception. Les schémas marqués `contract:schema` sont
  extraits par un script dans `schemas/` (fichiers JSON versionnés). Le schéma de
  `DossierDraft` 1.1 y devient `schemas/dossier-draft-1.1.schema.json`, source unique de la
  validation de la sortie de l'extraction et des tests.
- **`docs/openapi*.json`** est le reflet du code. La CI régénère chaque document et échoue si le
  fichier versionné diffère (test de dérive) : toute évolution d'API passe par une revue du
  différentiel.
- **Ruptures** : la CI compare le document OpenAPI de la branche à celui de la branche
  principale avec un outil de détection des ruptures [H : outil à choisir en phase 3] ; une
  rupture sans changement de `/v1` en `/v2` bloque la livraison (section 2.2).

### 9.2 Tests de contrat

| ID    | Test                                                                                                                                                                                                                        | Outil ou méthode                                                                                                                                                                                                                                           | Bloquant |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| TC-01 | Inventaire : l'ensemble (méthode, chemin) de `docs/openapi*.json` est égal à celui de la section 7, lue dans ce document, hors points marqués [H : décision] tant que le porteur n'a pas tranché                            | Script qui lit le tableau Markdown et le document OpenAPI                                                                                                                                                                                                  | oui      |
| TC-02 | Authentification : chaque point de la section 7 déclare le schéma de sécurité attendu ; un appel sans jeton rend 401, avec un jeton hors portée 403                                                                         | Tests générés depuis l'inventaire                                                                                                                                                                                                                          | oui      |
| TC-03 | Conformité des réponses au schéma, codes de statut documentés, type de contenu, en-têtes, absence de 5xx, rejet des données invalides                                                                                       | Schemathesis sur l'application ASGI, sans serveur réseau ; contrôles `response_schema_conformance`, `status_code_conformance`, `content_type_conformance`, `response_headers_conformance`, `not_a_server_error`, `negative_data_rejection`, `ignored_auth` | oui      |
| TC-04 | Équivalence du schéma `DossierDraft` : le composant généré par Pydantic et `schemas/dossier-draft-1.1.schema.json` acceptent et refusent les mêmes instances                                                                | Exemples de la section 3.5, instances générées depuis le schéma JSON, mutations (champ en trop, énumération fausse, confiance hors bornes)                                                                                                                 | oui      |
| TC-05 | Exemples de ce document : chaque bloc `contract:example` est valide pour son schéma                                                                                                                                         | Script de la section 9.4, exécuté en CI                                                                                                                                                                                                                    | oui      |
| TC-06 | Règles non exprimées par le schéma : symétrie de `champs_manquants`, plafond de confiance après contrôle, `needs_review`                                                                                                    | Validateur applicatif, VE-04, VE-24                                                                                                                                                                                                                        | oui      |
| TC-07 | Format d'erreur : toute réponse 4xx et 5xx suit le schéma `Error` ; `request_id` égal à l'en-tête `X-Request-Id` ; aucun fragment de l'entrée dans le corps (valeur canari)                                                 | Schemathesis et test canari (TA-38)                                                                                                                                                                                                                        | oui      |
| TC-08 | Confidentialité : `Cache-Control: no-store` sur les réponses listées en 2.9 ; aucune donnée personnelle dans un chemin ou une chaîne de requête du document OpenAPI (paramètres de chemin réduits aux UUID et énumérations) | Analyse du document OpenAPI et tests HTTP                                                                                                                                                                                                                  | oui      |
| TC-09 | Idempotence : rejeu de `POST /v1/sms` avec la même clé, un seul envoi au fournisseur factice ; clé réutilisée avec un autre corps : 422                                                                                     | Intégration avec fournisseur factice                                                                                                                                                                                                                       | oui      |
| TC-10 | Limitation de débit : 429, `Retry-After`, `RateLimit` et `RateLimit-Policy` à la syntaxe de la version 11 du brouillon (TA-20)                                                                                              | Intégration                                                                                                                                                                                                                                                | oui      |
| TC-11 | Webhooks : signature absente, fausse, hors fenêtre, rejouée (TA-19), sur des charges synthétiques de chaque fournisseur                                                                                                     | Intégration                                                                                                                                                                                                                                                | oui      |
| TC-12 | Démo : en configuration de production, `/v1/demo/*` et `/v1/webhooks/telephony/fake/*` rendent 404 (TA-24) ; `plaintext_draft_notice` n'apparaît dans aucune autre réponse                                                  | Intégration, deux configurations                                                                                                                                                                                                                           | oui      |
| TC-13 | Compatibilité : les exemples 1.0 de la passation restent lisibles par le lecteur de l'application ; un brouillon 1.1 lu par un lecteur 1.0 tolérant garde les champs historiques                                            | Tests du lecteur                                                                                                                                                                                                                                           | non      |

Ces tests complètent les tests d'accès TA-01 à TA-40 du document 03 et les cas VE du document 04
sans les remplacer. Ils s'exécutent dans la chaîne d'intégration continue de US-40, avant
l'évaluation.

### 9.3 Consommateurs

L'application mobile et la console sont les consommateurs. Un test de contrat dirigé par le
consommateur n'est pas proposé au MVP : un seul développeur tient les deux côtés et la dérive est
déjà détectée par TC-01 et la régénération du document OpenAPI [H]. Il deviendra utile si
l'application est confiée à une autre équipe.

### 9.4 Contrôle des exemples de ce document

Chaque schéma est précédé d'un commentaire `contract:schema <Nom>` et chaque exemple d'un
commentaire `contract:example <Nom>`. Un script lit ces blocs, résout les références entre
schémas par leur `$id`, et valide chaque exemple avec un validateur JSON Schema 2020-12, contrôle
des formats (`uuid`, `date`, `date-time`) activé. Pour cette version, les 15 schémas et les 19
exemples ont été validés le 12 octobre 2026 (journal de la session). Des contre-exemples ont été
contrôlés en même temps : les 13 contre-exemples sont refusés, dont `needs_review`
faux avec un brouillon de secours, `call_outcome` renseigné pour un débrief, date de destruction
de l'audio absente pour une entrée audio, motif `no_value` pour un contrôle `verified`, bloc `contact` sans son contrôle de téléphone.

## 10. Couverture des stories Must du MVP

| Story | Points d'accès qui la servent                                                                                                                                                                                         |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US-01 | `POST /v1/auth/otp/request`, `POST /v1/auth/otp/verify`, `POST /v1/account/dpa-acceptance` ; critère 5 : `GET /v1/devices/me/approval`, `POST /v1/devices/{device_id}/approve`, `POST /v1/devices/{device_id}/reject` |
| US-02 | `GET` et `PUT /v1/lines/me`                                                                                                                                                                                           |
| US-03 | `GET /v1/lines/me/forwarding-codes` ; `GET /v1/forwarding-codes/{operator}` (refdata)                                                                                                                                 |
| US-05 | `PUT /v1/availability`                                                                                                                                                                                                |
| US-06 | `POST /v1/webhooks/telephony/{provider}/call-incoming`, `WS /v1/voice/stream`, `POST /v1/sessions` (annonce par le code, D-04)                                                                                        |
| US-07 | `WS /v1/voice/stream`, `POST /v1/extract/text`                                                                                                                                                                        |
| US-08 | `PUT /v1/availability` ; `GET /v1/holidays/{zone}/{year}` ; `rdv_propose` du brouillon                                                                                                                                |
| US-09 | `WS /v1/voice/stream` ; `urgence` et `call_outcome: safety_redirect` du brouillon                                                                                                                                     |
| US-10 | `WS /v1/voice/stream` ; `call_outcome: caller_refused` du brouillon                                                                                                                                                   |
| US-11 | `POST /v1/extract/text` ; `DossierDraft` 1.1 ; `POST /v1/demo/runs` en démo                                                                                                                                           |
| US-12 | `POST /v1/drafts` (relay), `GET /v1/envelopes`, `POST /v1/envelopes/{envelope_id}/ack`                                                                                                                                |
| US-13 | `POST /v1/debrief`, `POST /v1/extractions/text`                                                                                                                                                                       |
| US-15 | `GET /v1/lexicons/{trade}` ; `provenance.lexicon`                                                                                                                                                                     |
| US-17 | `POST /v1/drafts/{draft_id}/review` ; `POST /v1/demo/runs/{draft_id}/review` en démo                                                                                                                                  |
| US-18 | `POST /v1/transcriptions` (recherche dite ; la recherche elle-même est sur l'appareil)                                                                                                                                |
| US-19 | `POST /v1/transcriptions` (réponse dite)                                                                                                                                                                              |
| US-20 | Aucun point dédié, par construction : rapprochement sur l'appareil à partir de `client.telephone` et `cle_humaine`                                                                                                    |
| US-21 | `POST /v1/receipts/scan`, `POST /v1/archive/blobs`                                                                                                                                                                    |
| US-22 | `POST /v1/expenses/voice`, `POST /v1/extractions/text` ; `depense.amount_basis`                                                                                                                                       |
| US-23 | Aucun point, par construction : marge calculée sur l'appareil (encaissements sans passage par le serveur)                                                                                                             |
| US-24 | Aucun point, par construction : export de l'appareil vers l'outil de l'artisan, sans copie chez Muninn (P-15)                                                                                                         |
| US-26 | `rdv_propose` du brouillon ; créneau `agent` inséré par voice-gateway ; `kept_agent_slots` de `PUT /v1/availability`                                                                                                  |
| US-28 | `POST /v1/transcriptions` (imprévu dit), `POST /v1/sms`                                                                                                                                                               |
| US-31 | `destruction` du brouillon ; `POST /v1/demo/runs` en démo                                                                                                                                                             |
| US-32 | Aucun point, par construction : base locale chiffrée ; seuls des contenus chiffrés transitent                                                                                                                         |
| US-33 | `PUT`, `HEAD` et `GET /v1/backup/blob`                                                                                                                                                                                |
| US-36 | `GET /v1/demo/scenarios`, `POST /v1/demo/runs`, `POST /v1/webhooks/telephony/fake/call-ended`                                                                                                                         |
| US-37 | `POST /v1/extract/text`, `/audio`, `/image` (harnais) ; `provenance` pour les versions                                                                                                                                |
| US-38 | Console (agrégats horaires) ; alimentée par les mesures `RunMetrics` et `POST /v1/drafts/{draft_id}/review`                                                                                                           |
| US-39 | `request_id` de toutes les réponses et en-tête `X-Request-Id`                                                                                                                                                         |
| US-40 | `provenance` (versions) ; tests de contrat TC-01 à TC-12 dans la chaîne de livraison                                                                                                                                  |
| US-46 | `GET /v1/versions` (le chargement est fait par worker-ingest, sans API)                                                                                                                                               |
| US-47 | `POST /v1/checks/phone-prefix`, `GET /v1/versions`                                                                                                                                                                    |
| US-48 | `GET /v1/lexicons/{trade}` (la relecture des termes passe par la console)                                                                                                                                             |
| US-50 | Section 5 entière                                                                                                                                                                                                     |
| US-51 | `POST /v1/checks/postal-commune`, `POST /v1/checks/phone-prefix` ; `checks` du brouillon                                                                                                                              |
| US-54 | `GET /v1/devices`, `POST /v1/devices/{device_id}/revoke` ; relay restreint aux appareils approuvés et non révoqués                                                                                                    |

Les 37 stories Must (36, plus US-54 ajoutée par D-22) sont couvertes. Quatre le sont « par construction », sans point d'accès
(US-20, US-23, US-24, US-32) : c'est la conséquence voulue de R1, pas un oubli. Les stories
Should sont aussi servies : US-04 (tests de renvoi), US-16 (`personal_lexicon`), US-27 et US-29
(SMS), US-34 (archive), US-35 (effacement), US-41 (`/health`, `/ready`), US-49
(`worked-holidays`, `holidays`). Le recours de l'artisan qui a perdu son seul appareil reste en attente de décision (CT-01).

## 11. Impacts sur les documents précédents

Ce document ne modifie aucun autre document. Les écarts suivants appellent une mise à jour par
leur auteur.

### 11.1 Impacts sur le modèle de données

Document visé : phase 1, document 02.

| ID    | Table                                 | Changement demandé                                                                                                                                                                                                                                                                                                  | Raison                                                                                                   |
| ----- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| MD-A1 | `app.devices`                         | `approved_at` (`timestamptz`, nul tant que l'appareil est en attente ; égal à `created_at` pour le premier appareil du compte) et `approved_by_device_id` (`uuid`, clé étrangère vers `app.devices`, mise à nul à la suppression ; nul pour le premier appareil et pour une approbation par phrase de récupération) | D-22, US-01 critère 5 : état d'approbation ; le relay ne lit que les appareils approuvés et non révoqués |
| MD-A2 | `app.devices`                         | `approval_method` (`text`, liste : `first_device`, `device`, `recovery_phrase`) ; `approval_code_hash`, `approval_attempts` (0 à 3), `approval_expires_at`                                                                                                                                                          | Approbation par code dérivé de la clé ; plafond d'essais                                                 |
| MD-A3 | `app.devices`                         | `auth_token_hash` : NN levé, mis à nul à la révocation (contrainte : nul si et seulement si `revoked_at` est renseigné) ; l'unicité reste, sur les valeurs non nulles                                                                                                                                               | US-54, critère 2 : l'empreinte du jeton est effacée ; le modèle la déclare aujourd'hui NN                |
| MD-A4 | `app.devices` (RLS)                   | Politique du relay : lecture des seuls appareils où `approved_at` est renseigné et `revoked_at` est nul                                                                                                                                                                                                             | Aucune enveloppe pour un appareil en attente                                                             |
| MD-A5 | `app.accounts`                        | `recovery_public_key` (`bytea`, 32 octets, facultatif) [H : en attente de décision du porteur]                                                                                                                                                                                                                      | Recours par la phrase de récupération (section 6.3) ; clé publique seulement, R1 et D-14 tenues          |
| MD-A6 | `app.extraction_runs`                 | `image_destroyed_at` (`timestamptz`, NN si `input_mode` = `image` et `finished_at` est renseigné)                                                                                                                                                                                                                   | `destruction.image_destroyed_at` du brouillon (US-21, critère 3 ; US-31)                                 |
| MD-A7 | `app.field_corrections`               | Liste fermée de `field_name` complétée de `contact.nom`, `contact.prenom`, `contact.telephone`, `contact.relation`                                                                                                                                                                                                  | D-25 : bloc `contact` ; égalité avec `FieldPath` (TC-04)                                                 |
| MD-A8 | `app.audit_events`                    | Types ajoutés : `device_approval_requested`, `device_approved`, `device_rejected`, `account_closure_requested`, `account_exported` ; clé de `meta` ajoutée : `approval_method`                                                                                                                                      | Traçabilité sans donnée personnelle (US-54, critère 4)                                                   |
| MD-A9 | Nouvelle table `app.idempotency_keys` | `account_id` ou identifiant du jeton de service, `key` (`uuid`), `route`, `request_hmac` (32 octets), `response_status`, `response_body` (`jsonb`, seulement pour les réponses sans donnée personnelle), `created_at`, `expires_at` (24 heures)                                                                     | Idempotence (section 2.5)                                                                                |

### 11.2 Autres documents

| ID    | Document visé                                                                                                  | Écart                                                                                      | Proposition                                                                                                        |
| ----- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| CA-01 | Phase 1, document 03, section 6.1                                                                              | L'api lit les jours fériés pour contrôler les jours travaillés (P-11)                      | Ajouter l'api aux consommateurs de `GET /v1/holidays/{zone}/{year}`                                                |
| CA-02 | Phase 1, document 03, section 4.2                                                                              | L'api appelle le relay pour la notification « nouvel appareil »                            | Ajouter cet appel, texte fixe, sans contenu                                                                        |
| CA-03 | Phase 1, document 03, section 5.3                                                                              | La révocation et l'approbation sont précisées par D-22 et US-54                            | Reprendre le cycle de vie de la section 6.3 ; retirer l'option « à arbitrer »                                      |
| CA-04 | Phase 0, document 02 (F-04)                                                                                    | F-04 fait appeler le STT par l'api, qui n'en détient pas la clé (document 03, section 5.6) | L'api passe par `POST /v1/transcribe` du composant extraction                                                      |
| CA-05 | Phase 0, document 02 (P-10) ; phase 0, document 01 (US-31, US-51) ; phase 1, document 04 (VE-01, VE-24, VE-25) | Points au conditionnel tranchés par D-24 (section 3.1)                                     | Les passer au contrat 1.1 ; VE-24 vérifie `not_checked` ; VE-25 (c) devient mesurable par `sms_capable`            |
| CA-06 | Phase 1, document 04 (VE-16 et section 3.1)                                                                    | Appel pour un tiers : le contrat a désormais le bloc `contact` (D-25)                      | Retirer la mention « le contrat n'a pas de champ de contact » ; écrire le test qui fera entrer ces cas dans le KPI |

## 12. Points incertains et décisions attendues

| ID    | Point                                                                                                                           | Proposition                                                                                                                                                           |
| ----- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-01 | Artisan qui a perdu son seul appareil : aucun appareil ne peut approuver (D-22)                                                 | Approbation par la phrase de récupération de D-14 (section 6.3), trois points marqués [H] ; recours hors ligne si la phrase est aussi perdue. **Décision du porteur** |
| CT-02 | Brouillon de secours sans LLM en fin d'appel (`fallback_no_llm`)                                                                | Le retenir : sans lui, une demande est perdue en silence quand le LLM est indisponible. **Décision du porteur**                                                       |
| CT-03 | Pas d'idempotence pour l'extraction (R1 interdit de garder la réponse)                                                          | Accepter le coût d'une relance, borné par les quotas                                                                                                                  |
| CT-04 | Contrôle `not_checked` ramène la confiance sous 0,7 : charge de vérification accrue pendant une panne de l'API des référentiels | Garder ce choix prudent ; le revoir avec ADR-08 après mesure                                                                                                          |
| CT-05 | Seuils, quotas, latences visées et délai de 200 ms avant `timeout` du contrôle                                                  | Valeurs [H], à mesurer en phase 4                                                                                                                                     |
| CT-06 | Granularité du préfixe (7 chiffres) et règle mobile ou fixe                                                                     | À confirmer sur MAJNUM et le plan de numérotation (VD-15)                                                                                                             |
| CT-07 | Forme de l'instruction rendue au CPaaS et transport du jeton du flux média                                                      | ADR-02                                                                                                                                                                |
| CT-08 | Annulation de la fermeture d'un compte pendant le délai de grâce                                                                | Décision du porteur, avec le registre (document 05)                                                                                                                   |
| CT-09 | Préremplissage par SIREN (P-16)                                                                                                 | Garder l'option sans la livrer tant qu'aucune story ne la porte                                                                                                       |
| CT-10 | En-têtes `RateLimit` d'un brouillon IETF actif, `Idempotency-Key` d'un brouillon expiré                                         | Conventions de Muninn inspirées des brouillons ; revoir à leur publication                                                                                            |
| CT-11 | Envoi d'une sauvegarde de 200 Mo en une requête                                                                                 | Mesurer en phase 3 ; envoi par morceaux si l'hébergeur borne la taille des requêtes                                                                                   |
| CT-12 | Libellé lisible d'un appareil (« téléphone de l'atelier ») pour choisir quel appareil révoquer                                  | Non retenu : donnée inutile au serveur ; l'empreinte de clé et la date suffisent [H]                                                                                  |

## 13. Sources

Sources consultées le 12 octobre 2026 par un agent de vérification, pour les affirmations sur
des normes et des outils tiers.

| Sujet                           | Source                                                                                                                                                                               | Ce qui a été lu                                                                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| En-tête `Deprecation`           | https://www.rfc-editor.org/rfc/rfc9745.html                                                                                                                                          | RFC 9745, mars 2025 ; valeur de type Date des champs structurés, exemple `@1688169599`                                                                                                           |
| En-tête `Sunset`                | https://www.rfc-editor.org/rfc/rfc8594.html                                                                                                                                          | RFC 8594, 2019, catégorie Informational ; valeur HTTP-date                                                                                                                                       |
| `Idempotency-Key`               | https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/                                                                                                          | Version 07 du 15 octobre 2025, brouillon expiré, sans numéro de RFC                                                                                                                              |
| `RateLimit`, `RateLimit-Policy` | https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/                                                                                                               | Version 11 du 23 mai 2026, brouillon actif ; paramètres `q`, `w`, `r`, `t`                                                                                                                       |
| `Retry-After`                   | https://www.rfc-editor.org/rfc/rfc9110.html                                                                                                                                          | Section 10.2.3 : HTTP-date ou nombre de secondes                                                                                                                                                 |
| Code 429                        | https://www.rfc-editor.org/rfc/rfc6585.html                                                                                                                                          | Section 4 ; `Retry-After` facultatif                                                                                                                                                             |
| OpenAPI 3.1.0                   | https://spec.openapis.org/oas/v3.1.0.html                                                                                                                                            | Objet Schema, sur-ensemble de JSON Schema 2020-12 ; dialecte par défaut `https://spec.openapis.org/oas/3.1/dialect/base`                                                                         |
| FastAPI et OpenAPI 3.1.0        | https://fastapi.tiangolo.com/reference/fastapi/ ; https://github.com/fastapi/fastapi/releases/tag/0.99.0                                                                             | 3.1.0 par défaut depuis 0.99.0 ; `/openapi.json` ; `openapi_version` est un attribut, pas un argument                                                                                            |
| Schemathesis                    | https://schemathesis.readthedocs.io/en/stable/ ; https://schemathesis.readthedocs.io/en/stable/guides/python-apps/ ; https://schemathesis.readthedocs.io/en/stable/reference/checks/ | OpenAPI 2.0 à 3.2 ; appel direct d'une application ASGI ; noms des contrôles                                                                                                                     |
| Problem Details                 | https://www.rfc-editor.org/rfc/rfc9457.html                                                                                                                                          | RFC 9457 rend obsolète la RFC 7807                                                                                                                                                               |
| Webhooks du paiement            | https://docs.stripe.com/webhooks                                                                                                                                                     | `Stripe-Signature` ; un même événement peut être reçu plusieurs fois ; dédoublonnage par l'identifiant d'événement, et par l'objet et le type pour deux événements distincts ; ordre non garanti |

Non vérifié : les champs d'empreinte de contenu normalisés par l'IETF (d'où l'en-tête propre
`Muninn-Ciphertext-SHA256`), les mécanismes de signature du fournisseur SMS (ADR-05), la forme
des instructions du CPaaS (ADR-02). Les signatures Twilio et Telnyx reprennent le document 03,
section 11.
