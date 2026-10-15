"""Commande `muninn-db` : applique ou annule les migrations Alembic.

Usage : `muninn-db upgrade` (jusqu'à la dernière), `muninn-db downgrade base`, `muninn-db current`.
L'URL vient de `DATABASE_URL` ; elle doit désigner le rôle propriétaire des schémas, pas le rôle
de lecture de l'API (D-56).
"""

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

DOSSIER_MIGRATIONS = Path(__file__).parent / "migrations"


def configuration(url: str | None = None) -> Config:
    """Configuration Alembic sans fichier `alembic.ini` : tout est porté par le paquet."""
    config = Config()
    config.set_main_option("script_location", str(DOSSIER_MIGRATIONS))
    if url is not None:
        config.attributes["url"] = url
    return config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="muninn-db", description="Migrations de la base Muninn")
    sous = parser.add_subparsers(dest="action", required=True)
    monter = sous.add_parser("upgrade", help="applique les migrations")
    monter.add_argument("cible", nargs="?", default="head")
    descendre = sous.add_parser("downgrade", help="annule des migrations")
    descendre.add_argument("cible")
    sous.add_parser("current", help="affiche la révision appliquée")
    args = parser.parse_args(argv)

    config = configuration()
    if args.action == "upgrade":
        command.upgrade(config, args.cible)
    elif args.action == "downgrade":
        command.downgrade(config, args.cible)
    else:
        command.current(config)


if __name__ == "__main__":
    main()
