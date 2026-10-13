# Besoin de production de Muninn

**Version :** 1.1
**Date :** 12 octobre 2026
**Historique :** la v1.1 applique la relecture indépendante, aligne les volumes sur
`05-chaine-llmops.md` et intègre D-29 (brouillon de secours, MD-3).
**Phase :** 2 (industrialisation)
**Statut :** proposition, à valider par le porteur
**Compétences servies :** C15 (cadre technique) ; préparation de C11 (monitorage du modèle), C19
(livraison continue) et C20 (surveillance)
**Documents liés :** passation back-end (document interne au porteur, hors dépôt) ;
`docs/decisions.md` (D-01 à D-29) ; phase 0 : `01-user-stories.md`, `02-flux-de-donnees.md` ; phase 1 :
`01-cartographie-des-donnees.md` (hypothèses HV), `02-modele-de-donnees.md`,
`03-acces-et-exposition.md`, `04-verification-exactitude.md` ; phase 2 : `03-observabilite.md`
(mesure des indicateurs), `05-chaine-llmops.md` (blocage des versions),
`06-architecture-technique.md` (composants et coûts)

Ce document ne contient aucune ligne de code. Les hypothèses sont marquées **[H]**.

## 1. Objet

Ce document fixe ce que la production doit garantir, avant de choisir comment la construire
(document 06). Il répond à quatre questions :

1. qui utilise Muninn, et avec quels volumes ;
2. quelles capacités sont critiques, et ce qu'une panne coûte ;
3. quels objectifs de service (SLO) sont mesurables, pour le produit et pour la démo ;
4. comment le service se dégrade, et combien de données on peut perdre (RPO) et en combien de
   temps on repart (RTO).

Deux cibles coexistent et ne se confondent jamais :

| Cible   | Période                         | Données                     | Trafic                                   |
| ------- | ------------------------------- | --------------------------- | ---------------------------------------- |
| Démo    | 14 octobre au 13 novembre 2026  | Synthétiques seulement (R9) | Scénarios lancés depuis la console       |
| Produit | Après la validation du POC (C1) | Réelles, chiffrées (R1)     | Appels renvoyés, application mobile, SMS |

La cible démo est celle qui sera mesurée et montrée au jury. La cible produit est une exigence de
conception : l'architecture du document 06 doit pouvoir l'atteindre sans refonte.

## 2. Utilisateurs et volumes

### 2.1 Utilisateurs

| Acteur            | Interface                                    | Produit                                   | Démo                                            |
| ----------------- | -------------------------------------------- | ----------------------------------------- | ----------------------------------------------- |
| Artisan           | Application mobile                           | 100, puis 1 000, puis 3 000 comptes [H]   | Simulé par l'exploitant dans la console (US-17) |
| Client final      | Voix (agent), SMS                            | 63 appels par artisan et par mois (HV-02) | Remplacé par le simulateur d'appel (US-36)      |
| Exploitant        | Console d'exploitation, CI, tableaux de bord | 1 personne                                | Le porteur, seul                                |
| Porteur du projet | Consoles des fournisseurs, traitement Sirene | 1 personne                                | Le même porteur ; jury en observateur           |

Les paliers de 100, 1 000 et 3 000 artisans sont ceux de la cartographie (phase 1, document 01,
section 5). Ils servent à dimensionner, pas à prévoir les ventes.

### 2.2 Volumes du produit

Hypothèses reprises de la phase 1 (document 01, section 5.1) : HV-01 (21 jours ouvrés), HV-02
(63 appels par mois), HV-03 (42 débriefs), HV-04 (21 tickets), HV-05 (10 dépenses dictées), HV-06
(47 SMS), HV-13 (40 requêtes HTTP par jour). Trois hypothèses nouvelles sont nécessaires pour
passer des volumes mensuels aux pointes. Le document 05 dimensionne la transcription sur environ
3 minutes, borne haute du déroulé de l'agent ; HP-02 est une durée moyenne, plus courte.


| Code  | Hypothèse nouvelle [H]                                               | Valeur                                                                                          |
| ----- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| HP-01 | Part du trafic d'une journée concentrée dans l'heure de pointe       | 15 %                                                                                            |
| HP-02 | Durée moyenne d'un appel pris par l'agent                            | 2,5 minutes (déroulé cible sous 3 minutes)                                                      |
| HP-03 | Jetons d'une extraction : entrée ; sortie ; part des appels relancés | 3 500 et 600 (`05-chaine-llmops.md`, section 5.5) ; 10 % de relances (hypothèse de ce document) |

Calculs, pour 1 000 artisans :

- appels : 63 × 1 000 = 63 000 par mois, soit 63 000 / 21 = 3 000 par jour ouvré ; en pointe,
  3 000 × 15 % = 450 appels par heure ;
- appels simultanés en pointe (loi de Little) : 450 / 60 × 2,5 = 18,75, soit environ 19 ;
- extractions (appels, débriefs, tickets, dépenses) : (63 + 42 + 21 + 10) × 1 000 = 136 000 par
  mois, soit 6 476 par jour ouvré et 971 par heure de pointe, environ 0,27 par seconde ;
- requêtes HTTP de l'application : 40 × 1 000 = 40 000 par jour, soit 6 000 en heure de pointe,
  environ 1,7 par seconde.

| Grandeur                          | 100 artisans | 1 000 artisans | 3 000 artisans |
| --------------------------------- | ------------ | -------------- | -------------- |
| Appels par mois                   | 6 300        | 63 000         | 189 000        |
| Appels par heure de pointe        | 45           | 450            | 1 350          |
| Appels simultanés en pointe       | 2            | 19             | 56             |
| Extractions par heure de pointe   | 97           | 971            | 2 914          |
| Requêtes HTTP par seconde, pointe | 0,17         | 1,7            | 5              |
| SMS par mois                      | 4 700        | 47 000         | 141 000        |

Les horaires de l'artisan peuvent couvrir le samedi et le dimanche (D-30) : HV-01 compte 21 jours
ouvrés, ce qui majore la pointe par jour. Un trafic de week-end étalerait la charge sans changer
les conclusions ci-dessous.

Conséquence : le débit ne dimensionne pas l'architecture. Ce qui la dimensionne, c'est la
**concurrence des appels** (une session vocale tient une connexion et des ressources pendant
2,5 minutes) et la **latence des fournisseurs d'IA**, pas le nombre de requêtes.

### 2.3 Volumes de la démo

Une seule base d'hypothèses est retenue : celle de `05-chaine-llmops.md` (sections 3.7 et 5.5),
avec le rythme mensuel de 15 évaluations de PR, 30 contrôles nocturnes et 4 contrôles de
stabilité. Les volumes du mois sont calculés sur le **jeu du 12 novembre**, le plus gros : c'est
la borne haute retenue pour les coûts. Le jeu du 29 octobre ne sert qu'à la période qui précède
le premier oral.

| Grandeur                              | Jeu du 29 octobre                                    | Jeu du 12 novembre (base des coûts)                                |
| ------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------ |
| Scénarios                             | 20 de test, 35 de conformité                         | 100 de test, 130 de conformité (40 de développement, hors verdict) |
| Appels d'une évaluation de PR         | 20 + 4 × 2 + 35 × 3 = 133 ; 266 avec la référence    | 100 + 19 × 2 + 130 × 3 = 528 ; 1 056 avec la référence             |
| Appels d'un contrôle nocturne         | 20 + 35 = 55 [H]                                     | 100 + 130 = 230                                                    |
| Appels d'un contrôle de stabilité     | 20 × 5 = 100 [H]                                     | 100 × 5 = 500                                                      |
| Extractions par mois                  | 15 × 266 + 30 × 55 + 4 × 100 = 6 040                 | 15 × 1 056 + 30 × 230 + 4 × 500 = 24 740                           |
| Parallélisme des appels au LLM        | 8 (`05-chaine-llmops.md`, section 3.7)               | 8                                                                  |
| Utilisateurs simultanés de la console | 1 à 3 (exploitant, éventuellement un membre du jury) | 1 à 3                                                              |

Les termes « 4 × 2 » et « 19 × 2 » comptent les deux exécutions supplémentaires des scénarios à
tolérance nulle du jeu de test (effectifs de 4 et 19 scénarios, tableau 4.3 du document 04 de la
phase 1, corrigé à la consolidation). Les appels du juge (VE-28) s'ajoutent : environ 4 500 par mois
[H : déduits du coût du juge du document 05].

## 3. Capacités et criticité

Échelle utilisée :

- **critique** : une panne fait perdre une donnée du client ou une demande du client final, ou
  enfreint une règle R1 à R10 ;
- **haute** : une panne bloque l'artisan, mais rien n'est perdu ; il peut réessayer ;
- **moyenne** : une panne retarde un service, sans perte ni blocage immédiat ;
- **basse** : une panne ne touche que l'exploitant ou le porteur.

| ID     | Capacité                                       | Stories             | Criticité produit           | Ce que coûte une panne                                           | Criticité démo                     |
| ------ | ---------------------------------------------- | ------------------- | --------------------------- | ---------------------------------------------------------------- | ---------------------------------- |
| CAP-01 | Prise de l'appel par l'agent vocal             | US-06 à US-10       | critique                    | Un client final raccroche sans laisser sa demande : client perdu | hors démo                          |
| CAP-02 | Extraction du brouillon d'un appel             | US-11, US-51        | critique                    | Demande reçue mais illisible pour l'artisan                      | critique                           |
| CAP-03 | Relais chiffré vers l'appareil                 | US-12               | critique                    | Appel manqué perdu si l'enveloppe disparaît avant livraison      | hors démo au 29/10, haute au 12/11 |
| CAP-04 | Destruction de l'audio et de la transcription  | US-31               | critique                    | Infraction à R2 et R3, perte de la promesse                      | critique                           |
| CAP-05 | Journalisation sans donnée personnelle         | US-39               | critique                    | Infraction à R4                                                  | critique                           |
| CAP-06 | Notification push sans contenu                 | US-12               | moyenne                     | Retard : l'appareil relève ses enveloppes à l'ouverture          | hors démo                          |
| CAP-07 | Débrief, ticket, dépense dictée                | US-13, US-21, US-22 | haute                       | L'artisan attend ; l'appareil garde la demande en file locale    | hors démo                          |
| CAP-08 | Envoi des SMS de rappel et d'imprévu           | US-27 à US-29       | haute                       | Client non prévenu ; l'envoi a une échéance                      | hors démo                          |
| CAP-09 | Connexion et enregistrement d'un appareil      | US-01               | haute                       | Nouvel artisan ou nouvel appareil bloqué                         | hors démo                          |
| CAP-10 | Synchronisation des disponibilités             | US-05, US-08        | haute                       | L'agent propose un créneau périmé, ou n'en propose pas           | hors démo                          |
| CAP-11 | API des référentiels                           | US-50, US-51        | moyenne                     | Champs marqués « non contrôlé » (mode dégradé de US-51)          | haute                              |
| CAP-12 | Sauvegarde et archive chiffrées                | US-33, US-34        | haute (durabilité critique) | Dépôt retardé : l'appareil garde la copie primaire               | hors démo                          |
| CAP-13 | Purges planifiées                              | US-41               | haute                       | Données gardées au-delà de la durée du registre (RGPD)           | moyenne                            |
| CAP-14 | Validation et correction d'un brouillon        | US-17               | haute (sur l'appareil)      | Le brouillon reste en attente                                    | critique                           |
| CAP-15 | Métriques, tableau de bord, alertes de qualité | US-38               | moyenne                     | Dégradation de l'extraction non vue                              | critique                           |
| CAP-16 | Évaluation et blocage d'une version            | US-37, US-40        | basse                       | Une livraison attend ; aucune version non évaluée ne part        | critique                           |
| CAP-17 | Chargement des référentiels                    | US-46, US-47        | basse                       | Version précédente servie, rien de cassé                         | moyenne                            |
| CAP-18 | Traitement Sirene et Urssaf                    | US-52, US-53        | basse                       | Étude de marché retardée                                         | basse                              |
| CAP-19 | Console                                        | US-36 et suivantes  | basse                       | L'exploitant perd sa vue ; le service continue                   | critique                           |

Lecture : la démo inverse une partie de l'échelle. Ce qui ne touche que l'exploitant en
production (console, évaluation, tableau de bord) est ce que le jury vient voir.

## 4. Objectifs de service (SLO)

### 4.1 Règles de définition

- Chaque SLO repose sur un indicateur (SLI) défini par deux points de mesure horodatés côté
  serveur. Le document `03-observabilite.md` décrit où et comment chaque point est émis.
- Un SLO de latence est exprimé en p50 et p95 sur une fenêtre fixée. Le p99 n'est pas retenu :
  sur les volumes de la démo, il n'a aucune valeur statistique.
- Sur un petit échantillon, un p95 n'est qu'une estimation grossière. Avec 20 scénarios, le p95
  empirique est la 19e valeur triée : le rapport le dit, et donne aussi le maximum.
- Aucun SLO ne porte sur le contenu d'un dossier : les indicateurs sont des comptes, des durées,
  des statuts et des versions (R4).

### 4.2 Table des SLO

| ID     | Indicateur (SLI) et points de mesure                                                                                 | Cible produit [H]                                    | Cible démo                                                                       | Fenêtre                                |
| ------ | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------- |
| SLO-01 | Disponibilité de l'api : part des requêtes valides qui ne reçoivent ni 5xx ni délai dépassé                          | 99,5 %                                               | 99 % pendant les créneaux de démo et de répétition                               | Mois civil ; créneau de démo           |
| SLO-02 | Disponibilité de la prise d'appel : part des appels renvoyés auxquels l'agent, ou le message de secours, répond      | 99,9 %                                               | sans objet (pas d'agent vocal)                                                   | Mois civil                             |
| SLO-03 | Latence de bout en bout : de la fin d'appel (`call_ended_at`) à l'enveloppe disponible pour l'appareil               | p50 ≤ 10 s ; p95 ≤ 30 s                              | sans objet le 29/10 ; mêmes cibles le 12/11                                      | 28 jours glissants                     |
| SLO-04 | Latence de la démo : du lancement du scénario dans l'api au `DossierDraft` rendu à la console                        | sans objet                                           | p50 ≤ 10 s ; p95 ≤ 30 s                                                          | Chaque évaluation et chaque répétition |
| SLO-05 | Latence de l'extraction seule : de l'entrée dans le composant extraction au brouillon validé, relance comprise       | p50 ≤ 6 s ; p95 ≤ 20 s                               | p50 ≤ 6 s ; p95 ≤ 20 s                                                           | 28 jours ; chaque évaluation           |
| SLO-06 | Latence de l'API des référentiels                                                                                    | p95 ≤ 50 ms (US-50)                                  | p95 ≤ 50 ms                                                                      | 28 jours ; chaque évaluation           |
| SLO-07 | Exactitude des six champs clés sur la partition de test (phase 1, document 04, VE-11)                                | ≥ 90 %, borne basse de Wilson ≥ 85 %                 | ≥ 90 % mesurés, intervalle publié                                                | Chaque version candidate               |
| SLO-08 | Échecs sur les cas à tolérance nulle (médical, gaz, injection, refus), sur 3 exécutions                              | 0                                                    | 0                                                                                | Chaque version candidate               |
| SLO-09 | Taux de `needs_review` en production                                                                                 | ≤ 20 % par heure, 20 extractions au moins (F-11, T4) | ≤ 20 % sur une évaluation                                                        | Heure glissante                        |
| SLO-10 | Taux de champs « non contrôlé » (API des référentiels muette)                                                        | ≤ 1 %                                                | 0 % hors scénario de panne volontaire                                            | 28 jours ; chaque évaluation           |
| SLO-11 | Champs corrigés par brouillon validé, approximation de l'exactitude en production (aucune vérité terrain n'y existe) | ≤ 1 en moyenne (HV-09 suppose 0,5)                   | mesuré, non borné                                                                | 28 jours                               |
| SLO-12 | Appels perdus : sessions d'appel terminées sans enveloppe, complète ou dégradée, dans les 10 minutes                 | ≤ 0,1 %                                              | 0 scénario sans brouillon ni erreur explicite                                    | Mois civil                             |
| SLO-13 | Coût d'une extraction (jetons du LLM, relance comprise)                                                              | ≤ 0,01 €                                             | ≤ 0,01 €, mesuré par le harnais                                                  | Chaque évaluation                      |
| SLO-14 | Coût complet d'un appel pris (CPaaS, STT, LLM de l'agent et de l'extraction, TTS)                                    | ≤ 0,15 € [H : à confirmer par le benchmark d'E2]     | sans objet                                                                       | Mois civil                             |
| SLO-15 | Retard des purges : écart entre l'échéance d'une donnée et sa suppression                                            | ≤ 24 h ; enveloppe ≤ 7 j + 1 h                       | ≤ 24 h                                                                           | Chaque exécution de purge              |
| SLO-16 | Coût Azure mensuel de l'environnement                                                                                | à fixer avec le modèle économique                    | ≤ 60 € par mois, tenu dans le scénario bas seulement (document 06, section 10.3) | Mois civil                             |

### 4.3 Justification des cibles

**Disponibilité (SLO-01, SLO-02).** La prise d'appel vise plus haut que l'api, car un appel
manqué ne revient pas, alors qu'une requête de l'application se rejoue. La cible de 99,9 % n'est
tenable que grâce au message de secours porté par le CPaaS (section 6) : si le back-end est
injoignable, le fournisseur de téléphonie joue un message fixe [H : fonction de repli à vérifier
chez le fournisseur retenu, ADR-02]. Sans ce repli, la cible serait bornée par la disponibilité
composée des composants (section 4.4).

**Latence (SLO-03 à SLO-06).** La passation back-end (document interne au porteur) fixe « moins de 30 secondes entre la fin
d'un appel et la réception du dossier par l'appareil ». Ce document la lit comme un p95 sur
l'enveloppe disponible côté serveur. La livraison push elle-même n'est pas sous le contrôle de
Muninn (FCM, APNs) : elle est mesurée à part, depuis l'accusé de réception, mais n'entre pas dans
le SLO. La cible p50 de 10 secondes laisse une marge pour une relance de l'extraction.

**Exactitude (SLO-07, SLO-08).** Ce sont les seuils de blocage de la phase 1 (document 04,
section 6), repris sans changement. Avec 20 scénarios, un score de 90 % est compatible avec une
exactitude réelle de 77,9 % à 95,8 % selon la corrélation des erreurs (même document, section
4.4) : la démo publie l'intervalle et ne prétend pas atteindre le KPI du POC.

**Coût (SLO-13, SLO-14).** Calcul pour une extraction (HP-03) avec les prix publics de Mistral au
12 octobre 2026, niveau Standard, en dollars par million de jetons :

| Modèle                      | Entrée ($/M) | Sortie ($/M) | Coût d'une extraction ($)                       | Avec 10 % de relances ($) | En euros  | Avec la majoration régionale de 10 % [H] |
| --------------------------- | ------------ | ------------ | ----------------------------------------------- | ------------------------- | --------- | ---------------------------------------- |
| Mistral Small 4 (v26.03)    | 0,15         | 0,6          | 3 500 × 0,15 / 10⁶ + 600 × 0,6 / 10⁶ = 0,000885 | 0,00097                   | 0,00086 € | 0,00094 €                                |
| Mistral Medium 3.5 (v26.04) | 1,5          | 7,5          | 3 500 × 1,5 / 10⁶ + 600 × 7,5 / 10⁶ = 0,00975   | 0,0107                    | 0,0094 €  | 0,0104 €                                 |

Source : <https://docs.mistral.ai/inference/pricing>, consultée le 12 octobre 2026. Conversion à
0,88 € pour 1 $ [H : rapport observé entre les prix en euros et en dollars de l'API des prix
Azure, pas un taux de change officiel]. Une majoration de 10 % sur les points de terminaison
régionaux est signalée par une source secondaire, non lue sur une page officielle. R5 impose le
point de terminaison UE : si cette majoration s'applique à lui, **Mistral Medium 3.5 ne tient pas
SLO-13** (0,0104 € pour 0,01 €), alors que Small 4 le tient largement. Ce point entre dans le
choix d'ADR-03 (document 06), en attente du porteur. Le coût complet d'un appel (SLO-14) dépend
du CPaaS, du STT et du TTS, non choisis : la cible de 0,15 € est une hypothèse, à remplacer par le
benchmark d'E2.

### 4.4 Disponibilité composée

La chaîne critique de la démo enchaîne la console, l'api, l'extraction, l'API des référentiels,
PostgreSQL et le fournisseur LLM. Sa disponibilité est au plus le produit de celles de ses
maillons. Le seul engagement chiffré lu est celui de PostgreSQL flexible sans haute
disponibilité : 99,9 % (document 06, section 11.1). La chaîne est donc bornée à 99,9 % au mieux,
avant même de compter Container Apps, dont le pourcentage n'a pas été lu, et le fournisseur LLM,
qui ne publie pas d'engagement pour son offre standard [H : non trouvé dans la documentation
lue]. Une prise d'appel à 99,9 % (SLO-02) n'est donc tenable que par le message de repli du
CPaaS (MD-2), qui ne dépend pas du back-end. La cible de 99 % de la démo pendant les créneaux
fixés est tenue par les moyens de secours (section 6.3), pas par les engagements des
fournisseurs.

## 5. Budgets d'erreur

### 5.1 Calcul

| SLO    | Cible  | Fenêtre du SLO     | Budget sur la fenêtre                                        |
| ------ | ------ | ------------------ | ------------------------------------------------------------ |
| SLO-01 | 99,5 % | Mois civil (30 j)  | 0,5 % des requêtes ; en temps : 43 200 min × 0,005 = 216 min |
| SLO-02 | 99,9 % | Mois civil         | 0,1 % des appels ; pour 63 000 appels, 63 appels             |
| SLO-03 | p95    | 28 jours glissants | 5 % des appels au-delà de 30 s                               |
| SLO-12 | 0,1 %  | Mois civil         | 63 appels sans enveloppe sur 63 000                          |

### 5.2 Politique

| Budget consommé sur la fenêtre | Conséquence                                                                                                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Moins de 50 %                  | Livraisons normales, y compris de prompts et de modèles, sous réserve de l'évaluation bloquante                   |
| 50 à 100 %                     | Livraisons de fiabilité en priorité ; tout changement du prompt ou du modèle exige un rapport de latence en plus  |
| Budget épuisé                  | Gel des livraisons fonctionnelles jusqu'au retour sous le seuil ; fiche d'incident (C21) ; revue en rétrospective |

Les SLO d'exactitude (SLO-07, SLO-08) n'ont pas de budget : ils bloquent chaque version (document
`05-chaine-llmops.md`). Un budget d'erreur suppose un trafic suffisant : en démo, la politique est
remplacée par une règle simple : trois répétitions complètes consécutives doivent réussir avant le
28 octobre à 18 h ; tout échec ouvre une fiche et remet le compte à zéro. Si la condition n'est
pas atteinte le 28 à 18 h, la démo du 29 se fait sur la dernière configuration qui a réussi une
répétition complète. Si l'échec vient d'Azure, c'est le plan B local ; si rien n'a réussi, c'est
le plan C (vidéo). L'écart est dit au jury, avec la fiche d'incident.

## 6. Modes dégradés

### 6.1 Principe

Un mode dégradé ne contourne jamais une règle R1 à R10. Il réduit le service rendu, l'annonce
honnêtement, et se mesure (SLO-10, SLO-12). Chaque bascule émet un événement sans donnée
personnelle, décrit dans `03-observabilite.md`.

### 6.2 Produit

| ID   | Panne                                            | Détection                                      | Comportement                                                                                                                                                                                                                                                                                                                          | Ce que voit l'utilisateur                                                                                     |
| ---- | ------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| MD-1 | LLM indisponible pendant l'appel                 | Délai ou erreur au premier tour de l'agent     | L'agent passe à un déroulé fixe : annonce (R6), recueil du seul numéro de rappel confirmé par touches ou par l'identifiant de l'appelant, annonce d'un rappel, raccroché. Rien n'est inventé                                                                                                                                          | Client final : « votre demande sera transmise, [Prénom] vous rappellera ». Artisan : enveloppe « à rappeler » |
| MD-2 | Back-end injoignable au moment de l'appel        | Repli du CPaaS (absence de réponse au webhook) | Le CPaaS joue un message fixe enregistré, sans recueil [H : fonction à vérifier, ADR-02]. Aucune donnée n'est créée                                                                                                                                                                                                                   | Client final : message d'indisponibilité et invitation à rappeler ou à envoyer un SMS                         |
| MD-3 | LLM indisponible pour l'extraction après l'appel | Erreur ou délai à l'appel du fournisseur       | Deux nouvelles tentatives en mémoire, espacées, dans une limite de 60 s [H]. Puis brouillon de secours `fallback_no_llm` (D-29), chiffré pour l'appareil : numéro et heure de l'appel, marqué à vérifier. La transcription est détruite (R3)                                                                                          | Artisan : « Appel de 14 h 02, à rappeler, à vérifier »                                                        |
| MD-4 | API des référentiels muette                      | Délai de 300 ms dépassé [H]                    | Champs marqués « non contrôlé », confiance abaissée (US-51, critère 4)                                                                                                                                                                                                                                                                | Artisan : champ « à vérifier » avec la raison en texte (EXA-02)                                               |
| MD-5 | Push indisponible                                | Erreur du fournisseur de notification          | Enveloppe gardée ; nouvelle tentative ; l'appareil relève ses enveloppes à l'ouverture                                                                                                                                                                                                                                                | Artisan : demande visible à la prochaine ouverture                                                            |
| MD-6 | Redis indisponible                               | Sonde de disponibilité                         | Tâches asynchrones retardées. La chaîne de l'appel n'en dépend pas (D-11)                                                                                                                                                                                                                                                             | Rien, sauf retard d'un SMS ou d'une purge                                                                     |
| MD-7 | PostgreSQL indisponible                          | Sonde `GET /ready`                             | Prise d'appel maintenue (configuration de ligne gardée en mémoire, durée bornée [H]). L'enveloppe, déjà chiffrée, est gardée **en mémoire** et réessayée jusqu'à 60 min, soit le RTO de la base (section 7.2). Elle n'est **pas durable** pendant ce temps : un redémarrage du composant la perd, et la perte est comptée dans SLO-12 | Client final : rien. Artisan : retard ; perte si la panne dépasse 60 min ou si le composant redémarre         |
| MD-8 | Budget mensuel des fournisseurs atteint          | Compteur de coût (phase 1, document 03, 5.4)   | Arrêt de l'agent conversationnel à 100 %, bascule sur MD-1                                                                                                                                                                                                                                                                            | Comme MD-1                                                                                                    |
| MD-9 | Stockage objet indisponible                      | Erreur au dépôt                                | L'appareil garde sa copie et réessaie (EXU-10)                                                                                                                                                                                                                                                                                        | Artisan : « sauvegarde en attente »                                                                           |

**MD-3, tranché par D-29.** Une extraction ratée après l'appel ne peut pas être rejouée plus tard :
la transcription n'a pas le droit d'exister au-delà de l'extraction (R3) et ne passe pas par la
file (D-11). Le brouillon de secours garantit qu'aucune demande n'est perdue en silence : l'artisan
sait qu'un client a appelé, et quand.

**MD-7, durabilité.** Pendant une panne de la base, l'enveloppe n'a pas de copie durable. Une
option rendrait l'attente durable : déposer l'enveloppe chiffrée dans le stockage objet, que le
serveur ne peut pas lire (R1 respectée). Elle n'est pas retenue ici ; elle est notée pour le
produit (BP-02).

### 6.3 Démo

| Panne                            | Réponse préparée                                                                                                                                                                                                                       |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM indisponible pendant l'oral  | Bascule affichée sur le faux fournisseur LLM, nommé comme tel à l'écran. Présentation du dernier rapport d'évaluation réel produit par la CI. L'écart est dit au jury                                                                  |
| API des référentiels arrêtée     | Rien à cacher : c'est le scénario du mode dégradé de US-51, montrable volontairement                                                                                                                                                   |
| Environnement Azure indisponible | Plan B : la même image de conteneur lancée par `docker compose` sur le poste du porteur, avec une base locale chargée par les mêmes scripts. Bascule en moins de 5 minutes, répétée le 27 octobre (`07-methode-agile.md`, section 6.1) |
| Poste ou réseau indisponible     | Plan C : enregistrement vidéo de la démo complète, fait le 28 octobre, avec ses horodatages                                                                                                                                            |
| Démarrage à froid trop lent      | Nombre minimal de répliques à 1 sur les composants de la chaîne pendant les créneaux de démo (document 06, section 10)                                                                                                                 |

## 7. RPO et RTO

### 7.1 Définitions

- **RPO** : quantité maximale de données qu'on accepte de perdre, exprimée en durée.
- **RTO** : durée maximale pour rendre le service après une panne.

### 7.2 Par actif

| Actif                                   | Nature                                           | RPO produit [H]                                                                                                  | RTO produit [H] | RPO démo                 | RTO démo                      |
| --------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------ | ----------------------------- |
| Enveloppes en attente (`app.envelopes`) | Seule copie d'un appel manqué non livré          | 5 min pour une enveloppe enregistrée ; une enveloppe créée pendant une panne de la base n'est pas durable (MD-7) | 1 h             | sans objet le 29/10      | sans objet                    |
| Autres tables du schéma `app`           | Métadonnées techniques                           | 15 min                                                                                                           | 4 h             | 24 h                     | 1 h                           |
| Schéma `ref`                            | Données publiques, rechargeables                 | Dernière version publiée                                                                                         | 4 h             | Dernière version publiée | 1 h (rechargement par le job) |
| Schéma `market`                         | Agrégats reproductibles depuis Sirene            | Dernière exécution                                                                                               | 2 jours         | Dernière exécution       | 1 jour                        |
| Redis                                   | Identifiants de tâches seulement (D-11)          | Perte acceptée : les tâches sont rejouables par idempotence                                                      | 30 min          | Perte acceptée           | 15 min                        |
| Blobs de sauvegarde et d'archive        | Copie secondaire, la primaire est sur l'appareil | Dernier dépôt de l'appareil                                                                                      | 24 h            | sans objet               | sans objet                    |
| Images de conteneur                     | Reconstructibles depuis Git                      | Dernier commit sur `main`                                                                                        | 30 min          | Dernier commit           | 15 min (révision précédente)  |
| Configuration et prompts                | Versionnés dans Git                              | 0                                                                                                                | 30 min          | 0                        | 15 min                        |
| Secrets                                 | Key Vault, suppression réversible                | 0                                                                                                                | 1 h             | 0                        | 30 min                        |

Le RPO de 5 minutes des enveloppes enregistrées est tenu par la restauration à un instant donné
de PostgreSQL, annoncée « jusqu'à cinq minutes » (document 06, section 11.2). Le RTO d'une heure
n'est pas garanti par Microsoft, qui annonce « de quelques minutes à quelques heures » : c'est un
écart assumé. Le délai d'attente de MD-7 est aligné sur ce RTO. Pour la démo, la base ne contient que des métadonnées
synthétiques et rechargeables : un RPO de 24 heures suffit.

### 7.3 Restauration et RGPD

Restaurer une sauvegarde de la base ressuscite des lignes déjà purgées (phase 1, document 02,
section 9.3). Règle : après toute restauration, les purges sont relancées **avant** la réouverture
du service, et la restauration est tracée dans `app.audit_events`. Une enveloppe restaurée peut
avoir déjà été livrée : l'appareil écarte les doublons par l'identifiant du brouillon (`draft_id`
du contrat 1.1, D-24).

## 8. Contrôle de cohérence

| Règle ou décision | Effet sur ce document                                                                                                            | Respectée |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------- |
| R1                | Les modes dégradés n'écrivent rien en clair ; l'enveloppe dégradée est chiffrée pour l'appareil                                  | oui       |
| R2, R3            | MD-3 détruit la transcription et envoie le brouillon de secours (D-29) ; aucune reprise différée n'est possible, et cela est dit | oui       |
| R4                | Les SLI sont des comptes, des durées, des statuts et des versions                                                                | oui       |
| R5                | Les cibles de coût supposent des points de terminaison UE                                                                        | oui       |
| R6                | MD-1 garde l'annonce en première phrase                                                                                          | oui       |
| R9                | La démo n'utilise que des données synthétiques ; le plan B aussi                                                                 | oui       |
| R10               | Aucun SLO n'exige un achat ; la fonction de repli du CPaaS (MD-2) relève d'ADR-02                                                | oui       |
| D-07              | La console reçoit le brouillon en clair en démo ; SLO-04 mesure cette réponse                                                    | oui       |
| D-29              | MD-3 suit la décision : brouillon de secours, transcription détruite                                                             | oui       |
| D-11              | Redis hors de la chaîne critique (MD-6), RPO de Redis sans objet                                                                 | oui       |
| D-13              | Aucune version précédente des sauvegardes : le RPO des blobs est celui du dernier dépôt                                          | oui       |

Écart signalé : la passation back-end dit « moins de 30 secondes » sans préciser de percentile.
Ce document propose un p95 (SLO-03). Une lecture « 100 % sous 30 s » serait intenable face à la
latence variable d'un fournisseur LLM.

## 9. Points incertains et décisions attendues

| ID    | Point                                                                                                            | Proposition                                                                                                                                                          |
| ----- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BP-01 | Lecture « p95 ≤ 30 s » du KPI de latence                                                                         | À valider par le porteur                                                                                                                                             |
| BP-02 | MD-7 : rendre durable l'enveloppe en attente pendant une panne de la base (dépôt chiffré dans le stockage objet) | Non retenu pour la démo ; à décider pour le produit. MD-3 est tranché par D-29                                                                                       |
| BP-03 | Fonction de repli du CPaaS (MD-2)                                                                                | Critère de choix d'ADR-02                                                                                                                                            |
| BP-04 | Cibles produit (99,5 %, 99,9 %, 0,15 € par appel)                                                                | Hypothèses ; à revoir après le benchmark d'E2 et le modèle économique                                                                                                |
| BP-05 | HP-01 à HP-03                                                                                                    | À remplacer par des mesures dès les premiers appels réels                                                                                                            |
| BP-06 | Engagement de disponibilité du fournisseur LLM                                                                   | Non trouvé ; à demander au fournisseur si le produit en dépend                                                                                                       |
| BP-07 | Créneaux de démo où le nombre minimal de répliques passe à 1                                                     | 23 octobre de 9 h à 21 h (répétition 1, J9) ; 27 octobre 14 h au 30 octobre 18 h ; 11 novembre 9 h au 13 novembre 18 h [H]. Soit 88 h en octobre et 57 h en novembre |

## 10. Sources

| Sujet                                     | Source                                                                                            | Consultée le    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------- |
| Prix de Mistral Small 4 et Medium 3.5     | <https://docs.mistral.ai/inference/pricing>                                                       | 12 octobre 2026 |
| Hébergement des données Mistral dans l'UE | <https://help.mistral.ai/en/articles/347629-where-do-you-store-my-data-or-my-organization-s-data> | 12 octobre 2026 |
| Zéro rétention chez Mistral               | <https://docs.mistral.ai/admin/monitor-comply/zero-data-retention>                                | 12 octobre 2026 |
| Hypothèses HV                             | Phase 1, `01-cartographie-des-donnees.md`, section 5.1                                            | sans objet      |
| Intervalles et seuils                     | Phase 1, `04-verification-exactitude.md`, sections 4.4 et 6                                       | sans objet      |
