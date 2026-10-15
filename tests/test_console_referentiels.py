"""Écran « Référentiels » de la console (sprint 3, étape 8 ; D-57).

L'API est simulée par des réponses écrites ici, au format de l'API réelle : l'écran est testé
seul, sans base. Chaque état est aussi passé à axe-core (WCAG 2.2 AA). L'intégration de bout en
bout, de la console à PostgreSQL, est testée dans `test_referentiels.py`.
"""

import json
from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, sync_playwright

from muninn.console.main import app as console
from muninn.console.main import date_lisible, get_client_api
from test_accessibilite import _violations

SOURCE_COG = {
    "jeu": "communes",
    "source_id": "SRC-07",
    "titre": "Code officiel géographique 2026",
    "editeur": "Insee",
    "licence": "Licence Ouverte 2.0",
    "url": "https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv",
    "date_source": "2026-01-01",
    "charge_le": "2026-10-15T14:12:24.608614+00:00",
    "version": 1,
    "table": "ref.communes",
}
CANDIDATE = {
    "nom": "Montreuil",
    "code_insee": "93048",
    "departement": "93",
    "codes_postaux": ["93100"],
    "via": "nom officiel",
    "references": [{"table": "ref.communes", "cle": "version 1, COM 93048"}],
}
REPONSES: dict[str, tuple[int, dict[str, Any]]] = {
    "trouve": (
        200,
        {"statut": "trouve", "motif": "Une commune correspond.", "candidates": [CANDIDATE],
         "sources": [SOURCE_COG]},
    ),
    "incoherent": (
        200,
        {"statut": "incoherent", "motif": "Aucune commune de ce nom n'a le code postal 93100.",
         "candidates": [CANDIDATE | {"nom": "Bagnolet", "codes_postaux": ["93170"]}],
         "sources": [SOURCE_COG]},
    ),
    "hors_corpus": (
        200,
        {"statut": "hors_corpus",
         "motif": "Aucune commune de ce nom. Aucune valeur n'est proposée.",
         "candidates": [], "sources": [SOURCE_COG]},
    ),
    "terme": (
        200,
        {"statut": "trouve", "motif": "Terme trouvé.", "seuil": 0.55,
         "terme": {"terme": "cumulus", "similarite": 1.0, "categorie": "other",
                   "source_id": "SRC-12", "reference": "cumulus",
                   "url": "https://fr.wiktionary.org/wiki/cumulus", "licence": "CC BY-SA 4.0",
                   "references": [{"table": "ref.lexicon_terms", "cle": "id 39"}]},
         "sources": [SOURCE_COG | {"source_id": "SRC-12", "titre": "Wiktionnaire",
                                   "editeur": "Wikimédia", "licence": "CC BY-SA 4.0",
                                   "date_source": None, "mode": "secours"}]},
    ),
    "hors_perimetre": (
        200,
        {"statut": "hors_perimetre", "motif": "Aucun lexique publié pour ce métier.",
         "seuil": 0.55, "terme": None, "sources": []},
    ),
    "marche": (
        200,
        {"statut": "trouve", "motif": "3 cellules.", "metier": "plomberie",
         "comptages": [
             {"naf_code": "43.22A", "headcount_band": "NN", "legal_category_group": "ei",
              "department_code": "FR", "establishments_count": 35009,
              "legal_units_count": 34829, "is_masked": False},
             {"naf_code": "43.22A", "headcount_band": "00", "legal_category_group": "other",
              "department_code": "FR", "establishments_count": None,
              "legal_units_count": None, "is_masked": True},
             {"naf_code": "43.22A", "headcount_band": "NN", "legal_category_group": "ei",
              "department_code": "75", "establishments_count": 900,
              "legal_units_count": 890, "is_masked": False},
         ],
         "sources": [SOURCE_COG | {"source_id": "SRC-01", "titre": "Stock Sirene"}]},
    ),
    "invalide": (
        422,
        {"detail": [{"msg": "Value error, donner un nom de commune, un code postal, ou les deux"}]},
    ),
    "indisponible": (503, {"detail": "Base des référentiels indisponible."}),
}  # fmt: skip


@pytest.fixture
def ecran() -> Iterator[Callable[[str], TestClient]]:
    """Console branchée sur une API simulée qui rend la réponse choisie."""

    def brancher(etat: str) -> TestClient:
        code, corps = REPONSES[etat]

        def repondre(requete: httpx.Request) -> httpx.Response:
            return httpx.Response(code, content=json.dumps(corps).encode())

        transport = httpx.MockTransport(repondre)
        console.dependency_overrides[get_client_api] = lambda: httpx.Client(
            transport=transport, base_url="http://api"
        )
        return TestClient(console)

    yield brancher
    console.dependency_overrides.clear()


@pytest.fixture(scope="module")
def navigateur() -> Iterator[Browser]:
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        yield navigateur
        navigateur.close()


def page(ecran: Callable[[str], TestClient], etat: str) -> str:
    client = ecran(etat)
    if etat == "marche":
        return str(client.get("/referentiels/marche", params={"metier": "plomberie"}).text)
    if etat in ("terme", "hors_perimetre"):
        return str(client.post("/referentiels/terme", data={"mot": "cumulus"}).text)
    return str(client.post("/referentiels/commune", data={"nom": "Montreuil"}).text)


ATTENDUS = {
    "trouve": ["Question :</strong> commune « Montreuil »", "Réponse tirée des données",
               "93048", "Code officiel géographique 2026", "Insee, Licence Ouverte 2.0",
               "01/01/2026", "15/10/2026 à 14:12 UTC", "ref.communes"],
    "incoherent": ["Nom et code postal incohérents", "Bagnolet", "93170"],
    "hors_corpus": ["Refus : hors des données", "Aucune valeur n&#39;est proposée"],
    "terme": ["cumulus", "0.55", "https://fr.wiktionary.org/wiki/cumulus",
              "non publiée par la source", "instantané de secours"],
    "hors_perimetre": ["Refus : hors du périmètre", "mot « cumulus », métier plomberie"],
    "marche": ["non employeur", "entrepreneur individuel", "35009",
               "masqué (secret statistique)"],
    "invalide": ["Entrée refusée : donner un nom de commune", 'role="alert"'],
    "indisponible": ["Base des référentiels indisponible.", 'role="alert"'],
}  # fmt: skip


@pytest.mark.parametrize("etat", list(ATTENDUS))
def test_etat_affiche(ecran: Callable[[str], TestClient], etat: str) -> None:
    html = page(ecran, etat)
    for attendu in ATTENDUS[etat]:
        assert attendu in html, attendu


def test_marche_n_affiche_que_les_totaux_nationaux(ecran: Callable[[str], TestClient]) -> None:
    assert "900" not in page(ecran, "marche")  # cellule départementale : comptée, pas listée


def test_ecran_vide_et_navigation(ecran: Callable[[str], TestClient]) -> None:
    html = ecran("trouve").get("/referentiels").text
    assert 'aria-current="page">Référentiels' in html
    assert "Réponse tirée des données" not in html


def test_valeurs_echappees(ecran: Callable[[str], TestClient]) -> None:
    html = ecran("hors_corpus").post("/referentiels/commune", data={"nom": "<b>x</b>"}).text
    assert "<b>x</b>" not in html


def test_api_injoignable() -> None:
    def panne(requete: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refus", request=requete)

    console.dependency_overrides[get_client_api] = lambda: httpx.Client(
        transport=httpx.MockTransport(panne), base_url="http://api"
    )
    try:
        html = TestClient(console).post("/referentiels/commune", data={"nom": "Paris"}).text
        assert "L&#39;API est injoignable." in html
    finally:
        console.dependency_overrides.clear()


def test_date_lisible() -> None:
    assert date_lisible("2026-10-15T14:12:24.608614+00:00") == "15/10/2026 à 14:12 UTC"
    assert date_lisible("2026-10-15T16:12:24+02:00") == "15/10/2026 à 14:12 UTC"
    assert date_lisible("2026-01-01") == "01/01/2026"
    assert date_lisible("pas une date") == "pas une date"


@pytest.mark.parametrize("etat", [*ATTENDUS, "vide"])
def test_etat_accessible(
    navigateur: Browser, ecran: Callable[[str], TestClient], etat: str
) -> None:
    html = ecran("trouve").get("/referentiels").text if etat == "vide" else page(ecran, etat)
    nombre, rapport = _violations(navigateur, html)
    assert nombre == 0, rapport
