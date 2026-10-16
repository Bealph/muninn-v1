"""Jeu de questions de démonstration (sprint 3, livrable) et sa vérification."""

from pathlib import Path

from muninn.referentiels import demonstration

STATUTS = {"trouve", "hors_corpus", "hors_perimetre", "incoherent"}


def test_jeu_conforme_au_livrable() -> None:
    """De 5 à 10 questions, couvertes et hors corpus, chacune avec sa réponse attendue."""
    questions = demonstration.questions()
    assert 5 <= len(questions) <= 10
    assert len({q["id"] for q in questions}) == len(questions)
    assert {q["statut"] for q in questions} >= {"trouve", "hors_corpus", "hors_perimetre"}
    for q in questions:
        assert q["statut"] in STATUTS and q["point"] in {"communes", "termes", "marche"}
        if q["statut"] in {"trouve", "incoherent"}:
            assert q["contient"] and q["source"], q["id"]


def test_ecarts_detectes() -> None:
    question = {"statut": "trouve", "contient": ["94300"], "source": "SRC-07"}
    juste = {"statut": "trouve", "candidates": [{"codes_postaux": ["94300"]}],
             "sources": [{"source_id": "SRC-07"}]}  # fmt: skip
    assert demonstration.ecarts(question, juste) == []
    faux = {"statut": "hors_corpus", "candidates": [], "sources": []}
    assert demonstration.ecarts(question, faux) == [
        "statut hors_corpus au lieu de trouve",
        "« 94300 » absent",
        "source SRC-07 non citée",
    ]


def test_document_lisible_conforme_au_jeu() -> None:
    """Le document du livrable dit la même chose que le jeu rejoué par la machine."""
    document = (
        Path(__file__).parents[1] / "docs/v1/sprints/sprint-3/questions-demonstration.md"
    ).read_text(encoding="utf-8")
    lignes = {
        ligne.split("|")[1].strip(): ligne
        for ligne in document.splitlines()
        if ligne.startswith("| Q")
    }
    assert set(lignes) == {q["id"] for q in demonstration.questions()}
    for q in demonstration.questions():
        assert f"`{q['statut']}`" in lignes[q["id"]], q["id"]
        for valeur in q["contient"]:
            if valeur != "wiktionary.org":  # lien rendu en clair dans le document
                assert valeur in lignes[q["id"]], (q["id"], valeur)
