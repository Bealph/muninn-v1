# Sprint 5 : instrumenter

Étape 3 de la checklist (V-10, D-40, D-87). Code : `src/muninn/traitements/metriques.py`,
`src/muninn/telemetrie.py`, routes de `src/muninn/api/agent.py` ; tests :
`tests/test_metriques_base.py`, `tests/test_telemetrie.py` ; mise en production :
`infra/azure/09-observabilite.sh`.

## 1. Trois sorties, une même mesure

| Sortie                            | Pour qui                                 | Source                              |
| --------------------------------- | ---------------------------------------- | ----------------------------------- |
| Métriques `GET /v1/demo/quality`  | Écran « Qualité », alerte AL-01 et AL-16 | PostgreSQL, schéma `app` (TB-6)     |
| Étapes `steps` de `/v1/demo/runs` | Écran « Démonstration » (suivi animé)    | Mesure en mémoire de l'appel        |
| Traces vers Application Insights  | Exploitant, diagnostic d'une panne       | OpenTelemetry, export direct (D-87) |

L'écran et les alertes de l'application lisent PostgreSQL et non Application Insights : les
journaux et les traces mettent plusieurs minutes à arriver dans Azure, trop pour une démonstration.

## 2. Les métriques

Fenêtres de 1 h, 24 h, 7 jours et 30 jours ; traitements du modèle simulé exclus ; résultat gardé
15 s, pour qu'un rafraîchissement répété ne charge pas la base.

| Signal              | Définition                                                       |
| ------------------- | ---------------------------------------------------------------- |
| Volume              | Traitements, dont dossiers, messages, traces sans contenu, refus |
| Taux de refus       | Refus sur traitements                                            |
| Taux d'erreur       | Brouillons de secours et relances, sur dossiers                  |
| Latence             | Médiane et 95e centile des durées, refus exclus                  |
| Coût                | Moyen par traitement et total, qualification et extraction       |
| Part « à vérifier » | Dossiers « à vérifier » sur dossiers (AL-01)                     |
| Garde-fous, borne   | Nombre de déclenchements par garde-fou ; borne d'outils atteinte |
| Corrections         | Par champ ; dossiers validés                                     |
| Série par heure     | Volume, dossiers, « à vérifier », refus, secours, 95e centile    |

## 3. Les traces et les étapes

`etape(nom, **attributs)` mesure une étape : elle l'ajoute à la liste de l'appel en cours et, si
la chaîne de connexion est présente, émet une trace. Étapes : `appel` (racine), `controle_entree`,
`qualification`, `message`, `agent`, `outil` (une par appel d'outil), `controles_serveur`.

Aucun contenu : les attributs passent par une liste blanche (catégorie, statut, outil, garde-fous,
jetons, coût…) et un texte n'est gardé que si c'est un code court sans espace. Un test capte les
traces dans un exportateur en mémoire et le vérifie. Le fournisseur de traces est propre au module :
Langfuse garde le sien.

Les deux environnements partagent le composant `appi-muninn`. Le champ `cloud_RoleName` les
distingue : `preproduction.muninn-api` ou `production.muninn-api`. Application Insights forme ce
champ à partir de `service.namespace` et de `service.name`, et ignore
`deployment.environment.name` : l'environnement est donc porté par `service.namespace`. Toutes
les étapes d'un appel s'affichent dans Application Insights comme des dépendances
(`dependencies`) d'une même opération (`operation_Id`).

Vérifié le 23 octobre 2026 sur l'appel de contrôle de la préproduction : 5 étapes, toutes rattachées
à la même opération. Les attributs se limitent à des codes et à des nombres.

`telemetrie.py` entre dans l'empreinte de l'évaluation : le module est importé par l'agent, une
modification relance donc V-08 en CI (test de garde existant).

## 4. Tests sur le poste

Depuis le 23 octobre 2026, la stratégie de contrôle d'application du poste bloque les extensions
compilées non signées (SQLAlchemy, psycopg, DuckDB). La suite tourne dans un conteneur Linux, comme
en CI : `make tests-conteneur` (452 tests, base comprise, aucun ignoré).
