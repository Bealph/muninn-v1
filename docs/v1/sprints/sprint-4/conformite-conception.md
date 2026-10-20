# Sprint 4 : conformité à la conception de la composante agentique

Étape 7 de la checklist, critère P1. Pour chaque engagement du dossier de conception V1
(`docs/v1/dossier-conception-v1.md`, § 3.1 à 3.4) : ce qui est annoncé, ce qui est livré au
20 octobre 2026, et la preuve. Les tests cités sont dans `tests/` ; ils tournent en CI sans
réseau. « Essai réel » renvoie aux essais avec le vrai modèle, en local, sur l'annexe A.

**Bilan** : 26 engagements ; 20 livrés et prouvés, 4 livrés en partie (affichage de la
provenance, SC-08, métrique bloquante de la borne, délai par appel d'outil), 2 prévus à l'étape 9
(base sans outils, métriques de trajectoire).

## 1. Choix (§ 3.1)

| Annoncé                                                                     | Livré                                                                           | Preuve                                                                                                                  |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| L'agent décide lui-même quand appeler un outil                              | Oui : boucle bornée, choix du modèle (`agent.py`)                               | `test_agent.py::test_outil_puis_reponse_et_communes_rendues` ; essai réel de l'étape 3 (`eval/agent/essai_etape3.json`) |
| Outils en lecture seule, par l'API des référentiels, sans accès à une base  | Oui : client HTTP seul, aucun accès à la base (D-18)                            | `outils.py` ; `test_agent.py::test_client_referentiels_appelle_l_api`                                                   |
| `chercher_communes` : égalité exacte après normalisation, avec département  | Oui                                                                             | `test_agent.py::test_outil_puis_reponse_et_communes_rendues` ; `test_referentiels.py`                                   |
| `chercher_terme_metier` : terme du lexique pour un mot et un métier         | Oui                                                                             | `test_agent.py::test_terme_metier_retenu`                                                                               |
| Rien du nom du client ne part vers un outil                                 | Oui : schéma des outils limité au nom de commune, au code postal, au mot        | `paquet_fichiers/outils.json` ; `test_extraction_contrat.py::test_outils_en_liste_fermee`                               |
| Politique, règle 1 : ne jamais remplacer une valeur entendue                | Oui                                                                             | `test_evaluateur.py::test_sc03_incoherence_signalee_sans_correction` ; essai réel, SC-03 3 sur 3                        |
| Règle 2 : remplir l'absent quand une seule valeur est possible, « déduit »  | Oui, par l'agent ou, à défaut, par le serveur (D-69)                            | `test_sc02_code_postal_deduit_par_l_agent`, `test_sc02_sans_outil_le_serveur_complete` ; essai réel, SC-02 3 sur 3      |
| Règle 3 : départager l'ambigu par un indice de la transcription             | Oui : indice cité par le modèle, vérifié par le serveur                         | `test_sc07_choix_de_l_agent_parmi_les_homonymes` ; essai réel, SC-07 3 sur 3                                            |
| Règle 4 : sans indice, ne pas choisir ; candidates jointes ; « à vérifier » | Oui, appliquée par une règle du serveur (D-69)                                  | `test_sc10_homonymes_jamais_choisis`, `test_choix_de_l_agent_sans_indice_refuse` ; essai réel, SC-10 3 sur 3            |
| Contrôle rejoué par le serveur ; seul ce contrôle fixe les statuts          | Oui                                                                             | `test_extraction_contrat.py::test_la_sortie_du_modele_ne_peut_pas_ecrire_un_champ_du_serveur`                           |
| Règle contre l'invention (commune, code postal)                             | Oui ; étendue à l'étape 7 au nom, au prénom, à la rue et au téléphone dit       | `test_invention_retiree`, `test_identite_non_dite_retiree`, `test_identite_dite_gardee`                                 |
| La console distingue « entendu » et « déduit par l'agent »                  | En partie : la provenance est dans l'enveloppe (D-67) ; l'affichage à l'étape 8 | `test_evaluateur.py::test_sc02_code_postal_deduit_par_l_agent` (provenance « déduit »)                                  |

## 2. Ce que l'agent décide (§ 3.2)

| Annoncé                                                                     | Livré                                                                     | Preuve                                                                       |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Les cinq décisions du tableau (SC-02, SC-07, SC-10, SC-03, SC-08)           | Quatre sur cinq : SC-08 échoue (le lexique ne mène pas à « chauffe-eau ») | Essai réel de l'étape 4, 3 exécutions : SC-08 0 sur 3 ; note `evaluateur.md` |
| Valeur de l'agent mesurée contre une base sans outils, mêmes scénarios      | Prévu à l'étape 9 (V-08)                                                  | Checklist, étape 9                                                           |
| Borne d'appels d'outils : zéro dépassement admis (bloquant)                 | La borne est appliquée ; la métrique bloquante en CI vient à l'étape 9    | `test_agent.py::test_borne_de_six_appels`                                    |
| Métriques de trajectoire observées (outil attendu, nombre, appels inutiles) | Prévu à l'étape 9 (harnais)                                               | Checklist, étape 9                                                           |

## 3. Alternatives écartées (§ 3.3)

Aucun écart : ni RAG, ni multi-agents, ni agent vocal temps réel, ni serveur MCP, ni mémoire de
l'agent dans le code du sprint 4. La qualification des appels (V-11) est une seule étape fermée,
sans outil : ce n'est pas un second agent.

## 4. Garde-fous (§ 3.4)

| Moment   | Annoncé                                                                                        | Livré                                                                                                                            | Preuve                                                                                                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Avant    | Consignes non modifiables ; transcription comme donnée ; outils en liste fermée                | Oui ; plus les règles d'entrée de D-63 (étape 5) et un jeton témoin (étape 7)                                                    | `test_bloc_de_donnees_delimite`, `test_outils_en_liste_fermee`, `test_agent.py::test_outil_inconnu_refuse_sans_arreter_l_agent` ; `test_entree.py` ; mesure `eval/garde_fous/mesure_entree.json` |
| Pendant  | Six appels d'outils au plus                                                                    | Oui                                                                                                                              | `test_agent.py::test_borne_de_six_appels`                                                                                                                                                        |
| Pendant  | Délai maximal par appel d'outil [H : 5 s]                                                      | En partie : le paramètre existe (`delai_outil_s`), le client HTTP prend un délai ; le branchement dans l'API se fait à l'étape 8 | `paquet_fichiers/parametres.json` ; `outils.py`                                                                                                                                                  |
| Après    | Validation par le schéma 1.1 ; une relance, puis brouillon partiel à vérifier                  | Oui                                                                                                                              | `test_relance_unique_puis_reponse_conforme`, `test_deux_sorties_hors_schema_donnent_un_brouillon_partiel`, `test_brouillon_partiel_apres_relance`                                                |
| Après    | LLM indisponible : brouillon de secours, à vérifier (D-29)                                     | Oui                                                                                                                              | `test_evaluateur.py::test_brouillon_de_secours_d29` ; `test_agent.py::test_echecs_du_fournisseur`                                                                                                |
| Après    | Règle « gaz » par la liste fermée : urgence `securite`, aucun rendez-vous, orientation en tête | Oui ; aussi dans la qualification, toutes catégories (Q-07)                                                                      | `test_sc04_regle_gaz` ; `test_qualification.py::test_gaz_dans_un_message` ; essais réels, SC-04 et SC-Q7 3 sur 3                                                                                 |
| Après    | Règle contre l'invention                                                                       | Oui (voir § 1)                                                                                                                   | `test_invention_retiree`                                                                                                                                                                         |
| Après    | Règle « santé » : tout champ avec un terme de la liste fermée est retiré                       | Oui ; aussi dans le message de qualification                                                                                     | `test_sc05_regle_sante` ; `test_qualification.py::test_message_ne_garde_que_ce_qui_est_dit` ; essai réel, SC-05 3 sur 3                                                                          |
| Après    | Statuts, provenance, versions, dates de destruction écrits par le serveur                      | Oui                                                                                                                              | `test_dossier_conforme_et_forme_publiee`, `test_la_sortie_du_modele_ne_peut_pas_ecrire_un_champ_du_serveur`                                                                                      |
| Toujours | Transcription détruite après extraction ; aucune transcription dans les journaux               | Oui : aucune référence gardée, date de destruction posée ; journaux sans contenu                                                 | `test_extraire_dossier_bout_en_bout_et_journal_sans_contenu`, `test_journaux_sans_contenu`, `test_journal_sans_contenu` (entrée, qualification)                                                  |

## 5. Ajouts du sprint 4, hors § 3.4

| Ajout                                                                                          | Décision   | Preuve                                                                                 |
| ---------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------- |
| Garde-fous d'entrée : refus motivé, nettoyage des invisibles, motifs d'injection en annotation | D-63       | `test_entree.py` ; `garde-fous-entree.md`                                              |
| Modération par le filtre standard d'Azure ; blocage : refus poli à texte fixe                  | D-70       | `test_sortie.py::test_refus_a_texte_fixe` ; `garde-fous-entree.md`                     |
| Fuite : jeton témoin et motifs de secret, texte vidé, dossier « à vérifier »                   | Étape 7    | `test_sortie.py` ; `test_fuite_du_temoin_retiree_et_signalee`                          |
| Hors rôle : liens et balisage retirés des textes libres                                        | Étape 7    | `test_sortie.py::test_hors_role_sans_lien_ni_balisage`                                 |
| Refus et garde-fous journalisés avec `request_id`, sans contenu                                | Étape 7    | `test_refus_journalise_avec_request_id_sans_contenu`, `test_message_qui_fuit_remplace` |
| Qualification des appels avant l'extraction                                                    | D-48, V-11 | `test_qualification.py` ; `qualification.md`                                           |

## 6. Écarts à suivre

- **SC-08** : l'objet n'atteint pas la liste L-08 (étape 9 ou lexique, après la V1).
- **Délai par appel d'outil** : à brancher sur `delai_outil_s` dans l'API (étape 8).
- **Affichage de la provenance** et échappement de tout texte à l'écran : écran « Agent » (étape 8).
- **Base sans outils et métriques de trajectoire** : harnais de l'étape 9.
