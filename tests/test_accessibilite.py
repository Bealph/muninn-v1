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

from outils_qualite import qualite, rendre_qualite

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


@pytest.mark.parametrize(
    ("chemin", "donnees"),
    [
        ("/agent", None),
        ("/agent/executer", {"mode": "scenario", "scenario_id": "P4-perimetre"}),
        ("/agent/executer", {"mode": "scenario", "scenario_id": "SC-Q2"}),
        ("/agent/executer", {"mode": "transcript", "transcript": ""}),
        ("/agent/lot", {"groupe": "qualification"}),
    ],
    ids=["formulaire", "dossier-et-outils", "dossier-faux-modele", "refus", "lot"],
)
def test_ecran_agent_accessible(
    navigateur: Browser, client_console: TestClient, chemin: str, donnees: dict[str, str] | None
) -> None:
    """États de l'écran « Agent » (D-62) : formulaire, dossier, refus, bilan d'un lot."""
    from muninn.api.agent import get_referentiels
    from muninn.api.main import app as api

    class HorsLigne:
        def communes(self, corps: dict[str, str]) -> dict[str, object]:
            raise ConnectionError

        def termes(self, corps: dict[str, str]) -> dict[str, object]:
            raise ConnectionError

    api.dependency_overrides[get_referentiels] = HorsLigne
    page = (
        client_console.get(chemin) if donnees is None else client_console.post(chemin, data=donnees)
    )
    assert page.status_code == 200
    nombre, rapport = _violations(navigateur, page.text)
    assert nombre == 0, rapport


def test_dossier_a_valider_accessible(
    navigateur: Browser, client_console: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Formulaire « Corriger et valider » (V-09) : le dossier est réputé enregistré."""
    import muninn.api.agent as routes

    monkeypatch.setattr(routes, "enregistrer", lambda e: True)
    page = client_console.post("/agent/executer", data={"mode": "scenario", "scenario_id": "SC-01"})
    assert page.status_code == 200 and "Valider le dossier" in page.text
    nombre, rapport = _violations(navigateur, page.text)
    assert nombre == 0, rapport


@pytest.mark.parametrize(
    ("corps", "statut"),
    [
        pytest.param(qualite(), 200, id="tout-va-bien"),
        pytest.param(qualite(a_verifier=10, part_a_verifier=0.4), 200, id="alerte"),
        pytest.param(qualite(total=5, dossiers=4, refus=0), 200, id="pas-assez"),
        pytest.param(None, 503, id="base-indisponible"),
    ],
)
def test_ecran_qualite_accessible(
    navigateur: Browser, corps: dict[str, object] | None, statut: int
) -> None:
    html, _ = rendre_qualite(corps, statut)
    nombre, rapport = _violations(navigateur, html)
    assert nombre == 0, rapport
