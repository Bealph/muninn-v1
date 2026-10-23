# Sprint 5 : l'écran « Qualité »

Étape 4 de la checklist. Public de cette note : l'évaluateur pair et l'exploitant. Public de
l'écran : un lecteur non développeur (jury, artisan), qui doit le comprendre sans explication
orale.

Code : `src/muninn/traitements/etat.py` (état du service), `src/muninn/traitements/metriques.py`
(chiffres), route `GET /v1/demo/quality` de `src/muninn/api/agent.py`, route `/qualite` de
`src/muninn/console/main.py` et gabarit `src/muninn/console/templates/qualite.html`.

## 1. Références

| Référence | Objet                                                         | Document                                                                 |
| --------- | ------------------------------------------------------------- | ------------------------------------------------------------------------ |
| V-10      | Vigie de la V1 : métriques tirées de la base, alerte affichée | `docs/v1/dossier-conception-v1.md`, tableau des exigences V1             |
| TB-6      | Page de démonstration de la console                           | `docs/conception/industrialisation/03-observabilite.md`, section 9       |
| D-83      | Trois alertes et leurs seuils (AL-01, AL-04, AL-16)           | `docs/decisions.md`                                                      |
| D-84      | Dérive simulée de la démonstration                            | `docs/decisions.md`                                                      |
| SLO-09    | Part « à vérifier » au plus 20 % par heure, 20 extractions    | `docs/conception/industrialisation/03-observabilite.md`, tableau des SLO |
| SLO-05    | Extraction : p50 au plus 6 s, p95 au plus 20 s                | `docs/conception/industrialisation/03-observabilite.md`, tableau des SLO |

## 2. Ce que montre l'écran

Le bandeau et le tableau des contrôles portent toujours sur la dernière heure. Les chiffres, le
graphique et les tableaux portent sur la période choisie : 1 heure, 24 heures, 7 jours ou
30 jours.

| Partie                  | Source                                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Bandeau d'état          | `evaluer()` sur les métriques de la dernière heure                                                                 |
| Contrôles               | Les trois règles de D-83 : ce qui est surveillé, seuil, valeur, verdict                                            |
| Chiffres de la période  | `app.traitements` : issues, `a_verifier`, `statut`, `duree_ms`, `cout_micro_eur`, statuts de contrôle de l'adresse |
| Graphique               | Série par heure de `app.traitements` ; une heure sans appel garde sa place                                         |
| Champs corrigés         | `app.corrections.champ`, affiché en français (« Code postal »)                                                     |
| Protections intervenues | `app.traitements.garde_fous`, affichées en français                                                                |
| Dernier appel           | `request_id`, scénario, issue et durée du traitement le plus récent                                                |
| Version du logiciel     | `/version` de l'API et de la console                                                                               |

L'écran ne montre aucun contenu d'appel : la route ne lit que des colonnes de codes, de nombres et
de noms de champs (`metriques.py`), et le test `test_dernier_appel_sans_contenu` fixe les cinq
seuls champs rendus pour le dernier appel. Le modèle simulé (scénario `P4-perimetre`) est exclu par
`NOT modele_simule` dans chaque requête : ses durées et coûts ne disent rien du service réel.

## 3. L'état du service

| Règle | Ce qui est surveillé                                               | Seuil        | Volume minimal      |
| ----- | ------------------------------------------------------------------ | ------------ | ------------------- |
| AL-01 | Part des dossiers « à vérifier »                                   | au plus 20 % | 20 dossiers         |
| AL-04 | Brouillons de secours (l'IA n'a pas répondu)                       | au plus 5 %  | 20 dossiers         |
| AL-16 | Temps de préparation du dossier par l'IA (extraction), 95e centile | au plus 20 s | 20 dossiers mesurés |

| Situation                                            | Bandeau                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| Au moins une règle au-dessus de son seuil            | Rouge, « Alerte », règles nommées, « Prévenir l'exploitant » |
| Aucune règle dépassée, toutes jugées                 | Vert, « Aucun seuil dépassé »                                |
| Aucune règle dépassée, certaines sans assez d'appels | Vert, « Aucun seuil dépassé », règles non jugées nommées     |
| Aucune règle n'a assez d'appels                      | Gris, « Pas assez d'appels pour juger »                      |

Chaque état a un mot et un symbole (●, ▲, ○) : la couleur n'est jamais seule porteuse du sens.

## 4. Choix et suite donnée par le porteur

Le 23 octobre 2026, le porteur a relu les six choix et retenu quatre améliorations ; il a laissé
l'orchestrateur ajouter ce qui manquait.

| Choix initial                                                     | Suite                                                                                                                                                               |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L'état se lit sur la dernière heure, quelle que soit la période   | Gardé ; le bandeau dit en plus jusqu'à quand l'état reste jugé sans nouvel appel, et l'heure du calcul                                                              |
| Volume minimal de 20, AL-16 compris                               | Gardé ; l'état gris dit combien de dossiers il y a et combien il en faut, chaque contrôle donne son volume                                                          |
| AL-16 mesurait le traitement entier                               | Remplacé : migration 0004 (colonne `duree_extraction_ms`), puis AL-16 sur l'extraction seule (SLO-05) ; un traitement antérieur, sans cette durée, n'est pas compté |
| « Erreurs du service » mêlait secours et nouveaux essais          | Remplacé : une carte « Brouillons de secours » (celle d'AL-04) et une carte « Nouveaux essais de l'IA »                                                             |
| Pas de lien vers Application Insights ; l'identifiant est affiché | Gardé ; le lien sera dans le classeur Azure Monitor                                                                                                                 |
| Actualisation désactivée par défaut                               | Remplacé : actualisation d'office si un appel a eu lieu il y a moins de 10 minutes (démonstration, rafale) ; décocher l'arrête                                      |

Ajouts de la seconde version :

| Ajout                                | Contenu                                                                                                                                              |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Historique des alertes sur 24 heures | Les trois règles rejouées toutes les 5 minutes sur l'heure qui précède, à partir de la base ; une ligne par épisode : début, fin, pire valeur        |
| Coût de l'IA sur le mois             | Total depuis le début du mois, projection au même rythme, part du budget Azure de 60 € (SLO-16), qui couvre aussi l'hébergement                      |
| Part « à vérifier » par heure        | Second graphique, avec le seuil de 20 % tracé ; la légende rappelle que l'alerte se calcule sur l'heure glissante                                    |
| Rafale de démonstration              | `eval/production/rafale.py --profil nominal` : 24 appels nominaux ; l'écran passe de « pas assez d'appels » à « aucun seuil dépassé » pour une heure |

La projection du coût se mesure depuis le premier traitement enregistré du mois, pas depuis le 1er :
le 23 octobre, avec des traitements enregistrés depuis le 22, la division par 23 jours donnait
0,21 € au lieu d'un rythme réel bien supérieur. Il faut une heure de mesure au moins.

L'historique est une reconstitution, pas un journal : un épisode plus court que 5 minutes peut lui
échapper, et une ligne purgée (30 jours) n'y figure plus. Les alertes notifiées par Azure Monitor
relèvent de l'étape 5.

## 5. Écarts à TB-6

| Élément de TB-6                     | État                                                                                            | Suite             |
| ----------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------- |
| AL-02c (durée du parcours de démo)  | Remplacée par AL-16, mesurée côté serveur                                                       | Assumé en V1      |
| Lien vers la trace du dernier appel | Identifiant affiché ; le lien sera dans le classeur Azure Monitor                               | Étape 4, classeur |
| Filtre `is_synthetic = true`        | Non disponible : tout le trafic de la V1 est de démonstration ; seul le modèle simulé est exclu | Reprendre en V2   |

## 6. Vérification

Commande : `make tests-conteneur ARGS="tests/test_etat.py tests/test_metriques_base.py
tests/test_console_qualite.py tests/test_accessibilite.py"` (Docker requis).

| Test                            | Ce qu'il vérifie                                                                               |
| ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `tests/test_etat.py`            | Les trois règles, seuils exacts (20 % pile : sous le seuil), volumes minimaux, cas mixte       |
| `tests/test_metriques_base.py`  | Chiffres calculés sur une base PostgreSQL réelle, « non contrôlé », dernier appel, état rendu  |
| `tests/test_console_qualite.py` | Écran rendu dans chaque état avec une API simulée, période, actualisation, graphique, pluriels |
| `tests/test_accessibilite.py`   | axe-core, WCAG 2.2 AA, dans les quatre états de l'écran                                        |

Résultat du 23 octobre 2026 (première version) : 38 tests passés, aucun échec. Seconde version :
`tests/test_etat_base.py` ajouté (échéance du jugement, historique retrouvant une alerte passée,
coût du mois, sur une base réelle) ; suite complète, 503 tests passés.

En production (révision `9aa617b`), l'écran a été lu après un appel SC-01 : capture
`preuves/etape-4-ecran-qualite-production.png`. Ce jour-là, la part « non contrôlé » (22 %) venait
des deux appels SC-10 : commune ambiguë, que le serveur refuse de trancher (D-69). Le libellé de
la carte a été précisé en conséquence.

L'absence de débordement sur un écran de 390 px a été mesurée une fois à la main (largeur de la
page égale à celle de l'écran), sans test automatique.

## 7. Relecture par un non-développeur

Deux relectures, le 23 octobre 2026 :

1. L'agent `relecteur-technique-fr`, sur le gabarit et les libellés : codes d'alerte remplacés par
   leur sens, jargon des protections traduit, action à suivre dite en clair.
2. **Relecture simulée**, à la demande du porteur, qui a jugé sans importance l'identité du lecteur
   pourvu qu'il ne soit pas développeur : un agent a joué un artisan plombier sans connaissance
   informatique, devant la seule capture de l'écran de production (révision `f4681c5`), sans le
   code ni la documentation. Ce n'est pas une personne réelle.

Ce que le lecteur a compris seul : « Aucune alerte sur les dernières 24 heures », les champs
corrigés, le coût de l'IA, les appels écartés. Ce qui l'a gêné, et ce qui a été corrigé :

| Constat du lecteur                                                                       | Correction                                                                                                                 |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| « Pas assez d'appels pour juger » : aucun verdict, rien sur quoi faire                   | Sans alerte sur 24 heures : « Aucun problème détecté depuis 24 heures… Rien à faire »                                      |
| « 100 % » à côté de « au plus 20 % », sur un seul dossier : alarme                       | Sous 20 dossiers, les nombres seuls (« 1 sur 1 dossier »), sans pourcentage                                                |
| Des barres au-dessus de la ligne rouge, et pourtant « aucune alerte »                    | Les heures de moins de 20 dossiers sont grisées et la légende le dit                                                       |
| Heures en « UTC » : est-ce l'heure de chez moi ?                                         | Heure de Paris partout, dite comme telle                                                                                   |
| Codes AL-xx, identifiant, version, « exploitant » mêlés au reste                         | Repliés dans « Détails pour le support technique » ; le bandeau dit « la personne qui gère Muninn »                        |
| Deux temps (3,3 s et 1,7 s) sous des libellés presque identiques                         | « Temps pour préparer un dossier » (fin de l'appel au dossier prêt) et « Temps de travail de l'IA »                        |
| « heure glissante », « inexploitable », « injoignable », « budget Azure », « 0 message » | « 60 dernières minutes », « inutilisable », « momentanément indisponible », « budget mensuel du projet », message expliqué |
| « Information que l'appelant n'a pas donnée » : l'IA invente-t-elle ?                    | « Information non dite par le client, retirée avant l'envoi du dossier »                                                   |
| « appels de démonstration » : sont-ce mes vrais clients ?                                | « des appels de démonstration joués par l'équipe, pas de vrais clients »                                                   |
| « 1 dossiers mesurés »                                                                   | Accord au singulier                                                                                                        |

Restent ouverts : un numéro à appeler en cas d'alerte (pas de contact défini pour la V1) et la
question « qui paie les 60 € » (le budget est celui du projet de certification).
