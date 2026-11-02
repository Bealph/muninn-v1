"""Révision de test par PR (C19) : droits minimaux, préproduction intouchée, contrôles réels.

Le script de la CI tourne contre un faux `az` et un faux `curl` placés en tête du PATH : aucun
appel à Azure. Les autres tests lisent la définition du rôle, le script de création et le
workflow.
"""

import json
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
AZURE = RACINE / "infra" / "azure"
TESTER = AZURE / "tester-pr.sh"
CREER = AZURE / "15-test.sh"
ROLE = AZURE / "roles" / "test-pr.json"
CI = RACINE / ".github" / "workflows" / "ci.yml"
BASH = shutil.which("bash")
SHA = "a" * 40

FAUX_AZ = """#!/usr/bin/env bash
echo "az $*" >> "$JOURNAL"
case "$*" in
  *"configuration.secrets"*) echo "$SECRETS" ;;
  *"ingress.fqdn"*) echo "ca-muninn-api-test.exemple" ;;
  *"show-tags"*) printf '%s\\n' $ETIQUETTES ;;
esac
"""

FAUX_CURL = """#!/usr/bin/env bash
echo "curl $*" >> "$JOURNAL"
case "$*" in
  *"/version"*) echo "{\\"git_sha\\":\\"$SERVI\\"}" ;;
  *"/health"*) echo '{"status":"ok","environment":"test"}' ;;
  *"/llm/essai"*) echo "{\\"fournisseur\\":\\"$FOURNISSEUR\\"}" ;;
esac
"""


def lancer(
    tmp_path: Path,
    secrets: str = "0",
    servi: str = SHA,
    fournisseur: str = "azure",
    etiquettes: list[str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], str]:
    dossier = tmp_path / "bin"
    dossier.mkdir()
    for nom, contenu in (("az", FAUX_AZ), ("curl", FAUX_CURL)):
        faux = dossier / nom
        faux.write_text(contenu, encoding="utf-8", newline="\n")
        faux.chmod(0o755)
    journal = tmp_path / "journal"
    journal.write_text("", encoding="utf-8")
    env = os.environ | {
        "JOURNAL": journal.as_posix(),
        "SECRETS": secrets,
        "SERVI": servi,
        "FOURNISSEUR": fournisseur,
        "ETIQUETTES": " ".join(etiquettes or [SHA]),
        "ATTENTE_ESSAIS": "2",
        "ATTENTE_PAUSE_S": "0",
        "REESSAI_PAUSE_S": "0",
    }
    env.pop("GITHUB_OUTPUT", None)
    env.pop("GITHUB_STEP_SUMMARY", None)
    script = (
        f'export PATH="$(cd "{dossier.as_posix()}" && pwd):$PATH"; bash "{TESTER.as_posix()}" {SHA}'
    )
    # Entrée maîtrisée : bash trouvé par `shutil.which`, faux outils écrits par le test.
    resultat = subprocess.run(  # noqa: S603
        [BASH or "bash", "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    return resultat, journal.read_text(encoding="utf-8")


avec_bash = pytest.mark.skipif(BASH is None, reason="bash absent")


@avec_bash
def test_une_pr_saine_est_servie_et_controlee(tmp_path: Path) -> None:
    resultat, journal = lancer(tmp_path)
    assert resultat.returncode == 0, resultat.stderr
    assert f"--image crmuninntest.azurecr.io/muninn:{SHA}" in journal
    assert f"GIT_SHA={SHA}" in journal
    assert "/llm/essai" in journal and "/health" in journal


@avec_bash
def test_la_preproduction_et_la_production_ne_sont_jamais_touchees(tmp_path: Path) -> None:
    _, journal = lancer(tmp_path)
    commandes_az = [ligne for ligne in journal.splitlines() if ligne.startswith("az ")]
    assert commandes_az
    for ligne in commandes_az:
        assert "preprod" not in ligne and "-prod" not in ligne, ligne
        assert "crmuninn.azurecr.io" not in ligne, ligne
        assert "ingress traffic" not in ligne and "revision deactivate" not in ligne, ligne
        if "containerapp" in ligne:
            assert "-n ca-muninn-api-test" in ligne, ligne


@avec_bash
def test_une_application_de_test_avec_secret_est_refusee(tmp_path: Path) -> None:
    resultat, journal = lancer(tmp_path, secrets="1")
    assert resultat.returncode != 0
    assert "containerapp update" not in journal


@avec_bash
def test_une_image_qui_ne_sert_pas_le_sha_echoue(tmp_path: Path) -> None:
    resultat, _ = lancer(tmp_path, servi="b" * 40)
    assert resultat.returncode != 0
    assert "ne sert pas" in resultat.stderr


@avec_bash
def test_un_modele_injoignable_echoue(tmp_path: Path) -> None:
    resultat, _ = lancer(tmp_path, fournisseur="faux")
    assert resultat.returncode != 0


@avec_bash
def test_le_registre_de_test_garde_les_dix_images_recentes(tmp_path: Path) -> None:
    etiquettes = [SHA] + [f"ancienne{i:02d}" for i in range(1, 13)]
    resultat, journal = lancer(tmp_path, etiquettes=etiquettes)
    assert resultat.returncode == 0, resultat.stderr
    supprimees = [ligne for ligne in journal.splitlines() if "repository delete" in ligne]
    assert [ligne.split("--image muninn:")[1].split()[0] for ligne in supprimees] == [
        "ancienne10",
        "ancienne11",
        "ancienne12",
    ]


def test_le_role_ne_peut_rien_supprimer_ni_basculer() -> None:
    """Liste fermée : toute action ajoutée au rôle doit passer par ce test."""
    role = json.loads(ROLE.read_text(encoding="utf-8"))
    assert set(role["Actions"]) == {
        "Microsoft.App/containerApps/read",
        "Microsoft.App/containerApps/write",
        "Microsoft.App/containerApps/revisions/read",
        "Microsoft.App/containerApps/listSecrets/action",
        "Microsoft.App/managedEnvironments/read",
        "Microsoft.App/managedEnvironments/join/action",
        "Microsoft.ManagedIdentity/userAssignedIdentities/read",
        "Microsoft.ManagedIdentity/userAssignedIdentities/assign/action",
    }
    assert role["DataActions"] == [] and role["AssignableScopes"] == ["__PORTEE__"]
    assert all("*" not in a and "delete" not in a.lower() for a in role["Actions"])


def test_l_application_de_test_est_creee_sans_base_ni_secret() -> None:
    texte = CREER.read_text(encoding="utf-8")
    assert "--revisions-mode single" in texte
    # Mise en conformité à chaque passage : une PR a pu changer l'échelle ou les variables.
    assert texte.count("--max-replicas 1") == 2 and "--replace-env-vars" in texte
    assert "--secrets" not in texte and "DATABASE_URL" not in texte
    assert '--user-assigned "$evaluation_id"' in texte
    # Aucun rôle intégré large : Container Apps Contributor permet de supprimer.
    assert "ROLE_CONTAINER_APPS_CONTRIBUTOR" not in texte
    assert "Contributor" not in texte and "Owner" not in texte


def job(nom: str) -> str:
    texte = CI.read_text(encoding="utf-8")
    debut = texte.index(f"\n  {nom}:\n")
    suite = texte.find("\n  ", debut + 1)
    while suite != -1 and texte[suite + 3] == " ":
        suite = texte.find("\n  ", suite + 1)
    return texte[debut : suite if suite != -1 else len(texte)]


def test_le_job_de_test_est_borne_et_requis() -> None:
    test = job("test")
    assert "if: github.ref != 'refs/heads/main'" in test
    assert "needs: build" in test
    assert "name: test" in test and "id-token: write" in test
    assert "name: preproduction" not in test and "name: production" not in test
    assert "queue: max" in test and "cancel-in-progress: true" not in test
    assert "crmuninntest.azurecr.io" in test and "crmuninn.azurecr.io" not in test
    assert "secrets." not in test
    assert "needs: [lint, tests, build, secrets, evaluation, test]" in job("verdict")


@avec_bash
@pytest.mark.parametrize(
    ("ref", "resultat_test", "vert"),
    [
        ("refs/pull/7/merge", "success", True),
        ("refs/pull/7/merge", "failure", False),
        ("refs/pull/7/merge", "skipped", False),
        # Lancement manuel sur une branche : la révision de test est exigée aussi.
        ("refs/heads/feat/essai", "skipped", False),
        ("refs/heads/feat/essai", "success", True),
        ("refs/heads/main", "skipped", True),
        ("refs/heads/main", "success", False),
    ],
)
def test_le_verdict_exige_la_revision_de_test_hors_de_main(
    ref: str, resultat_test: str, vert: bool
) -> None:
    verdict = job("verdict")
    script = textwrap.dedent(verdict.split("run: |\n", 1)[1])
    script = re.sub(
        r"\$\{\{ needs\.(\w+)\.result \}\}",
        "success",
        script.replace("${{ needs.test.result }}", resultat_test),
    ).replace("${{ github.ref }}", ref)
    assert "${{" not in script
    # Entrée maîtrisée : bash trouvé par `shutil.which`, script lu dans le workflow du dépôt.
    fin = subprocess.run(  # noqa: S603
        [BASH or "bash", "-e", "-c", script], capture_output=True, check=False
    )
    assert (fin.returncode == 0) is vert
