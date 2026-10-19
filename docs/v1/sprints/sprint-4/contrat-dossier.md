# Sprint 4 : le contrat `DossierDraft` 1.1 de la V1 et le paquet d'extraction

Étape 1 de la checklist. Référence : contrat d'API de la phase 2
(`docs/conception/industrialisation/04-contrat-api.md`, § 3) ; dossier V1, § 3 et V-07
(« contrat `DossierDraft` 1.1, sous-ensemble utile »).

## 1. Ce que contient le code

| Élément                 | Fichier                                            | Rôle                                                                                                     |
| ----------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Brouillon complet       | `src/muninn/extraction/contrat.py`, `DossierDraft` | Contrat 1.1, sous-ensemble V1 ; champs inconnus refusés à tous les niveaux                               |
| Sortie du modèle        | `src/muninn/extraction/contrat.py`, `SortieLLM`    | Contenu extrait et confiances brutes seulement : aucun champ du serveur (§ 3.2, M-04, M-05)              |
| Règles hors JSON Schema | `src/muninn/extraction/regles.py`                  | Règles 1, 2, 4 et 5 ; `champs_manquants` recalculé par le serveur, pas repris du modèle                  |
| Paquet d'extraction     | `src/muninn/extraction/paquet_fichiers/`           | Consigne système, gabarit du bloc de données, schéma de sortie, deux outils, paramètres                  |
| Chargement et empreinte | `src/muninn/extraction/paquet.py`                  | Lecture du paquet ; SHA-256 sur une liste fermée de chemins (paquet, extraction, fournisseur, `uv.lock`) |
| Tests                   | `tests/test_extraction_contrat.py`                 | 30 tests                                                                                                 |

## 2. Le sous-ensemble de la V1, et pourquoi

| Partie du contrat 1.1                    | En V1                                                          | Raison                                                                   |
| ---------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `source`                                 | `missed_call` seulement                                        | Débrief et dépenses hors V1 (dossier V1, § 2.3)                          |
| `depense`                                | Toujours nul                                                   | Règle 9 pour un appel manqué                                             |
| `contact` (appel pour un tiers, D-25)    | Absent                                                         | Champ facultatif ; hors KPI tant que son test n'est pas écrit (règle 12) |
| `demande.rdv_propose`                    | Toujours nul, absent du schéma demandé au modèle               | Rendez-vous hors V1 (§ 2.3) : le modèle ne peut pas en proposer          |
| `provenance.input_mode`                  | `text` ou `simulated`                                          | Aucun audio ni image côté serveur ; voix simulée au sprint 5 (V-12)      |
| `destruction`                            | `transcript_destroyed_at` seul renseigné                       | Règle 7 pour une entrée écrite ou simulée                                |
| `checks["client.telephone"]`             | Toujours `not_checked` (`no_value` ou `not_applicable`)        | Contrôle du numéro (ARCEP) hors V1 (§ 2.3)                               |
| `checks` de la commune et du code postal | Complets : statut, motif, référentiel, code INSEE, valeur dite | CA-1 à CA-5                                                              |
| `FieldPath`                              | Liste du contrat sans `depense.*` ni `contact.*`               | Une seule liste, testée par égalité avec le schéma du modèle             |

## 3. Ce que la V1 ajoute autour du contrat, sans le modifier

Le dossier V1 exige trois informations que le contrat 1.1 ne porte pas :

- la provenance **par champ** de la commune et du code postal, « entendu » ou « déduit par l'agent »
  (§ 3.1, CA-2) ; le champ `provenance` du contrat est celui de l'extraction entière ;
- les communes **candidates** jointes au dossier quand l'agent ne choisit pas (SC-10, CA-2) ;
- le dossier marqué « à vérifier » pour une incohérence ou une commune ambiguë (SC-03, SC-10), alors
  que la règle 6 réserve `needs_review` à une extraction incomplète.

Elles iront dans une enveloppe écrite par le serveur, à côté du brouillon, comme le contrat le
prévoit déjà pour les mesures d'exécution (`{draft, run}`, `RunMetrics`, § 4). Le brouillon reste
conforme au contrat 1.1 et `needs_review` garde le sens de la règle 6. L'enveloppe est construite
à l'étape 4 (évaluateur du serveur).

Décision D-67 (accordée par le porteur le 16 octobre 2026), avec trois conditions :

1. l'enveloppe ne porte aucune valeur du client : seulement des chemins de champ, des
   énumérations et des données publiques des référentiels (codes INSEE, noms de communes) ;
2. elle n'est ni stockée, ni journalisée (R1, R3, R4) ;
3. le contrat 1.1 n'est pas modifié ; hors V1, ces informations relèveraient d'une version
   suivante du contrat.

## 4. Le paquet d'extraction

| Fichier              | Contenu                                                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `consigne.md`        | Politique de l'agent (D-37, règles 1 à 4), transcription traitée comme une donnée, règles des champs, aucune donnée de santé, jeton témoin |
| `gabarit.txt`        | Date, métier, numéro présenté, puis la transcription entre balises ; les balises imitées dans la transcription sont retirées               |
| `schema_sortie.json` | Schéma de `SortieLLM`, mode strict ; aligné sur le modèle Pydantic par un test                                                             |
| `outils.json`        | `chercher_communes` et `chercher_terme_metier`, mode strict                                                                                |
| `parametres.json`    | `extraction-2026.10.1`, modèle `gpt-5.4-mini` version `2026-03-17`, six appels d'outils au plus, une relance, appels d'outils en série     |

Repris du banc T-06 : la politique, les deux outils, les appels d'outils en série et la limite de
4 000 jetons de sortie. Aucune température n'est transmise, comme au banc ; le comportement du
modèle sur ce point est vérifié dans la documentation à l'étape 2.

## 5. Ce qui reste à vérifier

- Les mots-clés du schéma acceptés par la sortie structurée stricte : vérifiés à l'étape 2 ;
  motifs et bornes retirés du schéma (`fournisseur-llm.md`, § 3).
- Les seuils de 0,7 et de 0,6 restent des hypothèses du contrat ([H : ADR-08]).
