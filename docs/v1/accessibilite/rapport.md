# Audit RGAA 4.1.2 de la console (C10) : rapport

**Date :** audit et corrections du 3 novembre 2026, décision sur 1.9 et 8.2 et parcours au lecteur
d'écran le 5 novembre 2026. **Protocole :** `protocole.md`, écrit avant l'audit. **Preuves :**
`grille.md` (après corrections, avec l'ancien verdict de chaque critère changé),
`grille-avant-corrections.md`, `mesures/`, `scenario-nvda.md` (parcours joué), tests
`tests/test_console_rgaa.py`. Mise en production : PR n° 221, version `f4edad7`.

## En clair

- Chapeau : Muninn est conçu pour devenir une application mobile, destinée à l'artisan. La version
  présentée à la soutenance se montre par une console web de démonstration, que l'artisan ne verra
  jamais : c'est elle que j'ai auditée, parce que c'est la seule interface de cette version qui
  utilise le modèle d'IA. J'ai vérifié les 106 critères du référentiel public d'accessibilité
  (RGAA) sur ses cinq écrans. Avant corrections, 56 des 72 critères qui concernent la console
  étaient respectés ; après correction des seize autres, tous le sont.
- Méthode : un outil automatique sur 29 pages relevées dans leurs différents états, des essais au
  clavier seul, à petite largeur et avec le texte agrandi, le validateur du W3C pour le code HTML,
  puis un parcours complet avec un lecteur d'écran (NVDA), à l'oreille seulement : 24 étapes sur
  24 conformes.
- Limite : l'audit suit la méthode publiée mais n'a pas la valeur d'un audit officiel, et il ne dit
  rien de l'application mobile, que ce référentiel ne couvre pas.

## 1. Cadrage

Muninn est conçu pour une **application mobile** (Android et iOS) destinée à l'artisan. Faute de
temps, la V1 n'en contient pas : elle tient le détail du produit côté serveur et se montre par une
**console web de démonstration et de test**, jamais présentée à l'artisan. La console est la seule
interface de la V1 qui intègre l'API du modèle : c'est elle que vise la compétence C10. Le RGAA 4.1
ne couvre pas les applications mobiles natives ; leur accessibilité reste traitée par la conception
(`docs/conception/sources_de_donnees/04-accessibilite-utilisabilite.md`).

## 2. Échantillon et méthode

J'ai mené l'audit seul : mesures outillées par un script de mesure, lecture des gabarits et du
JavaScript, parcours au lecteur d'écran.

- **Échantillon :** les cinq écrans de la console (Accueil, Référentiels, Agent, Démonstration,
  Qualité), chacun dans ses états : 17 états rendus, 7 états dynamiques de la Démonstration, puis 5
  états Agent rendus à neuf après corrections. Les pages types de l'échantillon RGAA (contact,
  mentions légales, accessibilité, plan du site, aide, authentification) n'existent pas dans une
  console de démonstration : absence notée, non comptée.
- **Moyens :** axe-core (WCAG 2.2 AA) ; clavier seul (Tab, Maj+Tab, focus, pièges) ; largeurs de
  320 et 640 px ; texte seul à 200 % ; espacements du texte ; validateur Nu du W3C, lancé en local
  dans son image officielle ; lecture des gabarits et du JavaScript ; parcours au lecteur d'écran.
- **Calcul :** méthode du RGAA. Un critère invalidé sur un écran est invalidé pour l'échantillon ;
  taux global = critères validés / critères applicables ; taux moyen = moyenne des taux par écran.

## 3. Résultats

| Mesure            | C / NC / NA (critères) | Taux global | Taux moyen | Mention                |
| ----------------- | ---------------------- | ----------- | ---------- | ---------------------- |
| Avant corrections | 56 / 16 / 34           | 77,8 %      | 90,6 %     | Partiellement conforme |
| Après corrections | 72 / 0 / 34            | 100 %       | 100 %      | Totalement conforme    |

Avant corrections, aucune non-conformité n'était bloquante au clavier : le parcours de la
Démonstration se faisait déjà entièrement au clavier seul ; le lecteur d'écran n'a été joué
qu'après corrections. L'audit initial annonçait 79,2 % ; le validateur Nu, lancé ensuite, a
relevé un saut de niveau de titre manqué (9.1, Qualité) : le taux a été recalculé à 77,8 %, pas
retouché.

**Mention :** totalement conforme sur l'échantillon audité, parcours au lecteur d'écran compris
(section 5).

## 4. Corrections

Le protocole prévoyait de corriger les seules non-conformités bloquantes ; il n'y en avait aucune.
J'ai décidé de corriger aussi les seize non-conformités « à planifier », en onze corrections :

| Critère(s)                | Écran(s)                     | Défaut                                                                  | Correction                                                                                                     |
| ------------------------- | ---------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 12.7                      | Tous                         | Aucun lien d'évitement                                                  | Lien « Aller au contenu », visible au focus ; `main` focalisable                                               |
| 8.2                       | Démonstration, Qualité       | Styles placés dans le corps de la page                                  | Styles dans l'en-tête (`{% block style %}`)                                                                    |
| 8.9                       | Démonstration                | `<i>` vides utilisés pour la mise en forme                              | `<span>`                                                                                                       |
| 8.7                       | Référentiels, Agent          | Codes anglais affichés bruts (« not_checked », « other »)               | Filtre `libelle` : libellés français                                                                           |
| 9.1                       | Qualité                      | Titre de niveau 3 juste après le titre de niveau 1                      | Titre de niveau 2                                                                                              |
| 10.4                      | Démonstration                | Texte à 200 % : écran de Karim rogné                                    | Cartes et pastilles repliables                                                                                 |
| 10.11                     | Agent                        | Listes de définitions débordant à 320 px                                | Terme et valeur l'un sous l'autre                                                                              |
| 11.10, 11.11              | Accueil, Référentiels, Agent | Champs obligatoires non signalés ; erreur sans nom de champ             | Mention « obligatoire » ; message nommant le champ, relié par `aria-describedby`                               |
| 11.12                     | Agent                        | Validation définitive sans confirmation                                 | Case « Je confirme la validation », obligatoire, contrôlée par le serveur                                      |
| 1.6, 3.1, 3.3, 10.2, 10.9 | Qualité                      | Graphiques : valeurs et séries portées par la seule forme et la couleur | Tableau des valeurs heure par heure relié aux graphiques ; séries à 3:1 au moins contre le fond et entre elles |
| 1.9                       | Qualité                      | `figure` sans `role` ni nom égal à sa légende (test 1.9.4)              | Texte d'introduction avant chaque graphique, sans figure (voir ci-dessous)                                     |

Le critère 1.7 devient applicable et conforme : les graphiques ont désormais une description
détaillée. La ligne pointillée du seuil reste à 1,5:1 contre les barres sombres ; l'information
qu'elle porte est donnée par le texte d'introduction et par le tableau des valeurs.

**Le conflit entre 1.9 et 8.2.** Ma première correction de 1.9 ajoutait un `role` à la `figure`,
comme le RGAA le demande ; le contre-audit a relevé la régression qu'elle introduisait : le
validateur Nu refuse un `role` sur une `figure` qui a une légende (« A figure element with a
figcaption descendant must not have a role attribute », `mesures/validateur-nu-apres.json`). Le
5 novembre 2026, le porteur a retenu l'option (b) : remplacer `figure` et légende par un texte
d'introduction, ce qui rend 1.9 non applicable et lève l'erreur. Options écartées : (a) motif du
RGAA et erreur Nu documentée, 98,6 % ; (c) statu quo, 97,3 %.

**Vérifications.** Chaque correction a son test de non-régression : 19 cas de test dans
`tests/test_console_rgaa.py`. **Contre-épreuve** (`mesures/contre-epreuve.txt`) : sur la console
d'avant les corrections, les 19 cas échouent ; après, les 19 passent. Le contre-audit, sur 29
rendus : axe-core sans violation, clavier sans piège, une seule régression, celle de 1.9 ci-dessus.
Après l'option (b), axe-core, le clavier et le validateur Nu ont été rejoués sur les trois états de
la Qualité, sans violation ni erreur (`mesures/qualite-option-b-axe-clavier.json`,
`mesures/validateur-nu-qualite-option-b.txt`).

## 5. Parcours au lecteur d'écran

Joué par moi le 5 novembre 2026 sur la console de production (version `f4edad7`), avec **NVDA 2026.3
et Firefox 159.0.1 (64 bits)**, combinaison de la base de référence du RGAA : 18 étapes sur les cinq
écrans, à l'oreille seulement, en 30 minutes. **Résultat : 18 étapes sur 18 conformes à l'attendu,
aucune remarque.** Détail : `scenario-nvda.md`.

Le parcours confirme notamment la structure des pages (titres, régions, navigation), les libellés
des champs, la lecture des tableaux de données, les annonces de statut et les phases de l'appel
(étape 13), l'arrêt (étape 15) et l'absence d'élément sans nom (étape 18).

**Complément ciblé**, joué le même jour, après la relecture du rapport (étapes 19 à 24 de
`scenario-nvda.md`) : il éprouve les points que l'audit réservait au lecteur d'écran et que le
premier parcours ne visait pas : le lien d'évitement, un champ obligatoire laissé vide, le message
d'erreur du champ « Transcription », la case de confirmation, le texte d'introduction des
graphiques et le tableau des valeurs. **Résultat : 6 étapes sur 6 conformes, aucune remarque ; 24
sur 24 pour l'ensemble du parcours.** Restent non éprouvés au lecteur d'écran, sans effet sur le
taux : l'actualisation automatique de la Qualité (30 secondes), le tableau
des contrôles sous 40rem de large, le groupe de boutons radio de l'Agent.

## 6. Critères WCAG 2.2 hors RGAA

La conception vise les WCAG 2.2 niveau AA ; six critères de ce niveau sont absents du RGAA 4.1.2 et
sont rapportés à part, hors du taux (protocole, section 2).

| Critère WCAG 2.2                  | Verdict        | Preuve                                                                                      |
| --------------------------------- | -------------- | ------------------------------------------------------------------------------------------- |
| 2.4.11 Focus non masqué           | Conforme       | Aucun élément fixe ou collant dans la console ; focus visible à chaque arrêt (clavier)      |
| 2.5.7 Mouvements de glissement    | Non applicable | Aucune interaction par glisser-déposer                                                      |
| 2.5.8 Taille des cibles (minimum) | Conforme       | Règle `target-size` d'axe-core passée sur les cinq écrans de production                     |
| 3.2.6 Aide constante              | Non applicable | La console n'offre aucun mécanisme d'aide répété d'une page à l'autre                       |
| 3.3.7 Saisie redondante           | Conforme       | La transcription est conservée après une erreur ; le formulaire de validation est prérempli |
| 3.3.8 Authentification accessible | Non applicable | La console n'a pas d'authentification                                                       |

## 7. Remarques hors taux

- Texte agrandi à 200 % : les pastilles de l'écran de Karim se coupent au milieu des mots ; c'est
  lisible, à améliorer.
- Si la confirmation manque et que la validation du navigateur est contournée, le formulaire du
  dossier disparaît : il faut rejouer l'appel.

## 8. Limites

- Je ne suis pas auditeur certifié : l'audit suit la méthode publiée, sans en avoir la valeur
  légale.
- Le script de mesure n'est pas dans le dépôt : ses résultats le sont (`mesures/`), mais leur
  reproduction exacte demande de le réécrire.
- Le lecteur d'écran a été joué avec une seule combinaison de la base de référence, sur Windows 11.
  Les mesures outillées ont tourné dans Chromium 153 (Playwright).
- L'état Agent « dossier validé » n'a pas été rendu en test, faute de base : il a été jugé sur le
  gabarit, puis parcouru en production (étape 11 du parcours).
- La console est une interface de démonstration : l'accessibilité de l'application mobile, la vraie
  interface de l'artisan, n'est pas mesurée ici.
