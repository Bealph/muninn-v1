# Pitch de Muninn en 3 minutes

**Public :** jury ou évaluateur de la formation « Dev IA agentique ».
**Durée :** 3 minutes, dont environ 30 secondes de démonstration en direct.
**Version :** 1.0, 19 octobre 2026 (sprint 4 en cours). Chiffres sourcés en fin de document.
**Débit visé :** environ 140 mots par minute. Texte à dire : 355 mots, soit environ 2 min 30, plus
15 s de manipulation pendant la démonstration, et 10 s de marge. Le texte entre guillemets est à dire ; le reste est
pour toi.

## Avant de commencer

- Ouvrir l'écran « Référentiels » de production dans un onglet et le rafraîchir :
  <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/referentiels>.
- Plan B si l'écran ne répond pas : les captures `docs/v1/sprints/sprint-3/preuves/etape-10-production-*.png`.

## 0:00 – 0:30 · Le problème

« Un artisan qui travaille seul passe ses journées sur les chantiers, les mains prises. Pendant ce
temps, son téléphone sonne, et il manque une partie de ses appels. Ce qu'il retient, il le note sur
un carnet, puis le ressaisit le soir. **Une demande oubliée, c'est un chantier perdu.** Et
l'administratif pèse : selon la CAPEB, 41 % des chefs d'entreprise du bâtiment le citent comme
source de stress. »

## 0:30 – 0:55 · La solution

« Muninn est son secrétariat automatique. Notre promesse : **il parle, Muninn se souvient.** Quand
l'artisan ne décroche pas, l'appel est renvoyé vers notre agent vocal. L'agent annonce qu'il est une
intelligence artificielle, recueille la demande et prépare un dossier : nom, téléphone, adresse,
objet, urgence. L'artisan le retrouve rangé et vérifié, et le valide d'un geste. »

## 0:55 – 1:10 · Le marché

« Le besoin est large. Rien qu'en plomberie, chauffage, électricité et serrurerie, notre propre
chaîne de données recense, sur le stock Sirene, 260 926 établissements actifs. Nous testons un prix
de 39 à 49 euros par mois. »

## 1:10 – 2:15 · La V1, et la démonstration

« Ce que je vous présente, c'est la V1, déployée sur Azure. Elle couvre tout le parcours : un appel
simulé, joué à deux voix puis transcrit ; un **agent outillé** qui extrait le dossier et consulte
nos référentiels quand une information manque ; des **garde-fous** à l'entrée et à la sortie, contre
la manipulation, la fuite de données ou une odeur de gaz ; une console où l'artisan valide ; une
vigie de la qualité. La vraie téléphonie et l'application mobile sont conçues, pas construites. »

**[Démonstration, 30 secondes]** Dans le champ « commune », taper « Montreuil », valider ; puis
« Vincennes ».

« Voici ce que l'agent consulte, en production. « Montreuil » : trois communes, dans trois
départements. Sans indice dans l'appel, l'agent ne choisit pas : il signale le dossier.
« Vincennes » : un seul code postal, 94300, avec sa source et sa licence. »

## 2:15 – 2:35 · La rigueur

« Derrière, une vraie chaîne d'ingénierie : six sources de données ouvertes, rechargées en une
commande ; une intégration continue bloquante, puis une livraison automatique en production ; un
modèle de langage choisi par un banc d'essai mesuré, pas sur une impression. L'audio et la
transcription sont détruits après l'extraction. »

## 2:35 – 2:50 · Où nous en sommes

« Les sprints 2 et 3 sont livrés, en production. Le sprint 4, l'agent et ses garde-fous, est en
cours ; le sprint 5 apportera la voix et la démonstration complète. **L'artisan parle. Muninn se
souvient.** Merci. »

## Après le sprint 5

Remplacer la démonstration par un appel simulé dans la console : le scénario SC-07 (« à Montreuil,
dans le 9-3 »), où l'agent déduit lui-même la commune 93048 et le code postal 93100. Remplacer aussi
« le sprint 4 est en cours » par l'état du moment.

## Ce que le pitch ne dit pas, pour répondre juste aux questions

- Le chiffre de Sirene compte des établissements actifs, quelle que soit leur taille, et non des
  artisans seuls.
- Le prix de 39 à 49 euros est une hypothèse à tester, pas un prix validé.
- Dans la V1, la console reçoit les dossiers en clair : c'est un écart assumé (P-03), car la
  console joue le rôle du téléphone de l'artisan.

## Sources des chiffres

| Chiffre                              | Source                                                                                     |
| ------------------------------------ | ------------------------------------------------------------------------------------------ |
| Carnet, ressaisie le soir            | Analyse stratégique, persona P1 et parcours (§ 3) ; dossier V1, § 1                        |
| 41 % (poids de l'administratif)      | CAPEB, 11e baromètre ARTI Santé, juin 2025 (analyse stratégique, § 1)                      |
| 260 926 établissements actifs        | Stock Sirene du 1er octobre 2026, NAF 43.22A, 43.22B, 43.21A et 43.32B (sprint 3, étape 6) |
| 39 à 49 euros par mois               | Analyse stratégique, réponse courte, point 5                                               |
| Trois « Montreuil », Vincennes 94300 | API Géo et codes postaux, chargés en production (sprint 3, étape 10)                       |
| Six sources ouvertes, une commande   | `docs/v1/sprints/sprint-3/sources.md` ; `muninn-ingestion tout`                            |
| Banc d'essai du modèle               | `docs/v1/banc-essai-t06/rapport.md` (48 extractions, D-61)                                 |
