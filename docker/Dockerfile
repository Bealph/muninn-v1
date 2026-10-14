# Image unique de Muninn : l'API et la console en sont deux processus (ADR-10).
# Construction en deux étapes : les outils de construction ne sont pas dans l'image finale.

FROM ghcr.io/astral-sh/uv:0.12.5 AS uv

FROM python:3.12-slim AS construction
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dépendances d'abord : cette couche reste en cache tant que le verrou ne change pas.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim AS execution
RUN useradd --create-home --uid 10001 muninn
WORKDIR /app
COPY --from=construction /app/.venv /app/.venv
ARG GIT_SHA=local
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    GIT_SHA=$GIT_SHA
USER muninn
EXPOSE 8000
# MUNINN_PROCESSUS=api (défaut) ou console : voir src/muninn/serveur.py.
CMD ["python", "-m", "muninn.serveur"]
