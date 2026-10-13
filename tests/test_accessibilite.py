"""Contrôle d'accessibilité automatique des pages de la console (axe-core, WCAG 2.2 AA).

Chaque état de la page (accueil, réponse, erreur) est rendu par la console, chargé dans un
Chromium sans interface, puis analysé par axe-core. Le moindre manquement fait échouer le test.
Prérequis local : `uv run playwright install chromium`.
"""

from collections.abc import Iterator

import pytest
from axe_playwright_python.sync_playwright import Axe
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, sync_playwright

# Règles WCAG 2.0, 2.1 et 2.2, niveaux A et AA (exigence de la phase 0, document 04),
# plus les bonnes pratiques d'axe-core.
REGLES = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]


@pytest.fixture(scope="module")
def navigateur() -> Iterator[Browser]:
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        yield navigateur
        navigateur.close()


def _violations(navigateur: Browser, html: str) -> tuple[int, str]:
    page = navigateur.new_page()
    try:
        page.set_content(html)
        resultats = Axe().run(
            page,
            options={"runOnly": {"type": "tag", "values": REGLES}, "resultTypes": ["violations"]},
        )
        return int(resultats.violations_count), str(resultats.generate_report())
    finally:
        page.close()


def test_accueil_accessible(navigateur: Browser, client_console: TestClient) -> None:
    nombre, rapport = _violations(navigateur, client_console.get("/").text)
    assert nombre == 0, rapport


def test_page_reponse_accessible(navigateur: Browser, client_console: TestClient) -> None:
    html = client_console.post("/essai", data={"question": "Bonjour", "modele": "A"}).text
    assert "Réponse simulée" in html
    nombre, rapport = _violations(navigateur, html)
    assert nombre == 0, rapport


def test_page_erreur_accessible(navigateur: Browser, client_console: TestClient) -> None:
    html = client_console.post("/essai", data={"question": "Bonjour", "modele": "B"}).text
    assert 'role="alert"' in html
    nombre, rapport = _violations(navigateur, html)
    assert nombre == 0, rapport
