"""Schémas `ref` et `market` et rôles de base (sprint 3, étape 1).

Ces tests demandent un PostgreSQL 16 : `TEST_DATABASE_URL` désigne un rôle autorisé à créer des
bases et des rôles. Chaque exécution crée une base neuve, puis la supprime. Sans cette variable, les
tests sont ignorés, sauf si `MUNINN_TESTS_BASE=obligatoire` (en CI) : ils échouent alors.
"""

from collections.abc import Iterator

import psycopg
import pytest
from alembic import command
from psycopg import errors, sql

from muninn.db.migrer import configuration
from outils_base import base_migree, connecter, exiger_base, url_postgres

exiger_base()

TABLES_REF = {
    "dataset_versions",
    "load_rejections",
    "communes",
    "commune_source_gaps",
    "postal_codes",
    "naf_trades",
    "trade_lexicons",
    "lexicon_terms",
}
TABLES_MARKET = {"sirene_runs", "sirene_counts"}
MOT_DE_PASSE = "test-seulement"  # noqa: S105 : rôle éphémère d'une base de test


@pytest.fixture(scope="module")
def base() -> Iterator[str]:
    with base_migree() as nom:
        yield nom


def connexion_role(base: str, groupe: str, suffixe: str) -> psycopg.Connection[tuple[object, ...]]:
    """Crée un rôle de connexion membre du groupe `<base>_<groupe>` et s'y connecte."""
    role = f"{base}_{suffixe}"
    with connecter(base) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} IN ROLE {}").format(
                sql.Identifier(role), sql.Literal(MOT_DE_PASSE), sql.Identifier(f"{base}_{groupe}")
            )
        )
    return connecter(base, user=role, password=MOT_DE_PASSE)


def inserer_version(conn: psycopg.Connection[tuple[object, ...]], **valeurs: object) -> int:
    ligne = {
        "dataset": "communes",
        "source_id": "SRC-07",
        "source_url": "https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv",
        "source_date": "2026-01-01",
        "retrieved_at": "2026-10-15T08:00:00Z",
        "file_sha256": bytes(32),
        "file_size_bytes": 3_000_000,
        "rows_read": 3,
        "rows_loaded": 2,
        "rows_rejected": 1,
        "status": "loading",
        "loader_version": "test",
    } | valeurs
    colonnes = sql.SQL(", ").join(sql.Identifier(c) for c in ligne)
    marques = sql.SQL(", ").join(sql.Placeholder() for _ in ligne)
    requete = sql.SQL("INSERT INTO ref.dataset_versions ({}) VALUES ({}) RETURNING id").format(
        colonnes, marques
    )
    resultat = conn.execute(requete, list(ligne.values())).fetchone()
    assert resultat is not None
    return int(str(resultat[0]))


def test_tables_creees(base: str) -> None:
    with connecter(base) as conn:
        lignes = conn.execute(
            "SELECT table_schema, table_name FROM information_schema.tables"
            " WHERE table_schema IN ('ref', 'market')"
        ).fetchall()
    assert {n for s, n in lignes if s == "ref"} == TABLES_REF
    assert {n for s, n in lignes if s == "market"} == TABLES_MARKET


def test_correspondance_naf(base: str) -> None:
    with connecter(base) as conn:
        lignes = conn.execute("SELECT naf_code, trade FROM ref.naf_trades ORDER BY 1").fetchall()
    assert lignes == [
        ("43.21A", "electricite"),
        ("43.22A", "plomberie"),
        ("43.22B", "chauffage"),
        ("43.32B", "serrurerie"),
    ]


def test_role_lecture_lit_sans_ecrire(base: str) -> None:
    with connexion_role(base, "lecture", "api") as api:
        assert api.execute("SELECT count(*) FROM ref.naf_trades").fetchone() == (4,)
        assert api.execute("SELECT count(*) FROM market.sirene_counts").fetchone() == (0,)
        with pytest.raises(errors.InsufficientPrivilege):
            api.execute("DELETE FROM ref.naf_trades")
        with pytest.raises(errors.InsufficientPrivilege):
            inserer_version(api)
        with pytest.raises(errors.InsufficientPrivilege):
            api.execute("CREATE TABLE ref.intrusion (x int)")


def test_role_ecriture_charge_sans_modifier_le_schema(base: str) -> None:
    with connexion_role(base, "ecriture", "ingestion") as ingestion:
        version = inserer_version(ingestion)
        ingestion.execute(
            "INSERT INTO ref.communes (version_id, commune_type, insee_code, name,"
            " name_normalized, department_code) VALUES (%s, 'COM', '2A004', 'Ajaccio',"
            " 'ajaccio', '2A')",
            [version],
        )
        with pytest.raises(errors.InsufficientPrivilege):
            ingestion.execute("DELETE FROM ref.naf_trades")
        with pytest.raises(errors.InsufficientPrivilege):
            ingestion.execute("CREATE TABLE ref.intrusion (x int)")
        ingestion.execute("DELETE FROM ref.dataset_versions WHERE id = %s", [version])


def test_contraintes(base: str) -> None:
    with connecter(base) as conn:
        version = inserer_version(conn)
        with pytest.raises(errors.CheckViolation):  # aucune ligne écartée en silence
            inserer_version(conn, rows_read=10)
        with pytest.raises(errors.CheckViolation):  # le jeu et la source vont ensemble
            inserer_version(conn, source_id="SRC-06")
        with pytest.raises(errors.CheckViolation):  # code postal sur 5 chiffres, en texte
            conn.execute(
                "INSERT INTO ref.postal_codes (version_id, postal_code, insee_code,"
                " laposte_name, routing_label) VALUES (%s, '1234', '01001', 'X', 'X')",
                [version],
            )
        with pytest.raises(errors.CheckViolation):  # commune déléguée sans commune parente
            conn.execute(
                "INSERT INTO ref.communes (version_id, commune_type, insee_code, name,"
                " name_normalized) VALUES (%s, 'COMD', '01015', 'Arbignieu', 'arbignieu')",
                [version],
            )
        with pytest.raises(errors.CheckViolation):  # licence imposée par la source
            lexique = conn.execute(
                "INSERT INTO ref.trade_lexicons (trade, version, status)"
                " VALUES ('plomberie', 'test', 'draft') RETURNING id"
            ).fetchone()
            assert lexique is not None
            conn.execute(
                "INSERT INTO ref.lexicon_terms (lexicon_id, term, term_normalized, category,"
                " source_id, source_ref, license, review_status)"
                " VALUES (%s, 'cumulus', 'cumulus', 'equipment', 'SRC-12', 'cumulus', 'CC0-1.0',"
                " 'accepted')",
                [lexique[0]],
            )
        conn.execute("DELETE FROM ref.dataset_versions")
        conn.execute("DELETE FROM ref.trade_lexicons")


def test_une_seule_version_publiee_par_jeu(base: str) -> None:
    with connecter(base) as conn:
        inserer_version(conn, status="published", published_at="2026-10-15T09:00:00Z")
        with pytest.raises(errors.UniqueViolation):
            inserer_version(conn, status="published", published_at="2026-10-15T10:00:00Z")
        conn.execute("DELETE FROM ref.dataset_versions")


def test_secret_statistique_impose_par_le_schema(base: str) -> None:
    with connecter(base) as conn:
        execution = conn.execute(
            "INSERT INTO market.sirene_runs (stock_date, source_url, naf_revision,"
            " query_version, service_name, processing_region, started_at, status)"
            " VALUES ('2026-10-01', 'https://www.data.gouv.fr/', 'rev2', 'test', 'duckdb',"
            " 'francecentral', now(), 'loading') RETURNING id"
        ).fetchone()
        assert execution is not None
        with pytest.raises(errors.CheckViolation):  # masquée mais avec une mesure
            conn.execute(
                "INSERT INTO market.sirene_counts VALUES"
                " (%s, '43.22A', '00', 'ei', 'ZZ', 'plomberie', 3, NULL, true)",
                [execution[0]],
            )
        conn.execute("DELETE FROM market.sirene_runs")


def test_annulation_puis_reapplication(base: str) -> None:
    url = url_postgres(base)
    command.downgrade(configuration(url), "base")
    with connecter(base) as conn:
        schemas = conn.execute(
            "SELECT nspname FROM pg_namespace WHERE nspname IN ('ref', 'market')"
        ).fetchall()
        roles = conn.execute(
            "SELECT rolname FROM pg_roles WHERE rolname IN (%s, %s)",
            [f"{base}_lecture", f"{base}_ecriture"],
        ).fetchall()
    assert schemas == []
    assert roles == []
    command.upgrade(configuration(url), "head")
    with connecter(base) as conn:
        assert conn.execute("SELECT count(*) FROM ref.naf_trades").fetchone() == (4,)
