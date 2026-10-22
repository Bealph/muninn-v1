# Sprint 4 : synthèse pour l'évaluation par le pair

Où trouver le résultat de chaque point du travail attendu, et ce qu'il dit, en une page par point.
Chemins relatifs à `docs/v1/sprints/sprint-4/`, sauf mention contraire. État au 21 octobre 2026,
production `81795dd`. Déroulé de la séance : `demonstration.md`.

## Vue d'ensemble

| N° | Travail attendu                          | Résultat en une ligne                                                                                       | Document d'entrée          | Critère du pair |
| -- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------- | --------------- |
| 1  | Composante agentique conforme au dossier | Agent outillé et ancré, en production ; V-08 117/120 (97,5 %) ; chaque promesse du dossier tracée           | `conformite-conception.md` | P1              |
| 2  | Garde-fous d'entrée                      | Trois couches ; 20 sur 20 phrases hostiles détectées, 0 sur 20 faux positifs ; 11 sur 11 en production      | `garde-fous-entree.md`     | P2, P3          |
| 3  | Garde-fous de sortie                     | Fuite, secrets, hors rôle, invention, gaz, santé ; refus à texte fixe, journalisé sans contenu              | `garde-fous-sortie.md`     | P2              |
| 4  | Si la composante agit                    | Aucune action d'écriture ; outils en liste fermée, borne de 6 appels, refus journalisé ; joué en production | `api-ecran-agent.md`, § 2  | P4              |
| 5  | Contrat personnel                        | CA-1 à CA-4 et CA-7 tenus sur Azure ; CA-5, CA-6 (partie 2), CA-8 au sprint 5 ; avenants écrits             | `contrat-personnel.md`     | P5              |
| 6  | Préparer le sprint 5                     | 17 signaux avec source, seuil, alerte et valeur de référence ; reprises du sprint 5                         | `signaux-sprint-5.md`      | sans objet      |

Vue de synthèse de tout le sprint : `livrable-composante-agentique.md` (ce qui tourne, garde-fous et
preuves, mesures, limites) ; bilan : `compte-rendu.md`.

## 1. Développer la composante agentique conformément au dossier de conception

**Résultat.** La composante gelée dans le dossier V1 (§ 3, D-37) est livrée et tourne en
production. Un appel est d'abord qualifié (V-11). Pour un dossier, l'agent lit la transcription,
produit un `DossierDraft` 1.1 et décide seul d'appeler deux outils en lecture seule
(`chercher_communes`, `chercher_terme_metier`), dans une boucle bornée sans framework (V-07). Le
serveur rejoue ensuite les contrôles et il est seul à écrire statuts et provenance. Les écarts au
dossier sont motivés par des décisions écrites : correspondance faite par le serveur (D-69),
départage par un département cité (D-78), urgence dite (D-80). Évaluation V-08 : 117/120,
IC 95 % 92,9 à 99,1 % ; une PR qui dégrade l'agent est bloquée par la CI (D-79).

**Point de vigilance, à dire avant qu'on le demande.** Sur ce jeu, l'agent fait aussi bien sans ses
outils (117/120 dans les deux cas), parce que le serveur couvre ce qu'une règle sait faire. Cadrage
écrit : `evaluation.md`, § 4 sexies.

| Quoi                                    | Où                                                                |
| --------------------------------------- | ----------------------------------------------------------------- |
| Annoncé, livré, preuve, ligne par ligne | `conformite-conception.md`, § 1 à 4 ; écarts : § 6                |
| La boucle de l'agent et ses bornes      | `agent.md`, § 1 ; code `src/muninn/extraction/agent.py`           |
| L'outil attendu est-il appelé ?         | `agent.md`, § 2 et § 4 (12 sur 12 le 21 octobre)                  |
| Ce que fixe le serveur après l'agent    | `evaluateur.md`, § 1 ; code `src/muninn/extraction/evaluateur.py` |
| Qualification des appels                | `qualification.md`, § 1 ; code `src/muninn/qualification/`        |
| Évaluation chiffrée et vigie            | `evaluation.md`, § 2, § 4 quater, § 4 quinquies                   |
| Traces sans contenu (Langfuse)          | `langfuse.md`, § 1 et § 5                                         |
| Décisions                               | `docs/decisions.md`, D-37, D-62 à D-80                            |
| **En direct**                           | Écran « Agent », SC-07 (« Montreuil, dans le 9-3 »)               |

## 2. Poser les garde-fous d'entrée : contenus hostiles, injection, hors-périmètre

**Résultat.** Trois couches, sans appel au LLM en plus (D-63) :

1. **Règles** : taille (8 000 caractères au plus), caractères de contrôle, motifs d'injection
   connus (`injection-2026.10.2`). Une entrée vide ou sans contenu exploitable est refusée à texte
   fixe.
2. **Modération** : filtre de contenu personnalisé d'Azure (`muninn-annotation-injection`, D-75).
   Le détournement est annoté sans bloquer ; la nocivité est bloquée.
3. **Hors-périmètre, par le LLM de qualification** : un appel hors du métier devient un message,
   jamais un dossier (CA-7, 24 sur 24 en production).

La transcription est toujours traitée comme une donnée, jamais comme une consigne. Un dossier
suspect sort neutralisé (« détournement suspecté », « à vérifier »).

**Mesure.** Le jeu a été figé avant la mesure :

- détection : 20 sur 20 phrases hostiles, IC 95 % 83,9 à 100 % ;
- faux positifs : 0 sur 20 phrases légitimes, IC 95 % 0 à 16,1 %.

En production depuis l'écran, 11 cas sur 11 sont tenus.

| Quoi                                          | Où                                                                           |
| --------------------------------------------- | ---------------------------------------------------------------------------- |
| Les trois couches et les règles               | `garde-fous-entree.md`, § 1 et § 2 ; code `src/muninn/extraction/entree.py`  |
| La mesure (détection, faux positifs)          | `garde-fous-entree.md`, § 3 ; jeu `eval/garde_fous/jeu_entree.json`          |
| Le filtre d'Azure (D-70, puis D-75)           | `garde-fous-entree.md`, § 4 et § 5 ; `api-ecran-agent.md`, § 4               |
| Hors-périmètre par la qualification           | `qualification.md`, § 1 ; `production.md`, § 3 (CA-7)                        |
| Preuve en production et journaux sans contenu | `production.md`, § 4 et § 5 ; `preuves/etape-11-hostiles.json`               |
| Tests                                         | `tests/test_entree.py`, `tests/test_qualification.py`                        |
| **En direct**                                 | Écran « Agent », mode texte libre : le texte hostile du pair ; Log Analytics |

## 3. Poser les garde-fous de sortie : fuite, secrets, hors rôle ; refus poli, journalisé

**Résultat.** Le serveur vérifie toute sortie du modèle, dossier comme message :

- **fuite** : jeton témoin des consignes, 9 motifs de secret (clés d'API, JWT, clé privée,
  `AccountKey=`, mot de passe…) ; le texte en cause est vidé ;
- **hors rôle** : schéma fermé en sortie structurée stricte ; liens et balisage retirés ;
- **invention** : une commune, un code postal, un nom, une rue ou un téléphone absents de la
  transcription sont retirés ;
- **règles métier** : « gaz » (urgence de sécurité, orientation en tête) et « santé » (aucune
  donnée médicale gardée) ;
- **refus poli** : un blocage du filtre donne un texte fixe, jamais un fragment de l'entrée.

Chaque garde-fou déclenché est journalisé par son code et le `request_id`, sans contenu.

**Preuve.** En production : aucune fuite sur 11 cas hostiles, aucun terme de santé sur 15 exécutions
de SC-05 (CA-4), orientation gaz 3 sur 3 (CA-3). Sur 1 509 lignes de journal, aucune ne contient de
donnée d'appel.

| Quoi                             | Où                                                                                        |
| -------------------------------- | ----------------------------------------------------------------------------------------- |
| Les garde-fous et leur effet     | `garde-fous-sortie.md`, § 1 ; code `src/muninn/extraction/sortie.py`                      |
| Vérification avec le vrai modèle | `garde-fous-sortie.md`, § 2                                                               |
| Revue de sécurité et corrections | `garde-fous-sortie.md`, § 4                                                               |
| Texte fixe du refus              | `MESSAGE_REFUS_CONTENU`, `src/muninn/extraction/evaluateur.py`                            |
| Journalisation sans contenu      | `production.md`, § 5 ; `langfuse.md`, § 5                                                 |
| Tests                            | `tests/test_sortie.py` (fuite, hors rôle, refus à texte fixe), `tests/test_evaluateur.py` |
| **En direct**                    | Phrase hostile qui demande la consigne ; SC-04 (gaz) ; SC-05 (« je suis diabétique »)     |

## 4. Si la composante agit : confirmation sur les actions sensibles, périmètre d'accès

**Résultat.** L'agent n'a aucune action d'écriture : la confirmation sur action sensible est sans
objet, et c'est argumenté.

- **Accès** : deux outils en lecture seule, en liste fermée. Ils passent par l'API des
  référentiels, en lecture seule et SQL paramétré (sprint 3). Aucun accès direct à une base, aucun
  MCP.
- **Périmètre appliqué par le code** :
  - un outil inconnu est refusé (`outil_inconnu`) et l'agent continue ;
  - six appels d'outils au plus ;
  - un délai par appel.
- **Journalisation** : chaque appel est journalisé, `agent.outil nom=… statut=…`, sans les arguments.
- **Validation humaine** : la seule action qui changera un état, la validation du dossier, sera
  faite par un humain (CA-5, sprint 5).

**Preuve.** Le scénario `P4-perimetre` remplace le modèle par un modèle simulé qui obéit à
l'injection. Joué en production le 21 octobre 2026 :

- l'outil `lire_base` est refusé (`outil_inconnu`) ;
- la borne de 6 appels est atteinte ;
- le verdict est conforme.

| Quoi                           | Où                                                                                                                                                              |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Non-applicabilité et périmètre | `conformite-conception.md`, § 4 ; `checklist.md`, ligne « Si la composante agit »                                                                               |
| Outils en liste fermée         | code `src/muninn/extraction/outils.py`                                                                                                                          |
| Le scénario P4 et l'écran      | `api-ecran-agent.md`, § 2                                                                                                                                       |
| Tests                          | `tests/test_agent.py` (outil inconnu, borne de six appels) ; `tests/test_api_agent.py::test_perimetre_p4_outil_refuse_et_borne` ; `tests/test_console_agent.py` |
| **En direct**                  | Écran « Agent », scénario `P4-perimetre`                                                                                                                        |

## 5. Dérouler le contrat personnel

**Résultat.** Chaque critère a son statut, sa preuve sur Azure (3 exécutions sur 3) et, s'il y a
lieu, son avenant écrit.

| Critère | Statut   | Preuve ou suite                                             | Avenant    |
| ------- | -------- | ----------------------------------------------------------- | ---------- |
| CA-1    | Tenu     | 3/3 après la règle D-80 (urgence dite)                      | Aucun      |
| CA-2    | Tenu     | 24/24 sur 4 séries                                          | D-69, D-78 |
| CA-3    | Tenu     | Gaz : 3/3, puis 3/3 sur la révision de D-80                 | Aucun      |
| CA-4    | Tenu     | Injection et santé : 15/15                                  | Aucun      |
| CA-5    | En cours | Correction et validation : sprint 5 (V-09)                  | Aucun      |
| CA-6    | En cours | Partie 1 tenue (PR dégradée bloquée) ; partie 2 au sprint 5 | D-79       |
| CA-7    | Tenu     | Qualification : 24/24                                       | Aucun      |
| CA-8    | En cours | Voix : sprint 5 (V-12)                                      | D-74       |

**À dire.** Un écart sur CA-1 (urgence, 1 fois sur 27) a été diagnostiqué : c'était une variation
du modèle. Il a été traité par une règle du serveur (D-80), sans affaiblir le critère. Aucun
critère n'a été affaibli pour passer.

| Quoi                           | Où                                                                                              |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| État critère par critère       | `contrat-personnel.md`, § 1 et § 2                                                              |
| Avenants en vigueur            | `contrat-personnel.md`, § 3 ; `docs/decisions.md`                                               |
| Preuves (sans contenu)         | `preuves/etape-11-criteres.json`, `preuves/etape-12-ca-1-2-4.json`, `preuves/etape-12-d80.json` |
| Script qui rejoue les critères | `eval/production/verifier_criteres.py`                                                          |
| Critères d'origine             | `docs/v1/dossier-conception-v1.md`, § 6                                                         |
| **En direct**                  | SC-01 et SC-04 depuis l'écran ; puis le contrat, § 1                                            |

## 6. Préparer le sprint 5 : signaux à surveiller

**Résultat.** 17 signaux, chacun avec sa source dans les journaux, son seuil (objectifs de service
de la phase 2), l'alerte qui le porte et sa valeur de référence mesurée en production le
21 octobre 2026.

| Signal (extrait)           | Référence                                  | Seuil              | Alerte         |
| -------------------------- | ------------------------------------------ | ------------------ | -------------- |
| Latence de l'extraction    | p50 2,7 s ; p95 3,4 s                      | p50 6 s ; p95 20 s | AL-16          |
| Coût d'une extraction      | 0,0037 € en moyenne                        | 0,01 €             | AL-15          |
| Refus du filtre de contenu | 0 sur 102                                  | 5 % [H]            | non disponible |
| Erreurs de la composante   | 0 brouillon de secours, 0 relance, 0 borne | 5 % ; 2 %          | AL-04, AL-09   |
| Part « à vérifier »        | 43 %, biaisé (trafic de vérification)      | 20 %               | AL-01          |

**À dire.** La fenêtre de référence est courte, et son trafic n'est fait que de cas choisis pour
éprouver l'agent. La part « à vérifier » de 43 % ne dit donc rien du produit. Proposition pour le
sprint 5 :

- AL-01 calculée et affichée par l'application ;
- latence et coût dans l'écran Qualité ;
- une alerte Azure Monitor sur les pannes du fournisseur.

| Quoi                             | Où                                                      |
| -------------------------------- | ------------------------------------------------------- |
| Tableau complet des signaux      | `signaux-sprint-5.md`, § 2                              |
| Ce que le sprint 5 doit en faire | `signaux-sprint-5.md`, § 3                              |
| Reprises du sprint 5             | `signaux-sprint-5.md`, § 4                              |
| Seuils et alertes d'origine      | `docs/conception/industrialisation/03-observabilite.md` |

## Questions probables, et où est la réponse

| Question                                                   | Réponse courte                                                                    | Où                                       |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------- |
| Pourquoi un agent, si les outils n'apportent rien ici ?    | Le serveur couvre les cas réglables ; l'agent garde les indices libres            | `evaluation.md`, § 4 sexies              |
| Vos phrases hostiles viennent du même jeu que vos règles ? | Oui : 20 sur 20 est une borne haute ; la borne basse (84 %) est la valeur retenue | `garde-fous-entree.md`, § 3              |
| Que voit-on dans les journaux ?                            | Le code du garde-fou et le `request_id`, jamais un mot de l'appel                 | `production.md`, § 5                     |
| Pourquoi des avenants ?                                    | Chacun est une décision écrite, motivée par une mesure                            | `contrat-personnel.md`, § 3              |
| Des incidents ?                                            | Deux, de livraison, résolus et testés                                             | `incidents/INC-05…`, `incidents/INC-06…` |
| 3 exécutions sur 3, est-ce un taux ?                       | Non : une preuve de stabilité ; les taux sont ceux de V-08, avec leur intervalle  | `evaluation.md`, § 4                     |
