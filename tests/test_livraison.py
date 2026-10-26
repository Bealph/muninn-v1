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
    "message",
    [
        "Too Many Requests(Ref A: x)",
        "Service Unavailable(<html>)",
        "(503) busy",
        # INC-08 : message exact de la livraison du 26 octobre 2026.
        "(ServerTimeout) The request timed out. Diagnostic information: timestamp '20261026T0908'",
    ],
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


# Nouvelle révision relue sur l'application, jamais prise dans la réponse de `update` (INC-07).
# Le faux `az` rend, à chaque lecture de l'application, le nom suivant de la liste (le dernier
# ensuite), et pour toute lecture de révision, le verdict choisi.


def nouvelle(
    tmp_path: Path,
    noms: list[str],
    verdict: str = "true",
    appel: str = 'nouvelle_revision app app--0082 "cond"',
) -> tuple[subprocess.CompletedProcess[str], int]:
    compteur = tmp_path / "lectures"
    compteur.write_text("0", encoding="utf-8")
    liste = tmp_path / "noms"
    liste.write_text("\n".join(noms) + "\n", encoding="utf-8", newline="\n")
    faux = tmp_path / "bin" / "az"
    faux.parent.mkdir()
    faux.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$2" = "show" ]; then\n'
        f'  n=$(( $(cat "{compteur.as_posix()}") + 1 )); echo "$n" > "{compteur.as_posix()}"\n'
        f'  t=$(wc -l < "{liste.as_posix()}"); [ "$n" -gt "$t" ] && n=$t\n'
        f'  sed -n "${{n}}p" "{liste.as_posix()}"\n'
        f'else echo "{verdict}"; fi\n',
        encoding="utf-8",
        newline="\n",
    )
    faux.chmod(0o755)
    script = (
        f'export PATH="$(cd "{faux.parent.as_posix()}" && pwd):$PATH"; GROUPE=rg; '
        f'source "{REESSAI.as_posix()}"; '
        f"{appel}"
    )
    env = os.environ | {"REVISION_PAUSE_S": "0", "REVISION_ESSAIS": "5", "REESSAI_PAUSE_S": "0"}
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


def test_reponse_perimee_puis_nouvelle_revision(tmp_path: Path) -> None:
    # Le cas du 23 octobre : l'application rend d'abord la révision en service.
    resultat, lectures = nouvelle(tmp_path, ["app--0082", "app--0082", "app--0083"])
    assert resultat.returncode == 0, resultat.stderr
    assert resultat.stdout == "app--0083\n"
    assert lectures == 3


def test_aucune_nouvelle_revision_echoue_sans_nom(tmp_path: Path) -> None:
    resultat, lectures = nouvelle(tmp_path, ["app--0082"])
    assert resultat.returncode != 0
    assert resultat.stdout == ""
    assert lectures == 5
    assert "Aucune nouvelle révision conforme" in resultat.stderr


def test_revision_recente_non_conforme_refusee(tmp_path: Path) -> None:
    # Une révision plus récente mais sans la modification voulue n'est jamais rendue.
    resultat, _ = nouvelle(tmp_path, ["app--0083"], verdict="false")
    assert resultat.returncode != 0
    assert resultat.stdout == ""


def test_relance_retrouve_la_revision_deja_creee(tmp_path: Path) -> None:
    resultat, lectures = nouvelle(tmp_path, ["app--0083"], verdict="True")
    assert resultat.returncode == 0, resultat.stderr
    assert resultat.stdout == "app--0083\n"
    assert lectures == 1


@pytest.mark.parametrize(
    "nom", ["deployer.sh", "07-langfuse.sh", "08-traitements.sh", "09-observabilite.sh"]
)
def test_aucun_script_ne_lit_le_nom_dans_la_reponse_de_update(nom: str) -> None:
    script = (RACINE / "infra" / "azure" / nom).read_text(encoding="utf-8")
    assert 'source "$(dirname "$0")/reessai.sh"' in script
    assert "latestRevisionName" not in script
    assert "nouvelle_revision " in script


@pytest.mark.parametrize(("verdict", "attendu"), [("true", 0), ("True", 0), ("false", 1), ("", 1)])
def test_revision_conforme(tmp_path: Path, verdict: str, attendu: int) -> None:
    # Sert à la relance : rien à changer si la révision en service porte déjà la modification.
    resultat, _ = nouvelle(tmp_path, ["app--0082"], verdict, "revision_conforme app app--0082 c")
    assert resultat.returncode == attendu, resultat.stderr
