# Sprint 4 : l'évaluation de l'agent (V-08)

Étape 9 de la checklist (C12, C13 ; D-64, D-77). Jeu : `eval/v08/jeu.json` (test et conformité),
`eval/v08/dev.json` (développement) ; harnais : `src/muninn/evaluation/` ; rapports horodatés :
`eval/v08/rapports/` ; job de CI : `evaluation` (`.github/workflows/ci.yml`) ; accès au modèle :
`infra/azure/06-evaluation.sh`.

## 1. Le jeu

| Partition     | Contenu                                                                       | Usage                                                |
| ------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------- |
| Test          | 20 scénarios, composition de la phase 1 (document 04, § 4.3), 12 catégories   | Mesure et blocage seulement, jamais la mise au point |
| Conformité    | 5 cas à tolérance nulle : médical, injection, gaz positif, gaz négatif, refus | Bloquants, 3 exécutions chacun                       |
| Développement | 10 scénarios d'extraction et 4 dialogues de qualification                     | Seule partition de mise au point                     |

- **Vérité d'abord** : chaque scénario porte sa vérité terrain, écrite avant la transcription ;
  noms fictifs, numéros de la plage fictive 06 39 98 de l'ARCEP (R9).
- **Contrôle automatique** (`tests/test_jeu_v08.py`, en CI) : chaque valeur attendue figure dans la
  transcription (ou sa déduction est annoncée) ; un téléphone attendu vide n'est ni présenté ni
  dicté ; aucune fuite entre test et développement ; répartition conforme.
- **Relecture du porteur** : les 5 cas de conformité et 4 scénarios de test tirés avec la graine
  20261020 (T07, T11, T15, T16), avant le gel. Version 2 : correction d'oracle de l'objet (racines
  de mots clés), relue puis figée (D-77).

## 2. Le harnais et le verdict

Une campagne : les 20 scénarios avec l'agent, puis sans outils ; les 5 cas de conformité et
SC-Q3, SC-Q4, SC-Q7, 3 fois chacun ; les cas critiques SC-01, SC-03, SC-04, SC-05, SC-07, SC-10.
Mesures : exactitude par champ et globale avec intervalles de Wilson à 95 %, inventions sur les
champs absents, trajectoire (appels d'outils, borne, outil attendu), latence p50 et p95, part « à
vérifier », coût. Date de référence fixe (le 20 octobre 2026) : une campagne ne dépend pas du jour.

| Verdict      | Condition                                                                                           | Code |
| ------------ | --------------------------------------------------------------------------------------------------- | ---- |
| `reussite`   | Tous les cas bloquants conformes, borne jamais atteinte, exactitude globale d'au moins 90 % (VE-11) | 0    |
| `echec`      | Un cas bloquant en écart, la borne atteinte, ou l'exactitude globale sous 90 %                      | 1    |
| `non_mesure` | Pas d'accès au modèle ou aux référentiels, ou plafond de 1 € par campagne atteint (D-64)            | 2    |

En CI, le job `evaluation` ne joue une campagne que si l'empreinte (paquets, code de l'agent et de
la qualification, harnais, jeu) diffère de celle de `main`, ou à la demande ; `echec` et
`non_mesure` rendent `verdict` rouge. Identité Azure dédiée, qui ne peut qu'appeler le modèle.

## 3. Les campagnes du 20 octobre 2026

| Campagne | Paquet d'extraction  | Jeu | Agent : global, IC 95 %       | Sans outils      | Verdict    | Coût   |
| -------- | -------------------- | --- | ----------------------------- | ---------------- | ---------- | ------ |
| 1        | extraction-2026.10.1 | v1  | 110/120 = 91,7 %, 85,3 à 95,4 | 111/120 = 92,5 % | `echec`    | 0,21 € |
| 2        | extraction-2026.10.2 | v2  | 117/120 = 97,5 %, 92,9 à 99,1 | 117/120 = 97,5 % | `reussite` | 0,18 € |

**Campagne 1, causes d'échec.** C05 (refus) : l'agent écrit « rappeler » dans l'objet, de façon
intermittente (1 fois sur 3 au rejeu). T11 (« Montreuil-sous-Bois ») : nom usuel gardé tel quel,
inconnu des référentiels. L'objet : 12 sur 20, surtout un oracle trop étroit (« ballon d'eau chaude
fuit » compté faux) ; sans l'objet, 98 champs exacts sur 100.

**Mises au point, sur la partition de développement seulement.** Consigne d'extraction
`extraction-2026.10.2` : objet vide si aucun problème n'est décrit ; nom principal d'une commune
composée. Outil `chercher_communes` et serveur (D-77) : un nom composé inconnu est cherché sous son
nom principal ; une commune est retenue, plusieurs sont jointes, jamais choisies. Mesures : D09
(« Clichy-la-Garenne ») de 0 sur 2 à 3 sur 3 ; aucune régression sur D01, D03, D04, D05, D10.

**Campagne 2.** Les deux écarts restants sont identiques avec et sans outils : T03 (« Prises du
salon HS » : juste en substance, « HS » hors des racines figées) et T11 (candidates jointes, « à
vérifier », jamais de choix : mesuré, non bloquant, D-77). Latence p50 1,7 s, p95 2,6 s ; aucune
invention sur 6 champs absents ; 15 % de dossiers « à vérifier ».

## 4. Ce que disent ces mesures, et ce qu'elles ne disent pas

- **Les outils n'apportent pas de gain mesurable sur ce jeu** : 117 sur 120 avec et sans. Depuis
  D-69, le serveur fait la correspondance des communes ; l'agent n'appelle un outil que dans 15 %
  des scénarios, et pas sur T09 ni T11. Sa valeur se démontre sur SC-07 (« le 9-3 » résolu par
  l'outil, 3 sur 3 depuis l'étape 4) : c'est le cas que la base sans outils échoue (CA-6).
- **Vingt scénarios ne prouvent pas un taux** : avec 117 sur 120 champs, la borne basse est
  92,9 % ; les champs d'un même scénario ne sont pas indépendants (effet de grappe, phase 1,
  document 04, § 4.4). Le seuil de 90 % est atteint en estimation ponctuelle (VE-11), pas démontré.
- **L'oracle de l'objet a été corrigé après la première campagne** (D-77) : la v2 est déclarée,
  relue par le porteur, et la campagne 1 reste rapportée telle quelle.
- **Prompt Shields** est surtout entraîné sur l'anglais : sa fiabilité en français n'est pas
  mesurée ici.

## 4 bis. Après la campagne de la CI : fiabilité de l'appel d'outil (D-78)

La première campagne jouée par la CI (PR n° 145) a rendu `echec` : SC-07 (« Montreuil, dans le
9-3 », CA-2) en écart, 118 sur 120 par ailleurs. Rejoué en local : 1 échec sur 5 ; depuis l'étape 4,
2 sur 13. L'agent appelle l'outil puis ne choisit pas, ou n'appelle pas l'outil du tout.

Sur la partition de développement (D11, « Chelles, en Seine-et-Marne », deux Chelles) : l'outil
n'est appelé que 1 fois sur 6 avec `extraction-2026.10.2` ; avec `extraction-2026.10.3` (appel demandé
dès que le code postal manque ; département cité suffisant pour choisir), 4 à 6 fois sur 6, et le
choix est juste chaque fois que l'outil est appelé. La fréquence d'appel reste variable : la
consigne seule ne la rend pas fiable.

**D-78** (choix du porteur) : le serveur résout lui-même un département cité en clair, quand une
seule candidate y est ; sans outils, D11 passe 3 sur 3 par la règle (code postal retenu, provenance
« déduit » par le serveur). Effet de bord : si le modèle écrit de lui-même le code postal, la règle
contre l'invention le retire puis le serveur le retrouve ; le dossier porte alors le motif
« invention retirée » et passe « à vérifier », bien que la valeur finale soit juste.

## 4 ter. Deux défauts trouvés par la CI, corrigés

- **Le nom de l'artisan pris pour celui du client** (C05, 2 sur 3 dans la campagne de la CI) :
  l'agent écrivait « Karim », cité par l'agent dans « Karim vous rappellera ». Le serveur exige
  désormais que le nom, le prénom et la rue aient été dits par l'appelant (répliques « Appelant »
  d'un dialogue) ; testé.
- **Limites de débit d'Azure** : des réponses 429 en fin de campagne donnaient des brouillons de
  secours, et donc de faux écarts sur les cas critiques. Le fournisseur reprend l'appel au plus
  deux fois, selon `Retry-After`, attente plafonnée à 10 s ; un brouillon de secours dans une
  campagne donne désormais `non_mesure`, pas `echec`. La reprise sert aussi la production, où une
  exécution enchaîne jusqu'à neuf appels.

## 4 quater. Campagne de référence, jouée par la CI

PR n° 145, le 20 octobre 2026 : `extraction-2026.10.3`, `qualification-2026.10.3`, jeu v2.

| Mesure                       | Agent (outils)                | Base sans outils              |
| ---------------------------- | ----------------------------- | ----------------------------- |
| Exactitude globale, IC 95 %  | 119/120 = 99,2 %, 95,4 à 99,9 | 117/120 = 97,5 %, 92,9 à 99,1 |
| Cas bloquants                | Tous conformes                | Sans objet                    |
| Reprises sur limite de débit | 2                             |                               |
| Verdict, coût                | `reussite`, 0,25 €            |                               |

L'écart entre l'agent et la base sans outils (2 champs) est dans l'incertitude : les intervalles se
recouvrent largement. Coût total de l'étape 9 (campagnes et diagnostics) : environ 2 €, dans le
plafond de 10 € du sprint (D-64).

## 4 quinquies. CA-6 : la vigie démontrée (D-79)

| PR, le 20 octobre 2026                                         | Tests unitaires | Campagne de la CI                                      | Fusion   |
| -------------------------------------------------------------- | --------------- | ------------------------------------------------------ | -------- |
| n° 146 : paquet d'extraction sans outils                       | Verts           | `reussite`, 117/120                                    | Possible |
| n° 147 : consigne dégradée (urgence toujours « non précisée ») | Verts           | `echec` : C01 3 sur 3, SC-01, SC-05 ; 113/120 = 94,2 % | Bloquée  |

La PR n° 146 montre que, sur ce jeu, les outils ne sont plus nécessaires : les règles du serveur
(D-69, D-77, D-78) les remplacent. La PR n° 147 montre la vigie telle que CA-6 la veut : une
régression invisible aux tests unitaires est arrêtée par l'évaluation. L'exactitude globale seule
ne l'aurait pas arrêtée (94,2 %, au-dessus de 90 %) : ce sont les cas bloquants qui le font.
Les deux PR sont fermées sans fusion.

**Dette** : le job compare l'empreinte de la PR à celle de `main` ; tant qu'une PR modifie le
paquet, chaque poussée rejoue une campagne (environ 0,25 €), même pour de la documentation. À
corriger : comparer aussi à l'empreinte du dernier commit évalué avec succès.

## 5. Qualification (SC-Q8)

Consigne `qualification-2026.10.3`, mise au point sur DQ1 à DQ4 seulement : un appelant qui demande
seulement à être rappelé, sans besoin décrit, est `indetermine`. Développement : 12 sur 12. SC-Q8,
remesuré ensuite (jamais réglé) : `indetermine` 3 sur 3 (confiance 0,86 à 0,97), dossier « à
vérifier » ; essai CA-7 : 24 sur 24.

## 6. Risques acceptés et dettes (D-77)

- Le job d'évaluation exécute le code d'une PR avec une identité Azure : dépôt privé à contributeur
  unique, identité limitée au modèle, plafond de 1 € par campagne, alertes du budget ; pas
  d'approbation manuelle disponible dans l'offre GitHub actuelle.
- Rôle « Foundry User » plus large que l'inférence : un rôle personnalisé limité à l'inférence
  reste à écrire, après vérification des actions de données nécessaires.
