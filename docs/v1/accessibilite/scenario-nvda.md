# Parcours au lecteur d'écran NVDA (C10)

Parcours joué par le porteur, selon le protocole (section 4). Durée : environ 45 minutes. Pour
chaque étape, noter « OK » ou ce qui a été entendu de travers, dans la colonne « Observé ».

## Préparation (10 minutes)

1. Installer NVDA, dernière version, depuis <https://www.nvaccess.org/download/> (gratuit), et
   Firefox s'il n'est pas déjà installé. NVDA, dernière version, avec Firefox fait partie de
   l'environnement de référence du RGAA pour ordinateur.
2. Ouvrir Firefox sur la console de production :
   <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/>.
   Les données sont fictives (règle R9) ; aucun vrai appel n'est passé.
3. Lancer NVDA (Ctrl+Alt+N). Fermer les yeux ou détourner le regard pendant les étapes : le but est
   d'utiliser la page **à l'oreille seulement**.

Commandes utiles (touche NVDA = Insert) :

| Touche           | Effet                                                   |
| ---------------- | ------------------------------------------------------- |
| Ctrl             | Faire taire NVDA                                        |
| NVDA+Flèche bas  | Tout lire depuis la position courante                   |
| H et Maj+H       | Titre suivant, précédent ; 1, 2, 3 : titre de ce niveau |
| D                | Région suivante (navigation, contenu principal)         |
| K, F, B, T       | Lien, champ de formulaire, bouton, tableau suivant      |
| Tab et Maj+Tab   | Élément interactif suivant, précédent                   |
| NVDA+F7          | Liste des éléments (titres, liens, régions)             |
| NVDA+Espace      | Basculer entre mode navigation et mode formulaire       |
| Ctrl+Alt+flèches | Se déplacer dans un tableau, cellule par cellule        |

## Parcours

| N°  | Écran         | Action                                                                                             | Attendu                                                                                     | Observé |
| --- | ------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------- |
| 1   | Accueil       | Recharger la page (F5), écouter le début                                                           | Titre de la page « Muninn, console de démonstration », langue française                     | OK      |
| 2   | Accueil       | NVDA+F7, onglet « Régions »                                                                        | Une navigation « Pages de la console » et un contenu principal                              | OK      |
| 3   | Accueil       | Dans la navigation, Tab sur chaque lien                                                            | Cinq liens ; « Accueil » annoncé comme page courante                                        | OK      |
| 4   | Accueil       | Touche 1, puis H plusieurs fois                                                                    | Titre « Muninn », puis « Version livrée », « Essai du modèle »                              | OK      |
| 5   | Accueil       | F jusqu'au champ de question, écrire « Bonjour », choisir le modèle, B jusqu'à « Envoyer », Entrée | Chaque champ annonce son libellé ; la réponse est annoncée ou trouvable par H (« Réponse ») | OK      |
| 6   | Référentiels  | Ouvrir « Référentiels » par la navigation ; H pour lister les sections                             | « Commune », « Terme de métier », « Marché (Sirene) »                                       | OK      |
| 7   | Référentiels  | Remplir « Nom de la commune » : Montreuil ; « Chercher la commune »                                | Le résultat et sa source sont lus ; une erreur serait annoncée                              | OK      |
| 8   | Référentiels  | « Voir le marché » pour plomberie ; T pour aller au tableau, Ctrl+Alt+flèches                      | Chaque cellule est lue avec son en-tête de ligne et de colonne ; « masqué » est dit en mots | OK      |
| 9   | Agent         | Ouvrir « Agent » ; F jusqu'à « Scénario », choisir SC-01 ; « Traiter l'appel »                     | Les champs et le bouton sont annoncés ; le dossier rendu est trouvable par H                | OK      |
| 10  | Agent         | Aller au formulaire « Corriger et valider (artisan) » ; Tab sur chaque champ                       | Chaque champ annonce son libellé ; les champs « à vérifier » sont identifiables à l'oreille | OK      |
| 11  | Agent         | Corriger un champ ; « Valider le dossier »                                                         | La confirmation « Dossier validé » est annoncée ou trouvable                                | OK      |
| 12  | Démonstration | Ouvrir « Démonstration » ; écouter le titre ; F jusqu'à « Scénario »                               | « Un appel manqué chez Karim Plomberie », puis le choix du scénario                         | OK      |
| 13  | Démonstration | B jusqu'à « Lancer l'appel », Entrée ; écouter sans toucher                                        | Les phases de l'appel sont annoncées au fil de l'eau, sans couvrir la voix des téléphones   | OK      |
| 14  | Démonstration | Après l'appel, H jusqu'à « Ce que fait Muninn après l'appel »                                      | Les étapes du traitement et le dossier se lisent dans l'ordre                               | OK      |
| 15  | Démonstration | Relancer un appel, puis « Arrêter » pendant l'appel                                                | L'arrêt est possible au clavier et annoncé                                                  | OK      |
| 16  | Qualité       | Ouvrir « Qualité » ; H pour les sections                                                           | « Ce que Muninn surveille sur la dernière heure », « Alertes des dernières 24 heures »      | OK      |
| 17  | Qualité       | « Choix de la période » : changer, « Afficher »                                                    | Le changement de période est annoncé ; chaque indicateur a un nom et une valeur lisibles    | OK      |
| 18  | Toute la page | Sur deux écrans, Tab du début à la fin de la page                                                  | Aucun élément sans nom (« bouton », « lien » seuls) ; on ne reste jamais bloqué             | OK      |

## Complément ciblé (environ 15 minutes)

Ajouté après la relecture du rapport : ces étapes éprouvent les points que l'audit réservait au
lecteur d'écran et que le parcours ci-dessus ne visait pas. Même console, même préparation.

| N°  | Écran   | Action                                                                                                                                                         | Attendu                                                                                                                                                              | Observé |
| --- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| 19  | Accueil | Recharger (F5), puis Tab une fois ; Entrée sur le premier lien ; NVDA+Flèche bas                                                                               | « Aller au contenu » est le premier arrêt ; après Entrée, la lecture reprend au titre « Muninn »                                                                     | OK      |
| 20  | Accueil | Laisser la question vide, aller sur « Envoyer » (B), Entrée                                                                                                    | Le libellé dit « obligatoire » ; un message d'erreur est annoncé et le focus revient sur le champ                                                                    | OK      |
| 21  | Agent   | Choisir « Transcription saisie », laisser le champ vide, « Traiter l'appel » ; puis F jusqu'au champ                                                           | L'erreur « Transcription : le champ est vide… » est annoncée ; sur le champ, NVDA dit « non valide » et lit le message                                               | OK      |
| 22  | Agent   | Choisir « Scénario », SC-01, « Traiter l'appel » ; dans le formulaire de validation, Tab jusqu'à la case ; « Valider le dossier » sans cocher, puis en cochant | La case est lue avec « obligatoire » et « La validation est définitive… » ; sans la cocher, l'envoi est refusé et annoncé ; cochée, « Dossier validé » est trouvable | OK      |
| 23  | Qualité | Période « les dernières 24 heures » ; H jusqu'à « Les chiffres sur… », puis flèche bas jusqu'aux graphiques                                                    | Le texte d'introduction est lu avant chaque graphique ; chaque graphique est annoncé comme une image, avec son titre                                                 | OK      |
| 24  | Qualité | Aller sur « Les valeurs heure par heure (tableau) », Entrée ; T, puis Ctrl+Alt+flèches                                                                         | Le tableau s'ouvre ; chaque cellule est lue avec son heure et sa colonne                                                                                             | OK      |

## Après le parcours

Noter la version de NVDA et de Firefox, la date, la durée, et toute remarque générale (débit,
annonces superflues, endroits où l'on se perd). Me transmettre le tableau rempli : je reporte les
observations dans la grille et le rapport, sans les reformuler.

| Champ              | Valeur                    |
| ------------------ | ------------------------- |
| Date               | 05/11/2026                |
| Version de NVDA    | 2026.3                    |
| Version de Firefox | Version 159.0.1 (64 bits) |
| Durée              | 30 minutes                |
| Remarques          | RAS                       |
