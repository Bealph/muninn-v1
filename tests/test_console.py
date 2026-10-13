"""Tests de la console : elle affiche la version livrée et la réponse rendue par l'API."""

from fastapi.testclient import TestClient

from muninn import __version__


def test_accueil_affiche_la_version_et_le_formulaire(client_console: TestClient) -> None:
    reponse = client_console.get("/")
    assert reponse.status_code == 200
    assert '<html lang="fr">' in reponse.text
    assert f"{__version__} (" in reponse.text
    assert 'name="question"' in reponse.text


def test_essai_affiche_la_reponse_du_llm(client_console: TestClient) -> None:
    reponse = client_console.post("/essai", data={"question": "Bonjour", "modele": "A"})
    assert reponse.status_code == 200
    assert "Réponse simulée (7 caractères reçus)." in reponse.text
    assert "faux" in reponse.text


def test_essai_affiche_l_erreur_de_l_api(client_console: TestClient) -> None:
    """Le modèle B n'est pas configuré dans les tests : l'API refuse, la console le dit."""
    reponse = client_console.post("/essai", data={"question": "Bonjour", "modele": "B"})
    assert reponse.status_code == 200
    assert "modèle B n&#39;est pas configuré" in reponse.text


def test_essai_echappe_le_html(client_console: TestClient) -> None:
    reponse = client_console.post("/essai", data={"question": "<script>x</script>"})
    assert "<script>x</script>" not in reponse.text
