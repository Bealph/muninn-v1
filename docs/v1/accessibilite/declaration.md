# Déclaration d'accessibilité : console de démonstration de Muninn

Établie le 5 novembre 2026, selon le modèle de déclaration publié avec le RGAA
(<https://accessibilite.numerique.gouv.fr/ressources/modele-de-declaration/>).

Cette déclaration s'applique à la **console web de démonstration et de test** de Muninn :
<https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/>. La
console n'est pas destinée à l'artisan : l'interface prévue pour lui est une application mobile,
hors de la version actuelle et hors du champ du RGAA 4.1. À ce stade, Muninn n'est pas soumis à
l'obligation d'accessibilité (document de conception 04, sections 2.2 et 2.3, sous réserve d'avis
juridique) : cette déclaration est volontaire, établie dans le cadre d'un projet de certification.

## État de conformité

La console de démonstration de Muninn est **totalement conforme** au référentiel général
d'amélioration de l'accessibilité (RGAA), version 4.1.2, sur l'échantillon audité, parcours au
lecteur
d'écran compris (rapport d'audit, section 5). Niveau visé
par la conception : WCAG 2.2, niveau AA.

## Résultats des tests

L'audit de conformité que j'ai réalisé révèle que **100 % des critères du RGAA version 4 sont
respectés** sur l'échantillon (72 critères applicables, 34 non applicables). Taux moyen : 100 %.
Avant corrections (audit initial du 3 novembre 2026), le taux global était de 77,8 %.

## Contenus non accessibles

- **Non-conformités :** aucune sur l'échantillon audité.
- **Dérogations pour charge disproportionnée :** aucune.
- **Contenus non soumis à l'obligation d'accessibilité :** sans objet.
- **Défauts connus, hors critères :** deux remarques, décrites dans le rapport d'audit
  (section 7) : pastilles coupées au milieu des mots avec le texte agrandi à 200 % ; formulaire du
  dossier perdu si la confirmation manque et que la validation du navigateur est contournée.
- **Pages types de l'échantillon RGAA absentes de la console :** contact, mentions légales,
  accessibilité, plan du site, aide, authentification. Cette déclaration n'est pas publiée dans la
  console : elle est jointe au rapport d'audit.

## Établissement de cette déclaration d'accessibilité

### Technologies utilisées

HTML5, CSS, JavaScript, SVG.

### Environnement de test

Firefox 159.0.1 avec NVDA 2026.3 sous Windows 11, combinaison de la base de référence du RGAA pour
ordinateur ; Chromium 153 (Playwright) pour les mesures outillées.

### Outils pour évaluer l'accessibilité

axe-core (WCAG 2.2 AA, dont la taille des cibles) ; validateur Nu du W3C, lancé en local dans son
image officielle ; inspection du code ; calcul des contrastes selon la formule des WCAG (luminance
relative), par script ; essais au clavier seul, à 320 px de large, avec le texte agrandi à 200 % et
les espacements du texte modifiés.

### Pages ayant fait l'objet de la vérification

- Accueil : `/`
- Référentiels : `/referentiels`
- Agent : `/agent`
- Démonstration : `/demonstration`
- Qualité : `/qualite`

## Retour d'information et contact

Si vous n'arrivez pas à accéder à un contenu ou à un service de la console, vous pouvez me
contacter pour obtenir une alternative accessible ou le contenu sous une autre forme : par courriel
à
<adiallo.ext@simplonformations.co>.

## Voies de recours

Sans objet : la console de démonstration n'est pas soumise à l'obligation d'accessibilité
(article 47 de la loi n° 2005-102).
