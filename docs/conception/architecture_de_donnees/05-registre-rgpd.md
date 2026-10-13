# Registre des activités de traitement de Muninn

**Version :** 1.2
**Date :** 12 octobre 2026
**Historique :** la v1.1 applique la relecture croisée avec les documents 01 et 02 et les arbitrages A1 à A8 de l'orchestrateur.
La v1.2 ajoute à RT-01 l'approbation des appareils et la clé publique de récupération (D-22,
D-28), inscrit les clés d'idempotence (24 heures) et suit D-27 pour le traitement Sirene (RT-07).
**Phase :** 1 (architecture de données)
**Statut :** proposition, à valider par le porteur puis par l'avis juridique (condition C3 de
l'analyse)
**Compétences servies :** C4 (base conforme au RGPD, durées de conservation) ; préparation de C20
**Documents liés :** `../sources_de_donnees/01-user-stories.md`, `../sources_de_donnees/02-flux-de-donnees.md`
(section 4), `../sources_de_donnees/03-sources-de-donnees.md` (section 5), `02-modele-de-donnees.md`,
`03-acces-et-exposition.md`, `06-big-data-externalise.md`, `../../decisions.md`

## 1. Objet, cadre et méthode

Ce document est le registre des activités de traitement prévu par l'article 30 du RGPD. Il est
rédigé avant la mise en service, à partir de la conception : il décrit ce que Muninn **fera**, et
sera mis à jour à chaque changement de traitement, de fournisseur ou de durée.

**Pourquoi tenir un registre.** L'article 30.5 dispense les organismes de moins de 250 personnes,
sauf pour les traitements non occasionnels, ceux qui comportent un risque pour les droits et
libertés, ou ceux qui portent sur des catégories particulières de données. La CNIL précise que
cette dérogation est « limitée à des cas très particuliers » et cite la gestion des clients parmi
les traitements non occasionnels (section 13, source S-03). Tous les traitements de Muninn sont
continus : le registre est obligatoire.

**Deux registres en un document.** Muninn agit à deux titres (section 2) :

- **responsable de traitement** pour ses propres finalités : registre de l'article 30.1, fiches
  RT-01 à RT-08 (section 4) ;
- **sous-traitant** des artisans pour les données de leurs clients : registre de l'article 30.2,
  fiches ST-01 à ST-04 (section 5).

**Contenu obligatoire, vérifié.**

| Registre du responsable (art. 30.1)                                                                                                     | Registre du sous-traitant (art. 30.2)                                                                      |
| --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| a) Nom et coordonnées du responsable, le cas échéant du responsable conjoint, du représentant et du délégué à la protection des données | a) Nom et coordonnées du sous-traitant, de chaque responsable pour le compte duquel il agit, et du délégué |
| b) Finalités du traitement                                                                                                              | b) Catégories de traitements effectués pour le compte de chaque responsable                                |
| c) Catégories de personnes concernées et de données                                                                                     | c) Transferts vers un pays tiers et, dans les cas de l'article 49.1, second alinéa, les garanties          |
| d) Catégories de destinataires, y compris dans des pays tiers                                                                           | d) Dans la mesure du possible, description générale des mesures de sécurité                                |
| e) Transferts vers un pays tiers et, dans les cas de l'article 49.1, second alinéa, les garanties                                       | sans objet                                                                                                 |
| f) Dans la mesure du possible, délais d'effacement                                                                                      | sans objet                                                                                                 |
| g) Dans la mesure du possible, description générale des mesures de sécurité (art. 32.1)                                                 | sans objet                                                                                                 |

Source : texte du RGPD reproduit par la CNIL (S-01). Les points e) et g) de l'article 30.1 ont été
lus mot à mot ; les autres points et l'article 30.2 l'ont été dans le résumé de la CNIL, sans
écart avec la liste ci-dessus. Le texte d'EUR-Lex n'a pas pu être affiché par l'outil de
vérification.

**Forme.** Chaque fiche suit les rubriques du modèle de la CNIL (S-02) : acteurs, finalités,
catégories de personnes et de données, durées, destinataires, transferts, mesures de sécurité.
Deux rubriques sont ajoutées, utiles à la conception : la base légale (article 6) et la place dans
l'analyse d'impact.

Les hypothèses sont marquées **[H]**. Une durée marquée [H] est une proposition à valider.

## 2. Responsable ou sous-traitant : la qualification

C'est le point clé du registre. Il décide qui répond aux personnes, qui fait l'analyse d'impact,
quel contrat lie Muninn aux artisans, et quelles données Muninn peut utiliser pour lui-même.

### 2.1 Les définitions

- **Responsable du traitement** : l'organisme qui « détermine les finalités et les moyens du
  traitement » (article 4.7).
- **Sous-traitant** : l'organisme qui « traite des données à caractère personnel pour le compte du
  responsable du traitement » (article 4.8).

### 2.2 Données des artisans : Muninn est responsable

Muninn décide seul pourquoi et comment il traite les données de ses clients artisans :
authentification, appareils, configuration de la ligne, abonnement, sécurité du service. Ces
finalités sont les siennes ; l'artisan y consent en souscrivant, il ne les définit pas. Muninn est
donc responsable de traitement (fiches RT-01 à RT-05, RT-08).

### 2.3 Données des clients finaux : Muninn est sous-traitant de l'artisan

Les personnes qui appellent l'artisan, dont les demandes deviennent des dossiers et qui reçoivent
des SMS, sont les clients de l'artisan. Cinq arguments font de l'artisan le responsable et de
Muninn son sous-traitant.

1. **La finalité est celle de l'artisan.** Recevoir les demandes de ses clients, les ranger, les
   rappeler, leur fixer un rendez-vous : c'est la gestion de sa clientèle. Sans artisan, aucun de
   ces traitements n'a de raison d'être.
2. **L'artisan décide de recourir au traitement et en fixe les éléments essentiels.** Il choisit
   de renvoyer sa ligne, règle l'agent (horaires, prise de rendez-vous, message), valide, corrige
   ou rejette chaque brouillon (US-17), décide d'envoyer chaque SMS (US-27, US-28), fixe la
   conservation de ses dossiers et les efface (US-35).
3. **Muninn agit sur instruction.** Le service exécute ce que l'artisan a paramétré ; l'agent
   s'annonce comme « l'assistant automatique de [Entreprise] » (R6, D-04), pas comme un service de
   Muninn.
4. **Muninn ne peut pas réutiliser ces données.** C'est un fait technique, pas seulement une
   promesse contractuelle : le serveur ne garde aucun dossier en clair, n'a aucune clé de
   déchiffrement (R1, D-14), détruit l'audio et la transcription (R2, R3). La sous-traitance est
   ici garantie par l'architecture.
5. **Les choix de Muninn portent sur les moyens non essentiels** : fournisseur de transcription,
   hébergeur, format du schéma, mesures de sécurité. Les lignes directrices 07/2020 du comité
   européen de la protection des données admettent que le sous-traitant décide de ces moyens
   (S-08) [H : paragraphe non relu sur le texte, voir les réserves de la section 13].

**L'argument contraire, à soumettre à l'avocat.** Muninn conçoit un service standardisé : le
schéma `DossierDraft`, les questions de l'agent et la liste des données collectées sont fixés par
Muninn, pas par chaque artisan. On peut y voir la détermination de moyens essentiels (quelles
données, auprès de qui), qui pèse vers la responsabilité, voire la responsabilité conjointe. La
réponse proposée : l'artisan choisit ce service en connaissance de cause et le paramètre, et la
liste des données reste celle qu'un artisan demande à tout client qui l'appelle (nom, adresse,
objet, numéro). Ce point n'est pas tranché par ce document (question Q-01).

### 2.4 Les zones mixtes, où Muninn redevient responsable

La qualification se fait finalité par finalité. Muninn devient responsable dès qu'il traite une
donnée de client final **pour lui-même**. Trois cas sont identifiés, et assumés :

| Cas                                                                  | Finalité propre à Muninn                  | Fiche        |
| -------------------------------------------------------------------- | ----------------------------------------- | ------------ |
| `caller_hash` sert à plafonner les appels d'un même numéro           | Lutte contre les abus, maîtrise des coûts | RT-04        |
| Les journaux et les métriques portent des traces des appels          | Sécurité, qualité de service              | RT-04, RT-05 |
| Un jeu d'évaluation constitué d'appels réels (passation, section 10) | Amélioration du produit                   | RT-06        |

Tout autre usage de données de clients finaux par Muninn serait un détournement de finalité et
ferait de Muninn un responsable sans base légale. L'architecture le rend impossible pour le
contenu des dossiers (R1) ; pour les métadonnées, c'est la matrice d'accès qui l'interdit
(document 03).

### 2.5 Conséquences pratiques

| Conséquence                                   | Mise en œuvre                                                                                                                                                                                                                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Contrat de sous-traitance avec chaque artisan | Annexe aux conditions générales, conforme à l'article 28.3 (instructions, confidentialité, sécurité, sous-traitants ultérieurs, aide aux droits, aide aux articles 32 à 36, suppression ou restitution en fin de contrat, audits) |
| Sous-traitants ultérieurs                     | Autorisation écrite générale de l'artisan ; information préalable de tout ajout ou remplacement, avec possibilité d'objection (art. 28.2) ; liste tenue en section 6                                                              |
| Information des clients finaux                | Obligation de l'artisan (art. 13). Muninn la facilite : annonce de l'agent (R6), modèle de mention fourni à l'artisan                                                                                                             |
| Exercice des droits des clients finaux        | Adressé à l'artisan ; Muninn l'aide (art. 28.3 e) et transmet toute demande reçue (section 8)                                                                                                                                     |
| Violation de données                          | Muninn notifie l'artisan sans délai injustifié ; l'artisan notifie la CNIL [H : art. 33 non relu pour ce document]                                                                                                                |
| Analyse d'impact                              | Obligation de l'artisan ; Muninn fournit une analyse type (section 9)                                                                                                                                                             |
| Registre de l'artisan                         | L'artisan tient le sien (gestion de la clientèle) ; Muninn fournit une fiche type (section 5.5)                                                                                                                                   |

## 3. Identification

| Rubrique                                         | Contenu                                                          |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| Organisme                                        | Muninn [H : structure juridique non créée à la date du document] |
| Représentant légal                               | Le porteur du projet [H]                                         |
| Délégué à la protection des données              | Non désigné [H : obligation à confirmer, question Q-14]          |
| Contact pour l'exercice des droits               | Adresse dédiée à créer [H]                                       |
| Responsables pour le compte desquels Muninn agit | Chaque artisan abonné, identifié par son compte (`app.accounts`) |
| Responsable conjoint                             | Aucun identifié (voir Q-01)                                      |
| Date de création du registre                     | 12 octobre 2026                                                  |
| Dernière mise à jour                             | 12 octobre 2026                                                  |

## 4. Fiches des traitements dont Muninn est responsable

Les mesures de sécurité communes sont décrites une fois, dans le document 03 : rôles PostgreSQL
distincts (section 5.1), sécurité au niveau des lignes (5.2), authentification (5.3), limitation
de débit (5.4), journaux sans DP (5.5), secrets (5.6), chiffrement (5.7). Chaque fiche ne cite que
ses mesures propres.

### RT-01. Comptes, appareils et authentification des artisans

| Rubrique               | Contenu                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité principale    | Créer et gérer le compte de l'artisan, authentifier ses appareils, lui notifier les nouvelles demandes                                                                                                                                                                                                                                                                                                                                                  |
| Sous-finalités         | Connexion par code à usage unique ; enregistrement, approbation et révocation des appareils (D-22) ; approbation d'un nouvel appareil par la phrase de récupération (D-28) ; notifications push sans contenu ; idempotence des requêtes ; préremplissage facultatif par le SIREN (SRC-02)                                                                                                                                                               |
| Base légale            | Exécution du contrat (art. 6.1 b)                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Personnes concernées   | Artisans abonnés ou à l'essai                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Catégories de données  | Empreinte de l'identifiant de connexion (numéro ou e-mail) ; empreinte du code ; SIREN (facultatif) ; clé publique, plateforme et jeton push de chaque appareil ; empreinte du jeton d'appareil ; dates de dernière activité, d'approbation et de révocation ; méthode d'approbation, empreinte du code d'approbation et nombre d'essais ; clé publique de récupération (facultative) ; clés d'idempotence avec l'empreinte HMAC du corps de la requête |
| Données exclues        | Identifiant de connexion en clair ; bloc `dirigeants` de SRC-02, écarté sans stockage ; clé privée de l'appareil, qui ne quitte pas le téléphone ; phrase de récupération, qui reste chez l'artisan (D-14, D-28) ; corps des requêtes rejouables                                                                                                                                                                                                        |
| Source                 | L'artisan ; SRC-02 pour le préremplissage                                                                                                                                                                                                                                                                                                                                                                                                               |
| Données sensibles      | Non                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Destinataires internes | api, relay (clé publique et jeton push seulement) ; document 03, section 4                                                                                                                                                                                                                                                                                                                                                                              |
| Sous-traitants         | Hébergeur ; fournisseur SMS et fournisseur d'e-mail (envoi du code) ; FCM et APNs (jeton push)                                                                                                                                                                                                                                                                                                                                                          |
| Transferts hors UE     | Jeton push et texte fixe, sans contenu, vers FCM (Google) et APNs (Apple) : exception à R5 acceptée et documentée (décidé : D-20) ; section 6                                                                                                                                                                                                                                                                                                           |
| Durée de conservation  | Code : validité 10 minutes ; empreinte purgée 24 heures après expiration. Compte, clé publique de récupération comprise : durée du contrat, puis 30 jours après la fermeture [H]. Appareil révoqué : 30 jours [H]. Jeton d'appareil : jusqu'à révocation, ou 90 jours sans usage [H] ; empreinte effacée à la révocation. Empreinte du code d'approbation : fin de l'attente. Clés d'idempotence : 24 heures [H]                                        |
| Mesures propres        | Empreintes HMAC avec poivre ; 5 essais par code ; limitation des demandes de code ; approbation d'un nouvel appareil par un appareil approuvé ou par la phrase de récupération, 3 essais de code ; notification d'un nouvel appareil ; jetons push chiffrés en base ; réponse rejouable gardée seulement si elle ne contient aucune DP                                                                                                                  |
| Analyse d'impact       | Incluse dans l'analyse de Muninn (section 9)                                                                                                                                                                                                                                                                                                                                                                                                            |

### RT-02. Paramétrage et fonctionnement du service pour l'artisan

| Rubrique               | Contenu                                                                                                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finalité principale    | Faire fonctionner la ligne Muninn selon les règles de l'artisan                                                                                                                                  |
| Sous-finalités         | Configuration de la ligne ; codes de renvoi et appel de test ; partage des disponibilités sans détail ; jours fériés travaillés                                                                  |
| Base légale            | Exécution du contrat (art. 6.1 b)                                                                                                                                                                |
| Personnes concernées   | Artisans                                                                                                                                                                                         |
| Catégories de données  | Nom d'entreprise, prénom, métier, horaires, message d'accueil, zone de jours fériés, numéro Muninn ; créneaux libres ou occupés des 14 prochains jours, sans nom ; résultats des tests de renvoi |
| Données exclues        | Nom et adresse des clients dans les créneaux (US-05)                                                                                                                                             |
| Source                 | L'artisan, par l'application                                                                                                                                                                     |
| Données sensibles      | Non                                                                                                                                                                                              |
| Destinataires internes | api ; voice-gateway (règles et créneaux de la ligne appelée)                                                                                                                                     |
| Sous-traitants         | Hébergeur ; LLM et TTS, qui reçoivent le nom d'entreprise et le prénom dans l'annonce                                                                                                            |
| Transferts hors UE     | Aucun prévu (R5)                                                                                                                                                                                 |
| Durée de conservation  | Configuration de la ligne : durée du contrat, puis 30 jours (cascade du compte) [H]. Créneaux : fenêtre glissante de 14 jours, passés purgés. Tests de renvoi : 30 jours [H]                     |
| Mesures propres        | Annonce de l'assistant impossible à retirer (US-02) ; lecture limitée à la ligne de l'appel par la RLS                                                                                           |
| Analyse d'impact       | Incluse dans l'analyse de Muninn                                                                                                                                                                 |

### RT-03. Abonnement et facturation

| Rubrique               | Contenu                                                                                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité principale    | Gérer l'essai, l'abonnement et sa facturation (lot 6 de la passation)                                                                                                                                   |
| Base légale            | Exécution du contrat (art. 6.1 b) ; obligation légale pour la conservation des pièces comptables de Muninn (art. 6.1 c)                                                                                 |
| Personnes concernées   | Artisans                                                                                                                                                                                                |
| Catégories de données  | Statut, offre, fin d'essai ; identifiant client chez le prestataire de paiement ; factures de Muninn                                                                                                    |
| Données exclues        | Données bancaires : jamais chez Muninn, seulement chez le prestataire (passation, section 4)                                                                                                            |
| Source                 | L'artisan ; le prestataire de paiement (webhooks)                                                                                                                                                       |
| Données sensibles      | Non                                                                                                                                                                                                     |
| Destinataires internes | api                                                                                                                                                                                                     |
| Sous-traitants         | Prestataire de paiement (Stripe, retenu par la passation)                                                                                                                                               |
| Transferts hors UE     | Stripe, par son entité européenne (décidé : D-20) [H : garanties de transfert à lire, section 6]                                                                                                        |
| Durée de conservation  | Données d'abonnement : durée du contrat. Factures et pièces justificatives de Muninn : 10 ans à compter de la clôture de l'exercice comptable [H : article L123-22 du Code de commerce à relire] (S-12) |
| Mesures propres        | Webhooks vérifiés par signature et rejoués refusés ; aucune donnée de carte                                                                                                                             |
| Analyse d'impact       | Non requise seule [H]                                                                                                                                                                                   |

### RT-04. Sécurité, journalisation et lutte contre les abus

| Rubrique               | Contenu                                                                                                                                                                                                                                                                                                              |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité principale    | Assurer la sécurité et la disponibilité du service, tracer les accès, détecter et limiter les abus                                                                                                                                                                                                                   |
| Sous-finalités         | Journal d'accès et de sécurité ; journal d'audit ; limitation de débit ; plafond d'appels par numéro appelant ; accès d'urgence ; purges et leur journal                                                                                                                                                             |
| Base légale            | Intérêt légitime de Muninn (art. 6.1 f) : sécuriser le service et maîtriser ses coûts. Mise en balance : données pseudonymisées, durées courtes, aucun profilage                                                                                                                                                     |
| Personnes concernées   | Artisans ; clients finaux qui appellent une ligne Muninn                                                                                                                                                                                                                                                             |
| Catégories de données  | Adresse IP, `request_id`, route, statut, durée ; identifiants opaques de compte et d'appareil ; événements d'audit sans contenu ; `caller_hash` (empreinte HMAC du numéro appelant), horodatage, durée et statut des appels                                                                                          |
| Données exclues        | Noms, numéros en clair, adresses postales, contenu des demandes, corps des requêtes (R4)                                                                                                                                                                                                                             |
| Source                 | Trafic du service ; webhooks du CPaaS                                                                                                                                                                                                                                                                                |
| Données sensibles      | Non                                                                                                                                                                                                                                                                                                                  |
| Destinataires internes | Exploitant (journaux filtrés, vue d'audit à identifiant masqué) ; worker-maintenance (purges)                                                                                                                                                                                                                        |
| Sous-traitants         | Hébergeur ; outil de journalisation et de suivi d'erreurs [H : non choisi]                                                                                                                                                                                                                                           |
| Transferts hors UE     | Aucun prévu (R5) [H : selon l'outil de journalisation retenu]                                                                                                                                                                                                                                                        |
| Durée de conservation  | Journal d'accès et de sécurité : 6 mois [H], borne basse de la recommandation de la CNIL (6 mois à 1 an, S-14). Journal de diagnostic : 30 jours [H]. Journal d'audit : 1 an [H]. Sessions d'appel et `caller_hash` : 90 jours [H : passation ; à justifier ou réduire, Q-05]. Sauvegardes de la base : 30 jours [H] |
| Mesures propres        | Liste blanche des champs journalisés ; adresse IP tronquée hors journal de sécurité [H] ; `caller_hash` pseudonymisé et non réversible sans le poivre ; journal d'audit en ajout seul                                                                                                                                |
| Analyse d'impact       | Incluse dans l'analyse de Muninn                                                                                                                                                                                                                                                                                     |

Limite à dire : une empreinte HMAC d'un numéro reste réversible par énumération pour qui détient
le poivre. `caller_hash` est une donnée pseudonymisée, donc une donnée personnelle.

### RT-05. Mesure et amélioration de la qualité de l'extraction

| Rubrique               | Contenu                                                                                                                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finalité principale    | Mesurer la qualité de l'extraction en production et détecter une dérive (US-38, US-40)                                                                                                                             |
| Base légale            | Intérêt légitime de Muninn (art. 6.1 f) : fournir un service fiable                                                                                                                                                |
| Personnes concernées   | Artisans (activité de leur compte) ; aucun client final identifiable                                                                                                                                               |
| Catégories de données  | Statut, versions, latences et horodatages de destruction de chaque extraction (`app.extraction_runs`) ; noms des champs corrigés, sans valeur (`app.field_corrections`) ; agrégats horaires sans colonne de compte |
| Données exclues        | Valeurs extraites ou corrigées ; transcriptions ; brouillons                                                                                                                                                       |
| Source                 | Composants du service ; application (nom du champ corrigé)                                                                                                                                                         |
| Données sensibles      | Non                                                                                                                                                                                                                |
| Destinataires internes | worker-maintenance (agrégation) ; exploitant (agrégats seulement)                                                                                                                                                  |
| Sous-traitants         | Hébergeur                                                                                                                                                                                                          |
| Transferts hors UE     | Aucun                                                                                                                                                                                                              |
| Durée de conservation  | Données par extraction et par correction : 90 jours [H], puis seuls les agrégats restent. Agrégats : 13 mois [H], cellules de moins de 5 masquées                                                                  |
| Mesures propres        | Agrégation avant consultation ; aucune valeur de champ collectée (US-17, critère 3)                                                                                                                                |
| Analyse d'impact       | Incluse dans l'analyse de Muninn                                                                                                                                                                                   |

L'évaluation sur jeux synthétiques (US-37) ne traite aucune donnée personnelle (R9) : elle
n'appelle pas de fiche.

**Traitements volontairement absents.** Aucune prospection commerciale (Sirene n'y sert pas,
document 03 de la phase 0, section 5). Aucun support client n'est conçu à ce jour : s'il est créé
(messagerie, téléphone), il fera l'objet d'une fiche. Les comptes nominatifs de l'exploitant et du
porteur chez les fournisseurs relèvent de la gestion des habilitations, à inscrire quand une
équipe existera [H]. La console de démonstration et le serveur MCP de l'exploitant
(décidé : D-21) ne traitent aucune DP (document 03, sections 6.2 et 6.3).

### RT-06. Constitution d'un jeu d'évaluation à partir d'appels réels

**Traitement prévu par la passation (section 10 : « 50 appels réels anonymisés »), non mis en
œuvre dans le projet de certification**, qui exclut tout POC terrain. La fiche existe pour que ce
traitement ne démarre pas sans décision.

| Rubrique               | Contenu                                                                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité principale    | Mesurer l'exactitude de l'extraction sur des appels réels (KPI de 90 % du POC)                                                                 |
| Base légale            | À déterminer : consentement des appelants ou intérêt légitime de Muninn (Q-11)                                                                 |
| Personnes concernées   | Clients finaux ayant appelé pendant le POC ; artisans participants                                                                             |
| Catégories de données  | Audio ou transcription, puis vérité terrain annotée : nom, numéro, adresse, objet de la demande                                                |
| Source                 | Appels du POC                                                                                                                                  |
| Données sensibles      | Possibles, à titre incident (un appelant peut évoquer sa santé, R7)                                                                            |
| Destinataires internes | Exploitant, harnais d'évaluation                                                                                                               |
| Sous-traitants         | Fournisseurs STT et LLM, pour les passes d'évaluation                                                                                          |
| Transferts hors UE     | Aucun admis (R5)                                                                                                                               |
| Durée de conservation  | Fin du POC plus 3 mois [H]                                                                                                                     |
| Mesures propres        | Hors dépôt et chiffré (R9) ; accès nominatif ; anonymisation à démontrer (la voix et le contenu d'une demande identifient souvent la personne) |
| Analyse d'impact       | Obligatoire avant toute collecte [H] ; condition C3                                                                                            |

Conflit à signaler : conserver un audio d'appel, même pour l'évaluation, contredit R2 tel qu'il
est écrit. Le jeu réel devrait être constitué de transcriptions anonymisées, ou R2 revue avec
l'avis juridique, comme pour US-42.

### RT-07. Étude de dimensionnement du marché (Sirene et Urssaf)

| Rubrique               | Contenu                                                                                                                                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité principale    | Compter les artisans solo de la tête de pont pour dimensionner le marché (US-52, US-53)                                                                                                                                                     |
| Base légale            | Intérêt légitime de Muninn (art. 6.1 f) ; réutilisation de données publiques sous Licence Ouverte                                                                                                                                           |
| Personnes concernées   | Entrepreneurs individuels inscrits dans Sirene                                                                                                                                                                                              |
| Catégories de données  | Colonnes lues : activité, tranche d'effectif, catégorie juridique, commune et code postal de l'établissement, statut de diffusion, dates. Colonnes d'identité et d'adresse fine présentes dans les fichiers téléchargés, jamais lues (P-18) |
| Source                 | Fichiers stock Sirene (SRC-01) ; séries de l'Urssaf (SRC-10), sans DP                                                                                                                                                                       |
| Données sensibles      | Non                                                                                                                                                                                                                                         |
| Destinataires internes | Porteur du projet ; schéma `market` (agrégats seulement)                                                                                                                                                                                    |
| Sous-traitants         | Microsoft Azure (décidé : D-27) : lac ADLS Gen2 et tâche Container Apps en France Central, dans le groupe de ressources du porteur (document 06)                                                                                            |
| Transferts hors UE     | Aucun prévu ; stockage et calcul en France Central (D-27) [H : accès à distance par une société mère établie hors UE, Q-07]                                                                                                                 |
| Durée de conservation  | Fichiers Sirene : supprimés à la fin du traitement, au plus tard sous 24 h [H]. Agrégats (schéma `market`) : 5 ans [H] ; aucun SIREN, secret statistique appliqué (document 02, section 4.2)                                                |
| Mesures propres        | Projection de colonnes ; aucun SIREN conservé ; secret statistique ; aucune prospection ; respect du statut de diffusion (document 03 de la phase 0, section 5)                                                                             |
| Analyse d'impact       | Non requise [H] : agrégats, aucune décision sur les personnes                                                                                                                                                                               |

Information des personnes : les données ne sont pas collectées auprès d'elles. L'exception de
l'article 14.5 b), information « impossible » ou exigeant « des efforts disproportionnés », est
envisagée [H : à confirmer, Q-12].

### RT-08. Gestion des demandes d'exercice des droits

| Rubrique               | Contenu                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| Finalité principale    | Recevoir, traiter et prouver le traitement des demandes d'accès, d'effacement, d'opposition |
| Base légale            | Obligation légale (art. 6.1 c ; art. 12 et 15 à 22)                                         |
| Personnes concernées   | Artisans ; clients finaux dont la demande arrive chez Muninn                                |
| Catégories de données  | Identité et coordonnées du demandeur, objet, date, réponse                                  |
| Source                 | Le demandeur                                                                                |
| Données sensibles      | Non                                                                                         |
| Destinataires internes | Porteur du projet                                                                           |
| Sous-traitants         | Fournisseur de messagerie [H]                                                               |
| Transferts hors UE     | Aucun prévu                                                                                 |
| Durée de conservation  | [H : 5 ans à compter de la réponse, à confirmer, Q-15]. Hors de la base de production       |
| Mesures propres        | Registre tenu hors de la base de production ; accès du seul porteur                         |
| Analyse d'impact       | Non requise                                                                                 |

## 5. Registre du sous-traitant

Muninn traite pour le compte de chaque artisan abonné. La liste des responsables pour le compte
desquels il agit est la table des comptes elle-même, avec la date d'acceptation du contrat de
sous-traitance (colonnes `dpa_accepted_at` et `dpa_version` de `app.accounts`).

Pour chaque fiche, la base légale est celle de l'artisan, responsable. Elle est indiquée à titre
d'aide, sous réserve de l'avis juridique (Q-02).

### ST-01. Prise d'appels par l'agent vocal et transmission chiffrée de la demande

| Rubrique                     | Contenu                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Traitements effectués        | Prise d'appel renvoyé ; dialogue avec l'agent ; transcription ; extraction d'un brouillon ; contrôle de la commune, du code postal et du préfixe du numéro par les référentiels ; réservation d'un créneau ; chiffrement pour les appareils ; notification ; remise et suppression de l'enveloppe                                        |
| Flux                         | F-02 ; F-06, messages 5 à 9                                                                                                                                                                                                                                                                                                              |
| Base légale de l'artisan [H] | Mesures précontractuelles prises à la demande de la personne (art. 6.1 b) : l'appelant demande une intervention                                                                                                                                                                                                                          |
| Personnes concernées         | Clients finaux qui appellent ; tiers éventuellement cités dans la demande                                                                                                                                                                                                                                                                |
| Catégories de données        | Voix ; numéro appelant ; nom, prénom ; adresse d'intervention ; objet et urgence de la demande ; disponibilités ; créneau accepté ; numéro dicté                                                                                                                                                                                         |
| Données sensibles            | Exclues par conception (R7) ; peuvent être dites par l'appelant et transiter, sans être retenues (Q-04)                                                                                                                                                                                                                                  |
| Sous-traitants ultérieurs    | CPaaS ; STT ; LLM ; TTS ; hébergeur ; push (jeton de l'appareil de l'artisan seulement, aucune donnée du client)                                                                                                                                                                                                                         |
| Transferts hors UE           | CPaaS : fournisseur choisi dans l'UE (décidé : D-20), choix dans ADR-02 ; push : jeton seulement, section 6                                                                                                                                                                                                                              |
| Durée de conservation        | Audio : durée de l'appel, détruit dans un bloc `finally` (R2). Transcription : durée de l'extraction (R3). Brouillon en clair : jusqu'au chiffrement. Enveloppe chiffrée : jusqu'à l'accusé de réception, 7 jours au plus. Créneau réservé, sans nom : 14 jours au plus. Chez les fournisseurs d'IA : zéro rétention exigée (R5, ADR-03) |
| Mesures de sécurité          | Annonce de l'assistant en première phrase (R6, D-04) ; `SealedBox` par appareil (R1) ; aucun écrit sur disque, en file ou en journal (R1 à R4, D-11) ; parades aux menaces propres au LLM (document 03, section 7)                                                                                                                       |

### ST-02. Extraction à la demande de l'artisan

| Rubrique                     | Contenu                                                                                                                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Traitements effectués        | Débrief dicté ou écrit ; ticket photographié ; dépense dictée ; transcription d'une recherche dite ou d'un imprévu dit                                                        |
| Flux                         | F-03, F-04 (messages 2 à 7), F-05, F-06 (T6)                                                                                                                                  |
| Base légale de l'artisan [H] | Exécution des contrats avec ses clients ; obligation légale pour les pièces comptables                                                                                        |
| Personnes concernées         | Clients finaux cités ; l'artisan lui-même (sa voix) ; fournisseurs cités sur les tickets                                                                                      |
| Catégories de données        | Voix de l'artisan ; noms, adresses, demandes des clients ; lexique personnel ; montants, fournisseurs, dates                                                                  |
| Données sensibles            | Exclues par conception (R7)                                                                                                                                                   |
| Sous-traitants ultérieurs    | STT ; LLM ; hébergeur                                                                                                                                                         |
| Transferts hors UE           | Aucun admis (R5)                                                                                                                                                              |
| Durée de conservation        | Durée de la requête. Rien n'est stocké côté serveur (US-13, US-21, US-22) ; le brouillon revient dans la réponse HTTPS                                                        |
| Mesures de sécurité          | Lexique personnel jamais stocké ni journalisé (US-16) ; fichiers temporaires chiffrés et supprimés si la pile écrit sur disque (document 02, section 3) ; réponses `no-store` |

### ST-03. Envoi de SMS aux clients finaux

| Rubrique                     | Contenu                                                                                                                                                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Traitements effectués        | Envoi d'un rappel de rendez-vous ou d'un message d'imprévu composé sur l'appareil, puis suivi du statut                                                                                 |
| Flux                         | F-06                                                                                                                                                                                    |
| Base légale de l'artisan [H] | Exécution du contrat avec le client (rendez-vous fixé)                                                                                                                                  |
| Personnes concernées         | Clients finaux                                                                                                                                                                          |
| Catégories de données        | Numéro de mobile ; texte (entreprise, créneaux) ; identifiant et statut chez le fournisseur                                                                                             |
| Données sensibles            | Non                                                                                                                                                                                     |
| Sous-traitants ultérieurs    | Fournisseur SMS (ADR-05) ; hébergeur                                                                                                                                                    |
| Transferts hors UE           | Selon ADR-05 ; traitement dans l'UE exigé (P-04)                                                                                                                                        |
| Durée de conservation        | Texte et numéro : oubliés après la réponse du fournisseur. `app.sms_jobs` (identifiant et statut) : 90 jours [H]. Journaux du fournisseur : selon ses conditions, à lire avant le choix |
| Mesures de sécurité          | Aucun envoi sans geste de l'artisan (US-28) ; quotas (document 03, section 5.4) ; aucun champ libre d'un brouillon dans le texte [H]                                                    |

Nature du message : un rappel purement informatif, lié à un rendez-vous déjà fixé, relève plutôt
du message de service que de la prospection. C'est une lecture par analogie de la page de la CNIL
qui distingue messages « transactionnels » et « relationnels », sans finalité promotionnelle
directe (S-15) ; elle ne cite pas les rappels de rendez-vous. Tout contenu promotionnel
requalifierait le message (Q-10).

### ST-04. Hébergement des sauvegardes et des archives chiffrées

| Rubrique                     | Contenu                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Traitements effectués        | Stockage, restitution et suppression de blobs chiffrés sur l'appareil                                                                                                                                                                                                                                                                                                                                                                 |
| Flux                         | F-07                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Base légale de l'artisan [H] | Exécution des contrats ; obligation légale de conservation des pièces comptables (L123-22)                                                                                                                                                                                                                                                                                                                                            |
| Personnes concernées         | Clients finaux de l'artisan ; l'artisan                                                                                                                                                                                                                                                                                                                                                                                               |
| Catégories de données        | Toutes les données des dossiers, illisibles pour Muninn ; métadonnées : taille, date, date de fin de conservation                                                                                                                                                                                                                                                                                                                     |
| Données sensibles            | Non attendues                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Sous-traitants ultérieurs    | Hébergeur et stockage objet (ADR-06)                                                                                                                                                                                                                                                                                                                                                                                                  |
| Transferts hors UE           | Aucun (R5)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Durée de conservation        | Sauvegarde : jusqu'à son remplacement, sans version antérieure (D-13). Archive : 10 ans à compter de la clôture de l'exercice comptable [H : article L123-22 du Code de commerce à relire], puis suppression par le worker. Fin du contrat : archives gardées 10 ans après la fermeture du compte, chiffrées et lisibles par le seul artisan (décidé : D-23), sous réserve d'une clause contractuelle et de l'avis de l'avocat (Q-06) |
| Mesures de sécurité          | XChaCha20-Poly1305, clé détenue par l'artisan seul (US-33, D-14) ; versionnage désactivé (D-13) ; aucun droit de suppression d'archive pour l'api                                                                                                                                                                                                                                                                                     |

Les données traitées ici restent des données personnelles pour l'artisan, qui détient la clé. Le
registre les traite comme telles, sans se prévaloir du fait que Muninn ne peut pas les lire.

### 5.5 Fiche type pour le registre de l'artisan

Muninn fournira à chaque artisan une fiche pré-remplie pour son propre registre : « gestion des
demandes et des dossiers clients », avec pour sous-traitant Muninn et la liste de la section 6.
La CNIL cite la gestion des clients parmi les traitements non occasionnels qu'une petite
entreprise doit inscrire à son registre (S-03).

## 6. Sous-traitants ultérieurs et transferts hors de l'Union

Aucun fournisseur n'est choisi à la date du document, sauf ceux que la passation retient. Le
tableau dit ce qui doit être vérifié avant tout contrat. Aucun compte n'est créé sans accord du
porteur (R10).

| Fournisseur             | Traitements         | Données reçues                                            | Localisation                                                                                                                                   | Garantie à obtenir                                                                                                     |
| ----------------------- | ------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Hébergeur (ADR-06)      | Tous                | Tout ce qui est stocké                                    | France ou UE (Scaleway, OVHcloud, Azure France Central)                                                                                        | Contrat de l'article 28 ; chiffrement des volumes ; pour une société mère hors UE, accès à distance à étudier (Q-07)   |
| LLM et STT (ADR-03)     | RT-02, ST-01, ST-02 | Conversation, transcription, image, audio, lexique métier | UE exigée (R5)                                                                                                                                 | Zéro rétention activée et vérifiée ; aucun entraînement sur les données ; contrat de l'article 28                      |
| TTS (ADR-04)            | ST-01               | Phrases de l'agent, dont nom et adresse reformulés        | UE exigée (R5)                                                                                                                                 | Idem                                                                                                                   |
| CPaaS (ADR-02)          | ST-01, RT-04        | Audio, numéros appelant et appelé                         | Fournisseur choisi dans l'UE (décidé : D-20). Twilio et Telnyx sont des sociétés établies aux États-Unis [H : région de traitement à vérifier] | Enregistrement désactivé ; durée des journaux d'appel ; garantie de transfert si hors UE                               |
| SMS (ADR-05)            | ST-03, RT-01        | Numéro, texte, code de connexion                          | UE exigée (P-04)                                                                                                                               | Contrat de l'article 28 ; durée de ses journaux                                                                        |
| E-mail                  | RT-01, RT-08        | Adresse, code de connexion                                | UE [H]                                                                                                                                         | Contrat de l'article 28                                                                                                |
| FCM (Google)            | RT-01               | Jeton push, texte fixe                                    | Service « global » : aucune option de localisation UE documentée (S-16)                                                                        | Décision d'adéquation UE–États-Unis, si le fournisseur y est certifié (S-10) ; exception à R5 acceptée (décidé : D-20) |
| APNs (Apple)            | RT-01               | Jeton push, texte fixe                                    | Non vérifiée                                                                                                                                   | Idem [H]                                                                                                               |
| Paiement (Stripe)       | RT-03               | Coordonnées de facturation, carte                         | Entité européenne de Stripe (décidé : D-20)                                                                                                    | Contrat de l'article 28 ou responsabilité propre du prestataire (Q-08)                                                 |
| Service big data (D-27) | RT-07               | Fichiers Sirene complets                                  | France Central : lac ADLS Gen2 et tâche Container Apps (document 06)                                                                           | Contrat de traitement de l'hébergeur Azure, le même que pour l'hébergement du service                                  |

**État de la décision d'adéquation UE–États-Unis** (vérifié le 12 octobre 2026) : décision
d'exécution (UE) 2023/1795 du 10 juillet 2023. Le Tribunal de l'Union a rejeté le recours en
annulation le 3 septembre 2025 (affaire T-553/23, S-10). Un pourvoi est pendant devant la Cour
(C-703/25 P) ; son issue n'a pas pu être vérifiée. Un transfert fondé sur cette décision reste
donc exposé à une annulation future : c'est un argument de plus pour réduire au minimum ce qui part
aux États-Unis.

## 7. Durées de conservation consolidées

| Donnée                               | Où                                             | Durée                                                                                                                       | Fondement                                                                  |
| ------------------------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Audio d'un appel ou d'un débrief     | Mémoire                                        | Durée du traitement                                                                                                         | R2                                                                         |
| Transcription                        | Mémoire                                        | Durée de l'extraction                                                                                                       | R3                                                                         |
| Brouillon en clair                   | Mémoire                                        | Jusqu'au chiffrement ou à la réponse HTTPS                                                                                  | R1                                                                         |
| Texte et numéro d'un SMS             | Mémoire                                        | Jusqu'à la réponse du fournisseur                                                                                           | US-27                                                                      |
| Valeurs envoyées au contrôle         | Mémoire de l'API des référentiels              | Durée de la requête                                                                                                         | P-05                                                                       |
| Code de connexion                    | `app.otp_challenges`                           | Validité 10 minutes ; empreinte purgée 24 heures après expiration                                                           | US-01                                                                      |
| Enveloppe chiffrée                   | `app.envelopes`                                | Accusé de réception, 7 jours au plus                                                                                        | Passation, section 9                                                       |
| Créneaux                             | `app.availability_slots`                       | Fenêtre de 14 jours, passés purgés                                                                                          | US-05                                                                      |
| Sessions d'appel et `caller_hash`    | `app.call_sessions`                            | 90 jours [H]                                                                                                                | Passation ; à justifier (Q-05)                                             |
| Exécutions d'extraction, corrections | `app.extraction_runs`, `app.field_corrections` | 90 jours [H], puis agrégats                                                                                                 | RT-05                                                                      |
| Agrégats de qualité                  | `app.*_metrics_hourly`                         | 13 mois [H]                                                                                                                 | Comparaison d'une année sur l'autre                                        |
| Envois de SMS                        | `app.sms_jobs`                                 | 90 jours [H]                                                                                                                | Suivi du statut ; litige sur un envoi                                      |
| Tests de renvoi                      | `app.forwarding_tests`                         | 30 jours [H]                                                                                                                | Assistance                                                                 |
| Webhooks traités                     | `app.processed_webhooks`                       | 7 jours [H]                                                                                                                 | Idempotence                                                                |
| Clés d'idempotence des requêtes      | `app.idempotency_keys`                         | 24 heures [H]                                                                                                               | Idempotence (contrat d'API de la phase 2, section 2.5)                     |
| Journal d'audit                      | `app.audit_events`                             | 1 an [H]                                                                                                                    | Traçabilité                                                                |
| Journal d'accès et de sécurité       | Journaux                                       | 6 mois [H]                                                                                                                  | Recommandation de la CNIL : 6 mois à 1 an (S-14)                           |
| Journal de diagnostic                | Journaux                                       | 30 jours [H]                                                                                                                | Diagnostic                                                                 |
| Sauvegardes de la base PostgreSQL    | Hébergeur                                      | 30 jours [H] ; toute purge est prolongée d'autant                                                                           | Restauration après incident (RT-04)                                        |
| Compte, ligne, appareils             | `app.accounts`, `app.lines`, `app.devices`     | Durée du contrat, puis 30 jours (cascade du compte) [H] ; jeton d'appareil : jusqu'à révocation, ou 90 jours sans usage [H] | RT-01                                                                      |
| Sauvegarde                           | Stockage objet                                 | Jusqu'au remplacement ; fin du contrat plus 30 jours [H]                                                                    | D-13                                                                       |
| Archive comptable                    | Stockage objet                                 | 10 ans à compter de la clôture de l'exercice comptable [H : article L123-22 du Code de commerce à relire]                   | L123-22 (S-12) ; après la fermeture du compte : D-23, sous réserve de Q-06 |
| Factures de Muninn                   | Comptabilité de Muninn                         | 10 ans à compter de la clôture de l'exercice comptable [H : article L123-22 du Code de commerce à relire]                   | L123-22                                                                    |
| Fichiers Sirene                      | Lac ADLS Gen2 (D-27)                           | Fin du traitement, au plus tard sous 24 h [H]                                                                               | RT-07                                                                      |
| Agrégats du dimensionnement          | Schéma `market`                                | 5 ans [H]                                                                                                                   | RT-07                                                                      |
| Demandes d'exercice des droits       | Hors production                                | 5 ans [H]                                                                                                                   | Q-15                                                                       |

Les purges sont exécutées par worker-maintenance et tracées dans `app.purge_runs` ; un échec
déclenche une alerte (US-41). Toute durée de cette table est prolongée de la rétention des
sauvegardes de la base (30 jours [H]) : une ligne supprimée y reste lisible jusqu'à leur
expiration.

## 8. Droits des personnes et leur mise en œuvre

Délai de réponse : un mois à compter de la réception, prorogeable de deux mois pour une demande
complexe ou des demandes nombreuses, avec information de la personne dans le premier mois
(article 12.3, S-04).

### 8.1 Artisans (Muninn responsable)

| Droit                   | Mise en œuvre                                                                                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Information (art. 13)   | Politique de confidentialité dans l'application et à l'inscription                                                                                                                                                                   |
| Accès (art. 15)         | Écran « Mes données » : export des données serveur du compte (compte, appareils, ligne, créneaux, statuts de SMS, sessions d'appel, audit) [H : point d'API à ajouter, P-09]                                                         |
| Rectification (art. 16) | Réglages de l'application                                                                                                                                                                                                            |
| Effacement (art. 17)    | Fermeture du compte : suppression des données serveur après 30 jours [H] ; factures de Muninn conservées (obligation légale, art. 17.3 b) ; archives légales de l'artisan gardées 10 ans, chiffrées (D-23)                           |
| Portabilité (art. 20)   | Export de la configuration en JSON ; les dossiers sont déjà sur l'appareil, exportables par l'artisan                                                                                                                                |
| Opposition (art. 21)    | Applicable aux traitements fondés sur l'intérêt légitime (RT-04, RT-05), pour des raisons tenant à la situation de la personne. Non applicable, par lecture du champ de l'article 21.1, aux traitements fondés sur le contrat (S-04) |
| Limitation (art. 18)    | Sur demande, gel des purges et des traitements concernés [H]                                                                                                                                                                         |

### 8.2 Clients finaux (artisan responsable, Muninn sous-traitant)

| Droit                          | Où s'adresse la personne | Mise en œuvre technique                                                                                                                                                                                                                                                                                                                                                            | Limite                                                                                                                                                                                          |
| ------------------------------ | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Information (art. 13)          | Artisan                  | Annonce de l'agent (R6) ; modèle de mention fourni à l'artisan ; politique en ligne [H]                                                                                                                                                                                                                                                                                            | Le support oral impose une information en deux niveaux (Q-03)                                                                                                                                   |
| Accès (art. 15)                | Artisan                  | L'artisan exporte le dossier depuis l'application (F-08) ; Muninn ne peut rien fournir, il ne lit aucun dossier                                                                                                                                                                                                                                                                    | `caller_hash` : seul le serveur peut le retrouver, voir effacement                                                                                                                              |
| Rectification (art. 16)        | Artisan                  | Correction dans l'application                                                                                                                                                                                                                                                                                                                                                      | Aucune                                                                                                                                                                                          |
| Effacement (art. 17)           | Artisan                  | US-35 : dossier effacé sur l'appareil ; sauvegarde suivante sans le dossier, sans version antérieure (D-13) ; événement d'audit sans DP. Traces serveur : l'appareil transmet le numéro, le serveur calcule son empreinte, supprime les sessions d'appel correspondantes du compte, puis oublie le numéro (document 03, X-06). Enveloppes en attente : expirées en 7 jours au plus | Pièces comptables conservées jusqu'à la fin de l'archive (art. 17.3 b, L123-22 ; US-34). Journaux des fournisseurs (CPaaS, SMS) : demande de suppression par leur interface, si elle existe [H] |
| Opposition (art. 21)           | Artisan                  | Refus de l'assistant pendant l'appel : seul le numéro est gardé pour un rappel (US-10). Refus d'être rappelé : l'artisan supprime le dossier                                                                                                                                                                                                                                       | Base contractuelle : l'opposition ne s'applique pas en tant que telle [H]                                                                                                                       |
| Limitation (art. 18)           | Artisan                  | Gel du dossier sur l'appareil [H]                                                                                                                                                                                                                                                                                                                                                  | Aucune                                                                                                                                                                                          |
| Décision automatisée (art. 22) | Sans objet               | Aucune décision fondée exclusivement sur un traitement automatisé : l'artisan valide chaque brouillon, le client accepte ou non un créneau                                                                                                                                                                                                                                         | Aucune                                                                                                                                                                                          |

**Demande reçue par Muninn.** Muninn ne peut pas identifier le client final dans ses données (R1).
Il transmet la demande à l'artisan concerné, si celui-ci est identifiable (numéro Muninn appelé),
dans un délai de 3 jours ouvrés [H], et répond au demandeur qu'elle a été transmise. C'est l'aide
prévue par l'article 28.3 e).

**Preuve de destruction.** La mention datée de destruction de l'audio et de la transcription
(US-31) est une assertion du serveur, adossée aux tests de conformité. Elle informe ; elle ne
prouve pas l'effacement physique de la mémoire (document 02, F-02, T7).

## 9. Analyse d'impact (AIPD) : condition C3 de l'analyse

### 9.1 Est-elle obligatoire ?

L'article 35.1 impose une analyse d'impact quand un traitement est « susceptible d'engendrer un
risque élevé pour les droits et libertés des personnes physiques ». L'article 35.3 cite trois cas,
dont aucun ne s'applique directement : évaluation systématique et approfondie fondée sur un
traitement automatisé, traitement à grande échelle de catégories particulières, surveillance
systématique d'une zone publique (S-05).

La CNIL retient neuf critères, issus des lignes directrices européennes, et écrit qu'une analyse
est requise dès que le traitement en remplit **au moins deux** (S-06).

| Critère                                             | Appliqué à Muninn (ST-01, ST-02)                                                                                  | Rempli         |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------- |
| Évaluation ou notation                              | Aucune notation des personnes                                                                                     | Non            |
| Décision automatique à effet juridique ou similaire | L'artisan valide chaque brouillon                                                                                 | Non            |
| Surveillance systématique                           | Aucune                                                                                                            | Non            |
| Données sensibles ou hautement personnelles         | Adresse du domicile, absence ou urgence au domicile, voix ; données de santé exclues mais possiblement dites (R7) | Probable [H]   |
| Grande échelle                                      | Faible au lancement ; élevée à la cible (milliers d'artisans, appels quotidiens) [H]                              | À la cible [H] |
| Croisement d'ensembles de données                   | Contrôle par des référentiels publics, sans donnée d'une autre personne                                           | Non            |
| Personnes vulnérables                               | Appelants âgés, en situation d'urgence (fuite, gaz)                                                               | Possible [H]   |
| Usage innovant ou nouvelle solution technologique   | Agent vocal à base de LLM, transcription et extraction automatiques                                               | Oui            |
| Exclusion du bénéfice d'un droit ou d'un contrat    | Le refus de l'assistant mène à un rappel, pas à une exclusion                                                     | Non            |

**Conclusion.** Au moins deux critères sont remplis (usage innovant, et données hautement
personnelles ou personnes vulnérables). Selon la lecture de la CNIL, l'analyse d'impact est
obligatoire pour ST-01 et ST-02.

La liste des quatorze types d'opérations pour lesquelles la CNIL exige une analyse (délibération
n° 2018-327) ne vise pas explicitement un agent vocal (S-07). L'entrée la plus proche, les
données biométriques servant à identifier une personne de manière unique parmi des personnes
vulnérables, ne s'applique pas : Muninn ne crée aucune empreinte vocale.

### 9.2 Qui la fait

Pour ST-01 et ST-02, l'obligation pèse sur le responsable, donc sur chaque artisan. Deux textes
permettent de l'organiser sans demander à chaque artisan une analyse qu'il ne saurait pas faire :

- une seule analyse peut porter sur « un ensemble d'opérations de traitement similaires qui
  présentent des risques élevés similaires » (article 35.1, S-05) ;
- le sous-traitant aide le responsable à respecter les articles 32 à 36 (article 28.3 f).

**Proposition.** Muninn rédige une **analyse type** de ses traitements ST-01 à ST-04, fournie à
chaque artisan avec le contrat de sous-traitance. Muninn rédige aussi sa propre analyse pour
RT-04, à cause de `caller_hash`, et pour RT-06 s'il est un jour mis en œuvre.

### 9.3 Quand

Avant tout traitement de données réelles : avant le premier appel réel, donc avant tout POC
terrain. C'est la condition C3 de l'analyse stratégique (analyse d'impact et avis juridique), déjà
citée par US-35 et US-42. Le projet de certification, qui n'utilise que des données synthétiques
(R9) et une téléphonie simulée, ne la déclenche pas ; il la prépare.

### 9.4 Contenu et matière déjà disponible

| Partie de l'analyse           | Matière disponible                                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Description des traitements   | Document 02 de la phase 0 (flux, section 4) ; ce registre                                                   |
| Nécessité et proportionnalité | Minimisation par construction : R1 à R4, US-05, contrôle par préfixe (US-51)                                |
| Risques pour les personnes    | Document 03 de la phase 1 (sections 5 et 7) ; points P-01 à P-18 du document 02                             |
| Mesures                       | Document 03 de la phase 1 (garde-fous et tests TA-01 à TA-40)                                               |
| Risques résiduels             | X-01 (transferts, exception acceptée par D-20), Q-04 (santé dite par l'appelant), sécurité des fournisseurs |

[H] Le contenu minimal de l'analyse est fixé par l'article 35.7 ; ce paragraphe n'a pas été relu
pour ce document. Le logiciel PIA de la CNIL peut servir de support [non vérifié].

### 9.5 Lien avec le règlement européen sur l'IA

Selon la Commission européenne, les obligations de transparence du règlement (UE) 2024/1689, dont
l'information des personnes qui interagissent avec un système conversationnel, prennent effet en
août 2026 ; le report adopté en 2026 vise les systèmes à haut risque, pas cette obligation
(S-11). R6 et D-04, qui font annoncer l'assistant dès la première phrase, vont dans ce sens.
L'article 50 n'a pas été relu mot à mot : la conformité exacte de la phrase d'annonce est à
confirmer (Q-16).

## 10. Contradictions et écarts signalés

| ID   | Écart                                                                                                                          | Règle     | Traitement proposé                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ | --------- | -------------------------------------------------------------------------------------- |
| X-01 | Push (FCM, APNs), paiement, peut-être CPaaS : opérés par des sociétés établies aux États-Unis, contre la lecture retenue de R5 | R5        | Décidé : D-20. Exception à R5 acceptée et documentée (document 03, section 9)          |
| X-02 | Archive de 10 ans et fin du contrat de sous-traitance                                                                          | R1, US-34 | Décidé : D-23, sous réserve d'une clause contractuelle et de l'avis de l'avocat (Q-06) |
| X-07 | RT-06 (appels réels conservés pour évaluation) contredit R2 s'il garde l'audio                                                 | R2        | Transcriptions anonymisées seulement, ou révision de R2 après avis                     |
| X-08 | La passation fixe 90 jours pour les sessions d'appel sans dire pourquoi ; une durée sans finalité n'est pas justifiable        | R4        | Finalité RT-04 retenue ; durée à justifier ou réduire (Q-05)                           |
| X-09 | Une donnée de santé dite par l'appelant transite en clair chez le STT et le LLM avant tout filtrage                            | R7        | Q-04 ; mesure : aucune rétention, refus d'extraction, test de conformité               |

## 11. Questions pour l'avocat

| ID   | Question                                                                                                                                                                                                                               |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q-01 | La qualification « artisan responsable, Muninn sous-traitant » tient-elle, alors que Muninn fixe le schéma des données collectées et les questions de l'agent ? Y a-t-il un risque de responsabilité conjointe ?                       |
| Q-02 | Quelle base légale l'artisan doit-il retenir pour le traitement des appels par un agent automatique : mesures précontractuelles, intérêt légitime ? Le choix change-t-il le droit d'opposition ?                                       |
| Q-03 | L'annonce orale de l'agent (R6) suffit-elle comme premier niveau d'information au titre de l'article 13 ? Quel second niveau prévoir (message, lien envoyé par SMS, politique en ligne) ?                                              |
| Q-04 | Un appelant peut dire une donnée de santé malgré R7 ; elle transite chez le STT et le LLM avant d'être refusée. Ce passage éphémère est-il un traitement de catégorie particulière (art. 9) ? Quelles mesures suffisent ?              |
| Q-05 | `caller_hash` conservé 90 jours pour la lutte contre les abus : la finalité et la durée sont-elles proportionnées ? Muninn est-il bien responsable de cette seule finalité ?                                                           |
| Q-06 | À la fermeture d'un compte, Muninn doit supprimer ou restituer les données (art. 28.3 g). Peut-il, sur instruction, garder l'archive comptable chiffrée jusqu'à son terme ? Sinon, la restitution suffit-elle ? Qui supporte le coût ? |
| Q-07 | Un hébergeur ou un service big data en France ou dans l'UE, filiale d'une société établie hors UE : y a-t-il transfert, au sens du RGPD, du seul fait d'un accès à distance possible ?                                                 |
| Q-08 | Le prestataire de paiement est-il sous-traitant de Muninn ou responsable de ses propres traitements (lutte contre la fraude, obligations bancaires) ?                                                                                  |
| Q-09 | Push : un jeton d'appareil et un texte fixe envoyés à FCM et APNs justifient-ils une analyse de transfert, compte tenu du pourvoi pendant contre la décision d'adéquation (C-703/25 P) ?                                               |
| Q-10 | Un SMS de rappel de rendez-vous envoyé au nom de l'artisan est-il un message de service hors du champ de la prospection ? Quelles mentions sont obligatoires ?                                                                         |
| Q-11 | Le jeu de 50 appels réels (RT-06) : base légale, information et recueil de l'accord des appelants, possibilité réelle d'anonymiser une demande vocale, responsable du traitement                                                       |
| Q-12 | L'étude Sirene (RT-07) peut-elle se prévaloir de l'article 14.5 b) pour l'information des entrepreneurs individuels ? Le traitement d'agrégats sans lecture des colonnes d'identité respecte-t-il le statut de diffusion partielle ?   |
| Q-13 | Perte de la clé de l'artisan (D-14) avant la fin des 10 ans de conservation : quelle répartition de responsabilité entre l'artisan et Muninn, et quelle clause écrire ?                                                                |
| Q-14 | Muninn doit-il désigner un délégué à la protection des données (art. 37) au regard du volume et de la nature des traitements à la cible ?                                                                                              |
| Q-15 | Combien de temps garder la trace des demandes d'exercice des droits et de leurs réponses ?                                                                                                                                             |
| Q-16 | La phrase d'annonce de l'agent satisfait-elle l'obligation de transparence de l'article 50 du règlement (UE) 2024/1689, et Muninn y est-il fournisseur ou déployeur ?                                                                  |
| Q-17 | La transcription en temps réel d'un appel, sans enregistrement conservé, relève-t-elle d'un régime propre aux communications électroniques ou aux interceptions, en plus du RGPD ?                                                     |
| Q-18 | Notification d'une violation : quel délai contractuel imposer à Muninn envers l'artisan, et quel contenu, pour que l'artisan tienne lui-même son délai de notification ?                                                               |

## 12. Décisions attendues du porteur

1. **Qualification** (section 2) : la valider comme position de travail, en attendant Q-01.
2. **Durées marquées [H]** (section 7), en particulier `caller_hash` (90 jours), journaux (6 mois
   et 30 jours), comptes fermés (30 jours).
3. **RT-06** : renoncer au jeu d'appels réels dans le projet de certification, et le soumettre à
   l'analyse d'impact et à l'avis juridique avant tout POC terrain.
4. **Analyse type pour les artisans** (section 9.2) : la retenir comme livrable avant tout POC
   terrain.
5. **X-01** : décidé : D-20. Exception à R5 acceptée et documentée pour le push et le paiement ;
   fournisseur de téléphonie choisi dans l'UE.

## 13. Sources

Consultées le 12 octobre 2026 par l'agent de vérification des sources. « Lu » : page ouverte et
passage cité lu. « Résumé » : passage lu dans un résumé de la CNIL. Les réserves sont dites.

| ID   | Source                                                                                                                                                                                                               | État                                                                                                                     |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| S-01 | RGPD, chapitre IV reproduit par la CNIL : https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre4                                                                                                     | Lu (art. 30.1 e et g, 35.1, 35.3, 28.2) ; résumé (art. 30.1 a à d et f, 30.2, 28.3)                                      |
| S-02 | CNIL, « Le registre des activités de traitement » et modèle simplifié : https://www.cnil.fr/fr/RGPD-le-registre-des-activites-de-traitement                                                                          | Lu ; rubriques du modèle relevées sur la page, fichier ODS non ouvert                                                    |
| S-03 | Même page, dérogation des moins de 250 salariés et traitements non occasionnels                                                                                                                                      | Lu                                                                                                                       |
| S-04 | RGPD, chapitre III reproduit par la CNIL : https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3                                                                                                    | Lu (art. 14.5 b, 22.1) ; résumé (art. 12.3, 17.3 b, 21)                                                                  |
| S-05 | RGPD, article 35 : même source que S-01                                                                                                                                                                              | Lu                                                                                                                       |
| S-06 | CNIL, « Ce qu'il faut savoir sur l'AIPD » : https://www.cnil.fr/fr/ce-quil-faut-savoir-sur-lanalyse-dimpact-relative-la-protection-des-donnees-aipd                                                                  | Lu : neuf critères, « au moins deux »                                                                                    |
| S-07 | CNIL, liste des traitements pour lesquels une AIPD est requise : https://www.cnil.fr/fr/liste-traitements-aipd-requise                                                                                               | Lu (PDF de 4 pages, quatorze types ; PDF non daté)                                                                       |
| S-08 | CEPD, lignes directrices 07/2020 sur les notions de responsable et de sous-traitant : https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-072020-concepts-controller-and-processor-gdpr_en | Page lue ; PDF illisible par l'outil : le passage sur les moyens non essentiels n'est connu que par un résumé secondaire |
| S-09 | RGPD, articles 2.2 c), 4.7 et 4.8, chapitre I reproduit par la CNIL : https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre1                                                                         | Lu                                                                                                                       |
| S-10 | Tribunal de l'UE, communiqué n° 106/25, affaire T-553/23 : https://curia.europa.eu/site/upload/docs/application/pdf/2025-09/cp250106en.pdf                                                                           | Lu ; décision 2023/1795 citée en note. Pourvoi C-703/25 P : résumé secondaire, issue non vérifiée                        |
| S-11 | Commission européenne, cadre réglementaire de l'IA : https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai                                                                                       | Lu ; texte de l'article 50 non lu                                                                                        |
| S-12 | Code de commerce, article L123-22 : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006219327/                                                                                                            | Lu : « conservés pendant dix ans »                                                                                       |
| S-13 | Texte officiel du RGPD sur EUR-Lex : https://eur-lex.europa.eu/eli/reg/2016/679/oj                                                                                                                                   | Non affiché par l'outil ; référence canonique                                                                            |
| S-14 | CNIL, recommandation sur la journalisation : https://www.cnil.fr/fr/la-cnil-publie-une-recommandation-relative-aux-mesures-de-journalisation                                                                         | Lu : « entre six mois et un an »                                                                                         |
| S-15 | CNIL, « Communication électronique : quelles règles ? » : https://www.cnil.fr/fr/communication-electronique-quelles-regles                                                                                           | Lu ; ne cite pas les rappels de rendez-vous                                                                              |
| S-16 | Firebase, confidentialité et localisation : https://firebase.google.com/support/privacy                                                                                                                              | Lu : FCM classé service global                                                                                           |

Réserves :

- les articles du RGPD ont été lus dans la reproduction de la CNIL, EUR-Lex n'ayant pas pu être
  affiché par l'outil ; une relecture sur EUR-Lex est conseillée avant l'avis juridique ;
- les articles 13, 33 et 35.7 n'ont pas été relus pour ce document ;
- la CNIL écrit qu'une AIPD est requise à partir de deux critères ; les lignes directrices
  européennes formulent cette règle de façon moins absolue [H : texte du WP248 non lu].
