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
    assert len(sources) == 14 and len(d["themes"]) == 9
    assert {s["theme"] for s in sources.values()} <= set(d["themes"])
    c = d["collecte"]
    assert c["fichier"] == "2026-11-05-3j.md" and c["total"] == 57 and c["retirees"] == 0
    liees = {e["fiche"] for e in c["entrees"] if e["fiche"]}
    # Seules les fiches dont l'entrée figure dans la dernière collecte y sont reliées.
    assert liees == {"v-2026-11-03-06", "v-2026-11-05-01"}
    assert len(d["fiches"]) == 10
    assert all(f["en_clair"] and f["verification"] for f in d["fiches"])
    s = d["synthese"]
    assert [r["n"] for r in s["recommandations"]] == ["R1", "R2", "R3"]
    assert all(r["en_clair"] for r in s["recommandations"]) and s["chapeau_clair"]
    assert set(s["raisonnements"]) == {"R1", "R3"} and len(s["sources_citees"]) == 1
    assert len(d["glossaire"]) >= 8
    # La séance qui a présenté la synthèse, et ses décisions consignées depuis.
    assert [(x["date"], x["participants"]) for x in s["seances"]] == [
        ("2026-11-06", ["Porteur", "formateur"])
    ]
    assert {"D-91", "D-94", "D-95"} <= set(d["decisions"])


def test_seances_rattachees_a_leur_synthese(tmp_path: Path) -> None:
    m = module()
    (tmp_path / "MODELE.md").write_text("| Support | `S-AAAA` |", encoding="utf-8")
    (tmp_path / "2026-12-01.md").write_text(
        "| Champ | Valeur |\n| --- | --- |\n| Participants | Porteur ; pair |\n"
        "| Support | `../syntheses/S-2026-11-30.md` |\n",
        encoding="utf-8",
    )
    assert m.lire_seances(tmp_path) == [
        {"date": "2026-12-01", "synthese": "S-2026-11-30", "participants": ["Porteur", "pair"]}
    ]
    journal = tmp_path / "decisions.md"
    lignes = "| ID | Date |\n| D-07 | 2026-10-12 |\n| D-12 | 2026-10-13 |\n"
    journal.write_text(lignes, encoding="utf-8")
    assert m.decisions_consignees(journal) == ["D-07", "D-12"]
    assert m.decisions_consignees(tmp_path / "absent.md") == []


def test_la_page_publiee_est_a_jour() -> None:
    """Une fiche ou une collecte modifiée sans régénérer la page fait échouer ce test."""
    m = module()
    assert PAGE.read_text(encoding="utf-8") == m.page(m.donnees()), (
        "vitrine.html périmée : relancer `python infra/veille/vitrine.py`"
    )
