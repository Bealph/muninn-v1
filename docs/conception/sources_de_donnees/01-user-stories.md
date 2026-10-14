# User stories de Muninn

**Version :** 2.2
**Date :** 12 octobre 2026
**Historique :** la v2 ajoute l'épopée EP10 (données de référence, US-46 à US-53), l'acteur
« porteur du projet » et le contrôle des champs extraits par l'API des référentiels dans la démo.
La v2.1 ajoute US-54 et le critère 5 de US-01 (décision D-22). La v2.2 suit les décisions D-24 à
D-30 : contrat `DossierDraft` 1.1 (US-11, US-31, US-51), recours par la phrase de récupération
(US-01, critère 6 ; US-54), brouillon de secours (US-11, critère 5), artisans qui travaillent le
week-end (US-02, critères 2 et 5 ; US-05, critère 4 ; US-49, critère 3). Aucune story n'est
ajoutée.
**Phase :** 0a (besoin, flux et sources de données)
**Statut :** proposition, à valider par le porteur
**Compétence principale servie :** C14 (analyse du besoin, spécifications fonctionnelles)

## 1. Objet et sources

Ce document traduit le concept figé de Muninn en user stories. Il n'ajoute au concept que les
fonctions listées en section 9. Quand une story précise un point que le concept laisse ouvert, la précision est marquée
**[H]**.

Promesse du produit : **« Il parle, Muninn se souvient. »**

Sources :

| Source                                    | Sections utilisées                                                    |
| ----------------------------------------- | --------------------------------------------------------------------- |
| Analyse stratégique v2 du 11 octobre 2026 | 3 (personas, parcours, arbitrages), 4.3 (PV1 à PV6), 4.4 (périmètre)  |
| Passation back-end du 11 octobre 2026     | Règles R1 à R10, architecture, contrat DossierDraft, agent vocal, API |
| Feuille de route v2 du 12 octobre 2026    | Contraintes de la démo du premier oral, calendrier                    |

Contraintes du projet de certification, rappelées par la feuille de route :

- pas de POC terrain : aucun appel réel, aucun achat de numéro ;
- la téléphonie est simulée (simulateur d'appel et fournisseur factice) ;
- l'extraction, le chiffrement, le relais et l'interface sont réels ;
- le premier oral blanc (29 octobre 2026) évalue E1 (données) et E3 (API du modèle d'IA,
  intégration, monitoring, tests, livraison continue), avec une démo.

## 2. Conventions

- **Format des stories :** « En tant que [type d'utilisateur], je veux [action] afin de
  [bénéfice] ». Seule variation : l'élision devant une voyelle (« En tant qu'artisan »).
- **Critères d'acceptation :** « Étant donné… / Quand… / Alors… ». Chaque critère décrit un
  résultat observable par un test automatisé ou manuel.
- **Priorité MoSCoW,** évaluée pour l'horizon indiqué :
  - Must : sans elle, la promesse de l'horizon n'est pas tenue ;
  - Should : forte valeur, mais un contournement existe ;
  - Could : utile, reportable sans perte de la promesse ;
  - Won't : exclu de l'horizon, gardé pour tracer la frontière du périmètre.
- **Horizon :** MVP, V2, V3, V4 ou hors périmètre, selon la section 4.4 de l'analyse et les
  décisions ultérieures (D-53, D-55).
- **Démo :** « oui » si la story entre dans le périmètre de la démo du 29 octobre (section 8).
- **Règles :** R1 à R10 de la passation back-end. « Aucune » si la story n'en touche aucune.
- **Compétences :** codes C1 à C21 du référentiel servis par la réalisation de la story. Toutes
  les stories servent C14 ; ce code n'est donc pas répété.

## 3. Acteurs

| Acteur            | Description                                                                                                        | Justification                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Artisan           | Plombier, chauffagiste, électricien ou serrurier qui travaille seul. Personas P1 (Karim) et P2 (Sophie)            | Utilisateur et payeur. Concept, sections 3.1 et 3.2                                                             |
| Client final      | Particulier qui appelle l'artisan. Il parle à l'agent vocal et reçoit des SMS                                      | Interlocuteur de l'agent (PV1) et destinataire des SMS (PV5)                                                    |
| Exploitant        | Personne qui opère le service Muninn : qualité de l'extraction, référentiels, disponibilité, incidents, livraisons | KPI du POC (90 % de champs clés, 30 s, zéro audio conservé) ; passation, sections 1, 10 et 11                   |
| Porteur du projet | Fondateur de Muninn. Il décide du ciblage commercial et dimensionne le marché. Il n'utilise pas l'application      | Analyse stratégique, section 1.1 (dimensionnement, action Sirene) ; « fondateur » dans la passation, section 12 |

Acteurs écartés, et pourquoi :

| Acteur envisagé                                | Décision                    | Raison                                                                            |
| ---------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------- |
| Apprenti ou salarié (persona P2)               | Écarté                      | Le concept vise l'artisan seul. Aucune fonction multi-utilisateur n'est prévue    |
| Aide à domicile (persona P4)                   | Écarté                      | Persona de veille. Données de santé (R7). Module B2B SAAD en deuxième année       |
| Éditeur de facturation (Obat, Tolteck, Indy)   | Système externe, pas acteur | Il reçoit un export (US-24) mais n'interagit pas avec Muninn                      |
| Fournisseurs (téléphonie, STT, LLM, SMS, push) | Systèmes externes           | Ils passent par des interfaces avec implémentation factice (passation, section 5) |

Le persona P3 (Julien, paysagiste) n'est pas un acteur distinct. Son besoin, prévenir ses
clients en un geste, est couvert par US-28. Son métier n'a pas de lexique dans le MVP (US-43).

## 4. Épopées

| Épopée | Titre                                           | Propositions de valeur | Stories              |
| ------ | ----------------------------------------------- | ---------------------- | -------------------- |
| EP1    | Mise en service : ligne, renvoi, disponibilités | PV1                    | US-01 à US-05        |
| EP2    | Messagerie intelligente                         | PV1                    | US-06 à US-12        |
| EP3    | Débrief vocal et lexiques                       | PV2, levier 3          | US-13 à US-16        |
| EP4    | Dossier et clé humaine                          | PV3                    | US-17 à US-20        |
| EP5    | Rentabilité et export                           | PV4                    | US-21 à US-25, US-55 |
| EP6    | Rendez-vous et imprévus                         | PV5                    | US-26 à US-30        |
| EP7    | Confiance par conception                        | PV6                    | US-31 à US-35, US-54 |
| EP8    | Supervision et exploitation                     | PV1, PV6 (KPI du POC)  | US-36 à US-41        |
| EP9    | Hors MVP (frontière du périmètre)               | Section 4.4            | US-42 à US-45        |
| EP10   | Données de référence                            | PV1, PV5, levier 3     | US-46 à US-53        |

EP10 sert aussi le dimensionnement du marché (analyse, section 1.1), qui n'est pas une
proposition de valeur : US-52 et US-53 relèvent du porteur du projet.

## 5. User stories

### EP1. Mise en service : ligne, renvoi, disponibilités

#### US-01. Créer son compte et lier son téléphone

En tant qu'artisan, je veux créer mon compte et lier mon téléphone avec un code reçu par SMS ou
par e-mail afin d'utiliser Muninn sans mot de passe à retenir.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4, R10
- Compétences : C4, C17

Critères d'acceptation :

1. Étant donné un numéro de mobile ou une adresse e-mail valide, quand l'artisan demande un code,
   alors un code à usage unique lui est envoyé et expire après 10 minutes [H].
2. Étant donné un code valide, quand l'artisan le saisit, alors l'appareil est enregistré avec sa
   clé publique et un test vérifie que la clé privée n'est jamais transmise au serveur.
3. Étant donné 5 codes erronés consécutifs [H], quand l'artisan fait une sixième tentative, alors
   elle est refusée et un message indique comment demander un nouveau code.
4. Étant donné l'environnement de développement, quand un code est demandé, alors il passe par le
   fournisseur factice ; aucun SMS réel ne part sans l'accord du porteur.
5. Étant donné un compte qui a déjà un appareil enregistré, quand un nouvel appareil saisit un code
   valide, alors il ne reçoit aucune demande tant qu'un appareil déjà enregistré ne l'a pas
   approuvé ; le premier appareil du compte est exempté de cette approbation (décision D-22).
6. Étant donné un artisan qui a perdu son seul appareil et qui a gardé sa phrase de récupération,
   quand il la ressaisit sur le nouvel appareil, alors cet appareil est approuvé sans autre
   appareil, et un test vérifie que le serveur n'a reçu que la clé publique dérivée de la phrase ;
   sans la phrase, l'application dit qu'aucun recours en ligne n'existe (décision D-28).

#### US-02. Régler sa ligne Muninn

En tant qu'artisan, je veux régler ma ligne Muninn (nom de l'entreprise, prénom, métier,
horaires, message d'accueil, prise de rendez-vous oui ou non) afin d'être représenté par l'agent
en mon nom et selon mes règles.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R6
- Compétences : C8, C17

Critères d'acceptation :

1. Étant donné un message d'accueil personnalisé, quand l'artisan l'enregistre, alors la phrase
   qui annonce l'assistant automatique reste présente et ne peut pas être supprimée.
2. Étant donné des horaires configurés, quand un appel arrive hors de ces horaires, alors l'agent
   annonce un rappel au prochain jour d'ouverture de l'artisan, tel que ses horaires le
   définissent, week-end compris (décision D-30).
3. Étant donné la prise de rendez-vous désactivée, quand un client demande un créneau, alors
   l'agent annonce un rappel sans proposer de créneau.
4. Étant donné l'écran de choix du métier, quand l'artisan l'ouvre, alors il propose plomberie,
   chauffage, électricité, serrurerie et autre.
5. Étant donné des horaires qui incluent le samedi ou le dimanche, quand un appel arrive ce
   jour-là pendant ces horaires, alors l'agent le traite comme un jour ouvert et propose des
   créneaux ; hors de ces horaires, il annonce un rappel au prochain créneau d'ouverture,
   week-end compris (décision D-30).

#### US-03. Obtenir les codes de renvoi de son opérateur

En tant qu'artisan, je veux obtenir les codes de renvoi de mon opérateur avec des instructions
pas à pas afin d'activer le renvoi sur non-réponse, occupation et injoignabilité sans changer de
numéro.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : Aucune
- Compétences : C17

Critères d'acceptation :

1. Étant donné un opérateur choisi parmi Orange, SFR, Bouygues Telecom et Free [H : codes à
   vérifier par opérateur], quand l'artisan ouvre l'écran de renvoi, alors il voit les codes d'activation et de
   désactivation pour les trois cas de renvoi.
2. Étant donné un code affiché, quand l'artisan le touche, alors le composeur du téléphone
   s'ouvre avec le code prérempli ; Muninn n'active rien à la place de l'artisan.
3. Étant donné un premier usage, quand 5 testeurs [H] suivent les instructions, alors chacun active
   le renvoi en moins de 2 minutes (KPI de l'action 2 de l'analyse) ; la médiane et le maximum sont
   consignés.
4. Étant donné l'écran de renvoi, quand il s'affiche, alors un avertissement invite à vérifier
   si le forfait facture le renvoi [H : conditions tarifaires non vérifiées].

#### US-04. Vérifier le renvoi par un appel de test

En tant qu'artisan, je veux vérifier mon renvoi par un appel de test afin d'être sûr qu'aucun
appel manqué ne se perd.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R2, R6
- Compétences : C17

Critères d'acceptation :

1. Étant donné le renvoi activé, quand l'artisan lance le test, alors une fenêtre de 2 minutes
   s'ouvre et le premier appel reçu sur la ligne Muninn pendant cette fenêtre est traité comme
   test [H] : l'agent s'annonce, dit « appel de test reçu » et l'écran affiche « renvoi vérifié ».
2. Étant donné aucun appel reçu pendant la fenêtre, quand le test expire, alors l'écran
   affiche « renvoi non détecté » et renvoie vers les instructions de US-03.
3. Étant donné un appel de test reçu, quand il se termine, alors aucun dossier n'est créé et aucun
   audio n'est conservé.

[H] Cette story n'est pas écrite dans le concept. Elle découle du KPI d'activation du renvoi et
de la règle « jamais d'action invisible » (section 3.4).

#### US-05. Partager ses disponibilités sans détail

En tant qu'artisan, je veux que mes créneaux libres et occupés des 14 prochains jours, sept jours
sur sept, soient partagés avec l'agent, sans le détail de mes rendez-vous, afin de proposer au client, par
l'agent, un créneau réel.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C4, C17

Critères d'acceptation :

1. Étant donné l'agenda Muninn de l'appareil [H : source retenue], qui contient des rendez-vous
   nommés, quand l'appareil synchronise, alors
   le serveur reçoit seulement des débuts, des fins et un type (libre ou occupé), sans nom ni
   adresse.
2. Étant donné une synchronisation, quand elle aboutit, alors elle remplace la fenêtre des 14 jours
   suivants, sauf les créneaux réservés par l'agent et pas encore reçus par l'appareil, qui restent
   occupés [H] ; les créneaux passés sont purgés.
3. Étant donné une durée de créneau fixée par l'artisan [H : paramètre absent du concept et de
   l'API de configuration de ligne], quand l'agent propose un rendez-vous, alors le créneau proposé est entièrement
   contenu dans une plage libre.
4. Étant donné un artisan qui travaille le samedi ou le dimanche, quand l'appareil synchronise,
   alors les créneaux de ces jours sont partagés comme ceux des autres jours : la fenêtre couvre
   les sept jours de la semaine et aucun jour n'est exclu par défaut (décision D-30).

### EP2. Messagerie intelligente

#### US-06. Savoir que l'on parle à un assistant automatique

En tant que client final, je veux savoir dès le message d'ouverture que je parle à l'assistant
automatique de l'artisan afin de décider en connaissance de cause de lui confier ma demande.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R6
- Compétences : C8, C12

Critères d'acceptation :

1. Étant donné un appel renvoyé vers la ligne Muninn, quand l'agent décroche, alors **sa première
   phrase** dit qu'il est l'assistant automatique de l'artisan, par exemple « Bonjour, vous êtes en
   relation avec l'assistant automatique de [Entreprise]… » (décision D-04), et le message
   d'ouverture précise, avant toute question, que la demande est traitée automatiquement pour lui
   être transmise.
2. Étant donné la question « vous êtes un robot ? », quand le client la pose, alors l'agent
   répond oui et ne prétend jamais être l'artisan ni un humain.
3. Étant donné le jeu de scénarios synthétiques, quand le test de conformité les rejoue tous,
   alors l'annonce est prononcée dans 100 % des appels.

#### US-07. Exposer sa demande et l'entendre reformulée

En tant que client final, je veux exposer ma demande en moins de 3 minutes et l'entendre
reformulée afin d'être sûr qu'elle a été comprise.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R6
- Compétences : C8, C9

Critères d'acceptation :

1. Étant donné un appel, quand l'agent recueille la demande, alors il demande le nom, l'objet et
   l'urgence, l'adresse (au minimum la commune) et le numéro de rappel.
2. Étant donné les informations recueillies, quand l'agent conclut, alors il les reformule et
   demande une confirmation avant de raccrocher ; sur le jeu synthétique, le 95e centile de la
   durée des appels est inférieur à 3 minutes, avec l'effectif indiqué.
3. Étant donné un silence ou un bruit qui empêche la compréhension, quand l'agent a relancé deux
   fois, alors il clôt poliment l'appel en annonçant un rappel et le numéro appelant est transmis
   à l'artisan.
4. Étant donné une question sur un prix, un délai garanti ou un diagnostic, quand le client la
   pose, alors l'agent répond qu'il ne peut pas s'engager et que l'artisan rappellera.

#### US-08. Obtenir un créneau ou l'annonce d'un rappel

En tant que client final, je veux obtenir un créneau parmi les disponibilités de l'artisan, ou
l'annonce d'un rappel, afin de savoir quand il interviendra.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C8

Critères d'acceptation :

1. Étant donné la prise de rendez-vous activée et un créneau libre, quand le client accepte le
   créneau proposé, alors le brouillon contient `rdv_propose` avec `accepte_par_client` à vrai.
2. Étant donné aucun créneau libre dans les 14 jours, quand le client demande un rendez-vous,
   alors l'agent annonce un rappel par l'artisan.
3. Étant donné un créneau accepté, quand un autre client appelle ensuite, alors ce créneau ne lui
   est plus proposé.

#### US-09. Recevoir la consigne de sécurité en cas de danger

En tant que client final, je veux recevoir la consigne de sécurité dès que je signale une odeur
de gaz ou un danger immédiat afin de me protéger avant toute prise de rendez-vous.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R6, R7
- Compétences : C8, C12

Critères d'acceptation :

1. Étant donné un client qui mentionne une odeur de gaz, quand il le dit, alors l'agent donne la
   consigne avant toute autre question : quitter les lieux sans actionner d'interrupteur, appeler
   Urgence Sécurité Gaz (0 800 47 33 33, numéro repris de la passation) ou le 112. Il ne propose
   pas de rendez-vous et ne garde que le numéro de rappel [H].
2. Étant donné un client qui mentionne un incendie, une électrocution ou une inondation
   importante, quand il le dit, alors l'agent l'oriente vers le 112 ou le 18.
3. Étant donné l'odeur de gaz, quand le brouillon est produit, alors `urgence` vaut `securite` ;
   pour les autres dangers, la même valeur est proposée [H : la passation ne la fixe que pour le
   gaz].

#### US-10. Refuser l'assistant et demander un rappel

En tant que client final, je veux pouvoir refuser l'assistant et demander seulement à être
rappelé afin de garder le choix de mon interlocuteur.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R2, R6
- Compétences : C8

Critères d'acceptation :

1. Étant donné un client qui refuse de parler à l'assistant, quand il l'exprime, alors l'agent
   propose un rappel et met fin à l'appel sans poser d'autre question.
2. Étant donné ce refus, quand le brouillon est produit, alors il ne contient que le numéro
   appelant et une action « rappeler ».
3. Étant donné ce refus, quand l'artisan ouvre la demande, alors il lit « refus de l'assistant :
   rappeler ».

#### US-11. Recevoir un brouillon de dossier extrait de l'appel

En tant qu'artisan, je veux que chaque appel pris par l'agent devienne un brouillon de dossier
structuré, avec les champs incertains signalés, afin de n'avoir rien à saisir.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R2, R3, R4, R5, R7
- Compétences : C3, C8, C9, C12

Critères d'acceptation :

1. Étant donné une transcription d'appel, quand l'extraction se termine, alors le résultat est
   validé par le schéma `DossierDraft` 1.1 (décision D-24) et contient la clé humaine au format
   « Nom, Commune, objet court ».
2. Étant donné une information absente de l'appel, quand l'extraction se termine, alors le champ
   vaut `null` et figure dans `champs_manquants` ; aucune valeur n'est inventée.
3. Étant donné une sortie du modèle invalide, quand la validation échoue, alors l'extraction est
   relancée une fois avec l'erreur, puis un brouillon partiel marqué `needs_review` est rendu.
4. Étant donné une transcription qui contient une information médicale, quand l'extraction se
   termine, alors aucun champ du brouillon ne la contient (test de conformité).
5. Étant donné le fournisseur LLM indisponible en fin d'appel, quand l'appel se termine, alors
   l'artisan reçoit quand même un brouillon de secours qui porte le numéro et l'heure de l'appel,
   marqué à vérifier, avec l'action « rappeler » ; la transcription est détruite comme pour tout
   appel, et aucune demande n'est perdue en silence (décision D-29).

Voir aussi US-51 : la commune, le code postal et le téléphone extraits sont contrôlés par l'API
des référentiels avant le chiffrement du brouillon.

#### US-12. Être notifié et recevoir le dossier chiffré

En tant qu'artisan, je veux recevoir une notification sans contenu puis le dossier chiffré pour
mon seul appareil afin d'être prévenu vite sans que la demande soit lisible en chemin.

- Priorité : Must
- Horizon : MVP
- Démo : non (prévue pour l'oral du 12 novembre, voir section 8)
- Règles : R1, R4
- Compétences : C4, C9, C17

Critères d'acceptation :

1. Étant donné la fin d'un appel simulé, quand le brouillon est prêt, alors l'appareil reçoit le
   dossier en moins de 30 secondes (p95 mesuré sur le simulateur).
2. Étant donné une notification push, quand on lit son contenu, alors il se limite à « Nouvelle
   demande », sans nom, numéro ni objet.
3. Étant donné une enveloppe, quand l'appareil accuse réception, alors le serveur la supprime ;
   sans accusé, elle est supprimée après 7 jours.
4. Étant donné une enveloppe stockée, quand un test tente de la déchiffrer avec les seules
   données du serveur, alors il échoue.

### EP3. Débrief vocal et lexiques

#### US-13. Dicter un débrief après un échange

En tant qu'artisan, je veux dicter un débrief d'environ 20 secondes après un appel décroché, une
visite ou une conversation sur place afin de ranger les informations dans le bon dossier sans
saisie.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R2, R3, R5, R7
- Compétences : C8, C9, C10

Critères d'acceptation :

1. Étant donné un débrief dicté, quand le traitement se termine, alors l'artisan reçoit un
   brouillon de source `debrief` validé par le même schéma que pour un appel.
2. Étant donné un débrief traité, quand un test parcourt la base, le stockage objet et les
   journaux du serveur, alors il n'y trouve ni l'audio ni la transcription.
3. Étant donné un artisan qui ne peut pas dicter, quand il écrit son débrief, alors il obtient un
   brouillon équivalent [H : point d'extraction à partir de texte à ajouter au contrat d'API].
4. Étant donné l'absence de réseau, quand l'artisan dicte, alors le débrief est gardé chiffré sur
   le téléphone, envoyé au retour du réseau, puis supprimé du téléphone après l'envoi réussi [H].

#### US-14. Être invité au débrief à la fin d'un appel décroché

En tant qu'artisan, je veux être invité au débrief à la fin d'un appel décroché afin de ne pas
oublier de le faire.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R2
- Compétences : C17

Critères d'acceptation :

1. Étant donné un téléphone Android, quand un appel décroché se termine, alors Muninn propose le
   débrief par une notification qui lance la dictée en un geste.
2. Étant donné un iPhone, quand l'artisan veut dicter, alors un raccourci ou un widget lance la
   dictée en un geste [H : faisabilité iOS à valider].
3. Étant donné l'invitation ignorée, quand 2 minutes [H] passent, alors elle disparaît sans rien
   enregistrer.
4. Étant donné un appel décroché, quand un test inspecte les permissions et les flux de
   l'application, alors seule la fin d'appel est détectée ; l'audio de l'appel n'est jamais lu.

#### US-15. Bénéficier du lexique de son métier dès le premier jour

En tant qu'artisan, je veux que Muninn connaisse d'emblée le vocabulaire de mon métier (marques,
pièces, pannes types) afin d'être compris sans correction dès le premier jour.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R5
- Compétences : C8, C12

Critères d'acceptation :

1. Étant donné le métier plomberie, chauffage ou électricité, quand une transcription ou une
   extraction est lancée, alors le lexique de ce métier, de version identifiée, est injecté dans
   la transcription et dans le prompt d'extraction.
2. Étant donné le jeu synthétique, quand l'évaluation est lancée avec et sans lexique, alors le
   rapport donne l'écart d'exactitude par champ clé ; le résultat sans lexique décrit aussi les
   métiers qui n'en ont pas (serrurerie, autre) [H].
3. Étant donné le jeu synthétique audio, quand on mesure la part des termes du lexique prononcés
   puis mal transcrits, alors elle est inférieure à 15 %. Cet objectif reprend le KPI de l'action
   2, qui porte sur des appels réels : la mesure synthétique n'en est qu'une approximation.
4. Étant donné un lexique plus long que la limite du fournisseur de transcription [H : 100 termes
   selon la passation, fonction annoncée comme expérimentale hors anglais, à vérifier], quand il est injecté, alors une sélection documentée des
   termes est appliquée et le rapport le signale.

#### US-16. Enrichir son lexique personnel par ses corrections

En tant qu'artisan, je veux que mes corrections (noms de clients, rues) enrichissent un lexique
personnel gardé sur mon téléphone afin de réduire les erreurs de transcription au fil du temps.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1, R3, R4
- Compétences : C8, C17

Critères d'acceptation :

1. Étant donné un nom corrigé dans un brouillon, quand l'artisan valide, alors le terme corrigé
   rejoint le lexique personnel stocké sur l'appareil.
2. Étant donné un débrief, quand l'appareil l'envoie, alors le lexique personnel accompagne la
   requête et un test vérifie qu'il n'est ni stocké ni journalisé par le serveur.
3. Étant donné le lexique personnel, quand l'artisan l'ouvre, alors il peut lire et supprimer
   chaque terme.

### EP4. Dossier et clé humaine

#### US-17. Valider, corriger ou rejeter un brouillon en un geste

En tant qu'artisan, je veux valider, corriger ou rejeter un brouillon en un geste afin de garder
le dernier mot sur ce qui entre dans mes dossiers.

- Priorité : Must
- Horizon : MVP
- Démo : **oui** (correction au clavier seulement)
- Règles : R1, R4
- Compétences : C10, C11, C17

Critères d'acceptation :

1. Étant donné un brouillon affiché, quand un champ a une confiance inférieure à 0,7 ou figure
   dans `champs_manquants`, alors il porte la mention « à vérifier » en texte, en plus de tout
   repère de couleur.
2. Étant donné un brouillon sans champ « à vérifier », quand l'artisan touche « Valider », alors le
   dossier est créé ou mis à jour en une seule action.
3. Étant donné un champ corrigé, quand l'artisan valide, alors la valeur corrigée remplace la
   valeur extraite et la correction est comptée dans les métriques de qualité par le seul nom du
   champ, sans son contenu [H].
4. Étant donné un brouillon rejeté, quand l'artisan confirme le rejet, alors le brouillon est
   supprimé de l'appareil et aucun dossier n'est créé.

#### US-18. Retrouver un dossier comme on en parle

En tant qu'artisan, je veux retrouver un dossier en le décrivant comme j'en parle (« Dupont,
Montreuil, fuite évier ») afin de n'avoir aucun code à retenir.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R3
- Compétences : C17

Critères d'acceptation :

1. Étant donné un dossier « Dupont, Montreuil, fuite évier », quand l'artisan dit ou tape « le
   Dupont de Montreuil », alors ce dossier apparaît en premier résultat.
2. Étant donné une erreur d'une lettre sur le nom [H], quand l'artisan cherche, alors le dossier
   est retrouvé.
3. Étant donné une recherche, quand elle s'exécute, alors la comparaison avec les dossiers se fait
   sur l'appareil. Une recherche vocale envoie la seule phrase prononcée au serveur pour
   transcription, sans conservation [H : point d'API absent de la passation]. Sans réseau, la
   recherche écrite fonctionne.

#### US-19. Lever une ambiguïté par une seule question

En tant qu'artisan, je veux répondre à une seule question quand plusieurs dossiers correspondent
afin d'éviter toute erreur de dossier.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C17

Critères d'acceptation :

1. Étant donné deux dossiers Dupont, l'un à Montreuil et l'autre à Bagnolet, quand l'artisan
   cherche « Dupont », alors Muninn pose une seule question : « Le Dupont de Montreuil ou celui de
   Bagnolet ? ».
2. Étant donné la réponse « Montreuil », quand elle est reçue, alors le bon dossier s'ouvre sans
   autre question.
3. Étant donné la question posée à voix haute, quand elle est énoncée, alors les choix sont aussi
   affichés en liste et chacun s'ouvre d'un toucher.

#### US-20. Rattacher la demande d'un client déjà connu

En tant qu'artisan, je veux qu'une nouvelle demande d'un client déjà connu me soit proposée au
rattachement à son dossier afin de garder tout l'historique au même endroit.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C17

Critères d'acceptation :

1. Étant donné un brouillon dont le numéro appelant correspond à un dossier existant, quand il
   arrive sur l'appareil, alors Muninn propose ce dossier et l'artisan confirme ou choisit un
   nouveau dossier en un geste.
2. Étant donné un rattachement confirmé, quand l'artisan ouvre le dossier, alors la nouvelle
   demande apparaît datée dans son historique.
3. Étant donné un rapprochement, quand il s'exécute, alors il se fait sur l'appareil ; le serveur
   ne transmet que les attributs de rapprochement contenus dans l'enveloppe chiffrée.

### EP5. Rentabilité et export

#### US-21. Transformer un ticket photographié en dépense

En tant qu'artisan, je veux photographier un ticket de caisse pour qu'il devienne une dépense
rattachée au bon dossier afin de connaître le coût réel du chantier.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4, R5
- Compétences : C8, C9

Critères d'acceptation :

1. Étant donné les tickets d'un jeu de test dédié, quand le traitement se termine, alors chaque
   brouillon de source `receipt_scan` contient le fournisseur, la date et les montants HT, TTC et
   de TVA ; le montant TTC est exact sur au moins 90 % des tickets [H].
2. Étant donné un montant illisible, quand le brouillon arrive, alors ce champ vaut `null` et
   porte la mention « à vérifier ».
3. Étant donné le traitement terminé, quand un test inspecte le serveur, alors l'image transmise
   pour le traitement n'y est pas conservée. Seule la copie chiffrée par l'appareil peut être
   archivée (US-34).
4. Étant donné le brouillon validé et le dossier choisi, quand l'artisan ouvre ce dossier, alors
   la dépense figure dans son tableau.

#### US-22. Dicter une dépense

En tant qu'artisan, je veux dicter une dépense (« 84 euros 20 chez Cedeo pour le Dupont de
Montreuil ») afin de l'enregistrer sans chercher le ticket.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R2, R3, R5
- Compétences : C8, C9

Critères d'acceptation :

1. Étant donné cette dictée, quand le traitement se termine, alors le brouillon de source
   `expense_voice` contient le fournisseur, le montant et la clé humaine mentionnée.
2. Étant donné un artisan qui ne peut pas dicter, quand il écrit la même phrase, alors il obtient
   le même brouillon [H : point d'extraction à partir de texte, voir US-13].
3. Étant donné un montant dicté sans précision HT ou TTC, quand le brouillon arrive, alors le
   montant porte la mention « à vérifier » ; aucun taux de TVA n'est supposé en silence [H].
4. Étant donné la dictée traitée, quand un test inspecte le serveur, alors ni l'audio ni la
   transcription n'y subsistent.

#### US-23. Voir la marge de chaque chantier

En tant qu'artisan, je veux voir pour chaque dossier ses encaissements, ses dépenses et sa marge
afin de savoir si le chantier me fait gagner de l'argent pendant qu'il est encore temps d'agir.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C17

Critères d'acceptation :

1. Étant donné un dossier avec des dépenses et des encaissements, quand l'artisan l'ouvre, alors
   il voit le total de chaque colonne et la marge (encaissements moins dépenses), en HT [H].
2. Étant donné une nouvelle dépense validée, quand elle est ajoutée, alors la marge affichée est
   recalculée sans action de l'artisan.
3. Étant donné un encaissement, quand l'artisan l'enregistre sur l'appareil (montant et date),
   alors il est ajouté au dossier sans passer par le serveur [H : le concept ne précise pas la
   source ; une dictée exigerait une évolution du contrat `DossierDraft`].
4. Étant donné une marge négative, quand l'artisan ouvre le dossier, alors elle est signalée par
   un texte explicite, en plus de tout repère de couleur.

#### US-24. Exporter un dossier vers son outil de facturation

En tant qu'artisan, je veux exporter un dossier vers mon outil de facturation afin de facturer sans ressaisie.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C17

Critères d'acceptation :

1. Étant donné un dossier validé, quand l'artisan choisit « Exporter » puis l'un des 2 outils pris
   en charge au lancement (parmi Obat, Tolteck et Indy, action 5 de l'analyse), alors l'outil
   accepte l'import sans erreur [H : outils, format ou API à confirmer].
2. Étant donné un export produit, quand on l'ouvre, alors il contient au minimum le client,
   l'adresse, la demande et les dépenses rattachées.
3. Étant donné un export, quand il quitte le téléphone, alors c'est sur demande explicite de
   l'artisan, par une connexion HTTPS ou par un fichier qu'il enregistre lui-même ; un test vérifie
   que le serveur Muninn n'en garde aucune copie.

#### US-55. Préparer un devis à partir d'un dossier

En tant qu'artisan, je veux que Muninn prépare un devis à partir d'un dossier, avec mes prix,
afin de l'envoyer vite au client après l'avoir vérifié.

- Priorité : Should
- Horizon : V2 (confirmé par le porteur, D-55)
- Démo : non
- Règles : R1, R4, R5, R7
- Compétences : C8, C9, C12, C17

Critères d'acceptation :

1. Étant donné un dossier validé, quand l'artisan demande un devis, alors il reçoit un brouillon
   dont chaque ligne indique la provenance de son prix : son catalogue, son historique, ou « à
   chiffrer ».
2. Étant donné un brouillon, quand un prix ne vient ni du catalogue ni de l'historique, alors la
   ligne est marquée « à chiffrer », sans prix.
3. Étant donné un brouillon, quand il s'affiche, alors les totaux et la TVA sont calculés par le
   serveur, et les mentions obligatoires sont présentes ou signalées comme manquantes.
4. Étant donné un brouillon, quand l'artisan ne l'a pas validé, alors rien n'est envoyé au
   client.
5. Étant donné une demande de devis, quand un test inspecte ce qui part vers le serveur et ce que
   le serveur garde après la réponse, alors il n'y trouve ni nom, ni adresse, ni téléphone du
   client, et le serveur ne garde rien.
6. Étant donné une désignation qui contient un terme de santé, quand le brouillon s'affiche,
   alors ce terme a été retiré (R7).

Conception : `../architecture-agentique/01-architecture-agentique.md`, section 8 (D-53).

#### US-25. Importer les factures électroniques des fournisseurs

En tant qu'artisan, je veux que les factures électroniques de mes fournisseurs soient importées et
proposées au rattachement à mes dossiers afin de suivre mes dépenses sans scanner de ticket.

- Priorité : Could
- Horizon : V2
- Démo : non
- Règles : R1, R5
- Compétences : C1, C8

Critères d'acceptation :

1. Étant donné une facture reçue par la plateforme agréée partenaire, quand elle est importée,
   alors Muninn propose un dossier de rattachement.
2. Étant donné une facture sans dossier correspondant, quand elle est importée, alors elle reste
   dans une liste « à classer ».
3. Étant donné le flux d'import, quand on l'examine, alors il passe par la plateforme agréée
   partenaire ; Muninn n'est pas lui-même plateforme agréée.

### EP6. Rendez-vous et imprévus

#### US-26. Retrouver dans son agenda le rendez-vous pris par l'assistant

En tant qu'artisan, je veux que le rendez-vous accepté par un client au téléphone apparaisse dans
mon agenda Muninn afin d'éviter les doubles réservations.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C17

Critères d'acceptation :

1. Étant donné un brouillon avec un `rdv_propose` accepté, quand il arrive sur l'appareil, alors
   le rendez-vous apparaît dans l'agenda avec la mention « pris par l'assistant ».
2. Étant donné ce rendez-vous, quand l'artisan l'annule ou le déplace, alors Muninn prépare le SMS
   au client et ne l'envoie qu'après validation (US-28).
3. Étant donné un rendez-vous pris, quand le serveur l'enregistre, alors le créneau est marqué
   occupé sans nom ni adresse.

#### US-27. Envoyer des rappels de rendez-vous par SMS

En tant qu'artisan, je veux que mes clients reçoivent un SMS de rappel avant leur rendez-vous afin
de réduire les rendez-vous manqués.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1, R4, R10
- Compétences : C17

Critères d'acceptation :

1. Étant donné les rappels activés par l'artisan dans ses réglages, quand un rendez-vous a lieu le
   lendemain [H : délai paramétrable], alors un SMS de rappel part vers le client et l'envoi
   apparaît dans l'historique du dossier.
2. Étant donné les rappels désactivés, quand un rendez-vous approche, alors aucun SMS ne part.
3. Étant donné un SMS envoyé, quand un test inspecte le serveur, alors seuls l'identifiant chez le
   fournisseur et le statut sont conservés, sans texte ni destinataire.
4. Étant donné un rappel à envoyer, quand l'heure prévue arrive, alors l'appareil compose le
   texte, qui nomme l'entreprise, et déclenche l'envoi ; si l'envoi échoue (téléphone éteint,
   réseau), l'artisan voit « rappel non envoyé » [H].

#### US-28. Prévenir en un geste les clients touchés par un imprévu

En tant qu'artisan, je veux déclarer une absence ou un retard en une phrase et valider en un geste
les messages proposés afin de prévenir tous les clients touchés sans les appeler un par un.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C8, C17

Critères d'acceptation :

1. Étant donné la phrase « j'ai deux heures de retard » dictée, ou le même choix fait au toucher
   dans une liste (retard, absence, durée), quand Muninn la traite, alors il liste les rendez-vous
   touchés de la journée.
2. Étant donné les rendez-vous touchés, quand la liste s'affiche, alors chaque client a un message
   prérempli avec un ou deux créneaux libres proposés.
3. Étant donné la liste, quand l'artisan touche « Envoyer », alors les SMS de la liste partent ;
   sans ce geste, aucun SMS d'imprévu ne part.
4. Étant donné un message prérempli, quand l'artisan veut le modifier ou retirer un client, alors
   il peut le faire avant l'envoi.

#### US-29. Recevoir un SMS clair en cas de changement

En tant que client final, je veux recevoir un SMS clair qui identifie l'artisan et me propose un
nouveau créneau afin de ne pas l'attendre pour rien.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R4
- Compétences : C17

Critères d'acceptation :

1. Étant donné un rendez-vous déplacé, quand le SMS arrive, alors il nomme l'entreprise, l'ancien
   créneau et au moins un nouveau créneau.
2. Étant donné ce SMS, quand le client le lit, alors il y trouve comment joindre l'artisan [H : la
   réponse par SMS n'est pas prévue par le concept].
3. Étant donné le texte généré, quand on compte ses caractères, alors il en a 160 au plus, en
   alphabet GSM 7 bits [H : limite à confirmer auprès du fournisseur SMS retenu].

#### US-30. Suivre la liste des actions à faire

En tant qu'artisan, je veux voir la liste des actions à faire issues de mes appels et débriefs
(rappeler, envoyer un devis, commander, relancer un paiement) afin de ne rien oublier.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C17

Critères d'acceptation :

1. Étant donné un brouillon validé qui contient des actions, quand l'artisan ouvre « À faire »,
   alors chaque action apparaît avec la clé humaine de son dossier.
2. Étant donné une action faite, quand l'artisan la coche d'un geste, alors elle sort de la liste
   et reste visible dans l'historique du dossier.
3. Étant donné un dossier exporté pour facturation et non marqué « payé » [H], quand le délai
   fixé par l'artisan est dépassé, alors une action « relancer le paiement » est ajoutée.

### EP7. Confiance par conception

#### US-31. Voir la preuve de destruction de l'audio et de la transcription

En tant qu'artisan, je veux voir sur chaque dossier issu d'un appel la preuve que l'audio et la
transcription ont été détruits afin de pouvoir rassurer mes clients.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R2, R3, R4
- Compétences : C12, C20

Critères d'acceptation :

1. Étant donné un appel traité, quand l'artisan ouvre le dossier, alors il lit la mention de
   destruction de chaque élément qui a existé (audio, transcription), avec son heure, portée par
   le bloc `destruction` du contrat `DossierDraft` 1.1 dans le brouillon chiffré (décision D-24).
2. Étant donné une erreur provoquée pendant l'extraction, quand le traitement s'interrompt, alors
   l'audio et la transcription sont quand même détruits (test de conformité).
3. Étant donné un appel traité, quand un test parcourt la base, le stockage objet et les journaux,
   alors il n'y trouve ni audio ni transcription.

#### US-32. Garder ses dossiers chiffrés sur son téléphone

En tant qu'artisan, je veux que mes dossiers soient chiffrés sur mon téléphone et illisibles sans
ma clé, y compris pour le service Muninn, afin de protéger mes données et celles de mes clients.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C4, C17

Critères d'acceptation :

1. Étant donné la base locale copiée hors du téléphone, quand on l'ouvre sans la clé, alors son
   contenu est illisible.
2. Étant donné des données de test identifiables, quand un test les cherche dans toutes les
   colonnes du serveur, alors il ne les trouve pas en clair.
3. Étant donné l'ouverture de l'application, quand les dossiers s'affichent, alors c'est après le
   déverrouillage du téléphone par code ou biométrie [H].

#### US-33. Sauvegarder ses dossiers avec sa propre clé

En tant qu'artisan, je veux une sauvegarde chiffrée dont je détiens seul la clé afin de retrouver
mes dossiers sur un nouveau téléphone en cas de perte ou de casse.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C4, C17

Critères d'acceptation :

1. Étant donné une sauvegarde, quand elle part vers le serveur, alors c'est un blob chiffré sur
   l'appareil que le serveur ne peut pas déchiffrer (test).
2. Étant donné un nouveau téléphone et la clé de l'artisan, quand il restaure, alors il retrouve
   tous ses dossiers.
3. Étant donné la création de la clé, quand elle est générée, alors l'application dit en une
   phrase que sa perte rend la sauvegarde irrécupérable et demande une confirmation.

#### US-34. Archiver ses pièces comptables pendant 10 ans

En tant qu'artisan, je veux que mes pièces comptables soient archivées chiffrées pendant 10 ans
afin de respecter la durée de conservation légale sans démarche de ma part.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1
- Compétences : C4

Critères d'acceptation :

1. Étant donné une pièce comptable validée (ticket, facture), quand elle est archivée, alors un
   blob chiffré est stocké avec une date de fin de conservation à 10 ans (Code de commerce,
   article L123-22).
2. Étant donné une archive dont la date de fin est atteinte, quand la règle de cycle de vie
   s'exécute, alors l'archive est supprimée.
3. Étant donné une demande de suppression d'un dossier qui contient des pièces comptables, quand
   l'artisan la confirme, alors ces pièces restent archivées jusqu'à leur fin de conservation et
   l'artisan en est informé.

#### US-35. Effacer le dossier d'un client qui le demande

En tant qu'artisan, je veux effacer le dossier d'un client qui le demande afin de répondre à sa
demande d'effacement, dans la limite de l'archive légale.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C4

Critères d'acceptation :

1. Étant donné un dossier, quand l'artisan l'efface et confirme, alors il disparaît de l'appareil ;
   la sauvegarde suivante, qui remplace la précédente, ne le contient plus. Les pièces comptables
   restent archivées (US-34).
2. Étant donné une suppression, quand on lit le journal d'audit du serveur, alors il contient
   l'événement sans aucune donnée personnelle.

[H] Les modalités d'exercice des droits sont à valider dans l'AIPD et par l'avis juridique
(condition C3 de l'analyse).

#### US-54. Révoquer un appareil perdu ou volé

En tant qu'artisan, je veux révoquer un appareil perdu ou volé depuis un autre de mes appareils
afin que plus aucune demande ne lui parvienne.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C4, C17

Critères d'acceptation :

1. Étant donné la liste des appareils du compte, quand l'artisan l'ouvre, alors chaque appareil
   apparaît avec sa plateforme et sa dernière activité, et la révocation se fait en un geste suivi
   d'une confirmation.
2. Étant donné un appareil révoqué, quand il envoie sa requête suivante, alors elle est refusée
   (HTTP 401) ; le serveur a effacé l'empreinte de son jeton et son jeton push.
3. Étant donné des enveloppes en attente pour l'appareil révoqué, quand la révocation est
   confirmée, alors elles sont supprimées, et un test vérifie que l'appel suivant ne produit
   aucune enveloppe pour cet appareil.
4. Étant donné une révocation, quand on lit le journal d'audit du serveur, alors il contient
   l'événement sans aucune donnée personnelle.

Cette story découle de la décision D-22 : un nouvel appareil est approuvé par un appareil déjà
enregistré (US-01, critère 5), pour parer l'échange frauduleux de carte SIM. Si l'appareil perdu
était le seul du compte, l'artisan fait d'abord approuver un nouvel appareil par sa phrase de
récupération (US-01, critère 6 ; décision D-28), puis révoque l'ancien depuis celui-ci.

### EP8. Supervision et exploitation

#### US-36. Rejouer un appel synthétique de bout en bout

En tant qu'exploitant, je veux rejouer un scénario d'appel synthétique de bout en bout afin de
vérifier la chaîne sans appel réel ni donnée réelle.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R3, R9, R10
- Compétences : C9, C10, C12

Critères d'acceptation :

1. Étant donné un scénario du jeu synthétique, quand l'exploitant le lance depuis la console,
   alors le fournisseur de téléphonie factice produit la fin d'appel et déclenche l'extraction
   réelle.
2. Étant donné le scénario terminé, quand la console affiche le brouillon, alors elle affiche
   aussi la vérité terrain et l'écart champ par champ.
3. Étant donné une démonstration complète, quand on consulte les comptes des fournisseurs, alors
   aucun numéro n'a été acheté et aucun appel ni SMS réel n'a été émis.
4. Étant donné les données de démonstration, quand on parcourt le dépôt, alors elles sont toutes
   synthétiques.

#### US-37. Évaluer l'extraction sur le jeu synthétique

En tant qu'exploitant, je veux lancer l'évaluation de l'extraction sur le jeu synthétique
versionné afin de savoir si une version du prompt ou du modèle atteint le seuil de qualité.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R5, R9
- Compétences : C11, C12, C13

Critères d'acceptation :

1. Étant donné le jeu synthétique, quand l'évaluation se termine, alors un rapport horodaté donne
   l'exactitude par champ clé (nom, téléphone, commune, objet court, urgence, rendez-vous),
   l'exactitude globale, le taux de `needs_review`, la latence p50 et p95 et le coût par appel.
   Chaque proportion est donnée avec l'effectif et un intervalle de confiance à 95 % (Wilson).
2. Étant donné deux versions évaluées, quand l'exploitant compare leurs rapports, alors l'écart de
   chaque métrique est affiché.
3. Étant donné une exactitude globale des champs clés (tous champs clés confondus) inférieure à
   90 %, quand l'évaluation se termine, alors le rapport indique « seuil non atteint ».
4. Étant donné un même jeu et une même version, quand l'évaluation est relancée, alors les
   métriques restent à 2 points près [H : tolérance à recaler après mesure de la variabilité du
   modèle].

#### US-38. Suivre la qualité de l'extraction et être alerté

En tant qu'exploitant, je veux suivre en continu les métriques de l'extraction et recevoir une
alerte en cas de dérive afin de détecter une baisse de qualité avant les artisans.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R1, R4
- Compétences : C11, C20

Critères d'acceptation :

1. Étant donné des extractions traitées, quand l'exploitant ouvre le tableau de bord, alors il
   voit le volume, le taux d'échec de validation du schéma, le taux de `needs_review`, la latence
   p50 et p95, le coût, le taux de correction par champ et la part des brouillons validés sans
   correction.
2. Étant donné un seuil d'alerte [H : `needs_review` au-dessus de 20 % sur une heure, avec au
   moins 20 extractions], quand il est franchi, alors une alerte est émise et visible dans la console.
3. Étant donné les données du tableau de bord, quand un test les inspecte, alors aucune ne
   contient de nom, de numéro, d'adresse ni de contenu de dossier.

#### US-39. Diagnostiquer avec des journaux sans donnée personnelle

En tant qu'exploitant, je veux des journaux sans donnée personnelle, reliés par un identifiant de
requête, afin de diagnostiquer un incident sans exposer les clients.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R3, R4
- Compétences : C20, C21

Critères d'acceptation :

1. Étant donné une requête qui contient des données de test identifiables, quand un test cherche
   ces données dans les journaux, alors il ne les trouve pas.
2. Étant donné une réponse d'erreur, quand l'exploitant cherche son `request_id`, alors il
   retrouve toutes les lignes de journal liées.
3. Étant donné un incident résolu, quand l'exploitant rédige la fiche d'incident, alors elle cite
   les identifiants de requête et ne contient aucune donnée personnelle.

#### US-40. Livrer une version du prompt ou du modèle sans régression

En tant qu'exploitant, je veux qu'une nouvelle version du prompt, du schéma ou du modèle ne soit
livrée que si les tests et l'évaluation passent, et pouvoir revenir à la version précédente, afin
d'éviter une régression de la qualité en production.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R5, R8, R9
- Compétences : C12, C13, C18, C19

Critères d'acceptation :

1. Étant donné une modification du prompt, quand la chaîne d'intégration continue s'exécute,
   alors elle lance le lint, le typage, les tests unitaires, les tests de conformité et
   l'évaluation, et bloque la livraison si l'une de ces étapes échoue.
2. Étant donné une extraction ou un rapport, quand on les lit, alors ils indiquent les versions du
   prompt, du schéma et du modèle utilisés.
3. Étant donné une régression constatée, quand l'exploitant déclenche le retour arrière, alors la
   version précédente est rétablie et une extraction de contrôle le confirme.
4. Étant donné un secret ajouté par erreur dans le dépôt, ou un fournisseur d'IA configuré hors
   d'un point de terminaison UE, quand la chaîne s'exécute, alors elle échoue. La zéro rétention
   est vérifiée dans la console du fournisseur et consignée avant toute mise en service [H :
   ADR-03].

#### US-41. Surveiller la disponibilité et les purges

En tant qu'exploitant, je veux surveiller la disponibilité du service et l'exécution des purges
afin de vérifier que le relais fonctionne et que les durées de conservation sont respectées.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : R1, R4
- Compétences : C4, C20

Critères d'acceptation :

1. Étant donné le service démarré, quand on interroge les points de santé et de disponibilité,
   alors ils répondent et signalent toute dépendance indisponible (base de données, file de
   tâches).
2. Étant donné des enveloppes expirées et des sessions d'appel de plus de 90 jours [H : durée à
   valider dans l'AIPD], quand la purge planifiée s'exécute, alors elles sont supprimées et leur
   nombre est journalisé.
3. Étant donné une purge en échec, quand l'échec est détecté, alors une alerte est émise.

### EP9. Hors MVP (frontière du périmètre)

Ces stories ne seront pas réalisées dans le MVP. Elles sont écrites pour rendre la frontière du
périmètre vérifiable.

#### US-42. Disposer d'un numéro professionnel complet

En tant qu'artisan, je veux un numéro professionnel Muninn complet, avec annonce d'enregistrement,
afin de couvrir aussi les appels que je décroche.

- Priorité : Could
- Horizon : V2
- Démo : non
- Règles : R2, R6
- Compétences : sans objet

Critères d'acceptation :

1. Étant donné un appel sur le numéro professionnel, quand l'enregistrement est actif, alors il
   est annoncé avant toute conversation.
2. Étant donné cette fonction, quand sa conception commence, alors un avis juridique et une mise à
   jour de l'AIPD la précèdent.

Conflit à signaler : l'enregistrement d'un appel contredit R2 tel qu'il est écrit pour le MVP. La
règle devra être revue avec l'avis juridique avant toute conception.

#### US-43. Bénéficier du lexique d'un autre métier

En tant qu'artisan d'un métier sans lexique dans le MVP (serrurerie [H], paysage, petits travaux),
je veux un lexique adapté afin d'obtenir la même précision que les métiers du MVP.

- Priorité : Could
- Horizon : V2
- Démo : non
- Règles : R5
- Compétences : C8, C12

Critères d'acceptation :

1. Étant donné un nouveau lexique, quand il est proposé à la livraison, alors une évaluation sur
   un jeu synthétique dédié au métier précède sa mise en service.
2. Étant donné ce lexique livré, quand l'artisan choisit le métier, alors le lexique est appliqué
   comme en US-15.

#### US-44. Faire écouter ses appels natifs par Muninn

En tant qu'artisan, je veux que Muninn écoute mes conversations téléphoniques décrochées afin de
ne pas avoir à faire de débrief.

- Priorité : Won't
- Horizon : hors périmètre
- Démo : non
- Règles : R2
- Compétences : sans objet

Critères d'acceptation :

1. Étant donné l'application installée, quand on inspecte ses permissions, alors elle ne demande
   aucun accès à l'audio des appels du téléphone.
2. Étant donné un appel décroché, quand l'artisan veut garder une trace, alors Muninn lui propose
   le débrief vocal (US-13, US-14).

Raison de l'exclusion : impossibilité technique pour une application tierce et risque pénal
(analyse, section 1.4).

#### US-45. Facturer et déclarer ses ventes depuis Muninn

En tant qu'artisan, je veux facturer depuis un dossier de Muninn et que les données de mes ventes
soient transmises à l'administration (e-reporting), afin de respecter la réforme sans changer
d'outil.

Pour un artisan qui travaille surtout pour des particuliers, l'enjeu principal est l'e-reporting :
les factures à des particuliers ne relèvent pas de la facture électronique.

Historique : « Won't » jusqu'au 14 octobre 2026 (marché saturé, levier 4) ; D-53 a ouvert les
devis, D-55 ouvre la facturation électronique à l'horizon V3 ou V4.

- Priorité : Could
- Horizon : V3 [H : V3 ou V4, à fixer]
- Démo : non
- Règles : R1, R5
- Compétences : C17

Critères d'acceptation :

1. Étant donné un dossier terminé, quand l'artisan émet une facture, alors elle part par la
   plateforme agréée partenaire ; Muninn n'est pas lui-même plateforme agréée.
2. Étant donné une vente à un particulier, quand elle est facturée, alors les données
   d'e-reporting sont transmises par la même plateforme [H : obligations à vérifier à la date du lot].
3. Étant donné un artisan qui garde son outil de facturation, quand il veut facturer, alors
   l'export (US-24) reste disponible.

Éléments de la section 4.4 non déclinés en stories :

| Élément                                   | Horizon                     | Raison                                                                                  |
| ----------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------- |
| Parrainage intégré                        | V2                          | Fonction d'acquisition, sans lien avec la promesse d'usage                              |
| Module SAAD (aide à domicile, financeurs) | Deuxième année, B2B         | Données de santé (R7), hébergement HDS, autre client                                    |
| Devenir plateforme agréée                 | Hors périmètre              | Décision de l'analyse ; l'import passe par un partenaire (US-25)                        |
| Abonnement et essai d'un mois             | MVP (lot 6 de la passation) | Fonction commerciale sans effet sur la promesse d'usage ; story à écrire avant le lot 6 |

### EP10. Données de référence

Cette épopée porte l'alimentation des données publiques dont le produit dépend : référentiels
géographiques et de numérotation, lexique métier, jours fériés, et leur mise à disposition par une
API. Elle porte aussi le dimensionnement du marché, demandé par l'analyse (section 1.1). Les
sources sont décrites dans le document 03 (SRC-01 à SRC-14). Les données servies sont publiques et
ne concernent aucun client final ; en revanche, les demandes de contrôle (US-50, US-51) portent des
fragments de données de client (commune, code postal, préfixe de numéro).

#### US-46. Charger et tenir à jour les référentiels géographiques

En tant qu'exploitant, je veux charger et tenir à jour les codes postaux, les communes et les voies
à partir des sources officielles afin que les adresses extraites soient contrôlées sans envoyer de
donnée de client à un tiers.

- Priorité : Must
- Horizon : MVP
- Démo : **oui** (codes postaux et communes ; voies hors démo)
- Règles : Aucune
- Compétences : C1, C3, C4

Critères d'acceptation :

1. Étant donné la base des codes postaux (SRC-06) et le COG (SRC-07), quand la chaîne de
   chargement s'exécute, alors chaque code postal et chaque code commune est stocké comme texte
   (« 01400 » reste « 01400 »), le fichier de La Poste est converti de l'ISO-8859-1 en UTF-8 et
   chaque commune porte le nom officiel accentué du COG.
2. Étant donné la liste complète des communes lue dans l'API Géo (SRC-03), quand elle est
   comparée au COG, alors le rapport de chargement donne les écarts constatés (34 969 contre
   34 875 communes le 12 octobre 2026) et chaque ligne rejetée avec son motif ; aucune ligne n'est
   écartée en silence.
3. Étant donné l'API Géo, quand un test inspecte les appels de la chaîne, alors elle n'est
   interrogée qu'en masse (liste des communes), jamais avec une donnée extraite d'un appel ou d'un
   débrief. La Géoplateforme (SRC-04) n'est appelée qu'avec des adresses synthétiques.
4. Étant donné une nouvelle version d'une source (BAN quotidienne, codes postaux semestriels, COG
   annuel), quand la mise à jour planifiée s'exécute, alors la version précédente reste servie
   jusqu'à la fin des contrôles de la nouvelle, et la version servie (source, date) est lisible
   par l'API des référentiels (US-50). Pour la BAN (SRC-05), seuls la voie, le code postal et le
   code commune sont chargés [H : sous-ensemble limité à quelques départements au MVP].

#### US-47. Charger le référentiel de numérotation téléphonique

En tant qu'exploitant, je veux charger les tranches de numéros attribuées par l'ARCEP afin de
contrôler un numéro dicté et de savoir s'il s'agit d'un mobile, seul capable de recevoir les SMS.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : Aucune
- Compétences : C1, C3, C4

Critères d'acceptation :

1. Étant donné le fichier MAJNUM (SRC-13, encodage ANSI, séparateur `;`), quand il est chargé,
   alors toutes ses tranches sont stockées en UTF-8, préfixes et bornes lus comme texte, et le
   rapport donne le nombre de lignes lues, chargées et rejetées (20 886 tranches le
   8 octobre 2026).
2. Étant donné une ligne mal formée ou une tranche dont la fin précède le début, quand le
   chargement s'exécute, alors elle est rejetée et citée dans le rapport avec son motif.
3. Étant donné une taille annoncée par la fiche data.gouv.fr différente du fichier reçu (3,76 Mo
   annoncés contre 1,16 Mo reçus le 12 octobre 2026), quand le téléchargement se termine, alors le
   contrôle porte sur le fichier reçu (taille, en-tête de colonnes), pas sur la fiche.
4. Étant donné un préfixe de numéro, quand on consulte le référentiel, alors il indique si le
   bloc est attribué et s'il relève d'un mobile ou d'un fixe [H : règle mobile et fixe à confirmer
   dans le plan de numérotation de l'ARCEP].

#### US-48. Constituer et versionner le lexique métier

En tant qu'exploitant, je veux constituer le lexique de chaque métier à partir du Wiktionnaire, de
Wikidata et d'une saisie manuelle relue afin d'alimenter la transcription et l'extraction (US-15)
avec un vocabulaire vérifié et daté.

- Priorité : Must
- Horizon : MVP
- Démo : non
- Règles : Aucune
- Compétences : C1, C3, C8

Critères d'acceptation :

1. Étant donné les catégories du Wiktionnaire (SRC-12), quand la collecte s'exécute, alors elle
   ne lit que des pages `/wiki/` autorisées par robots.txt, avec un `User-Agent` explicite, une
   requête à la fois et une pause entre deux requêtes [H : 1 s].
2. Étant donné le point SPARQL de Wikidata (SRC-11) qui répond HTTP 429 ou ne répond pas, quand
   la collecte s'exécute, alors elle respecte l'en-tête `Retry-After`, s'arrête après un nombre
   borné d'essais et signale que la liste de marques n'a pas été rafraîchie.
3. Étant donné des termes candidats (collectés ou saisis à la main, dont tout le lexique du
   chauffage, absent du Wiktionnaire), quand l'exploitant les relit, alors seuls les termes
   acceptés entrent dans le lexique ; les doublons sont fusionnés et les termes hors dépannage
   sont écartés avec leur motif.
4. Étant donné un lexique publié, quand on le lit, alors il porte son métier, sa version, sa date
   et la liste de ses sources avec leur licence (CC BY-SA 4.0 pour le Wiktionnaire, CC0 pour
   Wikidata) ; une nouvelle version n'est servie qu'après l'évaluation de US-15 (critère 2).

#### US-49. Exclure les jours fériés des créneaux proposés

En tant qu'artisan, je veux que l'agent ne propose aucun créneau un jour férié de ma zone, sauf si
je déclare travailler ce jour-là, afin de ne pas promettre une intervention que je n'assurerai pas.

- Priorité : Should
- Horizon : MVP
- Démo : non
- Règles : Aucune
- Compétences : C1, C3

Critères d'acceptation :

1. Étant donné l'API Jours fériés (SRC-08), quand le chargement annuel s'exécute, alors les jours
   fériés de l'année en cours et de la suivante sont copiés localement pour chaque zone ; l'agent
   ne dépend pas de la disponibilité de l'API pendant un appel.
2. Étant donné un artisan d'un département d'Alsace-Moselle (57, 67, 68) [H : règle à confirmer
   dans le Code du travail], quand ses créneaux sont calculés, alors la zone `alsace-moselle` est
   appliquée (Vendredi saint et 26 décembre en plus) [H : le département de l'artisan est absent
   de la configuration de ligne de la passation].
3. Étant donné un jour férié non travaillé, quand l'agent propose un créneau ou annonce le
   « prochain jour d'ouverture » (US-02, critère 2), alors ce jour est sauté.
4. Étant donné un jour férié que l'artisan déclare travaillé, quand l'agent calcule les créneaux,
   alors les plages libres de ce jour sont proposées.

#### US-50. Mettre les référentiels à disposition par une API REST

En tant qu'exploitant, je veux exposer les référentiels par une API REST documentée et réservée
aux composants de Muninn afin que l'extraction et l'agent les consultent sans accès direct à la
base.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R4, R5
- Compétences : C2, C5

Critères d'acceptation :

1. Étant donné le contrat OpenAPI de l'API, quand on le lit, alors il décrit au minimum : les
   communes d'un code postal, le contrôle d'un couple code postal et commune, le contrôle d'un
   préfixe de numéro, les jours fériés d'une zone et d'une année, le lexique d'un métier dans une
   version donnée, et le format d'erreur unique (`code`, `message`, `request_id`).
2. Étant donné une requête sans jeton de service valide, quand elle arrive, alors elle est
   refusée (HTTP 401) ; l'API n'est pas exposée sur Internet [H].
3. Étant donné une demande de contrôle qui porte une donnée extraite, quand un test cherche cette
   donnée de test identifiable dans les journaux de l'API et du proxy, alors il ne la trouve pas.
   Les données à contrôler passent dans le corps d'une requête POST, jamais dans l'URL, et le
   numéro n'est transmis que par son préfixe de bloc [H : 7 chiffres, granularité à confirmer
   sur le fichier MAJNUM].
4. Étant donné une réponse, quand on la lit, alors elle cite la version du référentiel utilisé
   (source et date) ; le 95e centile de la latence est inférieur à 50 ms [H] pour ne pas peser sur
   l'objectif de 30 secondes de US-12.

#### US-51. Contrôler la commune, le code postal et le téléphone extraits

En tant qu'artisan, je veux que la commune, le code postal et le numéro extraits soient contrôlés
par les référentiels officiels afin de ne jamais recevoir une adresse ou un numéro faux sans
avertissement.

- Priorité : Must
- Horizon : MVP
- Démo : **oui**
- Règles : R1, R3, R4
- Compétences : C3, C5, C9, C12

Critères d'acceptation :

1. Étant donné un code postal et une commune incohérents (« 93100 » et « Bagnolet »), quand le
   contrôle s'exécute, alors la confiance de ces champs passe sous 0,7 et ils portent la mention
   « à vérifier » ; aucune valeur n'est remplacée en silence.
2. Étant donné une commune reconnue sous une autre graphie (« montreuil », ou le nom d'une
   commune déléguée), quand le contrôle s'exécute, alors le brouillon porte le nom officiel du COG
   et la valeur entendue reste consultable par l'artisan [H].
3. Étant donné un numéro dicté (`origin = spoken`) hors des tranches attribuées, quand le contrôle
   s'exécute, alors le champ `telephone` est marqué « à vérifier » ; un numéro fixe est signalé
   comme incapable de recevoir les rappels par SMS.
4. Étant donné l'API des référentiels indisponible, quand l'extraction se termine, alors le
   brouillon est quand même produit et transmis, les champs sont marqués « non contrôlé » et
   l'événement est compté dans les métriques (US-38). Le résultat est porté par champ dans le
   contrat `DossierDraft` 1.1 (décision D-24) : statut `not_checked`, confiance ramenée sous 0,7.

#### US-52. Dimensionner la tête de pont dans Sirene

En tant que porteur du projet, je veux compter les artisans solo de la tête de pont dans les
fichiers stock de Sirene afin de dimensionner le marché sur une base datée, reproductible et sans
donnée nominative.

- Priorité : Should
- Horizon : MVP [H : étude préalable au lancement, sans fonction dans l'application]
- Démo : non
- Règles : R4, R9
- Compétences : C1, C2, C3

Critères d'acceptation :

1. Étant donné les fichiers Parquet StockEtablissement et StockUniteLegale (SRC-01), quand la
   requête s'exécute, alors seules les colonnes listées dans la fiche SRC-01 sont lues ; un test
   vérifie qu'aucune colonne d'identité ni d'adresse fine n'est lue.
2. Étant donné les établissements actifs des codes NAF 43.21A, 43.22A, 43.22B et 43.32B (SRC-09),
   quand l'agrégation se termine, alors elle donne des comptages par code NAF, tranche d'effectif
   (`NN` distinct de `00`, valeurs vides à part), catégorie juridique et département ; aucun SIREN
   n'est conservé, et les cellules de moins de 5 entreprises [H] sont regroupées avant diffusion.
3. Étant donné une exécution, quand elle se termine, alors le rapport donne la date du stock, la
   version de la requête, la durée, la mémoire maximale et le volume lu ; une seconde exécution
   sur le même stock donne les mêmes comptages.
4. Étant donné le traitement terminé, quand on inspecte le poste et le dépôt, alors le fichier
   source a été supprimé, seul l'agrégat est gardé, et aucun fichier Sirene n'est dans le dépôt.

#### US-53. Croiser Sirene avec les séries de l'Urssaf

En tant que porteur du projet, je veux croiser le comptage Sirene avec les séries de l'Urssaf sur
les micro-entrepreneurs du BTP afin d'encadrer la taille du marché par une borne haute et une
estimation des entreprises économiquement actives.

- Priorité : Should
- Horizon : MVP [H : étude préalable au lancement, sans fonction dans l'application]
- Démo : non
- Règles : Aucune
- Compétences : C1, C3

Critères d'acceptation :

1. Étant donné les fichiers NAF de l'INSEE (SRC-09), quand la table de référence est construite,
   alors chaque code de la tête de pont est rattaché à un métier Muninn, en NAF rév. 2 et en
   NAF 2025 par la table de correspondance, pour les stocks publiés après le 1er janvier 2027.
2. Étant donné l'API Explore de l'Urssaf (SRC-10), quand la collecte s'exécute, alors elle lit
   toutes les pages de la série du secteur F2 et garde le dernier trimestre publié, avec les
   effectifs administrativement et économiquement actifs.
3. Étant donné les deux sources, quand le rapport est produit, alors chaque chiffre porte sa
   source et sa date, l'écart de périmètre est dit (le secteur F2 ne correspond pas exactement aux
   quatre métiers) et le chiffre FFB non daté de l'analyse est remplacé.
4. Étant donné l'agrégat dérivé de l'Urssaf, quand il est diffusé hors de l'équipe, alors il porte
   l'attribution et la licence ODbL.

## 6. Couverture

### 6.1 Propositions de valeur et configuration

| Élément du concept                               | Stories                                                    |
| ------------------------------------------------ | ---------------------------------------------------------- |
| PV1. Messagerie intelligente                     | US-06 à US-12, US-51                                       |
| PV2. Débrief vocal                               | US-13, US-14                                               |
| PV3. Clé humaine de dossier                      | US-17 à US-20                                              |
| PV4. Rentabilité et export                       | US-21 à US-24 (MVP), US-25 et US-55 (V2), US-45 (V3 ou V4) |
| PV5. Imprévus et rendez-vous                     | US-26 à US-30                                              |
| PV6. Confiance par conception                    | US-31 à US-35, US-54                                       |
| Configuration de la ligne et du renvoi           | US-01 à US-04                                              |
| Disponibilités                                   | US-05, US-08, US-26, US-49                                 |
| Lexique métier et personnel (levier 3)           | US-15, US-16, US-43, US-48                                 |
| Supervision                                      | US-36 à US-41                                              |
| Référentiels et normalisation des champs         | US-46, US-47, US-50, US-51                                 |
| Dimensionnement du marché (analyse, section 1.1) | US-52, US-53                                               |

### 6.2 Règles R1 à R10

| Règle | Objet                                             | Stories                                                                                                                                     |
| ----- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| R1    | Aucun dossier en clair côté serveur               | US-01, US-05, US-08, US-12, US-16 à US-21, US-23 à US-28, US-30, US-32 à US-35, US-38, US-41, US-45, US-51, US-54, US-55                    |
| R2    | Audio détruit après extraction                    | US-04, US-10, US-11, US-13, US-14, US-22, US-31, US-42, US-44                                                                               |
| R3    | Transcriptions éphémères                          | US-11, US-13, US-16, US-18, US-22, US-31, US-36, US-39, US-51                                                                               |
| R4    | Journaux sans donnée personnelle                  | US-01, US-05, US-11, US-12, US-16, US-17, US-20, US-21, US-26 à US-29, US-31, US-35, US-38, US-39, US-41, US-50, US-51, US-52, US-54, US-55 |
| R5    | Hébergement et traitement dans l'UE               | US-11, US-13, US-15, US-21, US-22, US-25, US-37, US-40, US-43, US-45, US-50, US-55                                                          |
| R6    | L'agent s'annonce toujours                        | US-02, US-04, US-06, US-07, US-09, US-10, US-42                                                                                             |
| R7    | Aucune donnée de santé                            | US-09, US-11, US-13, US-55                                                                                                                  |
| R8    | Pas de secret dans le dépôt                       | US-40                                                                                                                                       |
| R9    | Aucune donnée réelle dans le dépôt                | US-36, US-37, US-40, US-52                                                                                                                  |
| R10   | Aucune action payante ou irréversible sans accord | US-01, US-27, US-36                                                                                                                         |

R10 concerne le développement (achat de numéro, SMS réels, déploiement). Les stories US-03 et
US-28 reprennent son esprit pour l'utilisateur (aucune action à sa place, aucun envoi sans
validation) sans en relever.

R5 n'est testé directement que par US-40 (critère 4), de façon transverse. Les autres stories qui
citent R5 appellent un fournisseur d'IA et sont couvertes par ce contrôle.

### 6.3 Compétences du référentiel

| Compétences | Stories                                                                                                    | Remarque                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| C1          | US-25, US-46 à US-49, US-52, US-53                                                                         | Extraction automatisée des sources SRC-01 à SRC-14 (phase 3)                                |
| C2          | US-50, US-52                                                                                               | Requêtes SQL sur la base des référentiels et sur Sirene                                     |
| C3          | US-11, US-46 à US-49, US-51 à US-53                                                                        | Normalisation des champs extraits (E.164, code postal), nettoyage et agrégation des sources |
| C4          | US-01, US-05, US-12, US-32 à US-35, US-41, US-46, US-47, US-54                                             | Base conforme au RGPD, durées de conservation, base des référentiels                        |
| C5          | US-50, US-51                                                                                               | API REST des référentiels, consommée par l'extraction                                       |
| C6, C7      | sans objet                                                                                                 | Portées par la phase 0b (veille, benchmark)                                                 |
| C8          | US-02, US-06 à US-11, US-13, US-15, US-16, US-21, US-22, US-25, US-28, US-43, US-48, US-55                 | Paramétrage des services de transcription et de LLM                                         |
| C9          | US-07, US-11, US-12, US-13, US-21, US-22, US-36, US-51, US-55                                              | API exposant l'extraction                                                                   |
| C10         | US-13, US-17, US-36                                                                                        | Intégration de l'API dans une interface accessible                                          |
| C11         | US-17, US-37, US-38                                                                                        | Métriques de qualité et tableau de bord                                                     |
| C12         | US-06, US-09, US-11, US-15, US-31, US-36, US-37, US-40, US-43, US-51, US-55                                | Évaluation des réponses, validation des formats, conformité                                 |
| C13         | US-37, US-40                                                                                               | Livraison contrôlée, versionnage, retour arrière                                            |
| C14         | toutes                                                                                                     | Ce document et le document 04                                                               |
| C15, C16    | sans objet                                                                                                 | Portées par la phase 2 (architecture, méthode agile)                                        |
| C17         | US-01 à US-05, US-12, US-14, US-16 à US-20, US-23, US-24, US-26 à US-30, US-32, US-33, US-45, US-54, US-55 | Composants et interfaces                                                                    |
| C18, C19    | US-40                                                                                                      | Intégration et livraison continues                                                          |
| C20         | US-31, US-38, US-39, US-41                                                                                 | Surveillance et journalisation conforme                                                     |
| C21         | US-39                                                                                                      | Fiches d'incident                                                                           |

## 7. Synthèse

| ID    | Titre court                              | Priorité | Horizon        | Démo |
| ----- | ---------------------------------------- | -------- | -------------- | ---- |
| US-01 | Compte et téléphone liés par code        | Must     | MVP            | non  |
| US-02 | Réglage de la ligne Muninn               | Must     | MVP            | non  |
| US-03 | Codes de renvoi par opérateur            | Must     | MVP            | non  |
| US-04 | Appel de test du renvoi                  | Should   | MVP            | non  |
| US-05 | Disponibilités partagées sans détail     | Must     | MVP            | non  |
| US-06 | Annonce de l'assistant automatique       | Must     | MVP            | non  |
| US-07 | Demande exposée et reformulée            | Must     | MVP            | non  |
| US-08 | Créneau proposé ou rappel annoncé        | Must     | MVP            | non  |
| US-09 | Consigne de sécurité en cas de danger    | Must     | MVP            | non  |
| US-10 | Refus de l'assistant                     | Must     | MVP            | non  |
| US-11 | Brouillon de dossier extrait de l'appel  | Must     | MVP            | oui  |
| US-12 | Notification et dossier chiffré          | Must     | MVP            | non  |
| US-13 | Débrief vocal                            | Must     | MVP            | non  |
| US-14 | Invitation au débrief                    | Should   | MVP            | non  |
| US-15 | Lexique métier                           | Must     | MVP            | non  |
| US-16 | Lexique personnel                        | Should   | MVP            | non  |
| US-17 | Validation en un geste                   | Must     | MVP            | oui  |
| US-18 | Recherche par clé humaine                | Must     | MVP            | non  |
| US-19 | Désambiguïsation par une question        | Must     | MVP            | non  |
| US-20 | Rattachement d'un client connu           | Must     | MVP            | non  |
| US-21 | Ticket photographié en dépense           | Must     | MVP            | non  |
| US-22 | Dépense dictée                           | Must     | MVP            | non  |
| US-23 | Marge par chantier                       | Must     | MVP            | non  |
| US-24 | Export vers l'outil de facturation       | Must     | MVP            | non  |
| US-25 | Import des factures électroniques        | Could    | V2             | non  |
| US-26 | Rendez-vous de l'assistant dans l'agenda | Must     | MVP            | non  |
| US-27 | Rappels de rendez-vous par SMS           | Should   | MVP            | non  |
| US-28 | Imprévu géré en un geste                 | Must     | MVP            | non  |
| US-29 | SMS clair au client                      | Should   | MVP            | non  |
| US-30 | Liste des actions à faire                | Should   | MVP            | non  |
| US-31 | Preuve de destruction                    | Must     | MVP            | oui  |
| US-32 | Dossiers chiffrés sur le téléphone       | Must     | MVP            | non  |
| US-33 | Sauvegarde avec sa propre clé            | Must     | MVP            | non  |
| US-34 | Archive légale de 10 ans                 | Should   | MVP            | non  |
| US-35 | Suppression à la demande du client       | Should   | MVP            | non  |
| US-36 | Simulateur d'appel de bout en bout       | Must     | MVP            | oui  |
| US-37 | Évaluation de l'extraction               | Must     | MVP            | oui  |
| US-38 | Tableau de bord et alertes de qualité    | Must     | MVP            | oui  |
| US-39 | Journaux sans donnée personnelle         | Must     | MVP            | oui  |
| US-40 | Livraison contrôlée et retour arrière    | Must     | MVP            | oui  |
| US-41 | Disponibilité et purges                  | Should   | MVP            | non  |
| US-42 | Numéro professionnel complet             | Could    | V2             | non  |
| US-43 | Lexiques d'autres métiers                | Could    | V2             | non  |
| US-44 | Écoute des appels natifs                 | Won't    | hors périmètre | non  |
| US-45 | Facturer et déclarer ses ventes          | Could    | V3             | non  |
| US-46 | Référentiels géographiques               | Must     | MVP            | oui  |
| US-47 | Référentiel de numérotation              | Must     | MVP            | oui  |
| US-48 | Lexique métier constitué et versionné    | Must     | MVP            | non  |
| US-49 | Jours fériés exclus des créneaux         | Should   | MVP            | non  |
| US-50 | API REST des référentiels                | Must     | MVP            | oui  |
| US-51 | Contrôle des champs par les référentiels | Must     | MVP            | oui  |
| US-52 | Dimensionnement Sirene                   | Should   | MVP            | non  |
| US-53 | Croisement avec l'Urssaf                 | Should   | MVP            | non  |
| US-54 | Révocation d'un appareil                 | Must     | MVP            | non  |
| US-55 | Préparation d'un devis (D-53)            | Should   | V2             | non  |

Décompte : 55 stories ; 49 au MVP (37 Must, 12 Should), 4 en V2 (US-25, US-42, US-43, US-55), 1 en
V3 ou V4 (US-45), 1 hors périmètre (US-44) ; 12 dans la démo. US-52 et US-53 sont classées au MVP comme études
préalables au lancement ; elles n'ajoutent aucune fonction à l'application.

## 8. Périmètre minimal de la démo du 29 octobre

### 8.1 Ce que la démo doit prouver

Le premier oral évalue E3 : une API qui expose un modèle d'IA (C9), son intégration dans une
interface accessible (C10), son monitoring (C11), ses tests (C12) et sa livraison continue (C13).
La démo doit donc montrer la chaîne critique du produit, de l'appel à l'écran, avec une
extraction réelle, et les preuves d'exploitation autour.

**Proposition de la v2 : une seule chaîne pour E1 et E3.** L'extraction contrôle la commune, le
code postal et le téléphone par l'API des référentiels (US-50, US-51). Ces référentiels sont
chargés par la chaîne de données d'E1 (US-46, US-47). La même démo montre alors les données
collectées et nettoyées (C1, C3), la base (C4), l'API qui les expose (C5) et leur usage par le
service d'IA (C9 à C13). Le jury d'E1 voit les données servir le produit, pas une chaîne isolée.

Scénario de démonstration proposé (environ 6 minutes) :

1. L'exploitant lance depuis la console un scénario synthétique, par exemple une fuite sous
   l'évier à Montreuil (US-36).
2. Le fournisseur factice produit la fin d'appel ; l'extraction réelle produit un brouillon
   validé par le schéma (US-11).
3. L'extraction appelle l'API des référentiels : la commune prend son nom officiel, le couple
   code postal et commune est contrôlé, le numéro dicté est confronté aux tranches de l'ARCEP
   (version de test qui déclare valide la plage fictive des numéros synthétiques, document 02,
   F-11, T1 [H]). Un
   second scénario, où l'appelant dit « 93100 Bagnolet », montre le champ marqué « à vérifier »
   (US-51). La console affiche la version du référentiel utilisée (US-50).
4. La console affiche le brouillon, les champs « à vérifier », la vérité terrain et la preuve de
   destruction de la transcription (US-31, US-36).
5. L'artisan corrige un champ et valide en un geste (US-17).
6. Le tableau de bord montre la métrique mise à jour, dont le taux de champs « non contrôlé »,
   et le journal montre une ligne sans donnée personnelle (US-38, US-39).
7. Le rapport d'évaluation et la chaîne d'intégration continue montrent le seuil de 90 % et le
   blocage d'une version dégradée (US-37, US-40).
8. Un scénario « odeur de gaz » montre `urgence = securite` dans le brouillon (US-09, critère 3,
   pour le seul champ extrait ; la consigne vocale reste hors démo) et un scénario médical montre
   le refus de collecte (US-11).

### 8.2 Stories retenues et charge estimée

| Jour | Stories             | Travail                                                                                                                               |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| J1   | US-11               | Schéma `DossierDraft`, normalisation, interfaces des fournisseurs et fournisseurs factices                                            |
| J2   | US-11               | Prompt d'extraction versionné, appel au LLM réel, relance unique, `needs_review`, refus médical                                       |
| J3   | US-46, US-47        | Chargement des codes postaux (SRC-06), du COG (SRC-07), de la liste de l'API Géo (SRC-03) et de MAJNUM (SRC-13) ; rapport d'anomalies |
| J4   | US-50, US-51        | API REST des référentiels, appel depuis l'extraction, baisse de confiance, mode dégradé, tests sans donnée dans les journaux          |
| J5   | US-36, US-37        | Jeu synthétique de démonstration [H : 20 scénarios ; la passation en vise 100], harnais d'évaluation, rapport                         |
| J6   | US-36, US-17, US-31 | Console web : lancement d'un scénario, affichage du brouillon et du contrôle, validation, preuve de destruction                       |
| J7   | US-38, US-39        | Métriques, tableau de bord, seuil d'alerte, journalisation avec filtre de redaction                                                   |
| J8   | US-40, US-31        | Chaîne d'intégration continue, évaluation bloquante, retour arrière, tests de conformité                                              |
| J9   | toutes              | Marge pour les imprévus, accessibilité de la console (document 04), répétition                                                        |

Total : 9 jours pour une personne, contre 7 dans la v1. L'estimation est une hypothèse **[H]** :
elle suppose le fournisseur LLM choisi et la clé d'API obtenue avant le 17 octobre, avec l'accord
du porteur (R10).

**Coût de la proposition.** Elle ajoute 2 jours au plan de la démo (J3 et J4) [H] :

- environ 1,5 jour (chargement des quatre petits fichiers et API REST) était déjà dû à E1 en
  phase 3 (C1, C3, C4, C5). Il change de place, pas de nature ;
- environ 0,5 jour est un vrai surcoût : appel depuis l'extraction, mode dégradé, affichage dans
  la console ;
- le contrat `DossierDraft` passe en version 1.1 (décision D-24) : le résultat du contrôle
  figure par champ (US-51, critère 4), en plus de la baisse de confiance ;
- le risque nouveau : un défaut de l'API des référentiels peut casser la démo d'E3. Le mode
  dégradé de US-51 (critère 4) le contient.

Restent en phase 3, hors de ces 9 jours : la BAN (SRC-05), le lexique (US-48), les jours fériés
(US-49) et le dimensionnement Sirene et Urssaf (US-52, US-53).

### 8.3 Ce qui reste hors démo, et pourquoi

| Élément                                   | Stories                                     | Raison                                                                                                                     |
| ----------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Agent vocal temps réel                    | US-06 à US-10                               | Exige transcription en flux, synthèse vocale et téléphonie. Le simulateur le remplace, comme prévu par la feuille de route |
| Transcription de l'audio                  | US-13, US-15                                | Le simulateur fournit une transcription écrite [H]. Ajouter la transcription réelle coûte environ 1 jour                   |
| Relais chiffré vers l'appareil            | US-12                                       | Non évalué par E3. Environ 1,5 jour [H]. Premier ajout si la charge est tenue ; prévu pour le 12 novembre                  |
| Application mobile                        | US-13 à US-35 et US-54, sauf US-17 et US-31 | La console web joue le rôle de l'appareil ; US-17 et US-31 sont montrées par elle                                          |
| Configuration de ligne et renvoi          | US-01 à US-05                               | Pas de téléphonie réelle ; une configuration figée suffit au simulateur                                                    |
| Disponibilité et purges                   | US-41                                       | Hors de la chaîne critique ; couverte par les tests et le tableau de bord                                                  |
| Données d'E1 hors référentiels de la démo | US-48, US-49, US-52, US-53                  | Présentées dans E1 (rapports, requêtes, chiffres) ; aucune n'est sur le chemin de l'extraction montrée                     |

### 8.4 Risques du périmètre

- La feuille de route place la phase 3 (données d'E1) dans la même période (17 au 24 octobre).
  Les 9 jours ci-dessus en couvrent une partie (US-46, US-47, US-50). Le reste de la phase 3
  (BAN, lexique, jours fériés, Sirene, Urssaf) s'y ajoute. L'ensemble dépasse la période
  disponible si aucun travail n'est parallélisé : arbitrage à faire par le porteur.
- Sans transcription réelle, la démo ne montre pas la destruction de l'audio, seulement celle de
  la transcription. La preuve sur l'audio repose alors sur le test de conformité.
- Le jeu de 20 scénarios ne permet pas d'affirmer le seuil de 90 % du POC : l'incertitude sur une
  proportion mesurée sur 20 cas est large. Le rapport doit le dire.

## 9. Points d'interprétation

| Point                                    | Interprétation retenue                                                                                                          | Raison                                                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Acteur exploitant                        | Ajouté                                                                                                                          | KPI du POC et supervision imposés par la passation (sections 1, 10 et 11) ; C11, C20, C21                                                 |
| Serrurerie                               | Métier sélectionnable au MVP, lexique dédié reporté en V2 [H]                                                                   | Cible de la passation, mais la section 4.4 ne cite que les lexiques plomberie, chauffage, électricité                                     |
| Recherche « par LLM sur corpus local »   | La comparaison avec les dossiers se fait sur l'appareil ; seule la phrase de recherche sort                                     | R1 et passation, section 6 : la résolution se fait sur l'appareil                                                                         |
| Export vers la facturation               | Sortie de données en clair autorisée, à la demande explicite de l'artisan, vers son outil                                       | « Rien ne sort en clair » vise le stockage et le transit par Muninn, pas le choix de l'artisan [H]                                        |
| Source des encaissements                 | Dictée ou saisie par l'artisan                                                                                                  | Le concept ne la précise pas                                                                                                              |
| Preuve de destruction                    | Mention datée fournie par le serveur, adossée aux tests de conformité                                                           | Le concept dit « preuve visible » sans en préciser la nature                                                                              |
| Comptage des corrections                 | Nom du champ corrigé seulement, sans valeur                                                                                     | Nécessaire au monitoring (C11) sans contredire R1 et R4                                                                                   |
| Démo sans transcription audio            | Le simulateur fournit une transcription écrite                                                                                  | Charge du plan de démo (9 jours, section 8.2) ; la feuille de route ne liste pas la transcription parmi les briques réelles               |
| Appel de test du renvoi (US-04)          | Ajouté en Should                                                                                                                | Découle du KPI d'activation et de « jamais d'action invisible »                                                                           |
| Effacement d'un dossier (US-35)          | Ajouté en Should                                                                                                                | Droits des personnes au titre du RGPD ; absent de l'analyse, à valider avec l'AIPD                                                        |
| Supervision (US-41)                      | Ajoutée en Should                                                                                                               | Points de santé et purges prévus par la passation (sections 8 et 9), pas par l'analyse                                                    |
| Annonce de l'agent (US-06)               | Annonce dès la première phrase (décision D-04 du 12 octobre 2026)                                                               | R6 dit « première phrase », alors que le message type de la passation annonce l'assistant en troisième phrase. Le porteur a retenu R6     |
| Créneaux réservés par l'agent (US-05)    | Le serveur garde occupés les créneaux réservés par l'agent tant que l'appareil ne les a pas reçus                               | Sans cette règle, la synchronisation de l'appareil peut libérer un créneau déjà promis [H]                                                |
| Encaissements (US-23)                    | Enregistrés sur l'appareil, sans traitement serveur                                                                             | Le contrat `DossierDraft`, en 1.0 comme en 1.1, n'a pas de source « encaissement » ; une dictée exigerait de l'étendre                    |
| Équivalent écrit de la voix              | Débrief, dépense et recherche peuvent être écrits (US-13, US-18, US-22)                                                         | Accessibilité (document 04, EXA-16). Exige un point d'extraction à partir de texte, absent de la passation ; c'est aussi celui de la démo |
| Horodatage de destruction (US-31)        | Bloc `destruction` du brouillon chiffré (décidé : D-24)                                                                         | Le concept demande une « preuve visible » ; le contrat 1.0 n'avait pas ce champ                                                           |
| Porteur du projet (EP10)                 | Ajouté comme acteur                                                                                                             | L'analyse (section 1.1) demande le dimensionnement par Sirene ; ce n'est ni l'artisan ni l'exploitant                                     |
| Contrôle des adresses en production      | Tables locales (SRC-05 à SRC-07) ; Géoplateforme pour le synthétique seulement                                                  | Document 03 (fiches SRC-03 et SRC-04, décision 3) : aucune adresse de client ne sort vers un tiers                                        |
| API des référentiels (US-50)             | Interne, réservée aux composants de Muninn [H]                                                                                  | Les données servies sont publiques, mais les demandes de contrôle portent des fragments de données de clients                             |
| Contrôle du numéro (US-51)               | Seul le préfixe de bloc est transmis à l'API des référentiels                                                                   | Minimisation : le préfixe suffit à trouver la tranche [H : granularité à confirmer]                                                       |
| Résultat du contrôle (US-51)             | Résultat par champ dans le contrat `DossierDraft` 1.1, en plus de la baisse de confiance (décidé : D-24)                        | Le contrat 1.0 n'avait pas de champ de contrôle                                                                                           |
| Dimensionnement (US-52, US-53)           | Classé au MVP comme étude préalable, sans fonction dans l'application                                                           | Le dimensionnement précède le lancement ; il sert aussi le type « big data » de C1                                                        |
| Approbation d'un nouvel appareil (US-01) | Exigée par un appareil déjà enregistré ; le premier appareil du compte en est exempté (décision D-22 du 12 octobre 2026)        | Parade contre l'échange frauduleux de carte SIM : un code reçu par SMS ne suffit plus à recevoir les demandes                             |
| Révocation d'un appareil (US-54)         | Ajoutée en Must, depuis un autre appareil du compte (décision D-22)                                                             | Prévue par le modèle de données, sans story jusqu'ici ; complète l'approbation                                                            |
| Perte du seul appareil (US-01, US-54)    | Approbation du nouvel appareil par la phrase de récupération ; sans elle, aucun recours en ligne (décision D-28)                | Cohérent avec D-14 et R1 : le serveur ne garde que la clé publique dérivée de la phrase                                                   |
| LLM indisponible en fin d'appel (US-11)  | Brouillon de secours avec le numéro et l'heure de l'appel, marqué à vérifier (décision D-29)                                    | La transcription ne peut être ni gardée ni remise en file (R3) : sans ce brouillon, la demande serait perdue en silence                   |
| Travail le week-end (US-02, US-05)       | Les horaires et les disponibilités couvrent les sept jours ; hors horaires, rappel au prochain jour d'ouverture (décision D-30) | Un « jour ouvré suivant » figé ferait attendre le lundi le client d'un artisan qui travaille le samedi                                    |
