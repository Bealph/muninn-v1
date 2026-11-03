"""Tests de la console : elle affiche la version livrée et la réponse rendue par l'API."""

import hashlib

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


def test_polices_de_muninn_servies_par_la_console(client_console: TestClient) -> None:
    """D-92 : Nunito et IBM Plex Mono viennent de la console, jamais d'un service tiers."""
    page = client_console.get("/").text
    assert 'font-family: "Nunito"' in page and "fonts.googleapis.com" not in page
    for nom in ("Nunito-Regular", "Nunito-Bold", "Nunito-Italic", "IBMPlexMono-Regular"):
        assert f"/static/polices/{nom}.woff2" in page
        police = client_console.get(f"/static/polices/{nom}.woff2")
        assert police.status_code == 200 and police.content[:4] == b"wOF2"
    licence = client_console.get("/static/polices/OFL-Nunito.txt")
    assert licence.status_code == 200 and "SIL Open Font License" in licence.text


def test_ibm_plex_mono_est_le_fichier_d_ibm(client_console: TestClient) -> None:
    """« Plex » est un nom réservé (SIL OFL 1.1) : une conversion qui touche aux données ferait une
    version modifiée, interdite sous ce nom (FAQ OFL, 2.2). Seul le WOFF2 publié par IBM est servi :
    `@ibm/plex-mono@2.5.0`, `fonts/complete/woff2/IBMPlexMono-Regular.woff2`."""
    police = client_console.get("/static/polices/IBMPlexMono-Regular.woff2").content
    attendu = "ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350"
    assert hashlib.sha256(police).hexdigest() == attendu
