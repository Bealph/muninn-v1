# Feuille de route V1

**Version :** 1.1
**Date :** 13 octobre 2026 (incréments de la V1, D-41)
**Objet :** le chemin du sprint 1 jusqu'à l'oral du 12 novembre, taillé sur la V1 (six jours de
développement) et sur la couverture des 21 compétences (`couverture-competences.md`).

À sa validation, elle remplace le calendrier de `docs/roadmap.md` (v2.2) pour la période du 12
octobre au 13 novembre ; celui-ci reste comme historique (décision proposée D-36).

**Après le 13 novembre**, cette feuille de route s'arrête : le projet reprend la feuille de route
du produit (`docs/roadmap.md`) et la conception des phases 0 à 2, sans les découpes de la V1
(D-42).

## 1. Jalons et portes

Une porte est un contrôle qui conditionne la suite : tant qu'elle n'est pas franchie, l'étape
suivante ne démarre pas.

| Porte | Date                    | Condition pour la franchir                                                                          | Qui décide         |
| ----- | ----------------------- | --------------------------------------------------------------------------------------------------- | ------------------ |
| P0    | mar. 13 octobre         | Dossier de conception V1 validé par le porteur, puis par le formateur ; aucune ligne de code avant  | Formateur, porteur |
| P1    | mer. 14 octobre au soir | Sprint 2 tenu en une journée ; sinon, périmètre revu par décision écrite avant le sprint 3 (étalon) | Porteur            |
| P2    | ven. 16 octobre         | Modèle LLM choisi et clés fournies (D-32, D-33) ; sinon, critères marqués « non probants »          | Porteur            |
| P3    | lun. 19 octobre au soir | V1 terminée : CA-1 à CA-6 vérifiés sur Azure, 3 exécutions sur 3                                    | Porteur            |
| P4    | mer. 21 octobre au soir | V1.0 complète et déployée : déploiement automatisé (C13), outillage de monitoring (C11)             | Porteur            |
| P5    | mer. 28 octobre, 18 h   | Gel : E1 et E3 rédigés en Word, démo répétée trois fois, plan B prêt                                | Porteur            |
| P6    | mer. 11 novembre, 18 h  | Gel : E1 à E5 rédigés, retours du premier oral intégrés, répétition des 90 minutes faite            | Porteur            |

## 2. Calendrier

| Période                              | Étape                                                | Contenu                                                                                                                                                                          | Compétences prouvées ou renforcées | Livrables  |
| ------------------------------------ | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ---------- |
| lun. 12 et mar. 13 octobre           | Sprint 1 : cadrer, choisir, concevoir                | Dossier de conception V1, couverture des compétences, feuille de route ; validation (P0)                                                                                         | C14, C15, C16                      | E4         |
| mer. 14 octobre                      | Sprint 2 : le socle et la chaîne                     | V-01 à V-03 : socle, ressources Azure, CI `verdict`, déploiement par script, retour arrière                                                                                      | C15, C17, C18                      | E4         |
| jeu. 15 et ven. 16 octobre           | Sprint 3 : les données et l'ancrage                  | V-04 à V-06 : collecte des cinq types de sources, nettoyage, base, API des référentiels, Sirene. En parallèle, comparaison des modèles LLM (T-06), puis P2                       | C1 à C5, C7 (en partie)            | E1, E2     |
| ven. 16 au lun. 19 octobre           | Sprint 4 : la composante agentique et les garde-fous | V-07, V-08 : agent outillé, politique, garde-fous, évaluation bloquante                                                                                                          | C8, C9, C12                        | E2, E3     |
| lun. 19 octobre                      | Sprint 5 : la vigie et la démo                       | V-09, V-10 : console, écran Qualité, alerte ; P3                                                                                                                                 | C10, C11, C17                      | E3, E4     |
| mar. 20 octobre                      | V1.0 complète, partie 1                              | Déploiement automatisé par la CI (OIDC) sur fusion dans `main`                                                                                                                   | C13, C19                           | E3, E4     |
| mer. 21 octobre                      | V1.0 complète, partie 2                              | OpenTelemetry vers Application Insights, alerte Azure Monitor ; P4                                                                                                               | C11, C20                           | E3, E5     |
| jeu. 22 au sam. 24 octobre           | Réserve                                              | Rattrapage d'un glissement, puis « si temps » dans l'ordre du dossier V1 (contrôle du numéro, 30 cas de conformité, lac de données, audio simulé, écran Marché)                  | selon l'élément                    | E1, E3     |
| dim. 25 au mer. 28 octobre           | Rédaction et répétitions du premier oral             | E1 (2 à 5 pages, avec le contexte du projet) et E3 (15 à 20 pages) en Word, captures, script de démo ; répétitions le 26, le 27 et le 28 ; plan B (local) et plan C (vidéo) ; P5 | sans objet                         | E1, E3     |
| jeu. 29 et ven. 30 octobre           | **Premier oral blanc**                               | E1 (15 min), E3 (20 min, démo comprise), retours (10 min)                                                                                                                        | C1 à C5, C9 à C13                  | E1, E3     |
| sam. 31 octobre et dim. 1er novembre | Veille et benchmark                                  | Dispositif de veille, synthèses, recommandations ; benchmark complet des services d'IA (transcription, synthèse vocale, téléphonie, LLM)                                         | C6, C7                             | E2         |
| lun. 2 et mar. 3 novembre            | V1.1                                                 | Révision de préproduction (environnement de test) ; ouverture automatique d'une fiche d'incident ; incident provoqué, résolu et documenté ; audit RGAA manuel                    | C10, C19, C20, C21                 | E4, E5     |
| mer. 4 au sam. 7 novembre            | Rédaction du second oral                             | E2 (15 à 20 pages), E4 (15 à 20 pages), E5 (2 à 5 pages) en Word ; E1 et E3 mis à jour avec les retours du jury                                                                  | sans objet                         | E1 à E5    |
| dim. 8 novembre                      | Marge                                                | Absorbe un retard de rédaction                                                                                                                                                   | sans objet                         | sans objet |
| lun. 9 au mer. 11 novembre           | Relecture et répétitions                             | Relecture des cinq livrables ; répétition des 90 minutes, au moins deux fois ; P6                                                                                                | sans objet                         | E1 à E5    |
| jeu. 12 et ven. 13 novembre          | **Oral blanc en situation réelle**                   | E1 à E5, 90 minutes                                                                                                                                                              | C1 à C21                           | E1 à E5    |

**Tout au long des sprints**, deux traces s'accumulent sans charge propre :

- une fiche par incident réel (cause, correctif, PR, test de non-régression), pour C21 ;
- le tableau GitHub Projects, les PR revues et un compte rendu court à la fin de chaque sprint,
  pour C16.

## 3. Vue d'ensemble

```mermaid
gantt
  title Muninn, du sprint 1 à l'oral du 12 novembre
  dateFormat YYYY-MM-DD
  axisFormat %d/%m
  section V1
  Sprint 1, cadrer et concevoir             :s1, 2026-10-12, 2d
  Sprint 2, socle et chaîne                 :s2, 2026-10-14, 1d
  Sprint 3, données et ancrage              :s3, 2026-10-15, 2d
  Sprint 4, agent et garde-fous             :s4, 2026-10-16, 4d
  Sprint 5, vigie et démo                   :s5, 2026-10-19, 1d
  section Premier oral
  V1.0 complète, C13 et C11       :c1, 2026-10-20, 2d
  Réserve et si temps                       :r1, 2026-10-22, 3d
  Rédaction E1 et E3, répétitions           :w1, 2026-10-25, 4d
  Oral blanc E1 et E3                       :milestone, o1, 2026-10-29, 0d
  section Second oral
  Veille et benchmark C6 et C7              :v2, 2026-10-31, 2d
  V1.1, C19, C20, C21, audit          :c2, 2026-11-02, 2d
  Rédaction E2, E4, E5                      :w2, 2026-11-04, 4d
  Marge                                     :m2, 2026-11-08, 1d
  Relecture et répétitions                  :p2, 2026-11-09, 3d
  Oral blanc E1 à E5                        :milestone, o2, 2026-11-12, 0d
```

Les sprints 3 et 4 se chevauchent le vendredi 16 et les sprints 4 et 5 le lundi 19, comme le prévoit
le dossier V1 (demi-journées). Le diagramme les montre à la journée.

## 4. Charge

| Bloc                                   | Jours de travail | Source de l'estimation                       |
| -------------------------------------- | ---------------- | -------------------------------------------- |
| V1 (sprints 2 à 5)                     | 6                | Dossier V1, §2.2                             |
| V1.0 complète                          | 1,25             | Couverture des compétences, §3               |
| Réserve                                | 3                | Hors plan                                    |
| Rédaction et répétitions, premier oral | 4                | [H : deux livrables, trois répétitions]      |
| Veille et benchmark                    | 2                | Couverture des compétences, §3               |
| V1.1                                   | 1,5              | Couverture des compétences, §3               |
| Rédaction, second oral                 | 4                | [H : trois livrables et mise à jour de deux] |
| Marge, relecture, répétitions          | 4                | Hors plan, pour la marge                     |

Le calendrier compte tous les jours, week-ends compris (D-30). [H] Les durées de rédaction ne
sont pas mesurées ; la première rédaction (E1 et E3) servira d'étalon pour la seconde.

## 5. Risques propres à la feuille de route

| Risque                                                        | Effet                                     | Parade                                                                                         |
| ------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Validation du formateur après le 13 octobre                   | Le sprint 2 recule d'autant               | Prévenir le formateur dès aujourd'hui ; le jour perdu est pris sur la réserve                  |
| Glissement de la V1 au-delà du 19 octobre                     | Les compléments obligatoires sont menacés | Réserve du 22 au 24 ; les « si temps » sont abandonnés en premier                              |
| Compléments obligatoires non livrés avant le 29 octobre       | C13 partielle devant le jury              | Repli : montrer la chaîne automatisée jusqu'à l'image, et dire honnêtement ce qui reste manuel |
| Retours du jury qui demandent des changements de fond         | La rédaction du second oral déborde       | Marge du 8 novembre ; les compléments du 2 et du 3 novembre peuvent être réduits               |
| Fatigue : travail tous les jours du 12 octobre au 13 novembre | Erreurs, qualité en baisse                | Prévoir au moins une demi-journée sans travail par semaine dans la réserve ou la marge [H]     |
