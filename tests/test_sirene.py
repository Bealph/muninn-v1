"""Agrégats Sirene : secret statistique et calcul par DuckDB (sprint 3, étape 6).

Aucun appel réseau : le calcul lit de petits fichiers Parquet écrits pour le test, avec les mêmes
colonnes et les mêmes types que le stock réel (catégorie juridique en entier).
"""

from datetime import date
from pathlib import Path

import duckdb

from muninn.ingestion import sirene
from muninn.ingestion.sirene import Comptages, Stock

CLE = ("43.22A", "00", "ei")


def test_cellule_sous_le_seuil_rejoint_zz_et_le_total_est_arrondi() -> None:
    comptages = Comptages(
        cellules={(*CLE, "75"): (12, 10), (*CLE, "48"): (2, 2), (*CLE, "2A"): (1, 1)},
        regroupees={CLE: (3, 3)},  # 48 et 2A, recomptés : sous le seuil, donc masquée
        nationaux={CLE: (15, 13)},
    )
    lignes = {ligne.departement: ligne for ligne in sirene.appliquer_secret(comptages)}
    assert set(lignes) == {"75", "ZZ", "FR"}  # 48 et 2A ne sont jamais servis
    assert (lignes["75"].etablissements, lignes["75"].entreprises) == (12, 10)
    assert lignes["ZZ"].masquee
    assert (lignes["FR"].etablissements, lignes["FR"].entreprises) == (15, 15)  # arrondis à 5
    assert all(c.reussi for c in sirene.controles(comptages, list(lignes.values())))


def test_total_national_sous_le_seuil_masque() -> None:
    comptages = Comptages(
        cellules={(*CLE, "75"): (3, 3)}, regroupees={CLE: (3, 3)}, nationaux={CLE: (3, 3)}
    )
    lignes = sirene.appliquer_secret(comptages)
    assert [(ligne.departement, ligne.masquee) for ligne in lignes] == [
        ("FR", True),
        ("ZZ", True),
    ]


def test_zz_au_dessus_du_seuil_servie_et_total_exact() -> None:
    comptages = Comptages(
        cellules={(*CLE, "75"): (20, 18), (*CLE, "48"): (3, 3), (*CLE, "15"): (4, 4)},
        regroupees={CLE: (7, 7)},
        nationaux={CLE: (27, 25)},
    )
    lignes = {ligne.departement: ligne for ligne in sirene.appliquer_secret(comptages)}
    assert (lignes["ZZ"].etablissements, lignes["FR"].etablissements) == (7, 27)


def test_controle_de_conservation_detecte_un_ecart() -> None:
    comptages = Comptages(
        cellules={(*CLE, "75"): (12, 10)}, regroupees={}, nationaux={CLE: (13, 10)}
    )
    resultats = {c.cas: c for c in sirene.controles(comptages, sirene.appliquer_secret(comptages))}
    assert not resultats["VD-21"].reussi


def ecrire_stock(dossier: Path) -> Stock:
    """Petit stock au format réel : une entreprise a deux établissements dans deux départements."""
    etablissements = dossier / "etablissements.parquet"
    unites = dossier / "unites.parquet"
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE e (siren VARCHAR, activitePrincipaleEtablissement VARCHAR,"
            " trancheEffectifsEtablissement VARCHAR, codeCommuneEtablissement VARCHAR,"
            " etatAdministratifEtablissement VARCHAR, denominationUsuelleEtablissement VARCHAR)"
        )
        lignes: list[tuple[str, str, str, str | None, str, str]] = [
            (f"1000000{i:02d}", "43.22A", "NN", "75056", "A", "nom") for i in range(6)
        ]
        lignes += [
            ("100000000", "43.22A", "NN", "93048", "A", "nom"),  # même SIREN, autre département
            ("200000000", "43.22A", "NN", "2A004", "A", "nom"),
            ("300000000", "43.22A", "NN", "97411", "A", "nom"),
            ("400000000", "43.22A", "NN", None, "A", "nom"),  # sans commune
            ("500000000", "43.22A", "NN", "75056", "F", "nom"),  # fermé
            ("600000000", "47.11A", "NN", "75056", "A", "nom"),  # hors tête de pont
        ]
        con.executemany("INSERT INTO e VALUES (?, ?, ?, ?, ?, ?)", lignes)
        con.execute(f"COPY e TO '{etablissements.as_posix()}' (FORMAT parquet)")
        con.execute("CREATE TABLE u (siren VARCHAR, categorieJuridiqueUniteLegale BIGINT)")
        unites_legales = [(f"1000000{i:02d}", 1000) for i in range(6)]
        unites_legales += [("200000000", 5499), ("300000000", 5710), ("400000000", 1000)]
        con.executemany("INSERT INTO u VALUES (?, ?)", unites_legales)
        con.execute(f"COPY u TO '{unites.as_posix()}' (FORMAT parquet)")
    return Stock(etablissements.as_posix(), unites.as_posix(), date(2026, 10, 1))


def test_calcul_duckdb_sur_un_petit_stock(tmp_path: Path) -> None:
    comptages = sirene.calculer(ecrire_stock(tmp_path), ["43.22A"])
    assert comptages.etablissements == 10  # actifs de la tête de pont, sans commune compris
    assert comptages.sans_departement == 1
    assert comptages.cellules == {
        ("43.22A", "NN", "ei", "75"): (6, 6),
        ("43.22A", "NN", "ei", "93"): (1, 1),
        ("43.22A", "NN", "sarl", "2A"): (1, 1),
        ("43.22A", "NN", "sas", "974"): (1, 1),
    }
    # Total national recompté sur les SIREN : 7 établissements, 6 entreprises (pas 7).
    assert comptages.nationaux[("43.22A", "NN", "ei")] == (7, 6)
    assert comptages.regroupees[("43.22A", "NN", "ei")] == (1, 1)


def test_codes_naf_controles() -> None:
    stock = Stock("a", "b", date(2026, 10, 1))
    for codes in ([], ["43.22A'); DROP TABLE x; --"]):
        try:
            sirene.requete(stock, codes)
        except ValueError:
            continue
        raise AssertionError(f"codes acceptés à tort : {codes}")
