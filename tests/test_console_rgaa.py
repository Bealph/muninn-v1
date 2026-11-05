"""Non-régression de l'audit RGAA 4.1.2 de la console (C10) : un test par non-conformité corrigée.

Grille : `docs/v1/accessibilite/grille.md`. Chaque test porte le numéro du critère qu'il garde.
"""

import re
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, sync_playwright

from muninn.console.main import libelle
from outils_qualite import EPISODE, qualite, rendre_qualite
from test_console_referentiels import ecran, page  # noqa: F401

ECRANS = ["/", "/referentiels", "/agent", "/demonstration", "/qualite"]


@pytest.fixture(scope="module")
def navigateur() -> Iterator[Browser]:
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        yield navigateur
        navigateur.close()


def _contraste(a: str, b: str) -> float:
    def lum(h: str) -> float:
        c = [int(h.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("chemin", ["/", "/referentiels", "/agent", "/demonstration"])
def test_12_7_lien_d_evitement_vers_le_contenu(client_console: TestClient, chemin: str) -> None:
    html = client_console.get(chemin).text
    corps = html[html.index("<body>") :]
    premier_lien = re.search(r"<a [^>]*>", corps)
    assert premier_lien and 'href="#contenu"' in premier_lien.group(0)
    assert '<main id="contenu" tabindex="-1">' in html


def test_8_2_aucun_style_dans_le_corps(client_console: TestClient) -> None:
    pages = [client_console.get(c).text for c in ["/demonstration"]]
    pages.append(rendre_qualite(qualite(), 200)[0])
    for html in pages:
        assert "<style" not in html[html.index("<body>") :]


def test_8_9_aucune_balise_i_de_mise_en_forme(client_console: TestClient) -> None:
    assert not re.search(r"<i[\s>]", client_console.get("/demonstration").text)


def test_8_7_codes_affiches_en_francais(
    client_console: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import muninn.api.agent as routes

    assert libelle("not_checked") == "non contrôlé" and libelle("other") == "autre"
    assert libelle("code_inconnu") == "code inconnu"
    monkeypatch.setattr(routes, "enregistrer", lambda e: True)
    html = client_console.post(
        "/agent/executer", data={"mode": "scenario", "scenario_id": "SC-01"}
    ).text
    codes = r"not_checked|partial_after_retry|fallback_no_llm|non_precise|sortie_invalide"
    assert not re.search(rf">[^<]*\b({codes})\b", html)


def test_8_7_categorie_du_terme_en_francais(ecran: Callable[[str], TestClient]) -> None:  # noqa: F811
    html = page(ecran, "terme")
    assert "<dd>other</dd>" not in html and "<dd>autre</dd>" in html


def test_9_1_aucun_saut_de_niveau_de_titre() -> None:
    for html in (rendre_qualite(qualite(), 200)[0], rendre_qualite(None, 503)[0]):
        niveaux = [int(n) for n in re.findall(r"<h([1-6])\b", html)]
        assert all(b - a <= 1 for a, b in zip(niveaux, niveaux[1:], strict=False)), niveaux


def test_10_11_dossier_sans_defilement_horizontal_a_320_px(
    navigateur: Browser, client_console: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import muninn.api.agent as routes

    monkeypatch.setattr(routes, "enregistrer", lambda e: True)
    html = client_console.post(
        "/agent/executer", data={"mode": "scenario", "scenario_id": "SC-01"}
    ).text
    p = navigateur.new_page(viewport={"width": 320, "height": 800})
    try:
        p.set_content(html)
        # Les tableaux peuvent défiler seuls ; les listes de définitions, jamais.
        debord = p.evaluate(
            "[...document.querySelectorAll('dl')].some(d => d.scrollWidth > d.clientWidth + 1)"
        )
        assert not debord
    finally:
        p.close()


def test_10_4_cartes_de_l_ecran_de_karim_repliables(client_console: TestClient) -> None:
    html = client_console.get("/demonstration").text
    assert "grid-template-columns: minmax(0, 1fr)" in html and "overflow-wrap: anywhere" in html
    assert "white-space: nowrap; margin-left" not in html  # pastilles de provenance repliables


@pytest.mark.parametrize(("chemin", "champ"), [("/", "question"), ("/referentiels", "mot")])
def test_11_10_champ_obligatoire_signale_dans_son_etiquette(
    client_console: TestClient, chemin: str, champ: str
) -> None:
    html = client_console.get(chemin).text
    assert re.search(rf'id="{champ}"[^>]*required', html)
    etiquette = re.search(rf'<label for="{champ}">(.*?)</label>', html)
    assert etiquette and "obligatoire" in etiquette.group(1)


def test_11_10_et_11_11_transcription_vide_nommee_et_reliee(client_console: TestClient) -> None:
    html = client_console.post(
        "/agent/executer", data={"mode": "transcript", "transcript": "  "}
    ).text
    assert "Transcription : le champ est vide." in html and 'id="erreur-champ"' in html
    assert re.search(
        r'id="transcript"[^>]*aria-invalid="true"[^>]*aria-describedby="erreur-champ"', html
    )


def test_11_12_validation_confirmee_explicitement(
    client_console: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import muninn.api.agent as routes

    monkeypatch.setattr(routes, "enregistrer", lambda e: True)
    html = client_console.post(
        "/agent/executer", data={"mode": "scenario", "scenario_id": "SC-01"}
    ).text
    assert re.search(r'name="confirme" value="oui" required', html)
    refus = client_console.post(
        "/agent/valider",
        data={"draft_id": "00000000-0000-0000-0000-000000000000", "origine": "{}"},
    ).text
    assert "Confirmation : cocher" in refus and "Dossier validé" not in refus


def test_1_6_et_10_9_valeurs_des_graphiques_en_tableau() -> None:
    html = rendre_qualite(qualite(episodes=[EPISODE]), 200)[0]
    assert html.count('aria-describedby="valeurs-horaires"') == 2
    tableau = re.search(r'<table id="valeurs-horaires">(.*?)</table>', html, re.S)
    assert tableau and "<caption>" in tableau.group(1)
    assert len(re.findall(r'<th scope="row">', tableau.group(1))) == 3  # trois heures avec appels


def test_1_9_et_8_2_graphiques_introduits_sans_figure() -> None:
    """Décision du porteur (option b) : le RGAA veut `role` sur une figure à légende, le HTML
    l'interdit ; chaque graphique est donc précédé d'un texte d'introduction, sans figure."""
    html = rendre_qualite(qualite(), 200)[0]
    assert "<figure" not in html and "<figcaption" not in html
    blocs = re.findall(r'<div class="graphique">\s*<p class="legende">[^<]+.*?<svg ', html, re.S)
    assert len(blocs) == 2


def test_3_3_series_contrastees() -> None:
    html = rendre_qualite(qualite(), 200)[0]
    couleurs = {
        n: re.search(rf"svg \.{n} {{ fill: (#[0-9a-f]{{6}}); }}", html).group(1)  # type: ignore[union-attr]
        for n in ("total", "verifier", "faible")
    }
    for c in couleurs.values():
        assert _contraste(c, "#ffffff") >= 3
    assert _contraste(couleurs["verifier"], couleurs["total"]) >= 3
    assert _contraste(couleurs["verifier"], couleurs["faible"]) >= 3
