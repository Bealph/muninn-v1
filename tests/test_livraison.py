"""Reprise des commandes `az` sur erreur passagère d'Azure pendant la livraison (INC-05).

Un faux `az` placé en tête du PATH échoue un nombre de fois choisi, avec le message d'erreur
choisi, puis réussit. Aucun appel à Azure.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
REESSAI = RACINE / "infra" / "azure" / "reessai.sh"
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="bash absent")


def lancer(
    tmp_path: Path, echecs: int, message: str
) -> tuple[subprocess.CompletedProcess[str], int]:
    compteur = tmp_path / "compteur"
    compteur.write_text("0", encoding="utf-8")
    faux = tmp_path / "bin" / "az"
    faux.parent.mkdir()
    faux.write_text(
        "#!/usr/bin/env bash\n"
        f'n=$(( $(cat "{compteur.as_posix()}") + 1 )); echo "$n" > "{compteur.as_posix()}"\n'
        f'if [ "$n" -le {echecs} ]; then echo "ERROR: {message}" >&2; exit 1; fi\n'
        'echo "revision-0002"\n',
        encoding="utf-8",
        newline="\n",
    )
    faux.chmod(0o755)
    script = (
        f'export PATH="$(cd "{faux.parent.as_posix()}" && pwd):$PATH"; '
        f'source "{REESSAI.as_posix()}"; '
        "az_tenace containerapp update --query properties.latestRevisionName -o tsv"
    )
    env = os.environ | {"REESSAI_PAUSE_S": "0", "REESSAI_ESSAIS": "4"}
    # Entrée maîtrisée : bash trouvé par `shutil.which`, script écrit par le test lui-même.
    resultat = subprocess.run(  # noqa: S603
        [BASH or "bash", "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    return resultat, int(compteur.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "message", ["Too Many Requests(Ref A: x)", "Service Unavailable(<html>)", "(503) busy"]
)
def test_erreur_passagere_reprise_puis_succes(tmp_path: Path, message: str) -> None:
    resultat, appels = lancer(tmp_path, echecs=2, message=message)
    assert resultat.returncode == 0, resultat.stderr
    assert resultat.stdout == "revision-0002\n"  # sortie de la commande réussie, inchangée
    assert appels == 3
    assert "erreur passagère" in resultat.stderr


def test_erreur_definitive_rendue_sans_reprise(tmp_path: Path) -> None:
    resultat, appels = lancer(tmp_path, echecs=1, message="ResourceNotFound")
    assert resultat.returncode != 0
    assert appels == 1
    assert "ResourceNotFound" in resultat.stderr


def test_erreur_passagere_persistante_finit_en_echec(tmp_path: Path) -> None:
    resultat, appels = lancer(tmp_path, echecs=10, message="Too Many Requests")
    assert resultat.returncode != 0
    assert appels == 4
    assert "Too Many Requests" in resultat.stderr


def test_la_livraison_passe_toutes_ses_commandes_az_par_la_reprise() -> None:
    script = (RACINE / "infra" / "azure" / "deployer.sh").read_text(encoding="utf-8")
    assert 'source "$(dirname "$0")/reessai.sh"' in script
    lignes = [ligne for ligne in script.splitlines() if not ligne.lstrip().startswith("#")]
    assert not any(" az containerapp" in ligne or "(az containerapp" in ligne for ligne in lignes)
