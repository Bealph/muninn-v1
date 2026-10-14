"""Lanceur de l'image : un seul point d'entrée, l'API ou la console selon MUNINN_PROCESSUS.

L'image est unique (ADR-10) ; le processus se choisit par une variable d'environnement plutôt
que par une commande surchargée, plus simple à déclarer dans Container Apps et docker compose.
"""

import os

import uvicorn

PROCESSUS = {"api": "muninn.api.main:app", "console": "muninn.console.main:app"}


def cible(nom: str) -> str:
    """Rend l'application à servir ; refuse un nom inconnu plutôt que de deviner."""
    if nom not in PROCESSUS:
        raise SystemExit(f"MUNINN_PROCESSUS inconnu : {nom!r} (attendu : api ou console).")
    return PROCESSUS[nom]


def main() -> None:
    uvicorn.run(
        cible(os.environ.get("MUNINN_PROCESSUS", "api")),
        host="0.0.0.0",  # noqa: S104 (conteneur : écoute sur toutes les interfaces)
        port=int(os.environ.get("PORT", "8000")),
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
