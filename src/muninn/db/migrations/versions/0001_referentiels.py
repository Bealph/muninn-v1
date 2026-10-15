"""Schémas `ref` et `market` de la V1, et rôles de lecture et d'écriture (sprint 3, étape 1).

Sous-ensemble du modèle physique de la phase 1
(`docs/conception/architecture_de_donnees/02-modele-de-donnees.md`, sections 3 et 4), limité aux
sources de la V1 (V-04 à V-06). Les écarts sont décrits dans
`docs/v1/sprints/sprint-3/schema.md`.

Révision : 0001
Précédente : aucune
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

CODE_INSEE = r"'^[0-9][0-9AB][0-9]{3}$'"
METIERS = "('plomberie', 'chauffage', 'electricite', 'serrurerie', 'autre')"

SCHEMAS = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE SCHEMA ref;
CREATE SCHEMA market;
"""

REF = f"""
CREATE TABLE ref.dataset_versions (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset         text NOT NULL,
    source_id       text NOT NULL,
    source_url      text NOT NULL,
    source_date     date NOT NULL,
    retrieved_at    timestamptz NOT NULL,
    file_sha256     bytea NOT NULL CHECK (octet_length(file_sha256) = 32),
    file_size_bytes bigint NOT NULL CHECK (file_size_bytes > 0),
    rows_read       integer NOT NULL CHECK (rows_read >= 0),
    rows_loaded     integer NOT NULL CHECK (rows_loaded >= 0),
    rows_filtered   integer NOT NULL DEFAULT 0 CHECK (rows_filtered >= 0),
    rows_rejected   integer NOT NULL CHECK (rows_rejected >= 0),
    channel         text NOT NULL DEFAULT 'production' CHECK (channel IN ('production', 'test')),
    status          text NOT NULL CHECK (status IN
                        ('loading', 'candidate', 'validated', 'published', 'retired', 'failed')),
    loader_version  text NOT NULL,
    report          jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(report) = 'object'),
    published_at    timestamptz,
    retired_at      timestamptz,
    -- Une source par jeu : le jeu dit ce qui est chargé, la source d'où il vient.
    CHECK ((dataset, source_id) IN (('communes', 'SRC-07'), ('postal_codes', 'SRC-06'),
                                    ('geo_api_communes', 'SRC-03'))),
    -- Aucune ligne écartée en silence (US-46, critère 2).
    CHECK (rows_read = rows_loaded + rows_filtered + rows_rejected),
    CHECK (status <> 'published' OR published_at IS NOT NULL),
    CHECK (status <> 'retired' OR retired_at IS NOT NULL)
);
-- Une seule version servie par jeu et par canal.
CREATE UNIQUE INDEX dataset_versions_publiee ON ref.dataset_versions (dataset, channel)
    WHERE status = 'published';

CREATE TABLE ref.load_rejections (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id  bigint NOT NULL REFERENCES ref.dataset_versions (id) ON DELETE CASCADE,
    line_number integer NOT NULL CHECK (line_number > 0),
    reason_code text NOT NULL CHECK (reason_code IN ('bad_format', 'bad_encoding',
                    'unknown_commune', 'duplicate', 'missing_field')),
    detail      text NOT NULL CHECK (char_length(detail) <= 500)
);
CREATE INDEX load_rejections_motif ON ref.load_rejections (version_id, reason_code);

CREATE TABLE ref.communes (
    version_id        bigint NOT NULL REFERENCES ref.dataset_versions (id) ON DELETE CASCADE,
    commune_type      text NOT NULL CHECK (commune_type IN ('COM', 'COMD', 'COMA', 'ARM')),
    insee_code        text NOT NULL CHECK (insee_code ~ {CODE_INSEE}),
    name              text NOT NULL,
    name_normalized   text NOT NULL,
    department_code   text CHECK (char_length(department_code) IN (2, 3)),
    parent_insee_code text CHECK (parent_insee_code ~ {CODE_INSEE}),
    PRIMARY KEY (version_id, commune_type, insee_code),
    CHECK (commune_type <> 'COM' OR department_code IS NOT NULL),
    CHECK (commune_type = 'COM' OR parent_insee_code IS NOT NULL)
);
CREATE INDEX communes_nom ON ref.communes (version_id, name_normalized);
CREATE INDEX communes_nom_trigrammes ON ref.communes USING gin (name_normalized gin_trgm_ops);
CREATE INDEX communes_parente ON ref.communes (version_id, parent_insee_code);

CREATE TABLE ref.commune_source_gaps (
    version_id   bigint NOT NULL REFERENCES ref.dataset_versions (id) ON DELETE CASCADE,
    insee_code   text NOT NULL CHECK (insee_code ~ {CODE_INSEE}),
    gap_type     text NOT NULL CHECK (gap_type IN
                     ('absent_from_cog', 'absent_from_geo_api', 'name_differs')),
    geo_api_name text,
    PRIMARY KEY (version_id, insee_code, gap_type),
    CHECK (gap_type = 'absent_from_geo_api' OR geo_api_name IS NOT NULL)
);

CREATE TABLE ref.postal_codes (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id    bigint NOT NULL REFERENCES ref.dataset_versions (id) ON DELETE CASCADE,
    postal_code   text NOT NULL CHECK (postal_code ~ '^[0-9]{{5}}$'),
    insee_code    text NOT NULL CHECK (insee_code ~ {CODE_INSEE}),
    laposte_name  text NOT NULL,
    routing_label text NOT NULL,
    line_5        text,
    UNIQUE NULLS NOT DISTINCT (version_id, postal_code, insee_code, line_5)
);
CREATE INDEX postal_codes_code ON ref.postal_codes (version_id, postal_code);
CREATE INDEX postal_codes_commune ON ref.postal_codes (version_id, insee_code);

CREATE TABLE ref.naf_trades (
    naf_revision text NOT NULL CHECK (naf_revision IN ('rev2', 'naf2025')),
    naf_code     text NOT NULL,
    trade        text NOT NULL CHECK (trade IN {METIERS}),
    label        text NOT NULL,
    PRIMARY KEY (naf_revision, naf_code)
);

CREATE TABLE ref.trade_lexicons (
    id                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trade                 text NOT NULL CHECK (trade IN {METIERS}),
    version               text NOT NULL,
    status                text NOT NULL CHECK (status IN
                              ('draft', 'candidate', 'published', 'retired')),
    evaluation_report_ref text,
    report                jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(report) = 'object'),
    created_at            timestamptz NOT NULL DEFAULT now(),
    published_at          timestamptz,
    UNIQUE (trade, version),
    -- Pas de publication sans évaluation (US-48, critère 4).
    CHECK (status <> 'published'
           OR (evaluation_report_ref IS NOT NULL AND published_at IS NOT NULL))
);
CREATE UNIQUE INDEX trade_lexicons_publie ON ref.trade_lexicons (trade)
    WHERE status = 'published';

CREATE TABLE ref.lexicon_terms (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lexicon_id       bigint NOT NULL REFERENCES ref.trade_lexicons (id) ON DELETE CASCADE,
    term             text NOT NULL CHECK (char_length(term) BETWEEN 1 AND 80),
    term_normalized  text NOT NULL,
    category         text NOT NULL CHECK (category IN
                         ('brand', 'part', 'equipment', 'fault', 'material', 'other')),
    source_id        text NOT NULL CHECK (source_id IN ('SRC-11', 'SRC-12', 'manual')),
    source_ref       text,
    license          text NOT NULL,
    review_status    text NOT NULL CHECK (review_status IN ('candidate', 'accepted', 'rejected')),
    rejection_reason text,
    stt_rank         smallint CHECK (stt_rank BETWEEN 1 AND 100),
    UNIQUE (lexicon_id, term_normalized),
    CHECK (source_id = 'manual' OR source_ref IS NOT NULL),
    -- La licence suit la source (registre des sources du sprint 3).
    CHECK ((source_id, license) IN (('SRC-11', 'CC0-1.0'), ('SRC-12', 'CC-BY-SA-4.0'),
                                   ('manual', 'internal'))),
    CHECK (review_status <> 'rejected' OR rejection_reason IS NOT NULL)
);
CREATE INDEX lexicon_terms_statut ON ref.lexicon_terms (lexicon_id, review_status);
CREATE UNIQUE INDEX lexicon_terms_rang ON ref.lexicon_terms (lexicon_id, stt_rank)
    WHERE stt_rank IS NOT NULL;
CREATE INDEX lexicon_terms_trigrammes ON ref.lexicon_terms
    USING gin (term_normalized gin_trgm_ops);
"""

# Codes de la tête de pont, fiches INSEE ouvertes une par une (phase 0, document 03, SRC-09).
NAF = """
INSERT INTO ref.naf_trades (naf_revision, naf_code, trade, label) VALUES
    ('rev2', '43.22A', 'plomberie',
     'Travaux d''installation d''eau et de gaz en tous locaux'),
    ('rev2', '43.22B', 'chauffage',
     'Travaux d''installation d''équipements thermiques et de climatisation'),
    ('rev2', '43.21A', 'electricite', 'Travaux d''installation électrique dans tous locaux'),
    ('rev2', '43.32B', 'serrurerie', 'Travaux de menuiserie métallique et serrurerie');
"""

MARKET = f"""
CREATE TABLE market.sirene_runs (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stock_date           date NOT NULL,
    source_url           text NOT NULL,
    naf_revision         text NOT NULL CHECK (naf_revision IN ('rev2', 'naf2025')),
    query_version        text NOT NULL,
    service_name         text NOT NULL,
    processing_region    text NOT NULL,
    small_cell_threshold smallint NOT NULL DEFAULT 5 CHECK (small_cell_threshold >= 1),
    started_at           timestamptz NOT NULL,
    finished_at          timestamptz,
    peak_memory_mb       integer CHECK (peak_memory_mb >= 0),
    bytes_read           bigint CHECK (bytes_read >= 0),
    rows_scanned         bigint CHECK (rows_scanned >= 0),
    rows_after_filter    bigint CHECK (rows_after_filter >= 0),
    result_sha256        bytea CHECK (octet_length(result_sha256) = 32),
    status               text NOT NULL CHECK (status IN
                             ('loading', 'published', 'retired', 'failed')),
    published_at         timestamptz,
    CHECK (status <> 'published' OR (published_at IS NOT NULL AND result_sha256 IS NOT NULL))
);
CREATE INDEX sirene_runs_stock ON market.sirene_runs (stock_date, query_version);
CREATE UNIQUE INDEX sirene_runs_publiee ON market.sirene_runs (naf_revision)
    WHERE status = 'published';

-- Aucun SIREN, aucun SIRET, aucune commune ni aucun code postal (phase 1, section 4.2).
CREATE TABLE market.sirene_counts (
    run_id               bigint NOT NULL REFERENCES market.sirene_runs (id) ON DELETE CASCADE,
    naf_code             text NOT NULL,
    headcount_band       text NOT NULL CHECK (headcount_band IN
                             ('NN', '00', 'empty', 'employer')),
    legal_category_group text NOT NULL CHECK (legal_category_group IN
                             ('ei', 'sarl', 'sas', 'other')),
    department_code      text NOT NULL CHECK (department_code ~ '^([0-9AB]{{2,3}}|ZZ|FR)$'),
    trade                text NOT NULL CHECK (trade IN {METIERS}),
    establishments_count integer CHECK (establishments_count >= 0),
    legal_units_count    integer CHECK (legal_units_count >= 0),
    is_masked            boolean NOT NULL,
    PRIMARY KEY (run_id, naf_code, headcount_band, legal_category_group, department_code),
    -- Masquée si et seulement si les deux mesures sont nulles.
    CHECK (is_masked = (establishments_count IS NULL AND legal_units_count IS NULL)),
    CHECK (is_masked OR (establishments_count IS NOT NULL AND legal_units_count IS NOT NULL))
);
"""

# Rôles de groupe, propres à chaque base (préproduction et production partagent le serveur) :
# `<base>_lecture` pour l'API, `<base>_ecriture` pour l'ingestion. Les rôles de connexion, avec
# leur mot de passe, sont créés hors des migrations et rattachés à ces groupes.
ROLES = """
DO $$
DECLARE
    base     text := quote_ident(current_database());
    lecture  text := quote_ident(current_database() || '_lecture');
    ecriture text := quote_ident(current_database() || '_ecriture');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_database() || '_lecture') THEN
        EXECUTE 'CREATE ROLE ' || lecture || ' NOLOGIN';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_database() || '_ecriture') THEN
        EXECUTE 'CREATE ROLE ' || ecriture || ' NOLOGIN';
    END IF;
    EXECUTE 'GRANT CONNECT ON DATABASE ' || base || ' TO ' || lecture || ', ' || ecriture;
    EXECUTE 'GRANT USAGE ON SCHEMA ref, market TO ' || lecture || ', ' || ecriture;
    EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA ref, market TO ' || lecture;
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ref, market TO '
            || ecriture;
    EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ref, market TO ' || ecriture;
    -- La table de correspondance NAF est alimentée par les migrations, pas par l'ingestion.
    EXECUTE 'REVOKE INSERT, UPDATE, DELETE ON ref.naf_trades FROM ' || ecriture;
    -- Les tables créées plus tard par le même propriétaire héritent des mêmes droits.
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ref, market GRANT SELECT ON TABLES TO '
            || lecture;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ref, market'
            ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ' || ecriture;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ref, market'
            ' GRANT USAGE, SELECT ON SEQUENCES TO ' || ecriture;
END
$$
"""

SUPPRIMER_ROLES = """
DO $$
DECLARE
    groupe text;
BEGIN
    FOREACH groupe IN ARRAY ARRAY[current_database() || '_lecture',
                                  current_database() || '_ecriture'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = groupe) THEN
            -- Retire les droits et privilèges par défaut de cette base ; les adhésions des rôles
            -- de connexion disparaissent avec le rôle de groupe.
            EXECUTE 'DROP OWNED BY ' || quote_ident(groupe);
            EXECUTE 'DROP ROLE ' || quote_ident(groupe);
        END IF;
    END LOOP;
END
$$
"""


def executer(bloc: str) -> None:
    """Exécute un bloc instruction par instruction : un appel du pilote, une instruction.

    Les blocs `DO` sont passés seuls : leur corps contient des points-virgules.
    """
    for instruction in bloc.split(";\n"):
        if instruction.strip():
            op.execute(instruction)


def upgrade() -> None:
    executer(SCHEMAS)
    executer(REF)
    executer(NAF)
    executer(MARKET)
    op.execute(ROLES)


def downgrade() -> None:
    op.execute(SUPPRIMER_ROLES)
    op.execute("DROP SCHEMA market CASCADE")
    op.execute("DROP SCHEMA ref CASCADE")
