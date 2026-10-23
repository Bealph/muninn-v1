"""Durée de la seule extraction dans `app.traitements` (sprint 5, étape 4 ; D-83, SLO-05).

AL-16 doit mesurer ce que promet SLO-05 : la latence de l'extraction (agent et contrôles du
serveur), sans la qualification qui la précède. `duree_ms` garde la durée du traitement entier,
celle que l'artisan ressent ; `duree_extraction_ms` est vide pour un message, une trace ou un
refus, et pour les traitements enregistrés avant cette migration.

La colonne est facultative : le code qui l'écrit n'est livré qu'une fois la migration appliquée
dans chaque environnement (workflow `donnees`). Les droits du rôle `<base>_app`, donnés sur la
table, couvrent la nouvelle colonne.

Révision : 0004
Précédente : 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE app.traitements ADD COLUMN duree_extraction_ms integer"
        " CHECK (duree_extraction_ms >= 0)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE app.traitements DROP COLUMN duree_extraction_ms")
