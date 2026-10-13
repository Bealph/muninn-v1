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
curl http://localhost:8000/health
```

La console s'ouvre sur <http://localhost:8001>.

## Développer

Prérequis : Python 3.12 et [uv](https://docs.astral.sh/uv/).

```bash
uv sync               # dépendances figées par uv.lock
uv run pytest         # tests
uv run ruff check .   # analyse statique
uv run mypy           # typage strict
```

## Documentation

| Document                                               | Contenu                                                                   |
| ------------------------------------------------------ | ------------------------------------------------------------------------- |
| [docs/roadmap.md](docs/roadmap.md)                     | Feuille de route par phase                                                |
| [docs/v1/](docs/v1/)                                   | Dossier de conception V1, couverture des compétences, feuille de route V1 |
| [docs/decisions.md](docs/decisions.md)                 | Journal des décisions du porteur                                          |
| [docs/conception/phase-0/](docs/conception/phase-0/)   | Phase 0a : stories, flux, sources, accessibilité, diagrammes              |
| [docs/suivi/competences.md](docs/suivi/competences.md) | Suivi des compétences du référentiel                                      |
| [docs/suivi/taches.md](docs/suivi/taches.md)           | Tâches faites et restant à faire                                          |
