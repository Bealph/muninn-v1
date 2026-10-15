"""Connexion à PostgreSQL par SQLAlchemy (pilote psycopg 3)."""

from sqlalchemy import Engine, create_engine

from muninn.core.config import get_settings


def url_sqlalchemy(url: str) -> str:
    """Rend une URL PostgreSQL utilisable par SQLAlchemy avec le pilote psycopg 3.

    `DATABASE_URL` suit le format usuel `postgresql://` ; SQLAlchemy choisirait alors psycopg2,
    absent du projet.
    """
    for prefixe in ("postgresql://", "postgres://"):
        if url.startswith(prefixe):
            return "postgresql+psycopg://" + url[len(prefixe) :]
    return url


def url_configuree() -> str:
    """Rend l'URL de `DATABASE_URL`, convertie ; erreur explicite si elle manque."""
    url = get_settings().database_url
    if url is None:
        raise RuntimeError("DATABASE_URL n'est pas définie")
    return url_sqlalchemy(url.get_secret_value())


def creer_moteur(url: str | None = None) -> Engine:
    """Crée un moteur SQLAlchemy ; par défaut sur `DATABASE_URL`."""
    return create_engine(url_sqlalchemy(url) if url else url_configuree(), pool_pre_ping=True)
