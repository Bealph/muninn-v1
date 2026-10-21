# Sprint 4 : l'agent d'extraction et sa boucle bornée

Étape 3 de la checklist (V-07 ; C8, C9). Code : `src/muninn/extraction/agent.py` (boucle),
`src/muninn/extraction/outils.py` (outils) ; tests : `tests/test_agent.py` ; essai réel :
`eval/agent/essai_etape3.py`.

## 1. Ce que fait la boucle

| Règle                               | Mise en œuvre                                                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Le code orchestre (A-1)             | Boucle écrite dans le projet, sans framework : le modèle décide seulement quand appeler un outil                                                |
| Deux outils, en liste fermée        | `chercher_communes`, `chercher_terme_metier` ; un autre nom est refusé, l'agent continue                                                        |
| Aucun accès aux bases (A-6)         | Les outils appellent l'API des référentiels ; ne partent que le nom de commune et le code postal, ou le mot et le métier                        |
| Six appels d'outils au plus         | Au-delà, l'appel n'est pas exécuté ; le modèle doit conclure sans outil                                                                         |
| Délais                              | Par appel au modèle (30 s) et par appel d'outil (5 s) ; un outil indisponible rend une erreur au modèle, sans arrêter l'agent                   |
| Une relance unique                  | Sortie hors schéma : une relance qui cite les chemins des champs fautifs, jamais leurs valeurs ; puis brouillon partiel (`partial_after_retry`) |
| Modèle indisponible                 | Délai dépassé ou panne : brouillon de secours (`fallback_no_llm`, D-29)                                                                         |
| Filtre de contenu                   | Refus : `content_refused`, jamais confondu avec une panne ; détournement annoté remonté (D-65)                                                  |
| Correction bénigne avant validation | Une valeur nulle prend une confiance de 0 et, pour le téléphone, une origine nulle ; aucune valeur n'est jamais créée ni modifiée               |
| Trace, sans contenu (R3, R4)        | Outils appelés et leur statut, étapes, tentatives, borne, jetons, coût, durée ; communes et termes rendus gardés pour l'évaluateur (étape 4)    |

## 2. Essai avec le vrai modèle

**Le 19 octobre 2026**, gpt-5.4-mini (version 2026-03-17), paquet `extraction-2026.10.1`, outils sur
l'API des référentiels de production ; scénarios de l'annexe A, transcriptions du banc T-06
(données synthétiques) ; 3 exécutions par scénario. Ce n'est pas l'évaluation de V-08 (étape 9).

| Scénario                         | Outil attendu appelé | Valeurs attendues                    | Ce qui se passe                                                                             |
| -------------------------------- | -------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------- |
| SC-02, Vincennes sans code       | 1 sur 3              | 1 sur 3                              | Deux fois, le modèle n'appelle pas l'outil et laisse le code postal vide : il n'invente pas |
| SC-07, Montreuil « dans le 9-3 » | 3 sur 3              | 3 sur 3 (Montreuil, 93100)           | Conforme                                                                                    |
| SC-08, « cumulus »               | 3 sur 3              | sans objet ici                       | Conforme ; il appelle aussi `chercher_communes`                                             |
| SC-10, Montreuil sans indice     | 2 sur 3              | 0 sur 3 (commune attendue vide)      | Il garde « Montreuil » au lieu de laisser la commune vide (règle 4 de la politique)         |
| **Total**                        | **9 sur 12**         | **7 sur 12** (SC-08 compté conforme) | 12 extractions complètes ; 2,2 s en médiane ; 0,045 € au total                              |

Un premier passage avait donné 9 brouillons partiels sur 12 : le modèle mettait une origine au
téléphone quand aucun numéro n'était connu. Corrigé par la consigne et par la correction bénigne
de la section 1 ; les mesures ci-dessus sont celles du second passage. Coût des deux passages et
du diagnostic : environ 0,13 €, dans le plafond du sprint (D-64).

## 3. Ce qui en découle

- **SC-02 et SC-10 sont les écarts déjà vus au banc T-06.** La consigne ne sera pas retouchée sur
  les scénarios de l'annexe A, qui sont les oracles du contrat : elle le sera sur la partition de
  développement du jeu d'évaluation (étape 9), puis mesurée sur la partition de test.
- **SC-10 pose une question de conception à l'étape 4.** La commune « Montreuil » est entendue ;
  la règle 1 interdit de remplacer une valeur entendue, la règle 4 demande de ne pas choisir sans
  indice, et CA-2 attend une commune vide avec les trois candidates jointes. L'évaluateur du
  serveur devra trancher : garder la valeur entendue en la marquant ambiguë, ou la vider. À
  soumettre au porteur avant d'écrire l'étape 4.
- **La règle contre l'invention reste la parade de SC-02** : sans outil, aucun code postal n'est
  inventé ; le dossier est « à vérifier » (étape 4).

## 4. Suite : ce que sont devenus les écarts

- **SC-10** : tranché par le porteur (D-69). La commune entendue est gardée, les candidates sont
  jointes, le dossier est « à vérifier » ; avenant de CA-2.
- **SC-02 et SC-07** : la correspondance faite par le serveur (D-69, D-77, D-78) remplit le code
  postal sans dépendre de l'appel d'outil ; la trace d'un appel à `chercher_communes` n'est plus
  exigée par CA-2 (D-78). La consigne a été renforcée sur la partition de développement
  seulement (D11, consigne `extraction-2026.10.3`, D-78).

**Nouvel essai, le 21 octobre 2026**, même protocole, paquet `extraction-2026.10.3`, attente de
SC-10 mise à jour selon D-69 (commune « Montreuil » gardée, code postal vide). Résultat :
`eval/agent/essai_etape3-2026-10-21.json`.

| Scénario                         | Outil attendu appelé | Valeurs attendues | Ce qui se passe                                     |
| -------------------------------- | -------------------- | ----------------- | --------------------------------------------------- |
| SC-02, Vincennes sans code       | 3 sur 3              | 3 sur 3           | Conforme                                            |
| SC-07, Montreuil « dans le 9-3 » | 3 sur 3              | 3 sur 3           | Conforme                                            |
| SC-08, « cumulus »               | 3 sur 3              | sans objet ici    | Conforme ; il appelle aussi `chercher_communes`     |
| SC-10, Montreuil sans indice     | 3 sur 3              | 3 sur 3           | Conforme ; « Montreuil » gardé, code postal vide    |
| **Total**                        | **12 sur 12**        | **12 sur 12**     | 12 extractions complètes ; 2,2 à 3,5 s ; 0,053 €    |

Portée : ces scénarios n'ont pas servi à régler la consigne (partition de développement
seulement), la mesure est donc honnête ; mais 12 exécutions ne font pas un taux. Pour SC-08, seul
l'appel de `chercher_terme_metier` est mesuré ici ; l'objet attendu (liste L-08) reste un écart
connu du lexique (`conformite-conception.md`, § 2).
