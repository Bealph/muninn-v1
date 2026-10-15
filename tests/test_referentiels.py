"""API des référentiels (sprint 3, étape 7) : réponses ancrées, sources citées, refus motivés.

La base de test est chargée par la vraie commande `muninn-ingestion tout`, avec des fichiers de
test à la place des téléchargements (voir `test_ingestion_base.py`).
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient

from muninn.api.limites import LimiteurDebit
from muninn.api.main import app
from muninn.console.main import app as console
from muninn.console.main import get_client_api
from muninn.core.config import get_settings
from muninn.ingestion import commande, lexique, sirene
from muninn.referentiels import depot
from muninn.referentiels.routes import get_limiteur_referentiels
from muninn.referentiels.seuil import SEUIL_LEXIQUE
from outils_base import base_migree, connecter, exiger_base, url_postgres
from test_ingestion_base import TOUT, servir
from test_sirene import ecrire_stock

exiger_base()

COMMUNES = "/v1/referentiels/communes"
TERMES = "/v1/referentiels/termes"


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Base chargée une fois pour le module : COG, codes postaux, lexique publié, Sirene."""
    patch = pytest.MonkeyPatch()
    stock = ecrire_stock(tmp_path_factory.mktemp("sirene"))
    with base_migree() as nom:
        patch.setenv("DATABASE_URL", url_postgres(nom))
        patch.setenv("GIT_SHA", "test")
        get_settings.cache_clear()
        patch.setattr(sirene, "localiser", lambda client: stock)
        servir(patch, TOUT)
        # Le lexique de test n'est pas dans les évaluations versionnées : on le déclare évalué,
        # le temps du chargement seulement.
        with pytest.MonkeyPatch.context() as evaluation:
            evaluation.setattr(
                lexique,
                "evaluation",
                lambda signature: {"rapport": "test", "date": "2026-10-15", "seuil": SEUIL_LEXIQUE},
            )
            assert commande.main(["tout"]) == 0
        yield nom
        patch.undo()
    get_settings.cache_clear()


@pytest.fixture
def client(base: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", url_postgres(base))
    get_settings.cache_clear()
    get_limiteur_referentiels.cache_clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def poster(client: TestClient, url: str, corps: dict[str, Any]) -> dict[str, Any]:
    reponse = client.post(url, json=corps)
    assert reponse.status_code == 200, reponse.text
    resultat: dict[str, Any] = reponse.json()
    return resultat


def test_commune_trouvee_avec_sources_et_references(client: TestClient) -> None:
    r = poster(client, COMMUNES, {"nom": "l'abergement-clemenciat"})
    assert r["statut"] == "trouve"
    [candidate] = r["candidates"]
    assert (candidate["nom"], candidate["code_insee"], candidate["codes_postaux"]) == (
        "L'Abergement-Clémenciat",
        "01001",
        ["01400"],
    )
    assert candidate["references"][0] == {"table": "ref.communes", "cle": "version 1, COM 01001"}
    assert candidate["references"][1]["table"] == "ref.postal_codes"
    cog, codes = r["sources"]
    assert (cog["source_id"], cog["editeur"], cog["licence"]) == (
        "SRC-07",
        "Insee",
        "Licence Ouverte 2.0",
    )
    assert cog["url"].startswith("https://www.insee.fr/") and cog["date_source"] == "2026-01-01"
    assert (codes["source_id"], codes["date_source"]) == ("SRC-06", "2026-10-08")


def test_references_retrouvees_en_base(client: TestClient, base: str) -> None:
    """L'évaluateur remonte de la référence citée à la ligne de la base."""
    r = poster(client, COMMUNES, {"nom": "Paris"})
    reference = r["candidates"][0]["references"][1]
    identifiant = int(reference["cle"].removeprefix("id "))
    with connecter(base) as conn:
        ligne = conn.execute(
            "SELECT postal_code, insee_code FROM ref.postal_codes WHERE id = %s", [identifiant]
        ).fetchone()
    assert ligne == ("75001", "75101")  # arrondissement rattaché à Paris


def test_code_postal_seul_et_arrondissement(client: TestClient) -> None:
    r = poster(client, COMMUNES, {"code_postal": "75001"})
    assert [(c["nom"], c["via"]) for c in r["candidates"]] == [("Paris", "code postal")]


def test_commune_deleguee_renvoie_a_la_commune_nouvelle(client: TestClient) -> None:
    r = poster(client, COMMUNES, {"nom": "Arbignieu"})
    assert [(c["code_insee"], c["via"]) for c in r["candidates"]] == [
        ("01001", "Arbignieu (COMD 01015)")
    ]


def test_nom_et_code_postal_incoherents(client: TestClient) -> None:
    r = poster(client, COMMUNES, {"nom": "Paris", "code_postal": "01400"})
    assert r["statut"] == "incoherent"
    assert r["candidates"][0]["codes_postaux"] == ["75001"]  # rien n'est corrigé ni inventé


@pytest.mark.parametrize(
    "corps",
    [
        {"nom": "Gotham City"},
        {"nom": "Quelle heure est-il ?"},
        {"code_postal": "99999"},
        {"nom": "'; DROP TABLE ref.communes; --"},
    ],
)
def test_commune_hors_corpus_sans_valeur(
    client: TestClient, base: str, corps: dict[str, str]
) -> None:
    r = poster(client, COMMUNES, corps)
    assert (r["statut"], r["candidates"]) == ("hors_corpus", [])
    with connecter(base) as conn:
        assert conn.execute("SELECT count(*) FROM ref.communes").fetchone() == (4,)


@pytest.mark.parametrize(
    "corps",
    [{}, {"code_postal": "1234"}, {"nom": "x" * 121}, {"nom": "Paris", "autre": 1}],
)
def test_entree_mal_formee_refusee(client: TestClient, corps: dict[str, Any]) -> None:
    assert client.post(COMMUNES, json=corps).status_code == 422


def test_terme_trouve_avec_attribution(client: TestClient) -> None:
    r = poster(client, TERMES, {"mot": "Cumulus", "metier": "plomberie"})
    assert r["statut"] == "trouve" and r["seuil"] == SEUIL_LEXIQUE
    terme = r["terme"]
    assert (terme["terme"], terme["similarite"], terme["licence"]) == (
        "cumulus",
        1.0,
        "CC BY-SA 4.0",
    )
    assert terme["url"] == "https://fr.wiktionary.org/wiki/cumulus"
    assert terme["references"][0]["table"] == "ref.lexicon_terms"
    wiktionnaire, wikidata = r["sources"]  # chaque source réelle du lexique est citée
    assert (wiktionnaire["source_id"], wiktionnaire["licence"]) == ("SRC-12", "CC BY-SA 4.0")
    assert wiktionnaire["url"].startswith("https://fr.wiktionary.org/")
    assert (wikidata["source_id"], wikidata["licence"]) == ("SRC-11", "CC0 1.0")


@pytest.mark.parametrize("mot", ["ordinateur", "robot", "Quelle est la capitale de la France ?"])
def test_terme_hors_corpus_sous_le_seuil(client: TestClient, mot: str) -> None:
    r = poster(client, TERMES, {"mot": mot, "metier": "plomberie"})
    assert (r["statut"], r["terme"]) == ("hors_corpus", None)
    assert str(SEUIL_LEXIQUE) in r["motif"]


@pytest.mark.parametrize("metier", ["electricite", "boulangerie"])
def test_terme_hors_perimetre(client: TestClient, metier: str) -> None:
    r = poster(client, TERMES, {"mot": "disjoncteur", "metier": metier})
    assert (r["statut"], r["terme"]) == ("hors_perimetre", None)


def test_marche_sirene_avec_secret(client: TestClient) -> None:
    reponse = client.get("/v1/referentiels/marche/plomberie")
    assert reponse.status_code == 200
    r = reponse.json()
    assert r["sources"][0]["source_id"] == "SRC-01"
    assert r["sources"][0]["date_source"] == "2026-10-01"
    servies = [c for c in r["comptages"] if not c["is_masked"]]
    assert all(min(c["establishments_count"], c["legal_units_count"]) >= 5 for c in servies)
    assert client.get("/v1/referentiels/marche/boulangerie").json()["statut"] == "hors_perimetre"


def test_connexion_en_lecture_seule(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Même avec un rôle autorisé à écrire, la connexion de l'API refuse toute écriture."""
    monkeypatch.setenv("DATABASE_URL", url_postgres(base))
    get_settings.cache_clear()
    with depot.connecter() as conn, pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        conn.execute("DELETE FROM ref.communes")
    get_settings.cache_clear()


def test_base_indisponible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://personne:rien@127.0.0.1:1/aucune")
    get_settings.cache_clear()
    assert TestClient(app).post(COMMUNES, json={"nom": "Paris"}).status_code == 503
    get_settings.cache_clear()


def test_limite_de_debit(client: TestClient) -> None:
    limiteur = LimiteurDebit([(60, 1)])
    app.dependency_overrides[get_limiteur_referentiels] = lambda: limiteur
    assert client.post(COMMUNES, json={"nom": "Paris"}).status_code == 200
    reponse = client.post(COMMUNES, json={"nom": "Paris"})
    assert reponse.status_code == 429 and "Retry-After" in reponse.headers


def test_seuil_conforme_a_l_evaluation_versionnee() -> None:
    evaluations = json.loads(Path(lexique.FICHIER_EVALUATIONS).read_text(encoding="utf-8"))
    assert {e["seuil"] for e in evaluations["evaluations"].values()} == {SEUIL_LEXIQUE}


def test_lexique_non_evalue_reste_candidat(monkeypatch: pytest.MonkeyPatch) -> None:
    with base_migree() as nom:
        monkeypatch.setenv("DATABASE_URL", url_postgres(nom))
        get_settings.cache_clear()
        servir(monkeypatch, TOUT)
        assert commande.main(["lexique"]) == 0
        with connecter(nom) as conn:
            assert conn.execute("SELECT status FROM ref.trade_lexicons").fetchone() == (
                "candidate",
            )
        r = TestClient(app).post(TERMES, json={"mot": "cumulus", "metier": "plomberie"}).json()
        assert r["statut"] == "hors_perimetre"
    get_settings.cache_clear()


def test_schemas_absents_rendent_un_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Base joignable mais pas encore migrée : refus propre, pas d'erreur 500."""
    with connecter("postgres") as admin:
        admin.execute("DROP DATABASE IF EXISTS muninn_test_vide")
        admin.execute("CREATE DATABASE muninn_test_vide")
    try:
        monkeypatch.setenv("DATABASE_URL", url_postgres("muninn_test_vide"))
        get_settings.cache_clear()
        client = TestClient(app)
        assert client.post(COMMUNES, json={"nom": "Paris"}).status_code == 503
        assert client.get("/v1/referentiels/marche/plomberie").status_code == 503
    finally:
        get_settings.cache_clear()
        with connecter("postgres") as admin:
            admin.execute("DROP DATABASE muninn_test_vide WITH (FORCE)")


def test_ecran_console_de_bout_en_bout(client: TestClient) -> None:
    """Console, API, PostgreSQL : la question de l'évaluateur rend la réponse et sa source."""
    console.dependency_overrides[get_client_api] = lambda: client
    try:
        ecran = TestClient(console)
        html = ecran.post("/referentiels/commune", data={"nom": "Paris"}).text
        assert "Réponse tirée des données" in html and "75056" in html
        assert "Code officiel géographique 2026" in html and "ref.postal_codes" in html
        html = ecran.post("/referentiels/commune", data={"nom": "Gotham City"}).text
        assert "Refus : hors des données" in html
        html = ecran.post(
            "/referentiels/terme", data={"mot": "cumulus", "metier": "plomberie"}
        ).text
        assert "https://fr.wiktionary.org/wiki/cumulus" in html
    finally:
        console.dependency_overrides.clear()
