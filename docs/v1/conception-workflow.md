# Muninn V1 : le workflow d'un appel

**Statut :** complément au dossier de conception V1, établi le 22 octobre 2026, après coup. Le
sprint 1 a produit le schéma d'architecture (§ 5.1) et le schéma de pilotage (§ 5.2) ; il n'a pas
schématisé le déroulé d'un appel. Ce document le fait, sans modifier le dossier gelé. Il montre le
workflow tel qu'il est conçu et livré au 22 octobre 2026, décisions postérieures au sprint 1
comprises (D-69, D-73, D-77, D-78, D-80).

Code de référence : `src/muninn/qualification/qualificateur.py` (`traiter_appel`),
`src/muninn/extraction/agent.py` (boucle), `src/muninn/extraction/evaluateur.py` (contrôles et
garde-fous).

**Ce que couvre la V1.**

| Partie                                                         | État au 22 octobre 2026                   |
| -------------------------------------------------------------- | ----------------------------------------- |
| Renvoi d'appel après 15 s sans réponse (D-68)                  | Hors V1 : simulé dans la console (R10)    |
| Conversation à deux voix, puis transcription (D-50)            | Sprint 5 (V-12) ; dialogue écrit d'ici là |
| Contrôle d'entrée, qualification, agent, contrôles, garde-fous | Livré au sprint 4, en production          |
| Dossier ou message affiché dans la console                     | Livré au sprint 4 (écran « Agent »)       |
| Correction et validation par l'artisan (CA-5)                  | Sprint 5 (V-09)                           |

## 1. Le déroulé d'un appel

Qui fait quoi, dans l'ordre. Les traits pleins sont des appels, les traits pointillés des réponses.
Rendus : `diagrammes/conception-workflow/svg/1-le-deroule-d-un-appel.svg` et `png/`.

```mermaid
sequenceDiagram
  autonumber
  actor A as Appelant
  participant L as Ligne de l'artisan
  participant V as Muninn, voix
  participant S as Serveur Muninn
  participant Q as Qualification (LLM)
  participant G as Agent (LLM)
  participant R as API des référentiels
  actor K as Artisan

  A->>L: Appelle l'artisan
  Note over L,K: L'artisan ne décroche pas
  L->>V: Renvoi après 15 s sans réponse (D-68)
  V->>A: Annonce : intelligence artificielle, transcription, droit de refuser (D-51)
  A->>V: Expose sa demande, puis questions et récapitulatif (trame v1.2)
  V->>S: Transcription, appelant et Muninn séparés, puis audio détruit (D-50)
  S->>S: Contrôle d'entrée : taille, caractères, motifs d'injection (D-63)
  S->>Q: Transcription contrôlée, traitée comme une donnée
  Q-->>S: Catégorie et confiance, puis règles du serveur appliquées (D-48)
  alt Fournisseur, personnel ou autre
    S->>K: Message rangé dans « Messages », sans autre extraction
  else Demande de service ou indéterminé
    S->>G: Transcription, consigne et deux outils en liste fermée
    loop Six appels d'outils au plus, délai par appel
      G->>R: chercher_communes ou chercher_terme_metier (lecture seule)
      R-->>G: Communes ou terme, avec leur source
    end
    G-->>S: Brouillon au schéma fermé, une relance si hors schéma
    S->>R: Contrôle de la commune et du code postal (D-69)
    R-->>S: Vérifié, incohérent, ou plusieurs candidates
    S->>S: Garde-fous et règles : gaz, santé, invention, fuite, hors rôle, urgence dite (D-80)
    S->>K: Dossier, avec statuts, provenance et « à vérifier » si besoin
  end
  K->>K: Relit, corrige si besoin, valide (CA-5)
  K->>A: Rappelle le client, seul l'artisan fixe un rendez-vous (D-76)
```

## 2. Les décisions en route

Chaque losange est une décision prise par une règle écrite dans le code, sauf la boucle de
l'agent, où le modèle décide lui-même d'appeler un outil, dans les bornes fixées par le serveur.
Rendus : `diagrammes/conception-workflow/svg/2-les-decisions-en-route.svg` et `png/`.

```mermaid
flowchart TD
  T["Transcription de l'appel"] --> E{"Contrôle d'entrée"}
  E -->|"vide ou sans contenu"| TR["Trace sans contenu : le numéro est gardé, aucun appel au modèle"]
  E -->|"trop longue"| RF["Refus à texte fixe, journalisé sans contenu"]
  E -->|"recevable ; motif d'injection relevé, jamais bloquant"| Q["Qualification par le LLM"]

  Q --> QR{"Règles du serveur"}
  QR -->|"modèle indisponible, sortie invalide, filtre (D-73), confiance sous 0,7"| IND["Indéterminé"]
  QR -->|"personnel ou autre, mais un besoin est dit ou un détournement relevé"| IND
  QR -->|"demande de service"| DS["Demande de service"]
  QR -->|"fournisseur, personnel ou autre"| MSG["Message pour l'artisan"]

  DS --> AG["Agent : lit la transcription, décide d'appeler ses outils"]
  IND --> AG
  AG --> BO{"Bornes de la boucle"}
  BO -->|"outil hors liste"| REF["Refusé, journalisé ; l'agent continue"]
  REF --> AG
  BO -->|"au-delà de six appels : outil non exécuté, le modèle conclut"| FIN
  BO -->|"réponse rendue"| FIN{"Sortie de l'agent"}
  FIN -->|"au schéma"| CT
  FIN -->|"hors schéma"| RL["Une relance, puis brouillon partiel"]
  FIN -->|"modèle indisponible"| SEC["Brouillon de secours (D-29)"]
  FIN -->|"bloquée par le filtre"| RP["Refus à texte fixe (D-73)"]
  RL --> CT
  SEC --> CT

  CT{"Commune et code postal, contrôlés par le serveur"}
  CT -->|"une seule commune"| OK["Vérifié ; valeur absente déduite"]
  CT -->|"plusieurs, département cité (D-78)"| OK
  CT -->|"plusieurs, sans indice"| AMB["Valeur entendue gardée, candidates jointes"]
  CT -->|"code et commune ne vont pas ensemble"| INC["Incohérent, rien n'est corrigé"]

  OK --> GF
  AMB --> GF
  INC --> GF
  GF{"Garde-fous et règles du serveur"}
  GF -->|"odeur de gaz"| GAZ["Urgence de sécurité, orientation en tête"]
  GF -->|"terme de santé"| SAN["Champ vidé"]
  GF -->|"valeur non dite"| INV["Valeur retirée"]
  GF -->|"urgence dite en clair (D-80)"| URG["Urgence relevée"]
  GF -->|"rien à signaler"| DOS
  GAZ --> DOS
  SAN --> DOS
  INV --> DOS
  URG --> DOS
  DOS{"Doute sur le dossier ?"}
  DOS -->|"non"| D1["Dossier prêt"]
  DOS -->|"oui : ambiguïté, incohérence, valeur retirée, indéterminé, secours"| D2["Dossier « à vérifier »"]
  D1 --> ART["L'artisan relit, corrige, valide et rappelle"]
  D2 --> ART
  MSG --> ART
```

## 3. Ce que les schémas ne montrent pas

- **Ce qui est journalisé.** À chaque étape, un événement sans contenu : le code du garde-fou, le
  `request_id`, la durée, le coût. La transcription est détruite après l'extraction
  (`production.md`, § 5).
- **Les seuils.** Le seuil de confiance de 0,7 est une hypothèse [H], non calibrée ; les autres
  bornes (six appels d'outils, délai par appel, une relance) viennent du paquet d'extraction
  versionné.
- **Le « à vérifier ».** Un dossier est « à vérifier » dès qu'un motif est levé ou qu'un champ clé
  présent reste incertain ; la liste exacte des motifs est dans `evaluateur.py` (`Motif`).
