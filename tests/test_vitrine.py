"""Vitrine de la veille (C6) : données extraites des fichiers, texte externe jamais interprété."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
VITRINE = RACINE / "infra" / "veille" / "vitrine.py"
PAGE = RACINE / "docs" / "veille" / "vitrine.html"


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vitrine", VITRINE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_segments_sans_html_et_liens_https_seulement() -> None:
    m = module()
    s = m.segments("Voir `al04.kql`, [la page](https://exemple.org/a) et <https://exemple.org/b>.")
    assert s == [
        {"t": "Voir "},
        {"code": "al04.kql"},
        {"t": ", "},
        {"a": "la page", "href": "https://exemple.org/a"},
        {"t": " et "},
        {"a": "https://exemple.org/b", "href": "https://exemple.org/b"},
        {"t": "."},
    ]
    # Un lien qui n'est pas en https reste du texte ; une balise reste du texte.
    assert m.segments("[x](javascript:alert(1)) <img src=x>") == [
        {"t": "[x](javascript:alert(1)) <img src=x>"}
    ]


def test_le_json_ne_peut_pas_fermer_la_balise_script(tmp_path: Path) -> None:
    m = module()
    modele = tmp_path / "modele.html"
    modele.write_text("<script>/*DONNEES*/</script>", encoding="utf-8")
    texte = m.page({"titre": "</script><script>alert(1)</script>", "x": "<!--<script>"}, modele)
    assert texte.count("</script>") == 1 and "<!--" not in texte
    charge = texte.removeprefix("<script>").removesuffix("</script>")
    assert json.loads(charge)["titre"].startswith("</script>")


def test_la_collecte_la_plus_longue_l_emporte_a_date_egale() -> None:
    m = module()
    noms = ["2026-11-03-7j.md", "2026-11-03-30j.md", "2026-11-02-30j.md"]
    assert max((Path(n) for n in noms), key=m.cle_collecte).name == "2026-11-03-30j.md"


def test_donnees_reelles_coherentes() -> None:
    d = module().donnees()
    sources = {s["code"]: s for s in d["sources"]}
    assert len(sources) == 14 and len(d["themes"]) == 8
    assert {s["theme"] for s in sources.values()} <= set(d["themes"])
    c = d["collecte"]
    assert c["fichier"] == "2026-11-03-30j.md" and c["total"] == 171 and c["retirees"] == 1
    liees = {e["fiche"] for e in c["entrees"] if e["fiche"]}
    assert len(liees) == 6  # la fiche 07 vient d'une source lue à la main
    assert all(f["en_clair"] and f["verification"] for f in d["fiches"])
    s = d["synthese"]
    assert [r["n"] for r in s["recommandations"]] == ["R1", "R2", "R3", "R4"]
    assert all(r["en_clair"] for r in s["recommandations"]) and s["chapeau_clair"]
    assert "R1" in s["raisonnements"] and len(s["sources_citees"]) == 3
    assert len(d["glossaire"]) >= 8


def test_la_page_publiee_est_a_jour() -> None:
    """Une fiche ou une collecte modifiée sans régénérer la page fait échouer ce test."""
    m = module()
    assert PAGE.read_text(encoding="utf-8") == m.page(m.donnees()), (
        "vitrine.html périmée : relancer `python infra/veille/vitrine.py`"
    )
