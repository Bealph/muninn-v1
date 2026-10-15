"""Agrégats Sirene (SRC-01) : établissements actifs de la tête de pont, par DuckDB (sprint 3, V-06).

Les fichiers Parquet du stock sont lus à distance, par requêtes HTTP partielles : seules les
colonnes de la requête versionnée sont transférées (environ 290 Mo sur 2,9 Go, mesuré le
15 octobre 2026). Les SIREN restent en mémoire, dans DuckDB, le temps des comptages ; seuls des
agrégats soumis au secret statistique entrent en base (phase 1, document 02, § 4.2).

Secret statistique, appliqué avant l'écriture, avec un seuil de 5 [H] :
1. une cellule (NAF, tranche, groupe juridique, département) dont l'une des deux mesures est sous
   le seuil perd son département : elle rejoint la cellule `ZZ` de son groupe ;
2. une cellule `ZZ` sous le seuil est masquée ;
3. le total national `FR` d'un groupe est calculé sur toutes les données ; il est masqué s'il est
   sous le seuil, et arrondi au multiple de 5 supérieur si la cellule `ZZ` du groupe est masquée
   (sinon on la retrouverait par différence) ;
4. toute mesure servie atteint le seuil.

Les cellules `ZZ` et `FR` sont recomptées sur les SIREN, pas additionnées : une entreprise peut
avoir des établissements dans plusieurs départements.
"""

import hashlib
import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import duckdb
import httpx

from muninn.core.config import get_settings
from muninn.ingestion.versions import Connexion, Controle, Resultat, valeur

URL_ETABLISSEMENTS = (
    "https://www.data.gouv.fr/api/1/datasets/r/a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
)
URL_UNITES_LEGALES = (
    "https://www.data.gouv.fr/api/1/datasets/r/350182c9-148a-46e0-8389-76c2ec1374a3"
)
FICHIER_REQUETE = Path(__file__).parent / "requetes" / "sirene_etablissements.sql"
SEUIL = 5
NAF = re.compile(r"[0-9]{2}\.[0-9]{2}[A-Z]")

Cle = tuple[str, str, str]  # code NAF, tranche d'effectif, groupe juridique
Mesures = tuple[int, int]  # établissements, entreprises (SIREN distincts)


@dataclass(frozen=True)
class Stock:
    """Adresses des deux fichiers Parquet d'un stock, et sa date."""

    etablissements: str
    unites_legales: str
    date: date


@dataclass
class Comptages:
    cellules: dict[tuple[str, str, str, str], Mesures] = field(default_factory=dict)
    regroupees: dict[Cle, Mesures] = field(default_factory=dict)  # cellules `ZZ`, réelles
    nationaux: dict[Cle, Mesures] = field(default_factory=dict)  # totaux `FR`, réels
    etablissements: int = 0  # lignes après filtre (actifs, codes NAF de la tête de pont)
    sans_departement: int = 0  # établissements sans commune, écartés des comptages


@dataclass(frozen=True)
class Ligne:
    cle: Cle
    departement: str
    etablissements: int | None
    entreprises: int | None

    @property
    def masquee(self) -> bool:
        return self.etablissements is None


def version_requete() -> str:
    return hashlib.sha256(FICHIER_REQUETE.read_bytes()).hexdigest()[:12]


def localiser(client: httpx.Client) -> Stock:
    """Suit les liens stables de data.gouv.fr ; la date du stock est celle du fichier."""
    adresses = []
    dates = []
    for url in (URL_ETABLISSEMENTS, URL_UNITES_LEGALES):
        reponse = client.head(url)
        reponse.raise_for_status()
        adresses.append(str(reponse.url))
        modifie = reponse.headers.get("Last-Modified")
        if modifie is None:
            raise ValueError(f"Sirene : date du fichier absente pour {url}")
        dates.append(parsedate_to_datetime(modifie).date())
    return Stock(adresses[0], adresses[1], dates[0])


def requete(stock: Stock, codes_naf: Iterable[str]) -> str:
    """Requête versionnée, avec les adresses et les codes NAF insérés comme littéraux contrôlés."""
    codes = sorted(codes_naf)
    if not codes or not all(NAF.fullmatch(c) for c in codes):
        raise ValueError(f"Sirene : codes NAF invalides {codes}")
    return (
        FICHIER_REQUETE.read_text(encoding="utf-8")
        .replace("{etablissements}", litteral(stock.etablissements))
        .replace("{unites_legales}", litteral(stock.unites_legales))
        .replace("{codes_naf}", ", ".join(litteral(c) for c in codes))
    )


def litteral(texte: str) -> str:
    return "'" + texte.replace("'", "''") + "'"


def calculer(stock: Stock, codes_naf: Iterable[str], seuil: int = SEUIL) -> Comptages:
    """Lit le stock et rend les comptages réels : cellules, `ZZ` et `FR`."""
    comptages = Comptages()
    with duckdb.connect() as con:
        con.execute(f"CREATE TEMP TABLE base AS {requete(stock, codes_naf)}")  # noqa: S608
        totaux = con.execute(
            "SELECT count(*), count(*) FILTER (WHERE department_code IS NULL) FROM base"
        ).fetchone()
        if totaux is None:
            raise RuntimeError("Sirene : comptage impossible")
        comptages.etablissements, comptages.sans_departement = int(totaux[0]), int(totaux[1])
        groupe = "naf_code, headcount_band, legal_category_group"
        for naf, tranche, juridique, departement, n_e, n_u in con.execute(
            f"SELECT {groupe}, department_code, count(*), count(DISTINCT siren) FROM base"  # noqa: S608
            " WHERE department_code IS NOT NULL GROUP BY ALL"
        ).fetchall():
            comptages.cellules[(naf, tranche, juridique, departement)] = (int(n_e), int(n_u))
        for naf, tranche, juridique, n_e, n_u in con.execute(
            f"SELECT {groupe}, count(*), count(DISTINCT siren) FROM base"  # noqa: S608
            " WHERE department_code IS NOT NULL GROUP BY ALL"
        ).fetchall():
            comptages.nationaux[(naf, tranche, juridique)] = (int(n_e), int(n_u))
        petites = [k for k, (n_e, n_u) in comptages.cellules.items() if min(n_e, n_u) < seuil]
        con.execute(
            "CREATE TEMP TABLE petites (naf_code VARCHAR, headcount_band VARCHAR,"
            " legal_category_group VARCHAR, department_code VARCHAR)"
        )
        if petites:
            con.executemany("INSERT INTO petites VALUES (?, ?, ?, ?)", petites)
        for naf, tranche, juridique, n_e, n_u in con.execute(
            f"SELECT {groupe}, count(*), count(DISTINCT siren) FROM base"  # noqa: S608
            f" JOIN petites USING ({groupe}, department_code) GROUP BY ALL"
        ).fetchall():
            comptages.regroupees[(naf, tranche, juridique)] = (int(n_e), int(n_u))
        con.execute("DROP TABLE base")  # les SIREN ne survivent pas aux comptages
    return comptages


def arrondi(valeur_reelle: int) -> int:
    return int(math.ceil(valeur_reelle / 5) * 5)


def appliquer_secret(comptages: Comptages, seuil: int = SEUIL) -> list[Ligne]:
    """Rend les lignes à écrire ; aucune mesure servie n'est sous le seuil."""
    lignes = [
        Ligne((naf, tranche, juridique), departement, n_e, n_u)
        for (naf, tranche, juridique, departement), (n_e, n_u) in comptages.cellules.items()
        if min(n_e, n_u) >= seuil
    ]
    zz_masquees = set()
    for cle, (n_e, n_u) in comptages.regroupees.items():
        if min(n_e, n_u) < seuil:
            zz_masquees.add(cle)
            lignes.append(Ligne(cle, "ZZ", None, None))
        else:
            lignes.append(Ligne(cle, "ZZ", n_e, n_u))
    for cle, (n_e, n_u) in comptages.nationaux.items():
        if min(n_e, n_u) < seuil:
            lignes.append(Ligne(cle, "FR", None, None))
        elif cle in zz_masquees:
            lignes.append(Ligne(cle, "FR", arrondi(n_e), arrondi(n_u)))
        else:
            lignes.append(Ligne(cle, "FR", n_e, n_u))
    return sorted(lignes, key=lambda ligne: (*ligne.cle, ligne.departement))


def controles(comptages: Comptages, lignes: list[Ligne], seuil: int = SEUIL) -> list[Controle]:
    """VD-21 (conservation), VD-23 (cohérence interne) et règle 4 du secret (bloquants)."""
    ecarts = []
    for cle, (n_e, _) in comptages.nationaux.items():
        gardees = sum(
            v[0] for k, v in comptages.cellules.items() if k[:3] == cle and min(v) >= seuil
        )
        if gardees + comptages.regroupees.get(cle, (0, 0))[0] != n_e:
            ecarts.append(cle)
    incoherentes = [k for k, (n_e, n_u) in comptages.cellules.items() if n_u > n_e]
    sous_seuil = [
        ligne
        for ligne in lignes
        if not ligne.masquee and min(ligne.etablissements or 0, ligne.entreprises or 0) < seuil
    ]
    return [
        Controle("VD-21", not ecarts, True, f"{len(ecarts)} groupes dont les cellules ne"
                 " redonnent pas le total national"),
        Controle("VD-23", not incoherentes, True, f"{len(incoherentes)} cellules avec plus"
                 " d'entreprises que d'établissements"),
        Controle("secret", not sous_seuil, True, f"{len(sous_seuil)} mesures servies sous le"
                 f" seuil de {seuil}"),
    ]  # fmt: skip


def empreinte(lignes: list[Ligne]) -> bytes:
    """Empreinte du résultat : deux exécutions sur le même stock donnent la même (VD-22)."""
    texte = "\n".join(
        f"{c[0]}|{c[1]}|{c[2]}|{ligne.departement}|{ligne.etablissements}|{ligne.entreprises}"
        for ligne in lignes
        for c in [ligne.cle]
    )
    return hashlib.sha256(texte.encode()).digest()


def ingerer(conn: Connexion, client: httpx.Client) -> Resultat:
    """Calcule et publie les agrégats du stock courant, sauf s'il est déjà servi."""
    stock = localiser(client)
    version = version_requete()
    servie = conn.execute(
        "SELECT id FROM market.sirene_runs WHERE status = 'published' AND naf_revision = 'rev2'"
        " AND stock_date = %s AND query_version = %s",
        [stock.date, version],
    ).fetchone()
    if servie is not None:
        return Resultat(jeu="sirene", statut="inchange", version_id=int(servie[0]))

    metiers = {
        str(code): str(metier)
        for code, metier in conn.execute(
            "SELECT naf_code, trade FROM ref.naf_trades WHERE naf_revision = 'rev2'"
        )
    }
    debut = datetime.now(UTC)
    comptages = calculer(stock, metiers)
    lignes = appliquer_secret(comptages)
    verifications = controles(comptages, lignes)
    echec = any(c.bloquant and not c.reussi for c in verifications)
    rapport: dict[str, Any] = {
        "unites_legales": stock.unites_legales,
        "sans_departement": comptages.sans_departement,
        "controles": [vars(c) for c in verifications],
    }
    with conn.transaction():
        execution = int(
            valeur(
                conn,
                "INSERT INTO market.sirene_runs (stock_date, source_url, naf_revision,"
                " query_version, service_name, processing_region, small_cell_threshold,"
                " started_at, finished_at, rows_after_filter, result_sha256, status, report)"
                " VALUES (%s, %s, 'rev2', %s, %s, %s, %s, %s, now(), %s, %s, %s, %s)"
                " RETURNING id",
                [
                    stock.date,
                    stock.etablissements,
                    version,
                    f"duckdb {duckdb.__version__}",
                    region(),
                    SEUIL,
                    debut,
                    comptages.etablissements,
                    empreinte(lignes),
                    "failed" if echec else "loading",
                    json.dumps(rapport, ensure_ascii=False),
                ],
            )
        )
        with conn.cursor().copy(
            "COPY market.sirene_counts (run_id, naf_code, headcount_band, legal_category_group,"
            " department_code, trade, establishments_count, legal_units_count, is_masked)"
            " FROM STDIN"
        ) as copie:
            for ligne in lignes:
                copie.write_row(
                    [
                        execution,
                        *ligne.cle,
                        ligne.departement,
                        metiers[ligne.cle[0]],
                        ligne.etablissements,
                        ligne.entreprises,
                        ligne.masquee,
                    ]
                )
        if not echec:
            conn.execute(
                "UPDATE market.sirene_runs SET status = 'retired'"
                " WHERE status = 'published' AND naf_revision = 'rev2'"
            )
            conn.execute(
                "UPDATE market.sirene_runs SET status = 'published', published_at = now()"
                " WHERE id = %s",
                [execution],
            )
    return Resultat(
        jeu="sirene",
        statut="failed" if echec else "published",
        version_id=execution,
        lues=comptages.etablissements,
        chargees=len(lignes),
        filtrees=comptages.sans_departement,
        controles=tuple(verifications),
    )


def region() -> str:
    """Lieu du traitement : la région Azure en préproduction et production, sinon le poste."""
    return "francecentral" if get_settings().environment != "local" else "local"
