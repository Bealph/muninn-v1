# Reste à faire : les sept cases non cochées

**Établi le :** 29 octobre 2026, après la repasse de `competences.md` (54 cases sur 61 ; C21 cochée par décision du porteur).

**Échéance :** oral blanc en situation réelle, E1 à E5, les 12 et 13 novembre 2026 ; gel des
livrables le 11 à 18 h (`docs/v1/roadmap-v1.md`).

Une case de `competences.md` n'est cochée que lorsque la preuve existe dans le dépôt. Pour chaque
case, ce document dit ce qu'exige le référentiel, ce qui existe déjà, le travail à faire, la preuve
attendue et la décision qui revient au porteur. Rien ne démarre sans son feu vert.

**Décisions du porteur (lundi 2 novembre) :** C6, registre dans le dépôt, collecte par flux RSS,
partage par une synthèse au pair et au formateur puis une séance datée ; C8, vérifier d'abord
l'éligibilité, puis décider ; C19, révision de test par PR ; C20, workflow planifié qui ouvre une
issue « Incident ». Les dates ci-dessous sont recalées et restent à valider par le porteur.

## 1. Vue d'ensemble

| Lot | Compétence | Case de `competences.md`                                       | Livrable | Date prévue     | Charge | Décision du porteur            |
| --- | ---------- | -------------------------------------------------------------- | -------- | --------------- | ------ | ------------------------------ |
| 1   | C6         | Dispositif de veille : sources, collecte, partage              | E2       | mer. 4 novembre | 0,5 j  | Dépôt, RSS, synthèse et séance |
| 1   | C6         | Synthèses et recommandations                                   | E2       | mer. 4 novembre | 0,5 j  | Aucune                         |
| 2   | C7         | Benchmark complet : transcription, synthèse vocale, téléphonie | E2       | jeu. 5 novembre | 1 j    | Périmètre de la mesure         |
| 3   | C8         | Demande de zéro rétention tracée (D-32)                        | E2       | lun. 2 novembre | 0,25 j | Vérifier d'abord, puis décider |
| 4   | C19        | Environnement de test                                          | E4       | mar. 3 novembre | 0,5 j  | Révision de test par PR        |
| 4   | C20        | Détection automatique d'incident                               | E5       | lun. 2 novembre | 0,5 j  | Workflow planifié              |
| 5   | C10        | Audit RGAA manuel                                              | E3       | ven. 6 novembre | 0,5 j  | Écrans de l'échantillon        |

Charge totale estimée : 3,75 jours, hors renfort de C21 (1 heure). La feuille de route prévoit
2 jours pour la veille et le benchmark et 1,5 jour pour la V1.1 ; le lot 3 s'y ajoute. Les
charges sont des estimations.

## 2. Lot 1 · C6, la veille

**Le référentiel :** « Organiser et réaliser une veille technique et réglementaire en animant le
travail collectif de sélection des sources, de collecte, de traitement et de partage des
informations afin de formuler des recommandations pour le projet toujours en phase avec l'état de
l'art. »

**Ce qui existe :** des vérifications de sources datées pendant les phases 0 à 2 ; les décisions
qui en découlent (`docs/decisions.md`). Aucun dispositif organisé.

**À faire :**

- [ ] Fixer les thèmes : technique (modèles et services d'IA, agents, évaluation et observabilité
      des LLM, voix) et réglementaire (règlement européen sur l'IA, RGPD, accessibilité, démarchage
      téléphonique).
- [ ] Choisir les sources, de 10 à 15, avec pour chacune son type (officielle, éditeur,
      recherche, presse), sa fiabilité et sa fréquence de lecture.
- [ ] Mettre en place la collecte : flux RSS ou alertes, et une fiche par information retenue
      (date, source, résumé, impact sur Muninn).
- [ ] Organiser le partage et le travail collectif, que le référentiel exige : un canal de
      partage, et un rituel court avec le pair ou le formateur, avec la trace d'au moins une
      séance.
- [ ] Rédiger deux ou trois synthèses datées, chacune terminée par une recommandation pour le
      projet, reliée si besoin à une décision D-xx.
- [ ] Vérifier chaque affirmation réglementaire à la source officielle, et citer la page.

**Preuve attendue :** `docs/veille/` avec le registre des sources, les fiches, les synthèses et
la trace de partage. Les deux cases de C6 sont alors cochées.

**Décision du porteur :** l'outil de collecte (lecteur RSS, alertes, simple fichier) et le canal
de partage (GitHub Discussions, note partagée, réunion avec le pair).

## 3. Lot 2 · C7, le benchmark complet

**Le référentiel :** « Identifier des services d'intelligence artificielle préexistants à partir
de l'expression de besoin […], en réalisant un benchmark de services existants et en analysant
leurs caractéristiques pour formaliser une ou plusieurs recommandations de services adaptés au
besoin. »

**Ce qui existe :** le banc d'essai des LLM T-06 (protocole commité avant la mesure, 48
extractions, D-61) ; le comparatif des services big data ; la comparaison des services de
transcription de D-50 (Azure AI Speech retenu, modèles OpenAI écartés faute de zone UE).

**À faire :**

- [ ] Écrire l'expression de besoin de chaque service : transcription (français, téléphone,
      deux locuteurs), synthèse vocale, téléphonie (numéro, renvoi d'appel, enregistrement).
- [ ] Fixer la grille avant de regarder les offres : traitement dans l'UE, rétention, qualité,
      latence, coût à l'usage, intégration (SDK, API), authentification, accessibilité de la
      documentation, maturité.
- [ ] Lister de 3 à 5 services par catégorie, à partir des sources de la veille.
- [ ] Mesurer ce qui peut l'être sans nouveau compte : la transcription et la synthèse d'Azure
      sur les dialogues synthétiques existants. Pour les autres services, une comparaison
      documentaire, sources citées. La téléphonie reste documentaire (R10 : pas d'achat, pas de
      compte fournisseur).
- [ ] Écrire la recommandation par catégorie, avec ses limites et ce qui la ferait changer.
- [ ] Relire le document par un relecteur indépendant avant de cocher.

**Preuve attendue :** `docs/v1/benchmark-services-ia/` avec le protocole (commité avant toute
mesure), la grille, les résultats et la recommandation.

**Décision du porteur :** mesurer ou non la transcription d'Azure sur les dialogues (coût de
quelques centimes, à confirmer), ou s'en tenir au documentaire hors LLM.

## 4. Lot 3 · C8, la demande de zéro rétention

**Le référentiel :** « Paramétrer un service d'intelligence artificielle en suivant sa
documentation technique et en respectant les spécifications du projet […]. »

**Ce qui existe :** la règle R5 (traitement dans l'UE, zéro rétention vérifiée), D-32, et le
constat du rapport T-06 : « la demande de zéro rétention (D-32, R5) reste ouverte et suppose un
compte géré ».

**À faire :**

- [x] Relire la documentation officielle de Microsoft sur la rétention des données et la
      surveillance des abus d'Azure OpenAI : conditions d'éligibilité, formulaire, délai. Citer
      les pages et leur date.
- Sans objet : le compte n'est pas éligible (D-89). Si le compte est éligible : le porteur
      dépose la demande ; consigner la date, la référence et la réponse.
- [x] S'il ne l'est pas : écrire une décision D-xx qui constate l'inéligibilité, ce qui reste
      garanti (zone de données UE, aucun contenu dans les journaux ni les traces) et la condition
      pour lever la limite en production réelle.

**Preuve attendue :** la décision D-xx dans `docs/decisions.md`, avec les sources. La case
s'appelle « demande tracée » : une demande déposée ou une inéligibilité documentée la satisfont.

**Décision du porteur :** déposer la demande, si le compte le permet.

## 5. Lot 4 · C19 et C20, l'environnement de test et la détection automatique

### C19, l'environnement de test

**Le référentiel :** « Créer un processus de livraison continue d'une application en s'appuyant
sur une chaîne d'intégration continue et en paramétrant les outils d'automatisation et les
environnements de test […]. »

**Ce qui existe :** une préproduction séparée, livrée avant la production avec la même image ;
une base PostgreSQL 16 de service dans la CI ; la feuille de route prévoyait une « révision de
préproduction (environnement de test) ».

**Deux options :**

| Option                     | Principe                                                                                                                  | Charge | Limite                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------- |
| A. Révision de test par PR | Chaque PR déploie une révision étiquetée en préproduction, sans trafic, contrôlée par des tests de fumée, puis désactivée | 0,5 j  | Modifie le workflow ci et les scripts |
| B. Documenter l'existant   | Décrire la préproduction et la base de service comme environnements de test paramétrés                                    | 0,1 j  | Preuve plus faible face à l'énoncé    |

**À faire (option A) :**

- [ ] Ajouter au workflow ci une tâche qui, sur une PR, déploie une révision étiquetée `pr-<n>`
      en préproduction, sans trafic.
- [ ] Jouer contre son adresse les tests de fumée (santé, version, un appel au modèle).
- [ ] Désactiver la révision à la fermeture de la PR.
- [ ] Faire la démonstration sur une PR, et la consigner.

**Réalisé le 2 novembre (D-90), avec un écart à ce plan :** la révision de test n'est pas créée
en préproduction mais sur une application dédiée, `ca-muninn-api-test`, sans base ni secret.
Une révision de PR sur l'API de préproduction laissait l'image de la PR dans le modèle de
l'application, d'où partent les scripts 07 à 13, et faussait le retour arrière. L'application
étant en révision unique, il n'y a rien à désactiver.

- [x] Job `test` du workflow ci : image poussée dans `crmuninntest`, servie sur l'application de
      test, contrôlée (santé, version, un appel au modèle), exigée par le verdict.
- [x] Démonstration : réussie sur les PR n° 204, 205 et 206.
- [x] Correctif : la fusion de C19 a d'abord bloqué la livraison continue (job ignoré sur `main`),
      corrigé par la PR n° 205 et vérifié par une livraison en préproduction et en production.

**Preuve attendue :** le workflow et une exécution réussie sur une PR.

### C20, la détection automatique d'incident

**Le référentiel :** « […] afin d'alimenter la feedback loop dans une approche MLOps, et de
permettre la détection automatique d'incidents. »

**Ce qui existe :** AL-04 détecte automatiquement les échecs du modèle et envoie un courriel ;
AL-01 et AL-16 s'affichent à l'écran. Il manque l'ouverture automatique d'une fiche d'incident.

**Deux options :**

| Option                          | Principe                                                                                                                                 | Charge | À vérifier                                                          |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------- |
| A. Workflow GitHub planifié     | Toutes les 15 minutes, lit les alertes Azure déclenchées (connexion OIDC existante) et ouvre une issue « Incident » à partir d'un modèle | 0,5 j  | Délai réel des workflows planifiés de GitHub                        |
| B. Groupe d'actions vers GitHub | AL-04 appelle un webhook qui crée l'issue                                                                                                | 0,5 j  | Authentification d'un webhook de groupe d'actions vers l'API GitHub |

**À faire (option A) :**

- [x] Créer un modèle d'issue « Incident », qui reprend la structure des fiches INC.
- [x] Écrire le workflow : lecture des alertes, déduplication (une seule issue par alerte),
      ouverture de l'issue avec l'heure, la règle et la gravité (PR n° 203).
- [x] Tester sur une alerte existante : essai du 2 novembre sur 30 jours, 1 alerte résolue lue,
      comme le compte propriétaire, aucune issue ouverte (PR n° 206).
- [x] Lors du prochain exercice de panne (renfort de C21) : une issue ouverte par AL-04. Fait le
      2 novembre : issue #210, une seule, sans doublon à la relance (INC-12). La vigie a été
      lancée à la main : son lancement planifié reste à prouver.

**Preuve attendue :** le workflow, et une issue ouverte automatiquement par une alerte.

**Décision du porteur :** l'option de C19 et celle de C20. Les scripts Azure qui modifient la
production sont lancés par le porteur (R10).

## 6. Lot 5 · C10, et le renfort de C21

### C21, cochée le 29 octobre : le renfort

**Le référentiel :** « Résoudre les incidents techniques en apportant les modifications
nécessaires au code de l'application et en documentant les solutions […]. »

**Décision du porteur (29 octobre) :** la case « incident provoqué, résolu et documenté » est
comptée sur l'exercice de panne du 26 octobre : panne provoquée en production (révision
`0000095`), détectée (écran Qualité, courriel AL-04), résolue (retour arrière, puis révision
`0000096`), documentée (checklist de l'étape 8, `preuves/etape-8-exercice-panne.json`). La
modification du code qu'exige l'énoncé est prouvée par INC-05, INC-07, INC-08 et INC-10, chacun
corrigé dans le code avec un test.

**Point faible à préparer :** l'exercice n'a entraîné aucune modification du code. Le correctif
du retour arrière (PR n° 190) le précède, et INC-08 est survenu pendant la livraison de cette PR,
pas pendant l'exercice. Réponse à tenir au jury : le brouillon de secours a tenu, aucun appel
n'a été perdu, le retour arrière a suffi.

**Renfort recommandé (30 minutes chacun) :**

- [x] Fiche de l'exercice, au format INC. Faite sur un nouvel exercice, le 2 novembre, plutôt
      que de reconstituer celui du 26 octobre : attentes fixées d'avance (H1 à H5), chronologie en
      UTC, ce que chaque outil a vu, écarts, suites
      (`docs/v1/sprints/sprint-5/incidents/INC-12-exercice-de-panne-2-novembre.md`).
- [x] Fiche INC-11 : `unknown_service` dans les traces Langfuse, incident réel trouvé le
      29 octobre, corrigé dans le code avec son test (PR n° 202) ; correctif constaté sur les
      traces de production le 2 novembre
      (`docs/v1/sprints/sprint-5/incidents/INC-11-service-inconnu-dans-langfuse.md`).

### C10, l'audit RGAA manuel

**Le référentiel :** « Intégrer l'API d'un modèle […] dans une application, en respectant les
spécifications du projet et les normes d'accessibilité en vigueur […]. »

**Ce qui existe :** axe-core en CI (WCAG 2.2 AA) sur les états des écrans ; la relecture manuelle
de l'écran Démonstration et quatre corrections avec leur test.

**À faire :**

- [ ] Fixer l'échantillon : les cinq écrans de la console (Accueil, Référentiels, Agent,
      Démonstration, Qualité), chacun dans ses états.
- [ ] Dérouler la grille du RGAA 4.1.2, critère par critère, au clavier seul, au lecteur d'écran
      (NVDA), avec un zoom à 200 % et un contrôle des contrastes.
- [ ] Calculer le taux de conformité selon la méthode du RGAA.
- [ ] Corriger les non-conformités bloquantes, chacune avec un test de non-régression.
- [ ] Rédiger la déclaration d'accessibilité.

**Preuve attendue :** la grille remplie, le taux, les corrections et la déclaration, dans
`docs/v1/accessibilite/`.

**Décision du porteur :** l'échantillon, et qui joue le parcours au lecteur d'écran.

## 7. Sujets ouverts le 29 octobre, à rattacher

Ils ne correspondent à aucune case, mais renforcent C20 et C21 s'ils sont traités :

- [x] PR n° 202 (nom du service dans les traces Langfuse) : fusionnée et livrée en production le
      29 octobre (`6f63267`).
- [ ] Courriel de résolution d'AL-04 non reçu le 26 octobre : cause à identifier.
- [ ] Écart entre le budget filtré par étiquette (21,32 €) et le groupe de ressources : chercher
      la ressource non étiquetée.
- [x] `docs/exploitation.md` : la phrase « une vraie panne du modèle ne se provoque pas en
      production » contredisait l'exercice du 26 octobre ; remplacée le 3 novembre.

## 8. Checklist de suivi

Cocher ici quand la preuve est dans le dépôt, puis cocher la case correspondante de
`competences.md` et mettre son compteur à jour.

- [ ] C6 · dispositif de veille (`docs/veille/`)
- [ ] C6 · synthèses et recommandations
- [ ] C7 · benchmark complet (`docs/v1/benchmark-services-ia/`)
- [x] C8 · demande de zéro rétention tracée (D-89)
- [x] C19 · environnement de test (workflow et exécution, D-90)
- [x] C20 · détection automatique d'incident (issue #210 ; lancement planifié constaté le 3 novembre ; limite écrite)
- [x] C21 · incident provoqué, résolu et documenté (exercice du 26 octobre, décision du porteur)
- [x] C21 · renfort : fiche de l'exercice (INC-12) et fiche INC-11
- [ ] C10 · audit RGAA manuel (`docs/v1/accessibilite/`)

Une fois les sept cases cochées : 61 sur 61. Les compétences concernées passent alors en
« Preuve produite », puis en « Validée » sur décision du porteur.
