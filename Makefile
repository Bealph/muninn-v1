# Commandes courantes de Muninn. `make` ou `make aide` liste les cibles.
# Shell POSIX requis : sous Windows, lancer depuis Git Bash. La CI appelle les mêmes cibles.

.DEFAULT_GOAL := aide
.PHONY: aide installer format lint types tests verifier base-demarrer base-arreter tests-base tests-conteneur         migrer ingerer calibrer questions api console image

# PostgreSQL 16 jetable pour le poste (identifiants d'essai, jamais ceux d'Azure).
PG_CONTENEUR ?= muninn-pg-essai
PG_PORT ?= 15432
PG_URL ?= postgresql://essai:essai-local@127.0.0.1:$(PG_PORT)
BASE ?= muninn
PORT_API ?= 8000
PORT_CONSOLE ?= 8001

aide: ## Liste les cibles
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /	/' | expand -t 16

installer: ## Installe les dépendances (verrou figé) et le navigateur du contrôle d'accessibilité
	uv sync --frozen
	uv run playwright install chromium

format: ## Formate le code et applique les corrections sûres de ruff
	uv run ruff format .
	uv run ruff check --fix .

lint: ## Analyse statique et contrôle du format, sans rien modifier
	uv run ruff check .
	uv run ruff format --check .

types: ## Typage strict (mypy)
	uv run mypy

tests: ## Tests ; ceux qui demandent une base sont ignorés sans TEST_DATABASE_URL
	uv run pytest -ra

verifier: lint types tests-base ## Ce que vérifie la CI, base comprise

base-demarrer: ## Démarre le PostgreSQL local (le crée au premier appel)
	@docker start $(PG_CONTENEUR) > /dev/null 2>&1 || docker run -d --name $(PG_CONTENEUR) 	  -e POSTGRES_USER=essai -e POSTGRES_PASSWORD=essai-local -e POSTGRES_DB=$(BASE) 	  -p 127.0.0.1:$(PG_PORT):5432 postgres:16-alpine > /dev/null
	@until docker exec $(PG_CONTENEUR) pg_isready -U essai -d $(BASE) > /dev/null 2>&1; do sleep 1; done
	@echo "PostgreSQL disponible : $(PG_URL)/$(BASE)"

base-arreter: ## Arrête le PostgreSQL local, ses données sont gardées
	docker stop $(PG_CONTENEUR)

tests-base: base-demarrer ## Tests, base comprise : aucun test de base n'est ignoré
	TEST_DATABASE_URL=$(PG_URL)/postgres MUNINN_TESTS_BASE=obligatoire uv run pytest -ra

# Le poste bloque désormais les extensions compilées non signées (SQLAlchemy, psycopg, DuckDB,
# constaté le 23 octobre 2026) : la suite tourne alors dans un conteneur Linux, comme en CI. La base
# est jointe par le réseau (host.docker.internal), pas en local : le mot de passe y est vérifié.
tests-conteneur: base-demarrer ## Tests, base comprise, dans un conteneur Linux (même uv que la CI)
	MSYS_NO_PATHCONV=1 docker run --rm -v "$$(pwd -W 2>/dev/null || pwd)":/app -w /app -v muninn-uv-cache:/root/.cache/uv -v muninn-pw-cache:/root/.cache/ms-playwright -e UV_PROJECT_ENVIRONMENT=/opt/venv -e UV_LINK_MODE=copy -e MUNINN_TESTS_BASE=obligatoire -e TEST_DATABASE_URL=postgresql://essai:essai-local@host.docker.internal:$(PG_PORT)/postgres python:3.12.10-slim-bookworm sh -c "pip install -q uv==0.12.5 && uv sync --frozen -q && uv run playwright install --with-deps chromium > /dev/null && uv run pytest -q -ra -p no:cacheprovider $(ARGS)"

migrer: base-demarrer ## Applique les migrations à la base locale
	DATABASE_URL=$(PG_URL)/$(BASE) uv run muninn-db upgrade

ingerer: migrer ## Charge les cinq sources dans la base locale (environ 4 min, réseau requis)
	DATABASE_URL=$(PG_URL)/$(BASE) GIT_SHA=$$(git rev-parse --short HEAD) uv run muninn-ingestion tout

calibrer: base-demarrer ## Mesure le seuil du lexique sur le jeu étiqueté (protocole du sprint 3)
	DATABASE_URL=$(PG_URL)/$(BASE) uv run python -m muninn.referentiels.calibration

questions: ## Rejoue le jeu de questions de démonstration (URL=adresse de l'API, locale par défaut)
	uv run muninn-questions $(or $(URL),http://127.0.0.1:$(PORT_API))

api: base-demarrer ## Lance l'API sur la base locale (port 8000)
	DATABASE_URL=$(PG_URL)/$(BASE) MUNINN_PROCESSUS=api PORT=$(PORT_API) uv run python -m muninn.serveur

console: ## Lance la console, branchée sur l'API locale (port 8001)
	MUNINN_PROCESSUS=console PORT=$(PORT_CONSOLE) API_BASE_URL=http://127.0.0.1:$(PORT_API) 	  uv run python -m muninn.serveur

image: ## Construit l'image Docker, étiquetée par le commit
	docker build -f docker/Dockerfile --build-arg GIT_SHA=$$(git rev-parse HEAD) -t muninn:local .
