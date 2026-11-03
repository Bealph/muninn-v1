"""Vitrine du benchmark C7 : données tirées du rapport et de la mesure, texte jamais interprété."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
VITRINE = RACINE / "infra" / "benchmark" / "vitrine.py"
PAGE = RACINE / "docs" / "v1" / "benchmark-services-ia" / "vitrine.html"


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vitrine_benchmark", VITRINE)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_gras_decoupe_avec_son_code() -> None:
    assert module().seg("**Contrôle (`fidelite.py`) :** 30 appels") == [
        {"b": [{"t": "Contrôle ("}, {"code": "fidelite.py"}, {"t": ") :"}]},
        {"t": " 30 appels"},
    ]


def test_blocs_puce_avec_sous_liste_et_suite() -> None:
    corps = "- Premier :\n  - a\n  - b\n\n  Suite du premier.\n- Second\n\n1. Un\n   suite\n2. Deux"
    liste, ordonnee = module().blocs(corps)
    assert liste["type"] == "liste" and not liste["ordonnee"] and len(liste["items"]) == 2
    assert len(liste["items"][0]["sous"]) == 2 and liste["items"][0]["suite"] == [
        [{"t": "Suite du premier."}]
    ]
    assert ordonnee["ordonnee"] and [i["s"][0]["t"] for i in ordonnee["items"]] == [
        "Un suite",
        "Deux",
    ]


def test_seuls_verdict_et_eliminatoires_sont_colores() -> None:
    m = module()
    tableau = m.blocs(
        "| Critère | A | B |\n| --- | --- | --- |\n| UE (éliminatoire) | Établi | Non établi |\n"
        "| Délai (principal) | Non publié | Mesuré |\n| Verdict | 1er | Écarté (UE) |"
    )[0]
    etats = [[c["e"] for c in ligne[1:]] for ligne in tableau["lignes"]]
    assert etats == [["oui", "non"], ["", ""], ["oui", "non"]]
    assert m.etat("Contradictoire (prix : activé)") == "non"
    assert m.etat("Établi sous réserve : région EU1") == "partie"


def test_donnees_reelles_coherentes() -> None:
    d = module().donnees()
    assert [r["categorie"] for r in d["reponse"]] == [
        "Transcription",
        "Synthèse vocale",
        "Téléphonie",
    ]
    assert all(r["clair"] for r in d["reponse"]) and d["chapeau_clair"] and d["mesure_clair"]
    assert d["services"] == 15 and [c["id"] for c in d["categories"]] == [
        "transcription",
        "synthese",
        "telephonie",
    ]
    assert all(
        c["grille"] and c["grille"]["lignes"][-1][0]["s"][0]["t"] == "Verdict"
        for c in d["categories"]
    )
    r = d["mesure"]["resultats"]
    assert r["appels_mesures"] == 48 and r["groupes_chiffres_exacts"] == 69
    assert d["regles"] and d["ecarts"] and d["limites"] and "D-93" in d["decisions"]


def test_le_json_ne_peut_pas_fermer_la_balise_script(tmp_path: Path) -> None:
    modele = tmp_path / "modele.html"
    modele.write_text("<script>/*DONNEES*/</script>", encoding="utf-8")
    texte = module().page({"titre": "</script><!--x"}, modele)
    assert texte.count("</script>") == 1 and "<!--" not in texte
    assert (
        json.loads(texte.removeprefix("<script>").removesuffix("</script>"))["titre"]
        == "</script><!--x"
    )


def test_la_page_publiee_est_a_jour() -> None:
    """Le rapport ou la mesure modifiés sans régénérer la page font échouer ce test."""
    m = module()
    assert PAGE.read_text(encoding="utf-8") == m.page(m.donnees()), (
        "vitrine.html périmée : relancer `python infra/benchmark/vitrine.py`"
    )
