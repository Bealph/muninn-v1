# Exigences d'accessibilité et d'utilisabilité de Muninn

**Version :** 1
**Date :** 12 octobre 2026
**Phase :** 0a (besoin, flux et sources de données)
**Statut :** proposition, à valider par le porteur
**Compétences servies :** C14 (exigences d'accessibilité), C10 et C17 (réalisation et audit)
**Document lié :** `01-user-stories.md` (identifiants US-01 à US-54)

## 1. Objet et périmètre

Ce document fixe les exigences d'accessibilité (EXA) et d'utilisabilité de terrain (EXU) de
Muninn, et la méthode de vérification de chacune. Les hypothèses sont marquées **[H]**.

Muninn expose trois interfaces :

| Interface                    | Utilisateurs                             | Horizon                                                 | Stories principales                                             |
| ---------------------------- | ---------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------- |
| Application mobile           | Artisan                                  | MVP (Android et iOS)                                    | US-01 à US-05, US-12 à US-35, US-49, US-51, US-54               |
| Console web de démonstration | Exploitant ; artisan simulé pour la démo | Phase 5, démo du 29 octobre 2026 ; exploitation ensuite | US-11, US-17, US-31, US-36 à US-40, US-46 à US-48, US-50, US-51 |
| Canal vocal et SMS           | Client final                             | MVP                                                     | US-06 à US-10, US-27, US-29                                     |

## 2. Référentiels et obligations

### 2.1 Référentiels en vigueur

Vérifications faites le 12 octobre 2026 sur les sources officielles.

| Référentiel    | Version en vigueur                                              | Constat                                                                                                                                                                          | Source                                                                                                    |
| -------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| RGAA           | 4.1.2, mise à jour du 18 avril 2023                             | Aligné sur les WCAG 2.1, niveaux A et AA                                                                                                                                         | https://accessibilite.numerique.gouv.fr/                                                                  |
| RGAA 5         | Non publié                                                      | « En cours de rédaction », publication annoncée fin 2026. Annonce : intégration des WCAG 2.2 et critères pour les applications mobiles                                           | https://www.numerique.gouv.fr/actualites/nouvelle-version-rgaa-2026/                                      |
| RGAA et mobile | Sans objet                                                      | La méthode RGAA 4.1 ne couvre pas les applications mobiles natives ; renvoi vers la norme EN 301 549                                                                             | https://design.numerique.gouv.fr/fr/accessibilite-numerique/rgaa/                                         |
| WCAG           | 2.2, recommandation W3C (version lue datée du 12 décembre 2024) | Niveaux A, AA, AAA                                                                                                                                                               | https://www.w3.org/TR/WCAG22/                                                                             |
| WCAG 3.0       | Brouillon de travail du 10 septembre 2026                       | Non applicable : document de travail                                                                                                                                             | https://www.w3.org/TR/wcag-3.0/                                                                           |
| EN 301 549     | V3.2.1, harmonisée en 2021 pour la directive (UE) 2016/2102     | Les pages françaises citent encore la V2.1.2 : contradiction entre sources officielles. Une V4.1.1 figure sur le serveur de l'ETSI (fichier du 2 septembre 2026), contenu non lu | https://digital-strategy.ec.europa.eu/en/policies/web-accessibility-directive-standards-and-harmonisation |
| Android        | Recommandation de plateforme                                    | Zone d'interaction d'au moins 48 dp × 48 dp ; outils Accessibility Scanner et TalkBack                                                                                           | https://developer.android.com/guide/topics/ui/accessibility/apps                                          |
| iOS            | Recommandation de plateforme                                    | Non vérifié : les pages Apple n'ont pas pu être lues (rendu JavaScript)                                                                                                          | https://developer.apple.com/design/human-interface-guidelines/accessibility                               |

Il n'existe pas de référentiel mobile officiel français publié à cette date. Le « RAAM » cité dans
certaines sources est un référentiel luxembourgeois.

### 2.2 Obligations légales

| Texte                                                                                                                          | Qui est assujetti                                                                                                                    | Situation de Muninn                                                                | Source                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Loi n° 2005-102, article 47                                                                                                    | Organismes publics, personnes privées chargées d'une mission de service public, entreprises au-delà d'un seuil de chiffre d'affaires | Non assujetti : seuil de 250 M€ de chiffre d'affaires annuel moyen en France       | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000809647 ; https://accessibilite.numerique.gouv.fr/obligations/champ-application/ |
| Article 47, champ des services                                                                                                 | Les applications mobiles font partie des services de communication au public en ligne                                                | Sans objet tant que Muninn n'est pas assujetti                                     | https://accessibilite.numerique.gouv.fr/obligations/champ-application/                                                               |
| Acte européen d'accessibilité : loi n° 2023-171 (article 16, article L412-13 du Code de la consommation) et décret n° 2023-931 | Produits et services listés (dont le commerce électronique), mis sur le marché ou fournis après le 28 juin 2025                      | En principe hors champ : services aux consommateurs uniquement (voir ci-dessous)   | https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000047281814 ; https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000048178349    |
| Exemption des microentreprises de services                                                                                     | Moins de 10 personnes et chiffre d'affaires ou total de bilan d'au plus 2 M€                                                         | Muninn au lancement serait exempté [H : effectif et chiffre d'affaires du porteur] | https://www.legifrance.gouv.fr/codes/id/LEGISCTA000047284903                                                                         |

**Champ de l'acte européen (vérifié le 12 octobre 2026, lecture des textes, pas un avis
juridique).** La directive (UE) 2019/882 s'applique aux services « provided to consumers »
(article 2, paragraphe 2). Le consommateur y est une personne physique qui agit hors de son
activité professionnelle (article 3, point 22). Le décret n° 2023-931 (article D. 412-50) renvoie
aux services définis à l'article 3 de la directive. Un service vendu uniquement à des artisans
pour leur activité est donc **en principe hors champ**. De plus, l'article L412-13, I, du Code de
la consommation dispense les entreprises de services de moins de dix personnes dont le chiffre
d'affaires ou le total du bilan « n'excède pas deux millions d'euros ». Réserves : le champ
« consommateurs » découle du renvoi du décret, pas du texte de L412-13 ; le régime des articles 47
et 48 de la loi n° 2005-102 n'a pas été vérifié pour ce point. Confirmation à demander dans l'avis
juridique (condition C3 de l'analyse). Source du texte de la directive :
<https://www.legislation.gov.uk/eudr/2019/882/article/2/adopted> (EUR-Lex illisible par l'outil).

Points non vérifiés :

- **Décret n° 2019-768** : cité par le site du RGAA, texte non relu.
- **EN 301 549, chapitres 6 (communication vocale bidirectionnelle) et 11 (logiciels)** : le
  document n'a pas pu être lu. Son application au canal vocal de l'agent n'est donc pas établie.
- **Recommandations Apple** (taille de cible, VoiceOver, Dynamic Type, Accessibility Inspector) :
  pages non lisibles par l'outil de vérification.

### 2.3 Niveau visé et décision

Aucune obligation légale ne s'impose à Muninn à ce stade. Le niveau est fixé volontairement :

| Interface                    | Niveau visé                                                                                                      | Méthode d'audit                                                                   |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Console web de démonstration | WCAG 2.2 niveau AA                                                                                               | Critères du RGAA 4.1.2, complétés par les critères ajoutés en WCAG 2.2 (voir 3.1) |
| Application mobile           | WCAG 2.2 niveau AA appliqué au mobile, plus les critères AAA 1.4.6 et 2.5.5 et les recommandations de plateforme | Tests outillés et manuels de la section 5 ; RGAA 5 dès sa publication             |
| Canal vocal et SMS           | Exigences propres (EXA-17, EXA-18) [H : faute de lecture de l'EN 301 549, chapitre 6]                            | Scénarios synthétiques et relecture                                               |

Justification :

- C10 et C14 exigent une application accessible et des exigences d'accessibilité explicites.
- Le RGAA 5 annoncé intègre les WCAG 2.2 : viser 2.2 dès maintenant évite une reprise.
- Les conditions de terrain (mains occupées, extérieur) rejoignent des critères AAA : ils sont
  retenus pour les écrans de terrain (EXU-01, EXU-03), avec des seuils marqués [H].

## 3. Exigences d'accessibilité (EXA)

Légende des interfaces : M = application mobile, W = console web, V = canal vocal et SMS.

### 3.1 Critères WCAG 2.2 utilisés

Niveaux relevés sur la référence rapide du W3C le 12 octobre 2026
(https://www.w3.org/WAI/WCAG22/quickref/).

| Critère | Nom                                       | Niveau | Ajouté en |
| ------- | ----------------------------------------- | ------ | --------- |
| 1.1.1   | Non-text Content                          | A      | 2.0       |
| 1.3.1   | Info and Relationships                    | A      | 2.0       |
| 1.3.4   | Orientation                               | AA     | 2.1       |
| 1.4.1   | Use of Color                              | A      | 2.0       |
| 1.4.3   | Contrast (Minimum) : 4,5:1                | AA     | 2.0       |
| 1.4.4   | Resize Text                               | AA     | 2.0       |
| 1.4.6   | Contrast (Enhanced)                       | AAA    | 2.0       |
| 1.4.10  | Reflow                                    | AA     | 2.1       |
| 1.4.11  | Non-text Contrast : 3:1                   | AA     | 2.1       |
| 2.1.1   | Keyboard                                  | A      | 2.0       |
| 2.2.1   | Timing Adjustable                         | A      | 2.0       |
| 2.4.2   | Page Titled                               | A      | 2.0       |
| 2.4.3   | Focus Order                               | A      | 2.0       |
| 2.4.6   | Headings and Labels                       | AA     | 2.0       |
| 2.4.7   | Focus Visible                             | AA     | 2.0       |
| 2.4.11  | Focus Not Obscured (Minimum)              | AA     | 2.2       |
| 2.5.1   | Pointer Gestures                          | A      | 2.1       |
| 2.5.2   | Pointer Cancellation                      | A      | 2.1       |
| 2.5.3   | Label in Name                             | A      | 2.1       |
| 2.5.4   | Motion Actuation                          | A      | 2.1       |
| 2.5.5   | Target Size (Enhanced) : 44 × 44 px CSS   | AAA    | 2.1       |
| 2.5.7   | Dragging Movements                        | AA     | 2.2       |
| 2.5.8   | Target Size (Minimum) : 24 × 24 px CSS    | AA     | 2.2       |
| 3.1.1   | Language of Page                          | A      | 2.0       |
| 3.2.6   | Consistent Help                           | A      | 2.2       |
| 3.3.1   | Error Identification                      | A      | 2.0       |
| 3.3.2   | Labels or Instructions                    | A      | 2.0       |
| 3.3.4   | Error Prevention (Legal, Financial, Data) | AA     | 2.0       |
| 3.3.7   | Redundant Entry                           | A      | 2.2       |
| 3.3.8   | Accessible Authentication (Minimum)       | AA     | 2.2       |
| 4.1.2   | Name, Role, Value                         | A      | 2.0       |
| 4.1.3   | Status Messages                           | AA     | 2.1       |

« 2.0 » signifie que la page ne marque ni « Added in 2.1 » ni « Added in 2.2 ».

### 3.2 Liste des exigences

#### EXA-01. Nom accessible de chaque élément

Chaque bouton, icône et champ a un nom accessible. Le nom prononcé contient le libellé visible,
pour permettre la commande vocale du système (« touche Valider »).

- Interfaces : M, W
- Critères : 1.1.1, 2.5.3, 4.1.2
- Stories : US-17, US-19, US-28, US-30, US-36 à US-38, US-48, et tout écran
- Vérification : lecteur d'écran (TalkBack, VoiceOver, NVDA) sur chaque écran ; Accessibility
  Scanner ; axe-core sur la console.

#### EXA-02. Aucune information portée par la couleur seule

Les états « à vérifier », « non contrôlé », « marge négative », « seuil non atteint », « jour
férié », « ligne rejetée », « terme écarté » et les alertes portent un texte, en plus de la
couleur.

- Interfaces : M, W
- Critères : 1.4.1
- Stories : US-17, US-21, US-23, US-37, US-38, US-46 à US-49, US-51
- Vérification : revue de l'écran en niveaux de gris (test manuel) ; contrôle que chaque état a un
  libellé textuel.

#### EXA-03. Contrastes minimaux

Texte : 4,5:1 au moins (3:1 pour le grand texte). Composants d'interface et graphiques utiles :
3:1 au moins. L'exigence de terrain EXU-03 renforce ce seuil sur mobile.

- Interfaces : M, W
- Critères : 1.4.3, 1.4.11
- Stories : tout écran ; graphiques du tableau de bord (US-38)
- Vérification : Colour Contrast Analyser sur la palette ; axe-core sur la console ; Accessibility
  Scanner sur l'application.

#### EXA-04. Taille des cibles tactiles

Console : 24 × 24 px CSS au minimum, 44 × 44 px CSS visés. Application : 48 × 48 dp au minimum
(recommandation Android), relevé par EXU-01 pour les actions principales.

- Interfaces : M, W
- Critères : 2.5.8, 2.5.5
- Stories : US-03, US-17, US-19, US-28, US-30
- Vérification : Accessibility Scanner (signale les cibles trop petites) ; mesure dans l'inspecteur
  de mise en page ; outils de développement du navigateur pour la console.

#### EXA-05. Texte agrandi et contenu redimensionnable

Avec un texte agrandi à 200 % et avec la taille de police maximale du système, aucun texte n'est
tronqué ni superposé et chaque action principale reste atteignable. La console s'affiche sans
défilement horizontal à 320 px CSS de large.

- Interfaces : M, W
- Critères : 1.4.4, 1.4.10
- Stories : tout écran
- Vérification : test manuel avec la taille de police maximale d'Android et d'iOS ; zoom du
  navigateur à 200 % et 400 %.

#### EXA-06. Orientation libre

L'application fonctionne en portrait et en paysage, sans blocage d'orientation.

- Interfaces : M
- Critères : 1.3.4
- Stories : tout écran
- Vérification : test manuel par rotation sur chaque écran.

#### EXA-07. Structure lisible par un lecteur d'écran

Les écrans ont des titres. Le brouillon de dossier groupe ses champs par bloc (client, adresse,
demande) avec un libellé par champ. L'ordre de lecture suit l'ordre visuel. La langue de l'écran
est déclarée en français.

- Interfaces : M, W
- Critères : 1.3.1, 2.4.2, 2.4.3, 2.4.6, 3.1.1, 3.3.2
- Stories : US-11, US-17, US-23, US-36, US-37, US-51
- Vérification : parcours complet au lecteur d'écran ; axe-core sur la console.

#### EXA-08. Messages d'état annoncés

L'arrivée d'une nouvelle demande, la fin d'une extraction, l'envoi des SMS, le déclenchement
d'une alerte, la révocation d'un appareil et l'enregistrement d'une décision de relecture du
lexique sont annoncés aux technologies d'assistance sans déplacer le focus.

- Interfaces : M, W
- Critères : 4.1.3
- Stories : US-12, US-17, US-28, US-36, US-38, US-48, US-54
- Vérification : lecteur d'écran pendant le scénario de démo ; revue du code des zones d'annonce.

#### EXA-09. Console utilisable au clavier

Toutes les fonctions de la console (lancer un scénario, valider, corriger, ouvrir un rapport)
sont utilisables au clavier seul. Le focus est visible et jamais masqué par un bandeau.

- Interfaces : W
- Critères : 2.1.1, 2.4.7, 2.4.11
- Stories : US-17, US-36 à US-38, US-40, US-46 à US-48, US-50
- Vérification : parcours complet au clavier seul (test manuel) ; axe-core.

#### EXA-10. Gestes simples et annulables

Aucune action n'exige un geste à tracé, un glissement ou un mouvement du téléphone. Un glissement
peut exister comme raccourci, jamais comme seul moyen. Une action se déclenche au relâchement et
peut être annulée en éloignant le doigt.

- Interfaces : M
- Critères : 2.5.1, 2.5.2, 2.5.4, 2.5.7
- Stories : US-17, US-28, US-30, US-54
- Vérification : revue de chaque interaction (inventaire des gestes) ; test manuel au toucher et
  avec un contacteur ou la commande vocale du système.

#### EXA-11. Connexion sans test cognitif

Le code à usage unique peut être collé ou rempli automatiquement depuis le SMS ou l'e-mail. Aucune
énigme ni transcription de caractères n'est demandée.

- Interfaces : M
- Critères : 3.3.8
- Stories : US-01
- Vérification : test manuel du remplissage automatique et du collage sur Android et iOS.

#### EXA-12. Erreurs signalées et actions sensibles confirmées

Une erreur est décrite en texte, avec le moyen de la corriger. L'envoi de SMS, la suppression
d'un dossier, le rejet d'un brouillon, la création de la clé de sauvegarde, l'approbation d'un
nouvel appareil et la révocation d'un appareil demandent une confirmation ou restent annulables.

- Interfaces : M, W
- Critères : 3.3.1, 3.3.4
- Stories : US-01, US-17, US-28, US-33, US-35, US-54
- Vérification : test manuel de chaque action sensible ; revue des messages d'erreur.

#### EXA-13. Pas de ressaisie

Une information déjà connue (extraite ou dictée) est proposée, jamais redemandée. L'export reprend
les données du dossier.

- Interfaces : M
- Critères : 3.3.7
- Stories : US-17, US-20, US-24
- Vérification : revue des parcours ; test des parcours de correction et d'export.

#### EXA-14. Pas de perte due à un délai

Valider un brouillon n'a pas de limite de temps. Quand un délai existe (code de connexion,
invitation au débrief), l'action reste possible autrement : nouveau code, raccourci de dictée.

- Interfaces : M
- Critères : 2.2.1
- Stories : US-01, US-14, US-17
- Vérification : test manuel après expiration de chaque délai.

#### EXA-15. Aide au même endroit

L'aide (instructions de renvoi, appel de test, contact) est accessible au même endroit sur tous
les écrans.

- Interfaces : M, W
- Critères : 3.2.6
- Stories : US-03, US-04
- Vérification : revue de navigation écran par écran.

#### EXA-16. Équivalence entre la voix et le toucher

Toute fonction vocale (débrief, dépense dictée, recherche, imprévu, correction) a un équivalent au
toucher et au clavier. Toute question posée à voix haute est aussi affichée. Un artisan qui ne
peut pas parler ou ne peut pas entendre utilise toutes les fonctions.

- Interfaces : M
- Critères : aucun critère WCAG direct ; principe d'équivalence [H]
- Stories : US-13, US-17, US-18, US-19, US-22, US-28
- Dépendance : un point d'extraction à partir de texte, absent de la passation back-end [H]
- Vérification : parcours complet de chaque story sans micro, puis sans son (test manuel).

#### EXA-17. Canal vocal adapté au client final

L'agent parle à un débit posé, accepte « répétez » à tout moment et reformule avant de conclure.
Il attend au moins 5 secondes [H] avant une relance, pour ne pas couper une personne qui parle
lentement ou qui bégaie. Le client peut toujours demander un simple rappel.

- Interfaces : V
- Critères : aucun critère WCAG ; EN 301 549, chapitre 6, non lu (section 2.2)
- Stories : US-06 à US-10
- Vérification : scénarios synthétiques avec pauses longues, demandes de répétition et débit lent ;
  écoute de contrôle.

Limite : un appelant sourd ou malentendant n'est pas servi directement par un canal vocal. Le
recours à un service de relais téléphonique est à vérifier [H]. Une alternative écrite n'est pas
prévue par le concept ; elle est à étudier en V2 [H].

#### EXA-18. SMS lisibles par tous

Les SMS sont rédigés en phrases courtes, sans abréviation. Dates et heures sont écrites en clair
(« mercredi 14 octobre à 9 h »). Le nom de l'entreprise figure au début. Aucun lien raccourci n'est
nécessaire pour comprendre le message.

- Interfaces : V
- Critères : aucun critère WCAG direct [H]
- Stories : US-27, US-29
- Vérification : lecture des modèles de SMS par TalkBack et VoiceOver ; relecture en langage clair.

#### EXA-19. Déclaration d'accessibilité volontaire

Une déclaration d'accessibilité est publiée pour la console puis pour l'application : niveau
visé, résultats d'audit, non-conformités connues, contact.

- Interfaces : M, W
- Critères : sans objet (bonne pratique inspirée de l'article 47, III)
- Stories : transverse
- Vérification : présence de la déclaration ; date de l'audit à moins d'un an.

#### EXA-20. Rapports et tableaux de la console d'exploitation

Les rapports de chargement, la relecture du lexique et les versions servies des référentiels
s'affichent dans des tableaux dont les en-têtes de lignes et de colonnes sont déclarés. Chaque
rapport commence par un résumé en texte (lignes lues, chargées, rejetées ; version, source et
date). Le filtre, le tri et la pagination sont utilisables au clavier, et le nombre de résultats
d'un filtre est annoncé sans déplacer le focus.

- Interfaces : W
- Critères : 1.3.1, 2.4.6, 4.1.3
- Stories : US-46, US-47, US-48, US-50
- Justification : un rapport compte des milliers de lignes (20 886 tranches pour US-47) ; sans
  en-têtes déclarés ni résumé, un lecteur d'écran le lit cellule par cellule. EXA-07 ne couvre que
  la structure du brouillon.
- Vérification : parcours au lecteur d'écran (NVDA) d'un rapport de chargement et de la file de
  relecture ; axe-core ; parcours au clavier seul du filtre et de la pagination.

## 4. Exigences d'utilisabilité de terrain (EXU)

Elles découlent des arbitrages de l'artisan (analyse, section 3.4), de la faille « interface de
bureau » (section 2.4, point 3) et du persona P1, qui reçoit ses appels « les mains dans une
chaudière » (section 3.2).

Le projet n'a pas de terrain (pas de POC). Les tests de terrain ci-dessous sont **simulés** :
gants de travail, téléphone en extérieur, bruit de chantier enregistré. Leurs seuils sont des
hypothèses **[H]** à confirmer par les entretiens de l'action 1 de l'analyse.

#### EXU-01. Cibles utilisables avec des gants

Les actions principales (Valider, Envoyer, Dicter, Rappeler) ont une cible d'au moins 64 dp ou
64 pt [H], espacées d'au moins 8 dp [H]. Les autres cibles respectent EXA-04.

- Interfaces : M
- Justification : mains occupées (sections 2.4 et 3.2) ; port de gants [H : non écrit dans
  l'analyse].
- Stories : US-13, US-14, US-17, US-28, US-30
- Vérification : essai de vraisemblance, sans valeur statistique : 10 essais par action principale
  avec des gants de travail, par un seul testeur, 9 réussites au moins [H] ; mesure des cibles
  dans l'inspecteur de mise en page.

#### EXU-02. Usage à une main

Les actions principales sont dans la moitié basse de l'écran, à portée du pouce. Aucune action
n'exige deux mains ni plusieurs doigts.

- Interfaces : M
- Justification : l'autre main tient un outil ou une pièce (section 3.2) [H].
- Stories : US-13, US-17, US-19, US-28, US-30
- Vérification : parcours de chaque story d'une seule main, sur un téléphone de 6,1 pouces et un de
  6,7 pouces [H].

#### EXU-03. Lisibilité en plein soleil

Les écrans de terrain (brouillon, à faire, agenda, imprévu) visent un contraste de texte de 7:1
(critère AAA 1.4.6). Texte courant de 16 sp au moins [H]. Aucune information en couleur pâle.

- Interfaces : M
- Justification : travail sur chantier et en extérieur [H : condition déduite du métier,
  non écrite dans l'analyse].
- Stories : US-17, US-23, US-26, US-28, US-30
- Vérification : Colour Contrast Analyser sur la palette ; lecture en extérieur, luminosité
  automatique, par temps ensoleillé (test manuel).

#### EXU-04. Robustesse au bruit de chantier

La dictée et l'agent vocal restent exacts dans le bruit. Les notifications passent aussi par la
vibration et l'écran, pas seulement par le son.

- Interfaces : M, V
- Justification : appels pris sur chantier (sections 3.2 et 3.3) ; bruit prévu dans le jeu
  d'évaluation de la passation back-end.
- Stories : US-07, US-12, US-13, US-15, US-22
- Vérification : évaluation (US-37) sur le jeu synthétique avec et sans bruit ; écart
  d'exactitude des champs clés de 5 points au plus, mesuré sur le jeu complet de 100 scénarios
  avec son intervalle de confiance [H] ; test manuel des notifications téléphone
  en mode silencieux.

#### EXU-05. La voix comme interface principale

Les actions fréquentes (débrief, dépense, recherche, imprévu) démarrent en un geste depuis une
notification, un widget ou un raccourci, puis se font à la voix. Un signal sonore et une
vibration marquent le début et la fin de l'écoute.

- Interfaces : M
- Justification : « zéro saisie » (section 3.6, rang 2) et faille « interface de bureau » (section
  2.4, point 3).
- Stories : US-13, US-14, US-18, US-22, US-28
- Vérification : chronométrage de l'écran verrouillé au début de la dictée, sans compter le
  déverrouillage biométrique : 2 gestes et 3 secondes au plus en médiane sur 10 essais [H].

#### EXU-06. Validation en un geste

Un brouillon sans champ « à vérifier » se valide d'un seul toucher. Une correction porte sur un
champ, à la voix ou au clavier. Aucun formulaire complet n'est jamais demandé.

- Interfaces : M, W
- Justification : « validation en un geste » (section 3.4, contrôle contre automatisation).
- Stories : US-17, US-20, US-28
- Vérification : comptage des gestes dans le scénario de démo et dans les tests d'interface ;
  1 geste pour un brouillon sans champ « à vérifier ».

#### EXU-07. Aucune action invisible

Toute action qui a un effet hors du téléphone (SMS, export, rendez-vous pris par l'assistant,
rattachement) est soit validée avant par l'artisan, soit affichée après dans l'historique du
dossier. Seuls les rappels SMS, activés explicitement dans les réglages, partent sans validation
au cas par cas.

- Interfaces : M, W
- Justification : « jamais d'action invisible » (section 3.4).
- Stories : US-03, US-20, US-24, US-26, US-27, US-28
- Vérification : inventaire des effets externes de chaque story, comparé aux écrans de validation
  et d'historique (revue) ; test d'interface : aucun SMS d'imprévu ni de replanification n'est
  envoyé sans le geste de validation ; chaque rappel envoyé figure dans l'historique.

#### EXU-08. Gain dès le premier jour, sans saisie

La mise en service (compte, ligne, renvoi) tient en 5 minutes [H], dont moins de 2 minutes pour
le renvoi. Le premier dossier arrive sans aucune saisie.

- Interfaces : M
- Justification : « effort contre gain » (section 3.4) ; KPI de l'action 2 (renvoi en moins de
  2 minutes) et de l'action 4 (70 % des dossiers créés sans saisie).
- Stories : US-01, US-02, US-03, US-11, US-17
- Vérification : test utilisateur chronométré sur un profil non technique [H] ; part des brouillons
  validés sans correction, au niveau du dossier, suivie par le tableau de bord (US-38).

#### EXU-09. Reprise après interruption

Une dictée ou une correction interrompue (appel entrant, passage en arrière-plan) est conservée et
reprend au même point.

- Interfaces : M
- Justification : travail fréquemment interrompu (parcours, section 3.3) [H].
- Stories : US-13, US-17, US-22, US-28
- Vérification : test manuel avec un appel entrant pendant chaque action.

#### EXU-10. Fonctionnement sans réseau

Les dossiers se consultent sans réseau, et la recherche écrite fonctionne sans réseau. Une dictée faite sans réseau est gardée chiffrée et
envoyée au retour du réseau.

- Interfaces : M
- Justification : données sur le téléphone (section 1.3, point 5) ; sous-sols et chaufferies [H].
- Stories : US-13, US-18, US-23, US-32
- Vérification : test manuel en mode avion.

#### EXU-11. Confiance rendue visible

Les preuves de confiance sont écrites en langage courant : « audio et transcription détruits à
10 h 42 », « dossier chiffré sur ce téléphone ». L'agent s'annonce toujours au client.

- Interfaces : M, V
- Justification : « confiance contre puissance » (section 3.4).
- Stories : US-06, US-31, US-32, US-33
- Vérification : test de compréhension sur 5 personnes [H] : chacune explique avec ses mots ce qui
  est détruit et ce qui est gardé.

#### EXU-12. Vocabulaire de l'artisan

Les libellés sont courts et sans jargon informatique : « à vérifier » et non « needs_review ».
Aucun score de confiance chiffré n'est affiché. Les termes techniques internes ne sont jamais
montrés à l'artisan.

- Interfaces : M, W
- Justification : cible non technique, adoption conditionnée à l'absence d'effort (section 3.4).
- Stories : US-11, US-17, US-23, US-31, US-51
- Vérification : revue des libellés contre une liste de termes interdits (noms de champs du
  schéma, scores de confiance, anglicismes techniques).

## 5. Méthode de vérification

### 5.1 Outils

| Outil                                | Interface   | Usage                                                 | Source                                                                                                |
| ------------------------------------ | ----------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| axe-core (Deque)                     | W           | Analyse automatique, intégrée aux tests de la console | https://github.com/dequelabs/axe-core                                                                 |
| NVDA et Firefox                      | W           | Lecteur d'écran, test manuel                          | https://www.nvaccess.org/                                                                             |
| Clavier seul                         | W           | Parcours manuel complet                               | sans objet                                                                                            |
| Colour Contrast Analyser (TPGi)      | M, W        | Mesure des contrastes de la palette                   | https://www.tpgi.com/color-contrast-checker/                                                          |
| Accessibility Scanner                | M (Android) | Analyse des écrans, cibles et contrastes              | https://developer.android.com/guide/topics/ui/accessibility/testing                                   |
| TalkBack                             | M (Android) | Lecteur d'écran, test manuel                          | https://developer.android.com/guide/topics/ui/accessibility/testing                                   |
| VoiceOver et Accessibility Inspector | M (iOS)     | Lecteur d'écran et inspection                         | https://developer.apple.com/documentation/accessibility/accessibility-inspector (contenu non vérifié) |
| Harnais d'évaluation (US-37)         | V, M        | Exactitude avec bruit, débit lent, pauses             | sans objet                                                                                            |

Les URL des outils tiers (axe-core, NVDA, TPGi) n'ont pas été vérifiées lors de cette
rédaction. Les outils automatiques ne détectent qu'une partie des défauts : chaque exigence garde
au moins un test manuel.

### 5.2 Moment de la vérification

| Moment                            | Vérifications                                                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| À chaque intégration continue     | axe-core sur les écrans de la console ; tests d'interface d'EXU-06 et d'EXU-07                                 |
| Avant la démo du 29 octobre       | Audit de la console : critères du RGAA 4.1.2 et critères WCAG 2.2 de la section 3.1, sur les écrans de la démo |
| À chaque version de l'application | Parcours TalkBack et VoiceOver, Accessibility Scanner, tests de terrain simulés                                |
| À la publication du RGAA 5        | Révision de ce document et du niveau visé                                                                      |

### 5.3 Exigences du périmètre de la démo du 29 octobre

La console de démonstration doit satisfaire, au minimum : EXA-01, EXA-02, EXA-03, EXA-04, EXA-05,
EXA-07, EXA-08, EXA-09, EXA-12, EXU-06, EXU-07 et EXU-12. L'audit de ces exigences sert de preuve
pour C10.

## 6. Traçabilité

Table produite à partir des listes « Stories » de chaque exigence. Les exigences marquées « tout
écran » ou « transverse » (EXA-01, EXA-03, EXA-05, EXA-06, EXA-19) s'appliquent en plus à toutes les
stories qui ont une interface.

| Story | Exigences                                                                                                                                      |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-01 | EXA-11, EXA-12, EXA-14, EXU-08                                                                                                                 |
| US-02 | EXU-08                                                                                                                                         |
| US-03 | EXA-04, EXA-15, EXU-07, EXU-08                                                                                                                 |
| US-04 | EXA-15                                                                                                                                         |
| US-05 | exigences transverses seulement (EXA-01, EXA-03, EXA-05, EXA-06, EXA-19)                                                                       |
| US-06 | EXA-17, EXU-11                                                                                                                                 |
| US-07 | EXA-17, EXU-04                                                                                                                                 |
| US-08 | EXA-17                                                                                                                                         |
| US-09 | EXA-17                                                                                                                                         |
| US-10 | EXA-17                                                                                                                                         |
| US-11 | EXA-07, EXU-08, EXU-12                                                                                                                         |
| US-12 | EXA-08, EXU-04                                                                                                                                 |
| US-13 | EXA-16, EXU-01, EXU-02, EXU-04, EXU-05, EXU-09, EXU-10                                                                                         |
| US-14 | EXA-14, EXU-01, EXU-05                                                                                                                         |
| US-15 | EXU-04                                                                                                                                         |
| US-16 | exigences transverses seulement (EXA-01, EXA-03, EXA-05, EXA-06, EXA-19)                                                                       |
| US-17 | EXA-01, EXA-02, EXA-04, EXA-07, EXA-08, EXA-09, EXA-10, EXA-12, EXA-13, EXA-14, EXA-16, EXU-01, EXU-02, EXU-03, EXU-06, EXU-08, EXU-09, EXU-12 |
| US-18 | EXA-16, EXU-05, EXU-10                                                                                                                         |
| US-19 | EXA-01, EXA-04, EXA-16, EXU-02                                                                                                                 |
| US-20 | EXA-13, EXU-06, EXU-07                                                                                                                         |
| US-21 | EXA-02                                                                                                                                         |
| US-22 | EXA-16, EXU-04, EXU-05, EXU-09                                                                                                                 |
| US-23 | EXA-02, EXA-07, EXU-03, EXU-10, EXU-12                                                                                                         |
| US-24 | EXA-13, EXU-07                                                                                                                                 |
| US-25 | sans objet (hors MVP) ; exigences à reprendre à leur conception                                                                                |
| US-26 | EXU-03, EXU-07                                                                                                                                 |
| US-27 | EXA-18, EXU-07                                                                                                                                 |
| US-28 | EXA-01, EXA-04, EXA-08, EXA-10, EXA-12, EXA-16, EXU-01, EXU-02, EXU-03, EXU-05, EXU-06, EXU-07, EXU-09                                         |
| US-29 | EXA-18                                                                                                                                         |
| US-30 | EXA-01, EXA-04, EXA-10, EXU-01, EXU-02, EXU-03                                                                                                 |
| US-31 | EXU-11, EXU-12                                                                                                                                 |
| US-32 | EXU-10, EXU-11                                                                                                                                 |
| US-33 | EXA-12, EXU-11                                                                                                                                 |
| US-34 | exigences transverses seulement (EXA-01, EXA-03, EXA-05, EXA-06, EXA-19)                                                                       |
| US-35 | EXA-12                                                                                                                                         |
| US-36 | EXA-01, EXA-07, EXA-08, EXA-09                                                                                                                 |
| US-37 | EXA-01, EXA-02, EXA-07, EXA-09                                                                                                                 |
| US-38 | EXA-01, EXA-02, EXA-03, EXA-08, EXA-09                                                                                                         |
| US-39 | sans objet (journaux techniques, sans interface utilisateur)                                                                                   |
| US-40 | EXA-09                                                                                                                                         |
| US-41 | sans objet (supervision technique)                                                                                                             |
| US-42 | sans objet (hors MVP) ; exigences à reprendre à leur conception                                                                                |
| US-43 | sans objet (hors MVP) ; exigences à reprendre à leur conception                                                                                |
| US-44 | sans objet (hors MVP) ; exigences à reprendre à leur conception                                                                                |
| US-45 | sans objet (hors MVP) ; exigences à reprendre à leur conception                                                                                |
| US-46 | EXA-02, EXA-09, EXA-20                                                                                                                         |
| US-47 | EXA-02, EXA-09, EXA-20                                                                                                                         |
| US-48 | EXA-01, EXA-02, EXA-08, EXA-09, EXA-20                                                                                                         |
| US-49 | EXA-02                                                                                                                                         |
| US-50 | EXA-09, EXA-20 (l'API n'a pas d'interface ; la console affiche les versions servies)                                                           |
| US-51 | EXA-02, EXA-07, EXU-12                                                                                                                         |
| US-52 | sans objet (étude préalable, sans interface dans l'application)                                                                                |
| US-53 | sans objet (étude préalable, sans interface dans l'application)                                                                                |
| US-54 | EXA-08, EXA-10, EXA-12                                                                                                                         |

## 7. Limites

- Aucun test avec des artisans réels ni avec des personnes en situation de handicap n'est prévu
  avant la soutenance. Les tests de terrain sont simulés.
- L'accessibilité du canal vocal repose sur des exigences propres, faute d'avoir lu le chapitre 6
  de l'EN 301 549.
- Le statut de Muninn au regard de l'acte européen d'accessibilité reste à trancher par l'avis
  juridique.
- Les seuils marqués [H] (64 dp, 7:1 sur les écrans de terrain, 5 secondes, 5 points d'écart) sont
  des choix de conception, à confirmer par les entretiens de l'action 1 de l'analyse.
