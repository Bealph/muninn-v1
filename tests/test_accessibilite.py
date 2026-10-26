"""Contrôle d'accessibilité automatique des pages de la console (axe-core, WCAG 2.2 AA).

Chaque état de la page (accueil, réponse, erreur) est rendu par la console, chargé dans un
Chromium sans interface, puis analysé par axe-core. Le moindre manquement fait échouer le test.
Prérequis local : `uv run playwright install chromium`.
"""

import json
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlsplit

import pytest
from axe_playwright_python.sync_playwright import Axe
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, Page, Route, sync_playwright

from outils_qualite import EPISODE, qualite, rendre_qualite
from test_console_demonstration import (
    EXTRAITS,
    reponse_dossier,
    reponse_gaz,
    reponse_message,
    synthese,
)

# Règles WCAG 2.0, 2.1 et 2.2, niveaux A et AA (exigence de la phase 0, document 04),
# plus les bonnes pratiques d'axe-core.
REGLES = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]


@pytest.fixture(scope="module")
def navigateur() -> Iterator[Browser]:
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        yield navigateur
        navigateur.close()


def _analyser(page: Page) -> tuple[int, str]:
    resultats = Axe().run(
        page,
        options={"runOnly": {"type": "tag", "values": REGLES}, "resultTypes": ["violations"]},
    )
    return int(resultats.violations_count), str(resultats.generate_report())


def _violations(navigateur: Browser, html: str) -> tuple[int, str]:
    page = navigateur.new_page()
    try:
        page.set_content(html)
        return _analyser(page)
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
        pytest.param(qualite(episodes=[EPISODE]), 200, id="historique"),
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


# --- Écran « Démonstration » (sprint 5, étape 6) -----------------------------------------------

ORIGINE = "http://console.test"


def test_ecran_demonstration_accessible(navigateur: Browser, client_console: TestClient) -> None:
    """État initial : choix du scénario, commandes, téléphones au repos."""
    nombre, rapport = _violations(navigateur, client_console.get("/demonstration").text)
    assert nombre == 0, rapport


Envois = list[tuple[str, dict[str, str], bytes]]


def _jouer(
    navigateur: Browser,
    html: str,
    scenario: str,
    synthese_rendue: tuple[int, dict[str, Any]] | None,
    appel_rendu: tuple[int, dict[str, Any]] | None,
    console: TestClient | None = None,
    largeur: int | None = None,
) -> tuple[Page, Envois]:
    """Joue l'appel dans Chromium jusqu'au bout (sonnerie de 3 s, sans son, mouvement réduit)."""
    page, envois = _ouvrir(navigateur, html, synthese_rendue, appel_rendu, console, True, largeur)
    _lancer(page, scenario)
    page.wait_for_function("!document.getElementById('lancer').disabled", timeout=30_000)
    return page, envois


def _lancer(page: Page, scenario: str) -> None:
    page.check(f'input[value="{scenario}"]')
    page.uncheck("#son")
    page.uncheck("#reel")
    page.click("#lancer")


def _ouvrir(
    navigateur: Browser,
    html: str,
    synthese_rendue: tuple[int, dict[str, Any]] | None,
    appel_rendu: tuple[int, dict[str, Any]] | None,
    console: TestClient | None = None,
    reduit: bool = True,
    largeur: int | None = None,
) -> tuple[Page, Envois]:
    """L'écran ouvert dans Chromium. Les requêtes de la page sont servies par `page.route` :
    réponses choisies par le test, ou, si `console` est donnée, relayées à la vraie console
    branchée sur l'API. Rend la page et les envois de l'enregistrement (paramètres, en-têtes,
    corps). `reduit` : préférence « mouvement réduit » du système."""
    envois: Envois = []
    page = navigateur.new_page(
        reduced_motion="reduce" if reduit else "no-preference",
        viewport={"width": largeur, "height": 800} if largeur else None,
    )

    def servir(route: Route) -> None:
        requete, chemin = route.request, urlsplit(route.request.url)
        if chemin.path == "/demonstration":
            route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
            return
        if chemin.path not in ("/demonstration/appel", "/demonstration/synthese"):
            route.abort()
            return
        corps_envoye = requete.post_data_buffer or b""
        if chemin.path == "/demonstration/appel":
            envois.append((chemin.query, requete.headers, corps_envoye))
        if console is not None:
            relaye = console.post(
                f"{chemin.path}?{chemin.query}", content=corps_envoye,
                headers={"Content-Type": requete.headers["content-type"]},
            )  # fmt: skip
            route.fulfill(status=relaye.status_code, content_type="application/json",
                          body=relaye.content)  # fmt: skip
            return
        rendu = appel_rendu if chemin.path == "/demonstration/appel" else synthese_rendue
        assert rendu is not None
        statut, corps = rendu
        route.fulfill(status=statut, content_type="application/json", body=json.dumps(corps))

    page.route("**/*", servir)
    page.goto(f"{ORIGINE}/demonstration")
    return page, envois


@pytest.mark.parametrize(
    ("scenario", "rendu", "attendus"),
    [
        pytest.param("SC-10", reponse_dossier(), ["À vérifier", "Quelle commune ?", "Montreuil"],
                     id="dossier-a-verifier"),
        pytest.param("SC-04", reponse_gaz(), ["Sécurité d'abord", "0 800 47 33 33", "vérifié"],
                     id="gaz"),
        pytest.param("SC-Q1", reponse_message(), ["Nouveau message · fournisseur", "Julie Lambert",
                                                  "06 99 00 00 11"], id="message"),
    ],
)  # fmt: skip
def test_demonstration_jouee_jusqu_au_resultat(
    navigateur: Browser,
    client_console: TestClient,
    scenario: str,
    rendu: dict[str, Any],
    attendus: list[str],
) -> None:
    """Parcours complet : synthèse, sonnerie, bulles, envoi de l'enregistrement (extraits mis
    bout à bout, `audio/mpeg`), chaîne tirée de `steps`, résultat réel sur le téléphone de
    Karim, chronomètre CA-8 ; puis analyse axe-core de l'écran final."""
    html = client_console.get("/demonstration").text
    page, envois = _jouer(navigateur, html, scenario, (200, synthese(scenario)), (200, rendu))
    try:
        assert page.inner_text("#statut").startswith("Reçu par Karim."), page.inner_text("#statut")
        assert _focus(page) == "lancer"  # revenu de « Arrêter », devenu inactif
        ((requete, entetes, corps),) = envois
        assert requete == f"scenario_id={scenario}"
        assert entetes["content-type"] == "audio/mpeg"
        assert corps == b"".join(EXTRAITS)
        assert page.locator("#chat .bulle").count() == 2
        noms = page.locator("#piste .noeud .l").all_inner_texts()
        assert noms[0] == "Transcription" and noms[1] == "Contrôle d'entrée"
        assert "2,4 s" in page.inner_text("#piste")  # durée mesurée de la transcription
        ecran_karim = page.text_content("#art") or ""  # texte brut, avant les capitales du CSS
        for texte in attendus:
            assert texte in ecran_karim, texte
        # Aucune valeur absente écrite en toutes lettres par le script.
        visible = page.inner_text("main")
        assert "null" not in visible and "undefined" not in visible and "NaN" not in visible
        assert "CA-8 : 45 s au plus, respecté." in page.inner_text("#chrono")
        assert page.inner_text("#erreur") == ""
        nombre, rapport = _analyser(page)
        assert nombre == 0, rapport
    finally:
        page.close()


def test_demonstration_jouee_contre_l_api(navigateur: Browser, client_console: TestClient) -> None:
    """Le vrai JavaScript contre la vraie API (faux fournisseurs de voix et de modèle) : les
    extraits décodés puis mis bout à bout par le navigateur sont relus tels quels par l'API."""
    html = client_console.get("/demonstration").text
    page, envois = _jouer(navigateur, html, "SC-04", None, None, console=client_console)
    try:
        assert page.inner_text("#erreur") == "", page.inner_text("#erreur")
        assert page.inner_text("#statut").startswith("Reçu par Karim.")
        assert envois[0][0] == "scenario_id=SC-04"
        # Ce que Muninn a entendu : autant de tours que de bulles jouées.
        entendus = page.locator("#entendu-liste li").count()
        assert entendus == page.locator("#chat .bulle").count() > 0
        assert page.locator("#piste .noeud .l").first.inner_text() == "Transcription"
        nombre, rapport = _analyser(page)
        assert nombre == 0, rapport
    finally:
        page.close()


@pytest.mark.parametrize(
    ("synthese_rendue", "appel_rendu", "attendu"),
    [
        pytest.param((503, {"code": "voice_unavailable", "message": "Voix indisponible.",
                            "request_id": "r-1"}), (200, {}), "Synthèse des voix impossible",
                     id="voix-indisponible"),
        pytest.param((200, synthese()),
                     (429, {"code": "rate_limited", "retry_after_s": 30,
                            "message": "Trop de demandes : réessayer plus tard."}),
                     "réessayer dans 30 s", id="appel-refuse"),
    ],
)  # fmt: skip
def test_demonstration_erreur_de_l_api_accessible(
    navigateur: Browser,
    client_console: TestClient,
    synthese_rendue: tuple[int, dict[str, Any]],
    appel_rendu: tuple[int, dict[str, Any]],
    attendu: str,
) -> None:
    """Une erreur de l'API s'affiche en clair, dans la zone `role="alert"`, et la démonstration
    s'arrête proprement (bouton « Lancer » rendu)."""
    html = client_console.get("/demonstration").text
    page, _ = _jouer(navigateur, html, "SC-Q4", synthese_rendue, appel_rendu)
    try:
        alerte = page.inner_text("#erreur")
        assert attendu in alerte, alerte
        assert page.inner_text("#statut").startswith("Démonstration interrompue.")
        nombre, rapport = _analyser(page)
        assert nombre == 0, rapport
    finally:
        page.close()


# --- Non-régression de la relecture d'accessibilité (WCAG 2.2 AA) ------------------------------
# Ces pages sont ouvertes sans « mouvement réduit » : les animations y tournent vraiment.

ANIMEES = "document.getAnimations().filter((a) => a.playState === 'running').length"
# Un premier tour long : la conversation dure assez pour agir pendant qu'elle se joue.
TOUR_LONG = "Bonjour, vous êtes bien chez Karim Plomberie, je prends votre message. " * 4


def _synthese_longue() -> dict[str, Any]:
    corps = synthese()
    corps["turns"][0]["text"] = TOUR_LONG.strip()
    return corps


def _focus(page: Page) -> str:
    return str(page.evaluate("document.activeElement ? document.activeElement.id : ''"))


def _en_conversation(page: Page) -> None:
    page.wait_for_function(
        "document.getElementById('statut').textContent.startsWith('Muninn en ligne.')",
        timeout=15_000,
    )


def test_arret_fige_l_ecran_et_rend_le_focus(
    navigateur: Browser, client_console: TestClient
) -> None:
    """2.2.2, 2.4.3, 1.3.1 : pendant la conversation, la bulle en cours expose tout son texte ;
    après « Arrêter », plus aucune animation, l'écran de Karim dit l'interruption et le focus
    revient sur « Lancer »."""
    html = client_console.get("/demonstration").text
    page, _ = _ouvrir(navigateur, html, (200, _synthese_longue()), (200, {}), reduit=False)
    try:
        _lancer(page, "SC-Q4")
        assert _focus(page) == "arreter"
        _en_conversation(page)
        assert page.evaluate(ANIMEES) > 0  # témoin : les barres et les points tournent
        # Texte complet de la bulle en cours dans l'arbre d'accessibilité, dès le début.
        assert (
            "Karim Plomberie, je prends votre message. Bonjour"
            in page.locator("#chat").aria_snapshot()
        )
        page.click("#arreter")
        page.wait_for_timeout(400)
        assert page.evaluate(ANIMEES) == 0
        assert _focus(page) == "lancer"
        assert "Appel interrompu." in (page.text_content("#art") or "")
    finally:
        page.close()


def test_case_animation_arrete_tout(navigateur: Browser, client_console: TestClient) -> None:
    """2.2.2 : décocher « Animation » pendant la conversation arrête barres et points."""
    html = client_console.get("/demonstration").text
    page, _ = _ouvrir(navigateur, html, (200, _synthese_longue()), (200, {}), reduit=False)
    try:
        _lancer(page, "SC-Q4")
        _en_conversation(page)
        assert page.evaluate(ANIMEES) > 0
        page.uncheck("#anim")
        page.wait_for_timeout(300)
        assert page.evaluate(ANIMEES) == 0
        page.click("#arreter")
    finally:
        page.close()


def test_erreur_fige_l_ecran_et_rend_le_focus(
    navigateur: Browser, client_console: TestClient
) -> None:
    """2.2.2, 2.4.3 : après une erreur de l'API, plus aucune animation, focus sur « Lancer »."""
    html = client_console.get("/demonstration").text
    erreur = {"code": "voice_unavailable", "message": "Voix indisponible.", "request_id": "r-1"}
    page, _ = _ouvrir(navigateur, html, (503, erreur), None, reduit=False)
    try:
        _lancer(page, "SC-Q4")
        page.wait_for_function("!document.getElementById('lancer').disabled", timeout=15_000)
        page.wait_for_timeout(400)
        assert page.evaluate(ANIMEES) == 0
        assert _focus(page) == "lancer"
        assert "Appel interrompu." in (page.text_content("#art") or "")
    finally:
        page.close()


@pytest.mark.parametrize("largeur", [320, 640])
def test_pas_de_defilement_horizontal(
    navigateur: Browser, client_console: TestClient, largeur: int
) -> None:
    """1.4.10 : à 320 et 640 px, ni l'écran initial ni le résultat ne débordent en largeur."""
    html = client_console.get("/demonstration").text
    deborde = "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    page, _ = _jouer(navigateur, html, "SC-10", (200, synthese("SC-10")),
                     (200, reponse_dossier()), largeur=largeur)  # fmt: skip
    try:
        assert page.inner_text("#statut").startswith("Reçu par Karim.")
        assert not page.evaluate(deborde), page.evaluate(
            "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"
        )
        page.goto(f"{ORIGINE}/demonstration")
        assert not page.evaluate(deborde)
    finally:
        page.close()
