"""Classeur Azure Monitor (sprint 5, étape 4) : modèle ARM construit sans Azure.

Le déploiement réel est fait par `infra/azure/10-classeur.sh` ; ici, on vérifie ce que le modèle
doit garantir à chaque relance.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
CONSTRUIRE = RACINE / "infra" / "azure" / "classeur" / "construire.py"


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("construire", CONSTRUIRE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_une_requete_par_section_et_rien_de_plus() -> None:
    c = module()
    assert [nom for nom, _, _ in c.SECTIONS] == list(c.requetes())


def test_contenu_au_format_des_exemples_officiels() -> None:
    contenu = module().contenu()
    assert contenu["version"] == "Notebook/1.0"
    types = {item["type"] for item in contenu["items"]}
    assert types == {1, 3, 9}  # texte, requête, paramètres : rien d'autre
    for item in contenu["items"]:
        if item["type"] == 3:
            assert item["content"]["queryType"] == 0
            assert item["content"]["visualization"] == "table"


def test_parametres_declares_pour_chaque_usage() -> None:
    c = module()
    parametres = next(i for i in c.contenu()["items"] if i["type"] == 9)
    declares = {p["name"] for p in parametres["content"]["parameters"]}
    utilises = set(re.findall(r"\{(\w+)\}", "\n".join(c.requetes().values())))
    assert utilises <= declares, utilises - declares


def test_requetes_d_un_appel_gardees_contre_un_identifiant_vide() -> None:
    # Sans garde, « Log_s has "" » rendrait toutes les lignes de journal.
    for nom, q in module().requetes().items():
        if "{Requete}" in q:
            assert '"{Requete}" != ""' in q, nom


def test_modele_arm_stable_et_ascii() -> None:
    sortie = subprocess.run(  # noqa: S603 : interpréteur courant, script du dépôt
        [sys.executable, str(CONSTRUIRE)], capture_output=True, check=True
    ).stdout
    sortie.decode("ascii")  # lisible par az quel que soit l'encodage de la console
    m = json.loads(sortie)
    (r,) = m["resources"]
    assert r["type"] == "Microsoft.Insights/workbooks" and r["apiVersion"] == "2023-06-01"
    assert r["name"] == "[guid(resourceGroup().id, 'muninn-classeur-exploitation')]"
    assert r["kind"] == "shared" and r["properties"]["category"] == "workbook"
    contenu = json.loads(r["properties"]["serializedData"])
    assert contenu == module().contenu()
    # Deux constructions donnent le même modèle : une relance ne change rien.
    assert (
        sortie
        == subprocess.run(  # noqa: S603
            [sys.executable, str(CONSTRUIRE)], capture_output=True, check=True
        ).stdout
    )
