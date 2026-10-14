# Reconstruire Muninn depuis le dépôt

Procédure pour repartir d'un clone neuf : lancer le projet en local, puis, si besoin, recréer
l'infrastructure Azure et les réglages GitHub dont dépend la chaîne de livraison. Aucun fichier
extérieur au dépôt n'est nécessaire, hormis les secrets listés ci-dessous.

Vérifiée le 14 octobre 2026 depuis un clone neuf : `docs/v1/sprints/sprint-2/preuves/etape-9-reconstruction.md`.

## Ce qui n'est pas dans le dépôt

| Élément                       | Où il vit                                      | Nécessaire pour                       |
| ----------------------------- | ---------------------------------------------- | ------------------------------------- |
| `.env`                        | Poste, copié de `.env.example`                 | Local ; la clé du LLM est facultative |
| Mot de passe PostgreSQL       | Gestionnaire de mots de passe du porteur       | Scripts Azure 01 et 03                |
| Adresse des alertes de budget | Porteur                                        | Script Azure 04                       |
| Accès Azure                   | `az login`, propriétaire du groupe `adialloRG` | Scripts Azure                         |
| Accès GitHub                  | `gh auth login`, administrateur du dépôt       | Réglages GitHub                       |

## Prérequis du poste

Git, Docker et docker compose ; pour développer : Python 3.12 et uv ; pour l'infrastructure :
Azure CLI avec l'extension `containerapp` (version épinglée dans `.github/workflows/ci.yml`) et
GitHub CLI.

Réglage local recommandé après le clonage : `git config user.email
"60009382+Bealph@users.noreply.github.com"`, pour ne pas publier d'adresse personnelle.

## 1. Lancer le projet en local

```bash
git clone https://github.com/Bealph/Muninn.git && cd Muninn
cp .env.example .env
docker compose up --build -d          # API :8000, console :8001, PostgreSQL
```

Le fournisseur de LLM par défaut est le faux fournisseur : aucune clé n'est nécessaire.

Pour développer :

```bash
uv sync --frozen
uv run playwright install chromium
uv run pytest && uv run ruff check . && uv run mypy
```

## 2. Recréer l'infrastructure Azure

Dans Git Bash, à la racine du dépôt, sur un commit de `main`, dans un seul terminal :

```bash
az login
python infra/azure/verifier-options.py infra/azure/*.sh   # « options absentes : 0 »
export POSTGRES_MOT_DE_PASSE="..."   # celui du gestionnaire de mots de passe, ou un nouveau
export COURRIEL_ALERTE="..."
bash infra/azure/00-foundry.sh       # ressource Foundry et modèles A et B
bash infra/azure/01-socle.sh         # registre, environnement, identités, PostgreSQL
bash infra/azure/02-image-initiale.sh
bash infra/azure/03-applications.sh  # applications, droits, confiance OIDC
bash infra/azure/04-budget.sh
```

Chaque script laisse intactes les ressources existantes. Détail, coûts et risques :
`infra/azure/README.md`.

## 3. Rétablir les réglages GitHub

```bash
gh auth login
bash infra/github/configurer.sh      # variables Azure, environnements, protection de main
```

## 4. Redéployer

Toute fusion dans `main` relance la chaîne : `verdict`, puis livraison en préproduction et en
production. Pour livrer sans changement de code, relancer la dernière exécution du workflow `ci`
sur `main` (onglet Actions, « Re-run all jobs »).
