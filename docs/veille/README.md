# Veille technique et réglementaire de Muninn (C6)

La veille tient le projet à jour sur ce qui peut changer ses choix : les services d'IA qu'il
utilise, la façon de les évaluer et de les observer, et les règles qui encadrent un assistant
téléphonique. Chaque information retenue aboutit à une fiche ; les fiches nourrissent des
synthèses datées, chacune terminée par une recommandation pour le projet.

## Thèmes

| Thème                       | Ce qu'on surveille                                                                         | Lien avec Muninn                            |
| --------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------- |
| Modèles et services d'IA    | Modèles A et B, Azure AI Foundry, Azure AI Speech, Container Apps                          | D-44 à D-46, D-50, D-61                     |
| Évaluation et observabilité | Langfuse, conventions OpenTelemetry pour l'IA générative, méthodes d'évaluation des LLM    | composants V-08, V-13 de la V1 ; D-64, D-87 |
| Agents et extraction        | Appel d'outils, sortie structurée, garde-fous                                              | composants V-07, V-11 de la V1              |
| Chaîne de livraison         | GitHub Actions (planification, environnements, OIDC)                                       | C13, C19, C20                               |
| Règlement européen sur l'IA | Obligations de transparence, calendrier d'application, lignes directrices de la Commission | Annonce de l'assistant (D-04)               |
| Données personnelles        | Recommandations de la CNIL, IA et RGPD, enregistrement des appels                          | Registre RGPD, D-32, D-89                   |
| Démarchage et téléphonie    | Consentement au démarchage, numérotation, renvoi d'appel                                   | Usage réel du raccordement (D-68)           |
| Accessibilité               | WCAG, RGAA                                                                                 | C10                                         |
| Marché et concurrence       | Réceptionnistes IA pour artisans, éditeurs de devis et de facturation, téléphonie IA       | Positionnement ; analyse stratégique        |

La veille du marché et de la concurrence a commencé au cadrage, avant ce dispositif : l'analyse
stratégique du 12 octobre 2026 (marché, concurrents, tendances, contraintes, sources citées) et les
captures des sites concurrents du 23 octobre, dans le dossier du concept (hors du dépôt). Ajoutée
comme thème le 9 novembre, à la suite de la séance avec le formateur ; elle se lit à la main, chaque
mois, sur les sites des concurrents cités par l'analyse.

## Le dispositif

Temps consacré : une heure par jour. S'y ajoutent des chaînes YouTube spécialisées, suivies hors
du registre : une information qui en vient est confirmée à la source primaire avant d'entrer
dans une fiche.

1. **Sources** : le registre `sources.md` (type, fiabilité, fréquence de lecture) et son export
   `sources.opml`, à importer dans un lecteur de flux.
2. **Collecte** : chaque semaine, `python infra/veille/collecter.py` lit les 11 flux et écrit les
   nouveautés de la période dans `collecte/AAAA-MM-JJ-<jours>j.md` (arXiv filtré par mots-clés ; les mots que
   la règle du dépôt exclut sont réglés sur le poste par `VEILLE_EXCLUSIONS`, jamais versionnés) ; les
   sources sans flux se lisent à la main, à leur fréquence. Une information est retenue si elle
   peut changer un choix, une mesure ou une obligation du projet.
3. **Fiche** : une par information retenue, dans `fiches/`, sur le modèle `fiches/MODELE.md` :
   date, source, résumé, impact sur Muninn, suite. Une affirmation réglementaire est vérifiée sur
   le texte officiel, dont la page est citée.
4. **Synthèse** : toutes les deux semaines, ou dès qu'une fiche change un choix, une synthèse
   datée dans `syntheses/`, terminée par une recommandation, reliée à une décision D-xx si elle
   est retenue.
5. **Partage et travail collectif** : le dépôt est le canal, et la vitrine de la veille le support.
   Chaque synthèse est présentée en séance courte (10 à 15 minutes) à au moins une personne
   extérieure au projet, qui peut proposer des sources, contester une recommandation ou poser une
   question ; les recommandations y sont discutées, puis je les tranche. Première séance avec le
   formateur le 6 novembre, sur la synthèse S-2026-11-05 (`seances/2026-11-06.md`) ; la
   présentation à l'oral blanc du 13 novembre en fait une seconde. La trace de chaque séance
   (participants par leur rôle, sans nom ; apports ; décisions et leurs suites) va dans `seances/`,
   sur le modèle
   `seances/MODELE.md`.
6. **Vitrine** : après chaque collecte, `python infra/veille/vitrine.py` régénère
   `vitrine.html`, une page qui présente le rapport (recommandations, fiches en clair et version
   technique, couverture des thèmes) et la collecte à trier ; elle est republiée au même lien
   privé. Le test `tests/test_vitrine.py` échoue si la page n'a pas été régénérée.

## Règles

- Une source sans date ou sans auteur identifiable n'est pas citée seule.
- Ce qui vient d'une source de presse ou d'un blog est confirmé à la source primaire avant
  d'entrer dans une recommandation.
- Les fiches ne contiennent ni secret ni donnée personnelle.
