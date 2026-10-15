"""Environnement Alembic : migrations écrites en SQL, sans modèle ORM."""

from alembic import context
from sqlalchemy import create_engine, pool

from muninn.db.connexion import url_configuree, url_sqlalchemy

config = context.config
url_passee = config.attributes.get("url")
url = url_sqlalchemy(url_passee) if url_passee else url_configuree()


def executer() -> None:
    if context.is_offline_mode():
        context.configure(url=url, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    # Aucune connexion gardée après la migration.
    moteur = create_engine(url, poolclass=pool.NullPool)
    with moteur.connect() as connexion:
        context.configure(connection=connexion, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()
    moteur.dispose()


executer()
