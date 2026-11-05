"""Vitrine de l'audit RGAA (C10) : données tirées du rapport, de la grille et du parcours NVDA."""

import importlib.util
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
VITRINE = RACINE / "infra" / "accessibilite" / "vitrine.py"
PAGE = RACINE / "docs" / "v1" / "accessibilite" / "vitrine.html"


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vitrine_accessibilite", VITRINE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_taux_et_criteres_coherents_avec_la_grille() -> None:
    d = module().donnees()
    t = d["taux"]
    assert (t["avant"]["c"], t["avant"]["nc"], t["avant"]["na"]) == (56, 16, 34)
    assert (t["apres"]["c"], t["apres"]["nc"], t["apres"]["na"]) == (72, 0, 34)
    assert len(d["criteres"]) == 106 and len(d["themes"]) == 13

    # Les comptes de la grille ligne par ligne retrouvent ceux de la section « Taux ».
    def etat(c: dict[str, object]) -> str:
        v = list(c["verdicts"].values())  # type: ignore[attr-defined]
        return "NC" if "NC" in v else "C" if "C" in v else "NA"

    comptes = {x: sum(etat(c) == x for c in d["criteres"]) for x in ("C", "NC", "NA")}
    assert comptes == {"C": 72, "NC": 0, "NA": 34}


def test_corrections_parcours_et_en_clair() -> None:
    d = module().donnees()
    assert len(d["corrections"]) == 11 and d["corrections"][0]["criteres"] == "12.7"
    assert len(d["nvda"]["etapes"]) == 24
    assert all(e["observe"] == "OK" for e in d["nvda"]["etapes"])
    assert d["nvda"]["champs"]["Version de NVDA"] == "2026.3"
    assert set(d["clair"]) == {"Chapeau", "Méthode", "Limite"}
    assert d["cadrage"] and d["limites"] and d["remarques"]


def test_la_page_publiee_est_a_jour() -> None:
    """Le rapport, la grille ou le parcours modifiés sans régénérer la page font échouer ce test."""
    m = module()
    assert PAGE.read_text(encoding="utf-8") == m.page(m.donnees()), (
        "vitrine.html périmée : relancer `python infra/accessibilite/vitrine.py`"
    )
