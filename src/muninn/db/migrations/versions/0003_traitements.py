"""Traitements enregistrés : schéma `app` (sprint 5, étape 1 ; D-82, D-85).

Pour la correction et la validation (V-09, CA-5) et les métriques tirées de la base (V-10) :
- `app.traitements` : une ligne par appel traité, ses mesures, sans contenu ;
- `app.dossiers` et `app.messages` : le brouillon et son enveloppe, ou le message
  (données synthétiques seulement, P-03) ;
- `app.corrections` : le champ corrigé et la date, jamais la valeur.
Jamais de transcription ni d'audio. Conservation de 30 jours (D-82) : une ligne de
`app.traitements` supprimée emporte son dossier, son message et leurs corrections.

Rôle de groupe `<base>_app` : lecture et écriture sur le seul schéma `app` ; le rôle de connexion
`<base>_traitements` y est rattaché hors des migrations (D-85). Le rôle de l'API (`<base>_lecture`)
n'a aucun droit sur ce schéma.

Révision : 0003
Précédente : 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE SCHEMA app;

CREATE TABLE app.traitements (
    request_id         text PRIMARY KEY CHECK (length(request_id) BETWEEN 1 AND 64),
    recu_le            timestamptz NOT NULL DEFAULT now(),
    route              text NOT NULL CHECK (route IN ('demo', 'extraction')),
    scenario_id        text CHECK (length(scenario_id) <= 40),
    modele_simule      boolean NOT NULL DEFAULT false,
    issue              text NOT NULL CHECK (issue IN ('dossier', 'message', 'trace', 'refus')),
    code_refus         text CHECK (code_refus ~ '^[a-z_]{1,40}$'),
    categorie          text CHECK (categorie ~ '^[a-z_]{1,40}$'),
    regle              text CHECK (regle ~ '^[a-z_]{1,40}$'),
    securite           boolean NOT NULL DEFAULT false,
    statut             text CHECK (statut ~ '^[a-z_]{1,40}$'),
    a_verifier         boolean,
    motifs             text[] NOT NULL DEFAULT '{}',
    garde_fous         text[] NOT NULL DEFAULT '{}',
    outils             integer NOT NULL DEFAULT 0 CHECK (outils >= 0),
    borne              boolean NOT NULL DEFAULT false,
    tentatives         integer CHECK (tentatives >= 0),
    urgence            text CHECK (urgence ~ '^[a-z_]{1,40}$'),
    urgence_serveur    boolean NOT NULL DEFAULT false,
    commune_statut     text CHECK (commune_statut ~ '^[a-z_]{1,40}$'),
    code_postal_statut text CHECK (code_postal_statut ~ '^[a-z_]{1,40}$'),
    jetons             integer NOT NULL DEFAULT 0 CHECK (jetons >= 0),
    cout_micro_eur     integer NOT NULL DEFAULT 0 CHECK (cout_micro_eur >= 0),
    duree_ms           integer NOT NULL CHECK (duree_ms >= 0),
    CHECK ((issue = 'refus') = (code_refus IS NOT NULL))
);
CREATE INDEX traitements_recu_le ON app.traitements (recu_le);

CREATE TABLE app.dossiers (
    draft_id   uuid PRIMARY KEY,
    request_id text NOT NULL UNIQUE REFERENCES app.traitements ON DELETE CASCADE,
    cree_le    timestamptz NOT NULL DEFAULT now(),
    etat       text NOT NULL DEFAULT 'brouillon' CHECK (etat IN ('brouillon', 'valide')),
    valide_le  timestamptz,
    brouillon  jsonb NOT NULL CHECK (jsonb_typeof(brouillon) = 'object'),
    enveloppe  jsonb NOT NULL CHECK (jsonb_typeof(enveloppe) = 'object'),
    CHECK ((etat = 'valide') = (valide_le IS NOT NULL))
);

CREATE TABLE app.messages (
    message_id uuid PRIMARY KEY,
    request_id text NOT NULL UNIQUE REFERENCES app.traitements ON DELETE CASCADE,
    recu_le    timestamptz NOT NULL DEFAULT now(),
    message    jsonb NOT NULL CHECK (jsonb_typeof(message) = 'object')
);

-- Une ligne par champ corrigé ; la valeur corrigée n'est jamais gardée (CA-5).
CREATE TABLE app.corrections (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    draft_id   uuid NOT NULL REFERENCES app.dossiers ON DELETE CASCADE,
    champ      text NOT NULL CHECK (champ ~ '^[a-z_.]{1,80}$'),
    corrige_le timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX corrections_draft_id ON app.corrections (draft_id);
"""

ROLE = """
DO $$
DECLARE
    base text := quote_ident(current_database());
    app  text := quote_ident(current_database() || '_app');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_database() || '_app') THEN
        EXECUTE 'CREATE ROLE ' || app || ' NOLOGIN';
    END IF;
    EXECUTE 'GRANT CONNECT ON DATABASE ' || base || ' TO ' || app;
    EXECUTE 'GRANT USAGE ON SCHEMA app TO ' || app;
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO ' || app;
    EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO ' || app;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA app'
            ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ' || app;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE, SELECT ON SEQUENCES TO ' || app;
END
$$
"""

SUPPRIMER_ROLE = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_database() || '_app') THEN
        EXECUTE 'DROP OWNED BY ' || quote_ident(current_database() || '_app');
        EXECUTE 'DROP ROLE ' || quote_ident(current_database() || '_app');
    END IF;
END
$$
"""


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(ROLE)


def downgrade() -> None:
    op.execute(SUPPRIMER_ROLE)
    op.execute("DROP SCHEMA app CASCADE")
