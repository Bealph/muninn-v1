"""Vigie (C20) : une alerte, déclenchée ou résolue, ouvre une issue « Incident », une seule fois.

La forme des alertes est celle de l'API Alerts Management, version 2019-03-01 (lue le
2 novembre 2026).
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

RACINE = Path(__file__).resolve().parents[1]
VIGIE = RACINE / "infra" / "github" / "vigie.py"
WORKFLOW = RACINE / ".github" / "workflows" / "vigie.yml"
REGLE = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/adialloRG/providers/"
    "microsoft.insights/scheduledqueryrules/al04-muninn-modele"
)


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vigie", VIGIE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def alerte(
    numero: int, condition: str = "Fired", debut: str = "2026-10-26T09:33:42Z"
) -> dict[str, Any]:
    return {
        "id": f"/subscriptions/0000/providers/Microsoft.AlertsManagement/alerts/{numero:04d}",
        "name": "al04-muninn-modele",
        "properties": {
            "essentials": {
                "severity": "Sev2",
                "monitorCondition": condition,
                "alertState": "New",
                "alertRule": REGLE,
                "targetResource": "/subscriptions/0000/resourceGroups/adialloRG/providers/"
                "microsoft.operationalinsights/workspaces/log-muninn",
                "startDateTime": debut,
            }
        },
    }


def test_une_alerte_declenchee_ouvre_une_issue() -> None:
    issues = module().a_ouvrir({"value": [alerte(1)]}, [])
    assert len(issues) == 1
    assert issues[0]["titre"] == "Incident · al04-muninn-modele · 2026-10-26T09:33:42Z"
    corps = issues[0]["corps"]
    assert "<!-- alerte-azure: /subscriptions/0000/providers/" in corps
    assert "| Gravité | Sev2 (avertissement) |" in corps
    assert "| Ressource visée | log-muninn |" in corps
    for section in ("## Symptôme", "## Diagnostic", "## Cause racine", "## Correctif"):
        assert section in corps


def test_une_alerte_deja_connue_n_ouvre_rien() -> None:
    """Même si l'issue est fermée : son corps porte toujours l'identifiant de l'alerte."""
    m = module()
    deja = m.a_ouvrir({"value": [alerte(1)]}, [])[0]
    assert m.a_ouvrir({"value": [alerte(1)]}, [{"number": 7, "body": deja["corps"]}]) == []


def test_une_alerte_resolue_avant_le_passage_ouvre_une_issue() -> None:
    """AL-04 se résout seule en 90 min environ et la vigie passe rarement : l'incident resterait."""
    issues = module().a_ouvrir({"value": [alerte(1, "Resolved")]}, [])
    assert len(issues) == 1
    assert "| Condition à la lecture | Resolved |" in issues[0]["corps"]


def test_une_alerte_passee_de_declenchee_a_resolue_n_ouvre_pas_deux_issues() -> None:
    """L'identifiant de l'alerte ne change pas à la résolution : l'issue déjà ouverte suffit."""
    m = module()
    deja = m.a_ouvrir({"value": [alerte(1, "Fired")]}, [])[0]
    assert (
        m.a_ouvrir({"value": [alerte(1, "Resolved")]}, [{"number": 7, "body": deja["corps"]}]) == []
    )


def test_une_condition_inconnue_n_ouvre_rien() -> None:
    assert module().a_ouvrir({"value": [alerte(1, "Autre")]}, []) == []


def test_plusieurs_alertes_dans_l_ordre_de_declenchement() -> None:
    reponse = {
        "value": [alerte(2, debut="2026-11-02T10:00:00Z"), alerte(1, debut="2026-11-02T09:00:00Z")]
    }
    titres = [i["titre"] for i in module().a_ouvrir(reponse, [])]
    assert titres == [
        "Incident · al04-muninn-modele · 2026-11-02T09:00:00Z",
        "Incident · al04-muninn-modele · 2026-11-02T10:00:00Z",
    ]


def test_reponse_vide_ou_incomplete() -> None:
    m = module()
    assert m.a_ouvrir({}, []) == []
    assert (
        m.a_ouvrir({"value": [{"properties": {"essentials": {"monitorCondition": "Fired"}}}]}, [])
        == []
    )


def test_ligne_de_commande(tmp_path: Path) -> None:
    (tmp_path / "alertes.json").write_text(json.dumps({"value": [alerte(3)]}), encoding="utf-8")
    (tmp_path / "issues.json").write_text("[]", encoding="utf-8")
    sortie = subprocess.run(  # noqa: S603 : interpréteur courant, script du dépôt
        [sys.executable, str(VIGIE), str(tmp_path / "alertes.json"), str(tmp_path / "issues.json")],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    assert len(json.loads(sortie)) == 1


def test_workflow_lecture_seule_et_actions_epinglees() -> None:
    """Le workflow n'a que les droits utiles, et chaque action tierce est épinglée par son SHA."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert "environment: vigie" in texte
    assert "issues: write" in texte and "id-token: write" in texte
    assert "contents: write" not in texte and "pull-requests: write" not in texte
    assert "monitorCondition=" not in texte  # les alertes résolues doivent rester visibles
    for ligne in texte.splitlines():
        if "uses:" in ligne:
            version = ligne.split("@", 1)[1].split()[0]
            assert len(version) == 40, ligne


def test_la_periode_longue_est_reservee_a_l_essai() -> None:
    """« 30d » lit tout le mois : seulement pour prouver la visibilité, en essai."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert 'filtre="timeRange=1d"' in texte
    assert 'if [ "$ESSAI" = "true" ] && [ "$PERIODE" = "30d" ]; then' in texte
    assert "ESSAI: ${{ github.event_name == 'workflow_dispatch' && inputs.essai }}" in texte
