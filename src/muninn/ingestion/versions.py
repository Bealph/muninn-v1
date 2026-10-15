"""Versions des jeux de référence : enregistrement, contrôles, publication.

Cycle d'une version (phase 1, document 02, section 8) : `candidate` à l'écriture, puis
`published` si les contrôles bloquants passent, `failed` sinon. La publication retire la version
précédente dans la même transaction : à tout instant, une seule version est servie, et une erreur
laisse la précédente intacte.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

import psycopg

from muninn.core.config import get_settings
from muninn.ingestion.telechargement import FichierRecu

Motif = Literal["bad_format", "bad_encoding", "unknown_commune", "duplicate", "missing_field"]
Connexion = psycopg.Connection[tuple[Any, ...]]


@dataclass(frozen=True)
class Rejet:
    ligne: int  # numéro de ligne du fichier, en-tête compris
    motif: Motif
    detail: str  # extrait de la ligne : donnée publique


@dataclass
class Lecture[T]:
    """Résultat de la lecture d'un fichier : lignes gardées, rejetées, filtrées."""

    lignes: list[T] = field(default_factory=list)
    rejets: list[Rejet] = field(default_factory=list)
    filtrees: int = 0
    lues: int = 0
    rapport: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Controle:
    """Contrôle d'exactitude (phase 1, document 04) : bloquant ou seulement rapporté."""

    cas: str  # identifiant VD
    reussi: bool
    bloquant: bool
    detail: str


@dataclass(frozen=True)
class Resultat:
    jeu: str
    statut: Literal["inchange", "candidate", "published", "failed"]
    version_id: int | None
    lues: int = 0
    chargees: int = 0
    filtrees: int = 0
    rejetees: int = 0
    controles: tuple[Controle, ...] = ()


def connecter() -> Connexion:
    """Connexion d'ingestion, sur `DATABASE_URL` (rôle d'écriture en production).

    En autocommit : chaque `conn.transaction()` est alors une vraie transaction, et non un point
    de sauvegarde dans une transaction ouverte par une lecture. Une version est ainsi publiée ou
    abandonnée seule, sans dépendre du sort des autres sources.
    """
    url = get_settings().database_url
    if url is None:
        raise RuntimeError("DATABASE_URL n'est pas définie")
    return psycopg.connect(url.get_secret_value(), autocommit=True)


def valeur(conn: Connexion, requete: str, parametres: list[Any]) -> Any:
    """Rend la première colonne de la première ligne ; erreur si la requête ne rend rien."""
    ligne = conn.execute(requete, parametres).fetchone()
    if ligne is None:
        raise RuntimeError(f"Requête sans résultat : {requete[:60]}")
    return ligne[0]


def version_publiee(conn: Connexion, jeu: str) -> tuple[int, bytes] | None:
    """Rend l'identifiant et l'empreinte de la version servie d'un jeu, s'il y en a une."""
    ligne = conn.execute(
        "SELECT id, file_sha256 FROM ref.dataset_versions"
        " WHERE dataset = %s AND channel = 'production' AND status = 'published'",
        [jeu],
    ).fetchone()
    return (int(ligne[0]), bytes(ligne[1])) if ligne else None


def charger[T](
    conn: Connexion,
    *,
    jeu: str,
    source_id: str,
    fichier: FichierRecu,
    date_source: date,
    lecture: Lecture[T],
    inserer: Callable[[Connexion, int, list[T]], None],
    controler: Callable[[Connexion, int], list[Controle]],
) -> Resultat:
    """Écrit une version candidate, la contrôle, puis la publie ou la marque en échec.

    Un fichier identique à la version servie (même empreinte) ne crée aucune version : le
    pipeline est rejouable sans doublon (VD-18).
    """
    servie = version_publiee(conn, jeu)
    if servie is not None and servie[1] == fichier.sha256:
        return Resultat(jeu=jeu, statut="inchange", version_id=servie[0])

    rapport = dict(lecture.rapport)
    rapport["url_finale"] = fichier.url_finale
    rapport["rejets_par_motif"] = compter_motifs(lecture.rejets)
    with conn.transaction():
        version_id = int(
            valeur(
                conn,
                "INSERT INTO ref.dataset_versions (dataset, source_id, source_url,"
                " source_date, retrieved_at, file_sha256, file_size_bytes, rows_read,"
                " rows_loaded, rows_filtered, rows_rejected, status, loader_version, report)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'candidate', %s, %s)"
                " RETURNING id",
                [
                    jeu,
                    source_id,
                    fichier.url,
                    date_source,
                    fichier.recupere_le,
                    fichier.sha256,
                    fichier.taille,
                    lecture.lues,
                    len(lecture.lignes),
                    lecture.filtrees,
                    len(lecture.rejets),
                    get_settings().git_sha,
                    json.dumps(rapport, ensure_ascii=False),
                ],
            )
        )
        with conn.cursor().copy(
            "COPY ref.load_rejections (version_id, line_number, reason_code, detail) FROM STDIN"
        ) as copie:
            for rejet in lecture.rejets:
                copie.write_row([version_id, rejet.ligne, rejet.motif, rejet.detail[:500]])
        inserer(conn, version_id, lecture.lignes)
        controles = controler(conn, version_id)
        rapport["controles"] = [vars(c) for c in controles]
        echec = any(c.bloquant and not c.reussi for c in controles)
        if not echec:
            conn.execute(
                "UPDATE ref.dataset_versions SET status = 'retired', retired_at = now()"
                " WHERE dataset = %s AND channel = 'production' AND status = 'published'",
                [jeu],
            )
        conn.execute(
            "UPDATE ref.dataset_versions SET status = %s, report = %s,"
            " published_at = CASE WHEN %s THEN now() END WHERE id = %s",
            [
                "failed" if echec else "published",
                json.dumps(rapport, ensure_ascii=False),
                not echec,
                version_id,
            ],
        )
    return Resultat(
        jeu=jeu,
        statut="failed" if echec else "published",
        version_id=version_id,
        lues=lecture.lues,
        chargees=len(lecture.lignes),
        filtrees=lecture.filtrees,
        rejetees=len(lecture.rejets),
        controles=tuple(controles),
    )


def compter_motifs(rejets: list[Rejet]) -> dict[str, int]:
    comptes: dict[str, int] = {}
    for rejet in rejets:
        comptes[rejet.motif] = comptes.get(rejet.motif, 0) + 1
    return comptes
