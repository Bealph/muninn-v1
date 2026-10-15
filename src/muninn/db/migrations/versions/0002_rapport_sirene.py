"""Rapport des exécutions Sirene (sprint 3, étape 6).

Garde, avec chaque exécution, ce que ses colonnes ne disent pas : adresse du fichier des unités
légales, établissements sans commune écartés, résultat des contrôles.

Révision : 0002
Précédente : 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE market.sirene_runs ADD COLUMN report jsonb NOT NULL DEFAULT '{}'"
        " CHECK (jsonb_typeof(report) = 'object')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market.sirene_runs DROP COLUMN report")
