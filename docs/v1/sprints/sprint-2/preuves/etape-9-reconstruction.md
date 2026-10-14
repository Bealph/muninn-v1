# Preuve de la reconstruction depuis un clone neuf (sprint 2, étape 9, critère P5)

**Date :** 14 octobre 2026
**Résultat :** depuis un clone neuf, sans autre fichier qu'un `.env` copié de `.env.example`, le
projet se lance en local et ses tests passent. Les réglages Azure et GitHub se rétablissent par
des scripts du dépôt. Cette preuve a été rédigée, commitée et poussée depuis ce clone : sa fusion
a relancé la chaîne jusqu'à la production.

## Protocole

1. Cloner `Bealph/Muninn` dans un dossier vierge, hors du dossier de travail habituel.
2. Vérifier que le clone ne contient aucun fichier local : ni `.env`, ni outillage, ni hooks.
3. Suivre `README.md` à la lettre : `cp .env.example .env`, construction de l'image **sans
   cache**, `docker compose up`.
4. Suivre la voie développement : `uv sync --frozen`, tests, ruff, mypy.
5. Combler ce qui manquait au dépôt pour une reconstruction complète, puis lancer ces scripts
   depuis le clone.
6. Rédiger la procédure dans le clone, la pousser depuis le clone et la fusionner : la chaîne
   doit livrer sans intervention.

## Constats

| Étape                                  | Résultat                                                                                 |
| -------------------------------------- | ---------------------------------------------------------------------------------------- |
| Clonage                                | 4 s ; commit `e495fee` ; aucun `.env`, aucun outil local, aucun hook                     |
| Image construite sans cache            | 26 s                                                                                     |
| `docker compose up`                    | API, console et PostgreSQL démarrés ; PostgreSQL `healthy`                               |
| API                                    | `/health` : `ok` ; `/version` rend la version et le SHA                                  |
| Console                                | Page affichée ; essai du modèle : « Réponse simulée (7 caractères reçus). »              |
| `uv sync --frozen`, tests, lint, types | 22 tests réussis ; ruff et mypy sans erreur ; 39 s au total                              |
| `00-foundry.sh` (nouveau)              | Ressource et deux déploiements trouvés, laissés tels quels                               |
| `infra/github/configurer.sh` (nouveau) | Variables, environnements et protection de `main` réécrits à l'identique, puis relus     |
| Fusion de la procédure                 | Voir la PR de cette preuve : `verdict`, puis livraison en préproduction et en production |

## Ce qui manquait au dépôt, et a été ajouté

- **Réglages GitHub** : la protection de `main`, les environnements de livraison et les variables
  Azure avaient été appliqués à la main. Ils sont désormais dans `infra/github/configurer.sh`.
- **Ressource Foundry et modèles** : créés dans le portail par le porteur. Ils sont désormais dans
  `infra/azure/00-foundry.sh`, avec les réglages relevés sur l'existant (format, version,
  capacité, option de mise à niveau, politique de filtrage).

## Limites

- Le chemin de création des scripts Azure n'a été exécuté qu'une fois, lors de la mise en place
  (étape 5). Celui de `00-foundry.sh` ne l'a jamais été, puisque la ressource existe. Seul leur
  passage sur l'existant est prouvé ici.
- La voie développement a utilisé le navigateur de test déjà installé sur le poste. Sur une
  machine neuve, `uv run playwright install chromium` le télécharge (environ 115 Mo).
- Le contrôle de reconstruction a été fait sur le poste du porteur, pas sur une machine neuve :
  Docker, uv, az et gh y étaient déjà installés.
