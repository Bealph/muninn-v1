# Contrat personnel : état critère par critère

> État au 21 octobre 2026, gardé pour l'historique. État en vigueur : `../sprint-5/contrat-personnel.md`
> (fin du sprint 5, 26 octobre 2026).

Étape 12 de la checklist du sprint 4 (critère du pair P5). État au **21 octobre 2026**, révision de
production `ca-muninn-api-prod--0000066` (`git_sha` 4151621, même code que 8e2dd5d) ; CA-1, CA-3 et
CA-4 vérifiés de nouveau sur la révision qui porte D-80 (`git_sha` f0efe3e).
Critères : dossier V1, § 6 (CA-1 à CA-6, le contrat) et critères complémentaires de la v1.5
(CA-7, CA-8, hors contrat). Condition commune : révision active d'Azure, modèle retenu
(gpt-5.4-mini), 3 exécutions sur 3.

Statuts : **tenu** (vérifié sur Azure dans sa forme en vigueur, chaque série à 3 sur 3) ;
**en cours** (pas encore vérifiable, sprint prévu, ou écart constaté et en traitement) ; **avenant** (forme modifiée par une décision écrite, indiqué à côté
du statut).

## 1. Synthèse

| Critère | Intitulé                        | Statut   | Avenant         | Preuve sur Azure                                 | Reste à faire                                  |
| ------- | ------------------------------- | -------- | --------------- | ------------------------------------------------ | ---------------------------------------------- |
| CA-1    | Le parcours promis              | Tenu     | Aucun           | 3/3 sur la règle D-80 ; avant : 26/27            | Rejouer depuis l'écran au sprint 5             |
| CA-2    | Les décisions de l'agent        | Tenu     | D-69, D-78      | 24/24 sur 4 séries (SC-07, SC-10)                | Aucun                                          |
| CA-3    | Le garde-fou de sécurité        | Tenu     | Aucun           | 3/3 (SC-04)                                      | Aucun                                          |
| CA-4    | La résistance à la manipulation | Tenu     | Aucun           | 12/12 sur 4 séries (SC-05)                       | Aucun                                          |
| CA-5    | La correction et la validation  | En cours | Aucun           | Non disponible (correction et validation : V-09) | Sprint 5, V-09                                 |
| CA-6    | La vigie                        | En cours | D-79 (partie 1) | Partie 1 tenue : PR n° 147 bloquée               | Partie 2 : retour arrière puis SC-01, sprint 5 |
| CA-7    | La qualification des appels     | Tenu     | Aucun           | 24/24 (SC-Q1 à SC-Q8)                            | Aucun                                          |
| CA-8    | La voix                         | En cours | D-74            | Non disponible (voix : V-12)                     | Sprint 5, V-12                                 |

Bilan du contrat (CA-1 à CA-6) : 4 tenus sur 6 (CA-1 avec la règle D-80, CA-2 avec avenant,
CA-3, CA-4) ; 2 en cours : CA-5 et CA-6 (partie 1 démontrée selon l'avenant D-79). Critères complémentaires : CA-7 tenu, CA-8 en cours avec avenant.
C'est un contrat « en passe d'être tenu », comme le demande le sprint 4 : CA-5, la partie 2 de
CA-6 et CA-8 dépendent d'éléments du sprint 5 (V-09, V-10, V-12), selon le plan du dossier V1
(§ 7). Aucun écart ne reste ouvert sur ce que le sprint 4 livre.

## 2. Détail par critère

### CA-1. Le parcours promis

- **Forme en vigueur** : dossier V1, § 6, sans changement.
- **Mesures** : SC-01 joué sur l'API de production (`POST /v1/demo/runs`, celle qu'appelle la
  console), 4 séries de 3 le 21 octobre 2026, sur la même révision :

  | Début (UTC) | Contrôles                    | Conformes | Durée côté client (s) |
  | ----------- | ---------------------------- | --------- | --------------------- |
  | 09:57       | Vérification du serveur      | 3/3       | 3,2 à 12,1            |
  | 10:00       | Vérification du serveur      | 3/3       | 3,1 à 4,2             |
  | 10:01       | Serveur et compléments (nom) | 3/3       | 3,0 à 3,7             |
  | 10:04       | Serveur et compléments (nom) | 2/3       | 2,7 à 3,4             |

  Total : 11/12. L'écart unique porte sur l'urgence (attendue `urgent` ; « c'est urgent, ça
  inonde la cuisine ») ; toutes les autres valeurs, les statuts, la provenance et la durée
  (30 s au plus) sont conformes à chaque exécution. Les deux premières séries n'ont pas de
  fichier de preuve : la première a été remplacée par une version du script qui contrôle aussi
  le nom ; la deuxième a tourné par erreur sans les compléments. Seule la dernière série est
  conservée, `preuves/etape-12-ca-1-2-4.json`, écart compris. Heures lues dans Log Analytics.
  Deux appels isolés (SC-05, SC-10) ont aussi servi à lire la forme de la réponse, sans verdict.
- **Statut avant D-80** : en cours. Le critère demande 3 sur 3 ; une série à 2 sur 3 suffit à ne pas le
  déclarer tenu, et retenir une autre série serait trier les résultats. Les rapports V-08 ne
  montrent pas cet écart (SC-01 conforme à chaque campagne, hors la PR dégradée n° 147).
- **Diagnostic** (21 octobre 2026, 15 exécutions de plus, valeur énumérée seule) : 15 fois
  `urgent` ; sur la journée, 26 sur 27 (96,3 %, IC 95 % : 81,7 à 99,3 %). L'exécution en écart
  est normale (statut `complete`, une tentative, outil appelé, aucun repli, aucun garde-fou) :
  c'est une variation du modèle. À ce taux, une série de 3 échoue environ une fois sur 9.
- **Traitement décidé** : D-80, règle du serveur « urgence dite » (choix du porteur parmi trois :
  consigne, règle du serveur, avenant) ; tests sur les négations, les questions, les
  conditions, les paroles de l'agent et la priorité du gaz ; confrontée aux oracles de V-08
  (déclenchée sur 5 scénarios, tous attendus `urgent`) ; campagne V-08 de la PR n° 159 :
  `reussite`, 117/120.
- **Vérification sur la révision `f0efe3e`** (21 octobre 2026, 11:03 UTC,
  `preuves/etape-12-d80.json`) : CA-1 3/3 (2,3 à 4,4 s), CA-3 3/3, CA-4 3/3. Journal : urgence
  `urgent` pour SC-01, `securite` pour SC-04, `normal` pour SC-05 ; la règle ne s'est pas
  déclenchée (`urgence_serveur=False`), le modèle ayant rendu `urgent` de lui-même. Elle reste le
  filet pour la variation observée, prouvé par les tests.
- **Statut** : tenu, sans avenant ; le critère garde sa forme et son exigence de 3 sur 3.
- **Autre écart** : la vérification passe par l'API et non par un clic dans la console. Le chemin
  est le même côté serveur ; le rejeu depuis l'écran est prévu dans la démonstration du sprint 5.

### CA-2. Les décisions de l'agent

- **Avenants** :
  - D-69 : pour SC-10, la commune reste « Montreuil » telle qu'entendue ; les trois candidates
    (28267, 85148, 93048) sont jointes, avec code postal et département ; dossier « à vérifier ».
  - D-78 : la provenance « déduit » peut venir de l'agent ou du serveur ; la trace d'un appel à
    `chercher_communes` n'est plus exigée.
- **Pourquoi** : l'agent (gpt-5.4-mini) n'appelle pas l'outil de façon fiable (mesures du
  20 octobre 2026, `evaluation.md`). Une règle du serveur sur un indice explicite est déterministe
  et testable ; l'agent garde les indices libres (architecture hybride, A-3).
- **Preuve** : `preuves/etape-11-criteres.json`, 6/6 ; puis trois séries de 6/6 à l'étape 12,
  dont la dernière, `preuves/etape-12-ca-1-2-4.json`, contrôle en plus le statut « vérifié » de
  SC-07, le code postal et le département de chaque candidate de SC-10.
  Évaluation V-08 : `evaluation.md`.

### CA-3. Le garde-fou de sécurité

- **Forme en vigueur** : sans changement.
- **Preuve** : `preuves/etape-11-criteres.json`, 3/3 : urgence `securite`, rendez-vous vide,
  première action insérée par la règle du serveur (« Orienter vers Urgence Sécurité Gaz… »).

### CA-4. La résistance à la manipulation

- **Forme en vigueur** : sans changement. Le filtre de contenu personnalisé (D-75) annote les
  détournements sans bloquer ; quand il bloque la qualification, l'appel passe à l'extraction
  (D-73). Ni l'un ni l'autre ne modifie le critère.
- **Preuve** : `preuves/etape-11-criteres.json`, 3/3 (commune, code postal, urgence, aucun champ
  ne contient « diabét ») ; trois séries de 3/3 à l'étape 12, dont la dernière,
  `preuves/etape-12-ca-1-2-4.json`, contrôle en plus l'objet dans la
  liste L-05, la commune et le code postal « vérifié », aucun autre statut que « non contrôlé ».
  Complément : prompts hostiles tirés depuis l'écran « Agent », 11/11 tenus (`production.md`, § 4).

### CA-5. La correction et la validation

- **État** : en cours. La correction d'un champ, la validation et la table des corrections
  relèvent de V-09 (console), au sprint 5. Rien n'est livré de ce critère au sprint 4.
- **Prérequis déjà livrés** : contrôle rejoué par le serveur, seul à écrire les statuts
  (sprint 4, étape 4) ; aucune valeur dans les journaux (`production.md`, § 5).

### CA-6. La vigie

- **Avenant D-79 (partie 1)** : la vigie se démontre par une PR qui dégrade réellement l'agent et
  que seule l'évaluation peut voir. La PR « outils désactivés » n'est plus la démonstration : avec
  D-69, D-77 et D-78, les outils n'apportent pas de gain mesurable sur ce jeu. L'avenant de CA-6
  écrit dans D-69 (second scénario d'ambiguïté) est remplacé par D-79.
- **Partie 1, tenue** : PR n° 147 (consigne qui rend l'urgence toujours « non précisée », tests
  unitaires verts) : campagne `echec`, `verdict` rouge, fusion refusée. PR n° 146 (outils
  désactivés) : campagne `reussite`, 117/120, résultat documenté (`evaluation.md`, § 4 quinquies
  et § 4 sexies).
- **Partie 2, en cours** : le mécanisme de retour arrière est prouvé depuis le sprint 2 (workflow
  `retour-arriere`, bascule du trafic en 33 à 40 s, `sprint-2/preuves/etape-8-retour-arriere.md`).
  Reste à démontrer l'enchaînement exact du critère : version dégradée déployée, retour arrière,
  SC-01 conforme à CA-1 en moins de 5 minutes. Prévu au sprint 5 (vigie, V-10).

### CA-7. La qualification des appels

- **Forme en vigueur** : sans changement. Dialogues SC-Q1 à SC-Q8 écrits au sprint 4 selon la
  trame, relus par le porteur, puis figés.
- **Preuve** : `preuves/etape-11-criteres.json`, 24/24 : messages sans dossier pour SC-Q1, SC-Q2,
  SC-Q5 et SC-Q6 ; dossiers pour SC-Q3, SC-Q4 et SC-Q8 ; urgence de sécurité pour SC-Q7.

### CA-8. La voix

- **Avenant D-74** : l'appel simulé est joué comme un vrai appel (sonnerie, attente avant que
  Muninn décroche, 15 s par défaut selon D-68, puis annonce et dialogue) ; les 45 secondes se
  comptent depuis la fin de l'appel joué, et non depuis le clic.
- **Pourquoi** : la sonnerie et le dialogue dépassent à eux seuls 45 s ; compter depuis la fin de
  l'appel garde le critère mesurable sur ce qui dépend de Muninn.
- **État** : en cours, V-12 au sprint 5.

## 3. Avenants en vigueur

| Décision | Date       | Critère | Changement                                                                  |
| -------- | ---------- | ------- | --------------------------------------------------------------------------- |
| D-69     | 2026-10-19 | CA-2    | SC-10 garde « Montreuil » ; candidates jointes ; « à vérifier »             |
| D-78     | 2026-10-20 | CA-2    | « Déduit » par l'agent ou le serveur ; trace de l'outil non exigée          |
| D-79     | 2026-10-20 | CA-6    | Partie 1 : PR dégradée vue par la seule évaluation (remplace D-69 sur CA-6) |
| D-74     | 2026-10-20 | CA-8    | Appel joué comme un vrai appel ; 45 s comptées depuis la fin de l'appel     |

Chaque avenant est une décision écrite du porteur, motivée par une mesure (`docs/decisions.md`,
`docs/decisions-detaillees.md`). Aucun critère n'a été affaibli pour passer : CA-2 garde ses
valeurs attendues, et la vigie de CA-6 bloque une dégradation réelle au lieu d'une dégradation
devenue sans effet.

## 4. Limites

- 3 exécutions sur 3 prouvent la stabilité sur la révision servie, pas un taux. Les taux, avec
  leurs intervalles, sont ceux de l'évaluation V-08 (`evaluation.md`).
- La vérification du serveur (`muninn.demo.verification`) ne contrôle pas tout le texte des
  critères : ni le nom de SC-01, ni l'objet et les statuts de SC-05, ni les statuts de SC-07, ni
  le code postal et le département des candidates de SC-10. Relevé à l'étape 12 ; le script de
  production ajoute ces contrôles (`complements`, essayés sur un brouillon conforme et un
  brouillon fautif) et la série de 10:04 UTC les inclut tous.
  Les reporter dans la vérification du serveur, pour l'écran « Agent », est une dette pour le
  sprint 5.
- La campagne de l'étape 11 (CA-3, CA-7) n'a pas été rejouée : la vérification du serveur couvre
  entièrement leur texte (SC-04 : urgence, rendez-vous, action ; SC-Q : issue, catégorie, nom,
  numéro, urgence).
