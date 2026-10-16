"""Commande `muninn-donnees` : ce que fait la tâche Container Apps d'une base (D-58).

En une commande, dans cet ordre :
1. migrations, avec le rôle propriétaire (`DATABASE_URL`, l'administrateur du serveur) ;
2. rôles de connexion de l'API et de l'ingestion, avec leurs mots de passe ;
3. ingestion de toutes les sources, avec le seul rôle d'écriture.
Code de sortie non nul si une étape échoue : l'exécution de la tâche apparaît alors en échec.
"""

import os
import sys

from alembic import command

from muninn.core.config import get_settings
from muninn.db import roles
from muninn.db.migrer import configuration
from muninn.ingestion import commande


def main() -> int:
    url = roles.url_admin()
    mots = roles.mots_de_passe()
    print("1/3 Migrations")
    command.upgrade(configuration(), "head")
    print("2/3 Rôles de connexion")
    noms = roles.preparer_roles(url, mots)
    print(f"   rôles prêts : {', '.join(noms)}")
    print("3/3 Ingestion, avec le rôle d'écriture")
    os.environ["DATABASE_URL"] = roles.url_du_role(url, noms[1], mots["ingestion"])
    get_settings.cache_clear()
    return commande.main(["tout"])


if __name__ == "__main__":
    sys.exit(main())
