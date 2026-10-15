# Muninn

Application mobile de secrétariat automatique pour l'artisan qui travaille seul.
Promesse : **« Il parle, Muninn se souvient. »**

Ce dépôt contient la conception puis le développement du back-end et d'une interface de
démonstration.

## Lancer le projet en local

Prérequis : Docker et docker compose.

```bash
cp .env.example .env          # puis remplir les valeurs locales ; .env n'est jamais versionné
docker compose up --build -d  # API sur le port 8000, console sur le port 8001, PostgreSQL
docker compose run --rm api muninn-db upgrade  # schémas des référentiels (ref, market)
curl http://localhost:8000/health
```

La console s'ouvre sur <http://localhost:8001> : elle affiche la version livrée et envoie une
question au modèle de langage à travers l'API.

Par défaut, `LLM_FOURNISSEUR=faux` : la réponse est simulée, sans réseau. Pour appeler le vrai
modèle, renseigner dans `.env` `LLM_FOURNISSEUR=azure`, `AZURE_AI_ENDPOINT` et les modèles A et B.
Hors conteneur, l'authentification passe par `az login` ; dans un conteneur local, par
`AZURE_AI_API_KEY`.

## Développer

Prérequis : Python 3.12 et [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                # dépendances figées par uv.lock
uv run playwright install chromium     # une fois : navigateur du contrôle d'accessibilité
uv run pytest                          # tests, dont le contrôle d'accessibilité axe-core (WCAG 2.2 AA)
uv run ruff check .                    # analyse statique
uv run mypy                            # typage strict
```

## Documentation

| Document                                                                   | Contenu                                                                   |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [docs/roadmap.md](docs/roadmap.md)                                         | Feuille de route par phase                                                |
| [docs/v1/](docs/v1/)                                                       | Dossier de conception V1, couverture des compétences, feuille de route V1 |
| [docs/decisions.md](docs/decisions.md)                                     | Journal des décisions du porteur                                          |
| [docs/decisions-detaillees.md](docs/decisions-detaillees.md)               | Décisions détaillées : problème, décision, raisons, limites               |
| [docs/sujets-detailles.md](docs/sujets-detailles.md)                       | Raccordement téléphonique, critères CA-1 à CA-8, règles R1 à R10          |
| [docs/reconstruction.md](docs/reconstruction.md)                           | Reconstruire le projet, l'infrastructure et la chaîne depuis le dépôt     |
| [docs/conception/sources_de_donnees/](docs/conception/sources_de_donnees/) | Phase 0a : stories, flux, sources, accessibilité, diagrammes              |
| [docs/suivi/competences.md](docs/suivi/competences.md)                     | Suivi des compétences du référentiel                                      |
| [docs/suivi/taches.md](docs/suivi/taches.md)                               | Tâches faites et restant à faire                                          |
