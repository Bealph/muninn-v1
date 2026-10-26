"""Retour arrière (`infra/azure/retour-arriere.sh`) avec un faux `az` et un faux `curl`.

Chaque cas décrit les révisions de l'API et de la console (nom, commit de l'image) et celle qui
reçoit le trafic ; le test lit les bascules demandées. Aucun appel à Azure. Le cas de la panne type
(révision de configuration : même image, autre réglage) échouait avant le 26 octobre 2026.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "infra" / "azure" / "retour-arriere.sh"
BASH = shutil.which("bash")
API, CONSOLE = "ca-muninn-api-prod", "ca-muninn-console-prod"

pytestmark = pytest.mark.skipif(BASH is None, reason="bash absent")

FAUX_AZ = r"""#!/usr/bin/env bash
app=""; prec=""
for a in "$@"; do [ "$prec" = "-n" ] && app="$a"; prec="$a"; done
case "$*" in
  *"revision list"*"--all"*) cat "$SCENARIO/$app.revisions" ;;
  *"revision list"*) cat "$SCENARIO/$app.service" ;;
  *"revision show"*) echo true ;;
  *"traffic set"*) echo "$app $*" >> "$SCENARIO/bascules" ;;
  *"containerapp show"*) echo api.exemple.invalid ;;
esac
"""
FAUX_CURL = """#!/usr/bin/env bash
echo "{\\"git_sha\\":\\"$SHA_SERVI\\"}"
"""


def lancer(
    tmp_path: Path, api: list[tuple[str, str]], console: list[tuple[str, str]],
    en_service: tuple[str, str], sha: str = "", servi: str = "",
) -> tuple[subprocess.CompletedProcess[str], list[str]]:  # fmt: skip
    """Révisions par date de création ; rend la sortie et les bascules (application, révision)."""
    scenario = tmp_path / "scenario"
    scenario.mkdir()
    for app, revisions, service in ((API, api, en_service[0]), (CONSOLE, console, en_service[1])):
        lignes = "".join(
            f"{nom}\tcrmuninn.azurecr.io/muninn:{commit}\n" for nom, commit in revisions
        )
        (scenario / f"{app}.revisions").write_text(lignes, encoding="utf-8", newline="\n")
        (scenario / f"{app}.service").write_text(service + "\n", encoding="utf-8", newline="\n")
    outils = tmp_path / "bin"
    outils.mkdir()
    for nom, contenu in (("az", FAUX_AZ), ("curl", FAUX_CURL)):
        (outils / nom).write_text(contenu, encoding="utf-8", newline="\n")
        (outils / nom).chmod(0o755)
    env = os.environ | {"SCENARIO": scenario.as_posix(), "SHA_SERVI": servi}
    commande = (
        f'export PATH="$(cd "{outils.as_posix()}" && pwd):$PATH"; '
        f'bash "{SCRIPT.as_posix()}" production {sha}'
    )
    # Entrée maîtrisée : bash trouvé par `shutil.which`, script du dépôt.
    resultat = subprocess.run(  # noqa: S603
        [BASH or "bash", "-c", commande], capture_output=True, text=True, encoding="utf-8",
        env=env, check=False,
    )  # fmt: skip
    fichier = scenario / "bascules"
    bascules = fichier.read_text(encoding="utf-8").splitlines() if fichier.exists() else []
    return resultat, [" ".join((b.split()[0], b.split("--revision-weight ")[1].split("=")[0]))
                      for b in bascules]  # fmt: skip


def test_livraison_normale_retour_a_la_version_precedente(tmp_path: Path) -> None:
    r, bascules = lancer(
        tmp_path, api=[("a1", "X"), ("a2", "Y")], console=[("c1", "X"), ("c2", "Y")],
        en_service=("a2", "c2"), servi="X",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert bascules == [f"{API} a1", f"{CONSOLE} c1"]


def test_panne_de_configuration_sans_sha(tmp_path: Path) -> None:
    # a3 : même image que a2, mauvais réglage. La console n'a pas bougé : elle reste sur c2.
    r, bascules = lancer(
        tmp_path, api=[("a1", "X"), ("a2", "Y"), ("a3", "Y")],
        console=[("c1", "X"), ("c2", "Y")], en_service=("a3", "c2"), servi="Y",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert bascules == [f"{API} a2", f"{CONSOLE} c2"]


def test_panne_de_configuration_avec_le_sha_servi(tmp_path: Path) -> None:
    # Demander Y alors que la révision en panne sert Y : revenir à a2, pas rester sur a3.
    r, bascules = lancer(
        tmp_path, api=[("a1", "X"), ("a2", "Y"), ("a3", "Y")],
        console=[("c1", "X"), ("c2", "Y")], en_service=("a3", "c2"), sha="Y", servi="Y",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert bascules == [f"{API} a2", f"{CONSOLE} c2"]


def test_retour_a_un_commit_ancien(tmp_path: Path) -> None:
    r, bascules = lancer(
        tmp_path, api=[("a1", "X"), ("a2", "Y"), ("a3", "Z")],
        console=[("c1", "X"), ("c2", "Y"), ("c3", "Z")], en_service=("a3", "c3"), sha="X",
        servi="X",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert bascules == [f"{API} a1", f"{CONSOLE} c1"]


def test_console_sans_le_commit_vise_rien_ne_bascule(tmp_path: Path) -> None:
    r, bascules = lancer(
        tmp_path, api=[("a1", "X"), ("a2", "Y")], console=[("c2", "Y")],
        en_service=("a2", "c2"), servi="X",
    )  # fmt: skip
    assert r.returncode != 0
    assert "ne porte le commit X" in r.stderr and bascules == []


def test_aucune_revision_anterieure(tmp_path: Path) -> None:
    r, bascules = lancer(
        tmp_path, api=[("a1", "X")], console=[("c1", "X")], en_service=("a1", "c1"), servi="X"
    )
    assert r.returncode != 0 and "Aucune révision antérieure" in r.stderr and bascules == []
