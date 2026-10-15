"""Téléchargement tracé d'un fichier source : adresse, date, empreinte, taille."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime

import httpx

from muninn import __version__

# Politique des fournisseurs (registre des sources du sprint 3) : agent identifié,
# requêtes en série.
# Format exigé par Wikimedia : <client>/<version> (<contact>) ; contact choisi par le porteur.
USER_AGENT = f"Muninn/{__version__} (https://github.com/Bealph) httpx"


@dataclass(frozen=True)
class FichierRecu:
    url: str  # adresse appelée, citée par la traçabilité
    url_finale: str  # après redirections
    contenu: bytes
    date_source: date | None  # en-tête Last-Modified, s'il existe
    recupere_le: datetime

    @property
    def sha256(self) -> bytes:
        return hashlib.sha256(self.contenu).digest()

    @property
    def taille(self) -> int:
        return len(self.contenu)


def client_http() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=httpx.Timeout(60.0)
    )


def telecharger(url: str, client: httpx.Client | None = None) -> FichierRecu:
    """Télécharge un fichier entier ; erreur HTTP levée telle quelle."""
    proprietaire = client is None
    client = client or client_http()
    try:
        reponse = client.get(url)
        reponse.raise_for_status()
    finally:
        if proprietaire:
            client.close()
    modifie = reponse.headers.get("Last-Modified")
    return FichierRecu(
        url=url,
        url_finale=str(reponse.url),
        contenu=reponse.content,
        date_source=parsedate_to_datetime(modifie).date() if modifie else None,
        recupere_le=datetime.now(UTC),
    )
