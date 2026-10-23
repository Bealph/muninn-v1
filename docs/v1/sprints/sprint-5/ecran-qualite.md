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

| Règle | Ce qui est surveillé                           | Seuil        | Volume minimal |
| ----- | ---------------------------------------------- | ------------ | -------------- |
| AL-01 | Part des dossiers « à vérifier »               | au plus 20 % | 20 dossiers    |
| AL-04 | Brouillons de secours (l'IA n'a pas répondu)   | au plus 5 %  | 20 dossiers    |
| AL-16 | Temps de préparation d'un dossier, 95e centile | au plus 20 s | 20 traitements |

| Situation                                            | Bandeau                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| Au moins une règle au-dessus de son seuil            | Rouge, « Alerte », règles nommées, « Prévenir l'exploitant » |
| Aucune règle dépassée, toutes jugées                 | Vert, « Aucun seuil dépassé »                                |
| Aucune règle dépassée, certaines sans assez d'appels | Vert, « Aucun seuil dépassé », règles non jugées nommées     |
| Aucune règle n'a assez d'appels                      | Gris, « Pas assez d'appels pour juger »                      |

Chaque état a un mot et un symbole (●, ▲, ○) : la couleur n'est jamais seule porteuse du sens.

## 4. Choix faits pendant l'étape

| Choix                                                                                  | Raison                                                                                                                                                                    | Décision attendue du porteur |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| L'état se lit sur la dernière heure, quelle que soit la période                        | Fenêtre des alertes de D-83 ; sur 30 jours, une panne de l'heure en cours serait noyée                                                                                    | Valider ou défaire           |
| Volume minimal de 20 pour AL-16 aussi                                                  | D-83 le fixe pour AL-01 et AL-04 ; un 95e centile sur trois appels n'a pas de sens                                                                                        | Valider ou défaire           |
| AL-16 mesure le traitement entier (`app.traitements.duree_ms`), qualification comprise | Seule durée enregistrée ; plus longue que l'extraction de SLO-05, elle déclenche plus tôt, jamais plus tard                                                               | Valider ou défaire           |
| « Erreurs du service » compte secours et nouveaux essais ; AL-04, les secours seuls    | Le chiffre décrit tout ce qui a mal tourné ; l'alerte suit la définition de D-83                                                                                          | Valider ou défaire           |
| Pas de lien vers Application Insights ; l'identifiant est affiché                      | La console est publique : le lien mettrait l'identifiant de l'abonnement Azure dans la page, sans rien ouvrir pour un visiteur non connecté ; le classeur portera ce lien | Valider ou défaire           |
| Actualisation automatique désactivée par défaut                                        | Une page qui se recharge pendant la lecture gêne ; on l'active pour la dérive simulée (D-84)                                                                              | Valider ou défaire           |

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

Résultat du 23 octobre 2026 : 38 tests passés, aucun échec. En production (révision `9aa617b`),
l'écran a été lu après un appel SC-01 : capture `preuves/etape-4-ecran-qualite-production.png`.
Ce jour-là, la part « non contrôlé » (22 %) venait des deux appels SC-10 : commune ambiguë, que le
serveur refuse de trancher (D-69). Le libellé de la carte a été précisé en conséquence. L'absence de débordement sur un écran
de 390 px a été mesurée une fois à la main (largeur de la page égale à celle de l'écran), sans test
automatique.

Relecture par un non-développeur : à faire (dernière case de l'étape 4). Une première relecture par
l'agent `relecteur-technique-fr` a fait reformuler l'écran : codes d'alerte remplacés par leur
sens, jargon des protections traduit, action à suivre dite en clair.
