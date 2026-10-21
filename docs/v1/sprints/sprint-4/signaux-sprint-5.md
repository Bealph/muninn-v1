# Sprint 4 : les signaux à surveiller au sprint 5

Étape 13 de la checklist. Ce que le sprint 5 doit surveiller sur la composante agentique, avec la
source du signal, le seuil, l'alerte qui le porte et la valeur de référence mesurée pendant ce
sprint. Seuils et alertes : phase 2, `docs/conception/industrialisation/03-observabilite.md`
(SLO-xx, AL-xx) ; un seuil marqué [H] est une hypothèse de ce document, à confirmer.
Principe OB-1 : aucun signal ne porte de contenu (ni transcription, ni valeur du dossier).

## 1. Fenêtre de référence

| Élément     | Valeur                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------- |
| Source      | Log Analytics, `ContainerAppConsoleLogs_CL`, application `ca-muninn-api-prod`                  |
| Période     | 21 octobre 2026, 09:02 à 10:34 UTC (l'agent ne sert en production que depuis ce jour-là)       |
| Volume      | 118 qualifications, 102 extractions, 297 appels au modèle                                      |
| Révisions   | `0000065` et `0000066` (même code), avant la règle « urgence dite » (D-80)                     |
| Biais connu | Trafic de vérification seulement : campagnes de l'étape 11 et 12, prompts hostiles, ambiguïtés |

Le trafic n'est pas représentatif d'un usage réel : il est fait de scénarios choisis pour éprouver
l'agent. Les valeurs ci-dessous sont des repères, pas des taux de production.

## 2. Signaux

| Signal                                 | Source aujourd'hui                                                         | Seuil                                                        | Alerte                              | Référence (21 octobre 2026)                                           |
| -------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------- | --------------------------------------------------------------------- |
| Latence de l'extraction                | `extraction.fin duree_ms`                                                  | p50 ≤ 6 s, p95 ≤ 20 s (SLO-05)                               | AL-16                               | p50 2,7 s ; p95 3,4 s (102)                                           |
| Latence de la qualification            | `qualification.fin duree_ms`                                               | non fixé ; p95 ≤ 5 s [H]                                     | non disponible                      | p50 0,9 s ; p95 2,7 s (118)                                           |
| Latence du parcours de démonstration   | durée côté client de `POST /v1/demo/runs` (scripts de production)          | p50 ≤ 10 s, p95 ≤ 30 s (SLO-04)                              | AL-02c                              | SC-01 : 2,7 à 12,1 s (12 mesures)                                     |
| Coût d'une extraction                  | `extraction.fin cout_micro_eur`                                            | ≤ 0,01 € (SLO-13)                                            | AL-15                               | moyenne 0,0037 € ; p95 0,0044 €                                       |
| Coût d'une qualification               | `qualification.fin cout_micro_eur`                                         | inclus dans le coût d'un appel                               | AL-15                               | moyenne 0,0008 €                                                      |
| Budget                                 | budget Azure du groupe ; plafonds de l'évaluation (D-64)                   | ≤ 60 € par mois (SLO-16) ; 1 € par campagne, 10 € par sprint | budget Azure ; verdict `non_mesure` | campagne V-08 : 0,18 €                                                |
| Refus du filtre de contenu             | `extraction.refus code=content_refused` ; `qualification.fin regle=filtre` | ≤ 5 % sur 1 h, 20 appels [H]                                 | non disponible                      | 0 sur 102 ; 0 sur 118                                                 |
| Refus des règles d'entrée              | `extraction.refus code=…` ; HTTP 422                                       | suivi, pas d'alerte                                          | non disponible                      | 3 (entrées vides tirées exprès à l'étape 12)                          |
| Détournements signalés                 | `entree.controle motifs=INJ-…` ; `extraction.fin garde_fous=detournement`  | suivi ; hausse brutale [H]                                   | AL-14 (motif)                       | 54 lignes `INJ-…` sur 61 contrôles ; 27 dossiers neutralisés          |
| Messages au lieu d'un dossier          | `qualification.fin issue=message`                                          | suivi                                                        | non disponible                      | 12 sur 118 (scénarios SC-Q)                                           |
| Erreurs du fournisseur                 | `agent.fin statut` ; `extraction.fin statut=fallback_no_llm`               | ≤ 5 % sur 1 h, 20 extractions                                | AL-04 ; AL-24                       | 0 brouillon de secours sur 102                                        |
| Relance de validation                  | `agent.fin tentatives` ; `statut=partial_after_retry`                      | ≤ 2 % sur 24 h, 50                                           | AL-09                               | 0 relance sur 102                                                     |
| Borne d'outils atteinte                | `agent.fin borne=True`                                                     | 0 (bloquant en CI, V-08)                                     | verdict de la CI                    | 0 sur 102                                                             |
| Référentiels indisponibles             | `extraction.fin commune=not_checked` ; `agent.outil statut`                | « non contrôlé » ≤ 1 % (SLO-10)                              | AL-10                               | non disponible : la raison du « non contrôlé » n'est pas extraite ici |
| Part « à vérifier »                    | `extraction.fin a_verifier`                                                | ≤ 20 % par heure, 20 extractions (SLO-09)                    | AL-01                               | 44 sur 102 (43 %) : biaisé, voir ci-dessous                           |
| Erreurs HTTP de l'API de démonstration | journal d'accès, `POST /v1/demo/runs`                                      | 5xx ≤ 0,5 % sur 1 h, 100 requêtes                            | AL-05                               | 118 réponses 200, aucune 5xx                                          |
| Urgence relevée par le serveur (D-80)  | `extraction.fin urgence_serveur`                                           | suivi                                                        | non disponible                      | non disponible : signal ajouté par D-80                               |

**La part « à vérifier » de 43 % ne dit rien du produit.** Les campagnes du 21 octobre jouent
exprès des cas qui doivent finir « à vérifier » : homonymes sans indice (SC-10), incohérence
(SC-03), prompts hostiles neutralisés. Sur ce trafic, AL-01 serait en alerte, à juste titre au
sens du calcul et à tort au sens du produit. Le seuil de 20 % se lit sur un trafic nominal ; la
référence valable sera prise sur le jeu de démonstration du sprint 5, rejoué à blanc.

## 3. Ce que le sprint 5 doit en faire

V-10 (dossier V1) : métriques tirées de la base, écran Qualité, alerte calculée et affichée par
l'application ; puis, pour la V1.0 complète (D-40, D-52), traces OpenTelemetry vers Application
Insights et une alerte Azure Monitor. Proposition, à valider au cadrage du sprint 5 :

1. **AL-01, calculée par l'application** : part « à vérifier » par heure, 20 extractions au moins,
   affichée dans l'écran Qualité. C'est l'alerte que le dossier V1 promet.
2. **AL-16 et AL-15 en lecture** dans l'écran Qualité : latence p50 et p95, coût moyen.
3. **Une alerte Azure Monitor** sur Log Analytics : AL-04 (brouillons de secours et erreurs du
   fournisseur), la plus utile en démonstration parce qu'elle se provoque par une panne volontaire.
4. Les signaux sans source extraite (« non contrôlé » par raison, urgence relevée) passent dans
   les métriques tirées de la base, quand le dossier y sera enregistré (CA-5).

## 4. Reprises pour le sprint 5

| Sujet                                 | Origine                                       | Ce qu'il faut livrer                                                                                                                                                                                                                                                   |
| ------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dossier enregistré, corrigé et validé | CA-5 ; V-09 ; question du porteur, 21 octobre | Stockage du dossier, état « brouillon » puis « validé » ; table des corrections (champ, jamais la valeur) ; route de correction et de validation qui rejoue le contrôle du serveur ; correction et « Valider » dans l'écran ; SC-03 de bout en bout, 3 sur 3 sur Azure |
| Vigie, partie 2                       | CA-6, D-79                                    | Version dégradée déployée, retour arrière, SC-01 conforme à CA-1 en moins de 5 minutes                                                                                                                                                                                 |
| Voix                                  | CA-8, D-74 ; demande du porteur, 20 octobre   | Appel joué comme un vrai appel (sonnerie, attente de 15 s, annonce, dialogue) ; 45 s comptées depuis la fin de l'appel joué                                                                                                                                            |
| Suivi animé du déroulé                | Demande du porteur, 20 octobre                | Déroulé étape par étape, rejoué depuis la liste chronologique rendue par l'API, mention « rejoué », sans animation si refusée                                                                                                                                          |
| Contrôles du texte des critères       | Dette décidée le 21 octobre                   | Reporter dans `muninn.demo.verification` les contrôles que seul le script de production fait                                                                                                                                                                           |
| Rôle Foundry plus restreint           | Dette, D-77                                   | Rôle limité à l'inférence pour l'identité de l'application                                                                                                                                                                                                             |
