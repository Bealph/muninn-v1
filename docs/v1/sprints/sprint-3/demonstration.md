# Démonstration du sprint 3 devant l'évaluateur

**But :** faire constater par l'évaluateur, en direct et en production, chacun des six critères de
l'évaluation par le pair. Pour chaque critère : ce que l'évaluateur constate, ce que je fais, la
durée, et la preuve versionnée qui sert de secours si le direct échoue.

**Adresses de production :**

- écran : <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/referentiels> ;
- API et Swagger : <https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io/docs>.

## 1. Préparation, 15 minutes avant

1. Ouvrir l'écran et `/docs` une première fois, puis 5 minutes avant de commencer : hors trafic,
   l'application s'endort, et le premier appel peut dépasser 20 secondes.
2. Rejouer le jeu de questions : `make questions URL=https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io`
   (attendu : 10 sur 10).
3. Ouvrir dans le navigateur : l'onglet Actions (workflow « donnees »), `sources.md`, `rgpd.md`,
   et le jeu de questions `questions-demonstration.md`, à proposer à l'évaluateur s'il manque d'idées.

## 2. Ordre de passage

Le rejeu des données dure environ 3 minutes, runner compris : je le lance en premier et je le
laisse tourner pendant les critères suivants.

| Ordre | Critère | Durée en direct | Ce qui tourne en arrière-plan |
| ----- | ------- | --------------- | ----------------------------- |
| 1     | P4      | 1 min           | Rejeu des données (3 min)     |
| 2     | P5      | 1 min           | Rejeu                         |
| 3     | P2      | 4 min           | Rejeu                         |
| 4     | P3      | 3 min           | Aucun                         |
| 5     | P4, fin | 1 min           | Aucun                         |
| 6     | P1      | 3 min           | Aucun                         |
| 7     | P6      | 2 min           | Aucun                         |

## 3. Les six critères

### P1. Les sources sont identifiées et licites

- **L'évaluateur constate :** le registre des six sources (`sources.md`) donne pour chacune sa
  licence, son adresse, ses conditions d'usage, revérifiées le 15 octobre 2026 contre les pages
  officielles. La note `rgpd.md` dit, source par source, s'il y a des données personnelles :
  aucune pour cinq d'entre elles (non-applicabilité argumentée), des entrepreneurs individuels
  dans Sirene (minimisation appliquée : colonnes lues, aucun fichier sur disque, SIREN en mémoire
  seulement, agrégats sous secret statistique).
- **Je fais :** j'ouvre les deux documents ; je montre, dans l'écran « marché », une cellule
  « masqué (secret statistique) ».
- **Secours :** les deux documents eux-mêmes.

### P2. Les réponses sont traçables

- **L'évaluateur constate :** il tape lui-même une commune dans l'écran de production. La réponse
  donne, pour chaque commune, la table et la clé de la ligne en base, et cite ses sources : titre,
  éditeur, licence, date de la source, date de chargement, version, avec un lien vers le fichier
  d'origine. Pour un terme de métier, le lien mène à la page du Wiktionnaire.
- **Je fais :** je lui laisse le clavier ; s'il n'a pas d'idée, je propose « Montreuil » (trois
  communes) puis « cumulus » en plomberie. Il suit le lien de la source jusqu'au fichier de
  l'INSEE ou à la page du Wiktionnaire.
- **Secours :** `preuves/etape-10-production-commune.png` ; Swagger (`/docs`), même réponse en JSON.

### P3. Le refus hors corpus est démontré

- **L'évaluateur constate :** il pose lui-même une question hors sujet. Une commune qui n'existe
  pas, un mot sans rapport avec la plomberie ou une question libre donnent « Refus : hors des
  données », avec le motif et aucune valeur proposée ; un métier non couvert donne « Refus : hors
  du périmètre » ; un nom et un code postal qui ne vont pas ensemble donnent « incohérents ».
- **Je fais :** je lui laisse le clavier ; sinon : « Gotham City », « ordinateur » en plomberie,
  « disjoncteur » en électricité, « Bagnolet » avec 93100.
- **À dire :** le seuil du terme le plus proche (0,55) a été calibré par un protocole écrit et
  commité avant la mesure (`calibration-seuil.md`).
- **Secours :** `preuves/etape-10-production-refus.png` et les captures de l'étape 8.

### P4. Le pipeline est rejouable en une commande

- **L'évaluateur constate :** une seule commande relance tout le chargement en production, sans
  le poste : la tâche Container Apps fait migrations, rôles et ingestion, puis le jeu de questions
  est rejoué. Les cinq sources sont « inchangée » : le rejeu ne crée aucun doublon. La tâche est
  aussi planifiée le 3 de chaque mois (D-60).
- **Je fais :** `gh workflow run donnees -f environnement=production`, ou l'onglet Actions ;
  au retour, j'ouvre le journal de l'exécution.
- **Secours :** exécution 38874739291 du 16 octobre 2026 (83 s, 10 sur 10) ;
  `preuves/etape-10-production.md`. En local : `make ingerer`.

### P5. Tout est visible en production

- **L'évaluateur constate :** l'écran et l'API tournent sur Azure, livrés par la chaîne du
  sprint 2 ; aucun notebook. `/version` rend le commit servi.
- **Je fais :** je montre les deux adresses et le dernier passage de la chaîne dans Actions.
- **Secours :** `compte-rendu.md`, section 4.

### P6. Le journal des retours est tenu

- **L'évaluateur constate :** `retours.md` liste chaque retour du pair, sa décision (traité,
  reporté ou écarté), sa justification et le lien qui l'atteste.
- **État :** en attente des retours du pair ; à remplir avant la démonstration.

## 4. Après la démonstration

- Vérifier que le rejeu a réussi et que le jeu de questions est à 10 sur 10.
