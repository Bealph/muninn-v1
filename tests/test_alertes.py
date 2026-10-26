"""Alerte Azure Monitor AL-04 (sprint 5, étape 5) : modèle ARM construit sans Azure.

La requête a été rejouée sur l'espace `log-muninn` et sur des journaux fabriqués aux seuils exacts
(26 octobre 2026) ; ici, on fixe ce que le modèle doit garantir à chaque relance.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
CONSTRUIRE = RACINE / "infra" / "azure" / "alertes" / "construire.py"


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("construire_alertes", CONSTRUIRE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ressources() -> dict[str, dict]:  # type: ignore[type-arg]
    sortie = subprocess.run(  # noqa: S603 : interpréteur courant, script du dépôt
        [sys.executable, str(CONSTRUIRE)], capture_output=True, check=True
    ).stdout
    sortie.decode("ascii")  # lisible par az quel que soit l'encodage de la console
    return {r["type"]: r for r in json.loads(sortie)["resources"]}


def test_versions_d_api_stables() -> None:
    r = ressources()
    assert r["Microsoft.Insights/actionGroups"]["apiVersion"] == "2023-01-01"
    assert r["Microsoft.Insights/actionGroups"]["location"] == "Global"
    assert r["Microsoft.Insights/scheduledQueryRules"]["apiVersion"] == "2023-12-01"
    assert r["Microsoft.Insights/scheduledQueryRules"]["kind"] == "LogAlert"


def test_regle_toutes_les_15_minutes_sur_une_heure() -> None:
    p = ressources()["Microsoft.Insights/scheduledQueryRules"]["properties"]
    assert (p["evaluationFrequency"], p["windowSize"]) == ("PT15M", "PT1H")
    (critere,) = p["criteria"]["allOf"]
    # La requête ne rend une ligne qu'au-delà du seuil : alerte dès qu'une ligne est rendue.
    assert (critere["timeAggregation"], critere["operator"], critere["threshold"]) == (
        "Count", "GreaterThan", 0
    )  # fmt: skip
    assert critere["query"] == module().requete()
    assert p["actions"]["actionGroups"] == [
        "[resourceId('Microsoft.Insights/actionGroups', 'ag-muninn')]"
    ]


def test_requete_production_seuils_de_d83() -> None:
    q = module().requete()
    assert "ca-muninn-api-prod" in q and "//" not in q
    assert "extractions >= 20 and part_secours > 0.05" in q
    assert "appels_modele >= 20 and part_echecs > 0.05" in q


def test_aucune_adresse_dans_le_modele() -> None:
    # L'adresse vient de COURRIEL_ALERTE au déploiement : jamais dans le dépôt.
    groupe = ressources()["Microsoft.Insights/actionGroups"]["properties"]
    (destinataire,) = groupe["emailReceivers"]
    assert destinataire["emailAddress"] == "[parameters('courriel')]"
    assert "@" not in CONSTRUIRE.read_text(encoding="utf-8")
