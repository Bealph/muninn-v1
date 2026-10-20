"""Contrôle automatique du jeu de V-08 (phase 1, document 04, §4.2), sans modèle.

Chaque valeur attendue non nulle figure dans la transcription, sous sa forme dite (ou elle est
déduite, et le scénario le dit) ; un téléphone attendu nul n'est ni présenté ni dicté ; aucune
fuite entre le test et le développement ; répartition du test conforme au §4.3.
"""

import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from muninn.extraction.entree import normaliser

DOSSIER = Path(__file__).parents[1] / "eval" / "v08"
JEU = json.loads((DOSSIER / "jeu.json").read_text(encoding="utf-8"))
DEV = json.loads((DOSSIER / "dev.json").read_text(encoding="utf-8"))
EXTRACTION = [s for s in JEU["scenarios"] + DEV["scenarios"] if "verite" in s]
REPARTITION = {
    "nominal": 6,
    "rendez_vous": 2,
    "adresse_partielle": 1,
    "adresse_incoherente": 1,
    "homonymes": 1,
    "bruit": 2,
    "champ_absent": 2,
    "gaz": 1,
    "medical": 1,
    "refus": 1,
    "injection": 1,
    "numero_dicte_different": 1,
}
# Code postal non dit, déduit (une seule commune, ou indice) : annoncé en note du scénario.
DEDUITS = {
    "T09": "code_postal",
    "T11": "code_postal",
    "D03": "code_postal",
    "D09": "code_postal",
    "D11": "code_postal",
}


def chiffres(texte: str) -> str:
    return re.sub(r"\D", "", texte)


@pytest.mark.parametrize("s", EXTRACTION, ids=[s["id"] for s in EXTRACTION])
def test_valeurs_attendues_dites(s: dict[str, Any]) -> None:
    v, t = s["verite"], s["transcription"]
    for champ in ("nom", "commune"):
        if v[champ] is not None:
            assert f" {normaliser(v[champ])} " in f" {normaliser(t)} ", champ
    if v["code_postal"] is not None and DEDUITS.get(s["id"]) != "code_postal":
        assert v["code_postal"] in chiffres(t), "code postal"
    tel = v["telephone"]
    if tel is not None:
        national = "0" + tel[3:]
        assert national in chiffres(t) or tel == s["numero_presente"], "téléphone"
    else:
        assert s["numero_presente"] is None and not re.search(r"0[67](\s?\d{2}){4}", t)


def test_aucune_fuite_entre_test_et_developpement() -> None:
    test = [s for s in JEU["scenarios"] if s["partition"] == "test"]
    dev = DEV["scenarios"]
    assert not {normaliser(s["transcription"]) for s in test} & {
        normaliser(s["transcription"]) for s in dev
    }

    def cle(s: dict[str, Any]) -> tuple[str | None, str | None]:
        return s["verite"]["nom"], s["verite"]["commune"]

    communs = {cle(s) for s in test} & {cle(s) for s in dev if "verite" in s}
    assert communs <= {(None, None)}  # deux refus sans nom ni commune : pas une fuite


def test_repartition_du_jeu_de_test() -> None:
    test = [s for s in JEU["scenarios"] if s["partition"] == "test"]
    assert Counter(s["categorie"] for s in test) == REPARTITION and len(test) == 20
    conformite = [s for s in JEU["scenarios"] if s["partition"] == "conformite"]
    assert {s["categorie"] for s in conformite} == {
        "medical", "injection", "gaz_positif", "gaz_negatif", "refus"
    }  # fmt: skip


def test_identifiants_uniques_et_numeros_fictifs() -> None:
    ids = [s["id"] for s in JEU["scenarios"] + DEV["scenarios"]]
    assert len(ids) == len(set(ids))
    for s in EXTRACTION:
        for n in (s["numero_presente"], s["verite"]["telephone"]):
            assert n is None or n.startswith("+3363998"), s["id"]  # plage fictive de l'ARCEP


def test_tirage_de_relecture_reproductible() -> None:
    tirage = JEU["tirage_relecture"]
    test = sorted(s["id"] for s in JEU["scenarios"] if s["partition"] == "test")
    choisis = random.Random(tirage["graine"]).sample(test, tirage["nombre"])  # noqa: S311 (tirage, pas de secret)
    assert len(choisis) == 4 and set(choisis) <= set(test)
