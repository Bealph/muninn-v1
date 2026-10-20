# Sprint 4 : la qualification des appels

Étape 6 de la checklist (V-11, D-48 ; D-71, D-72). Code : `src/muninn/qualification/` ; tests :
`tests/test_qualification.py` ; dialogues : `eval/qualification/scenarios.json` ; essai réel :
`eval/qualification/essai_etape6.py`. Conception : `docs/conception/appels-et-voix/01-qualification-des-appels.md`.

## 1. Ordre des opérations

1. **Garde-fous d'entrée** (étape 5). Une entrée sans contenu donne une trace sans contenu (numéro,
   heure, motif), sans appel au modèle (Q-09). Dans un dialogue, seules les paroles de l'appelant
   comptent : l'annonce de l'agent n'est pas un contenu.
2. **Classification par le LLM** : une seule étape, schéma fermé de 7 champs, sans outil. Ce n'est
   pas un agent. Paquet versionné `qualification-2026.10.1`, dans l'empreinte d'évaluation.
3. **Règles du serveur** (asymétrie des erreurs, §4.2). La catégorie devient `indetermine` si :

   - le modèle est indisponible, ou sa sortie est hors schéma ;
   - la confiance déclarée est sous 0,7 ;
   - `personnel` ou `autre`, avec une expression de la liste `besoin-2026.10.1` ;
   - `personnel` ou `autre`, avec un motif d'injection connu (étape 5).

   `fournisseur` n'est jamais rétrogradé. La règle « gaz » vaut dans toutes les catégories (Q-07).

4. **Issue.** `demande_service` et `indetermine` : dossier par l'agent d'extraction ; `indetermine`
   ajoute le motif `qualification_indeterminee` (« à vérifier »). `fournisseur`, `personnel` et
   `autre` : un `MessageRecu`, sans autre extraction (Q-08).

**Le message ne garde que ce qui a été dit** : un nom ou une société absents de la transcription
sont retirés ; le numéro de rappel est le numéro présenté, un numéro dicté différent est noté à
part ; un message qui contient un terme de santé de la liste fermée est remplacé par un texte fixe
(R7). Le `DossierDraft` 1.1 n'est pas modifié. Le journal porte catégories, confiance, règle,
coût et durée, jamais un contenu (testé).

## 2. Garde-fou de complaisance

La liste des 37 expressions de besoin a été figée et poussée (commit `a2c35f7`) avant l'écriture
des dialogues. Les dialogues ont été relus par le porteur, SC-Q3 réécrit selon D-71, puis figés
(commit `f08d697`) avant la première exécution. Ni la liste, ni la consigne, ni le seuil n'ont été
modifiés après l'essai.

## 3. Essai avec le vrai modèle

**Le 20 octobre 2026**, gpt-5.4-mini, référentiels de production, 8 scénarios, 3 exécutions
chacun ; 0,068 € ; aucun refus du filtre. Ce n'est pas la vérification sur Azure (étape 11).

| Scénario | Catégorie du modèle (3 sur 3)  | Issue             | CA-7    | Conception (§7)                                     |
| -------- | ------------------------------ | ----------------- | ------- | --------------------------------------------------- |
| SC-Q1    | `fournisseur`                  | Message           | 3 sur 3 | Conforme                                            |
| SC-Q2    | `personnel`                    | Message           | 3 sur 3 | Conforme                                            |
| SC-Q3    | `demande_service`              | Dossier           | 3 sur 3 | Conforme                                            |
| SC-Q4    | `demande_service`              | Dossier           | 3 sur 3 | Conforme : la consigne de l'appelant est sans effet |
| SC-Q5    | `autre`                        | Message           | 3 sur 3 | Conforme                                            |
| SC-Q6    | `fournisseur`                  | Message           | 3 sur 3 | Conforme                                            |
| SC-Q7    | `demande_service`              | Dossier, sécurité | 3 sur 3 | Conforme                                            |
| SC-Q8    | `demande_service`, 0,74 à 0,86 | Dossier           | 3 sur 3 | **Écart** : dossier non « à vérifier »              |

**CA-7 est satisfait, 24 sur 24** : son texte demande pour SC-Q8 un dossier, jamais un message.
**La conception (Q-05) ne l'est pas, 0 sur 3** : elle attend `indetermine`, donc un dossier « à
vérifier ». Le modèle déclare une confiance de 0,74 à 0,86 sur un appel sans objet ; l'agent
d'extraction note ensuite l'objet « rappeler », avec une confiance de 0,9, et aucune règle ne
signale le dossier. La confiance déclarée n'est pas calibrée, comme la conception le disait.

Les règles de rétrogradation ne se sont jamais déclenchées : le modèle a classé correctement les
sept autres scénarios. Elles restent testées sans réseau.

## 4. Limites connues

- **Liste des besoins** : « mon chauffe-eau fuit » n'est pas couvert (« ça fuit » et « qui fuit »
  le sont) ; dans SC-Q4, seul le récapitulatif de l'agent contient « qui fuit ». La recherche porte
  sur toute la transcription, répliques de l'agent comprises (conforme au §4.2).
- **Liste « santé »** : « cardiologue » n'y figure pas (liste fermée de l'annexe A, non modifiée).
- **Huit scénarios ne prouvent pas un taux** (§7) : ils protègent les cas critiques.

## 5. Décision sur SC-Q8

**Choix du porteur, le 20 octobre 2026** : l'écart est documenté tel quel, sans règle ajoutée ni
réglage. La consigne ou le seuil seront revus à l'étape 9, sur la partition de développement,
distincte des scénarios de test : ajuster sur ces huit scénarios serait de la complaisance.
Conséquence en attendant : un appel ambigu donne un dossier sans alerte ; il n'est jamais perdu
dans un message.

## 6. Après l'étape 7 : SC-Q8 change sans réglage ciblé

L'étape 7 a ajouté une ligne à la consigne de qualification (le jeton témoin), donc une nouvelle
version, `qualification-2026.10.2`. Rejoué le 20 octobre 2026, 3 exécutions : 24 sur 24 ; SC-Q8
est désormais classé `indetermine` par le modèle lui-même (confiance 0,33 à 0,48), donc dossier
« à vérifier », 3 sur 3. Aucun réglage ne visait SC-Q8 ; la sensibilité de la classification à une
ligne sans rapport est elle-même un résultat : la conformité de SC-Q8 n'est pas acquise. Le point
de l'étape 9 (partition de développement) est maintenu.

## 7. Après l'étape 9

La consigne `qualification-2026.10.3`, mise au point sur les dialogues de développement DQ1 à DQ4
seulement, classe `indetermine` un appel qui ne demande qu'un rappel sans besoin décrit. SC-Q8,
remesuré sans réglage : `indetermine` 3 sur 3 ; CA-7 : 24 sur 24 (`evaluation.md`, § 5).
