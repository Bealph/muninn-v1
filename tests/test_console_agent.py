"""Écran « Agent » de la console (sprint 4, étape 8 ; D-62), sans réseau ni modèle réel."""

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from muninn.api.agent import get_referentiels
from muninn.api.limites import LimiteurDebit
from muninn.api.main import app as api
from muninn.api.main import get_fournisseur, get_limiteur
from muninn.llm.fournisseur import FauxFournisseur, reponse_faux


class ReferentielsHorsLigne:
    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")


@pytest.fixture(autouse=True)
def referentiels_hors_ligne() -> None:
    api.dependency_overrides[get_referentiels] = ReferentielsHorsLigne


MESSAGE_FOURNISSEUR = json.dumps(
    {"categorie": "fournisseur", "confiance": 0.95, "nom_appelant": "Julie Lambert",
     "societe": "Sanitaires Dupuis", "numero_dicte": None,
     "message": "Livraison <b>jeudi</b>.", "rappel_souhaite": True}
)  # fmt: skip


def test_ecran_liste_les_scenarios(client_console: TestClient) -> None:
    html = client_console.get("/agent").text
    assert 'aria-current="page">Agent' in html
    for code in ("SC-01", "SC-Q8", "P4-perimetre"):
        assert f'value="{code}"' in html


def test_perimetre_affiche_outil_refuse_et_borne(client_console: TestClient) -> None:
    html = client_console.post(
        "/agent/executer", data={"mode": "scenario", "scenario_id": "P4-perimetre"}
    ).text
    assert "Modèle simulé" in html and "<code>lire_base</code>" in html
    assert "outil_inconnu" in html and "borne atteinte" in html
    assert "conforme à l'attendu" in html


def test_message_ajoute_a_la_liste_et_echappe(client_console: TestClient) -> None:
    f = FauxFournisseur(scenario=[reponse_faux(contenu=MESSAGE_FOURNISSEUR)])
    api.dependency_overrides[get_fournisseur] = lambda: f
    html = client_console.post(
        "/agent/executer",
        data={"mode": "transcript", "transcript": "Appelant : Julie Lambert, Sanitaires Dupuis.",
              "trade": "plomberie", "caller_number": "+33699000011"},
    ).text  # fmt: skip
    assert "Message (fournisseur)" in html and "Julie Lambert, Sanitaires Dupuis" in html
    assert "<b>jeudi</b>" not in html  # balisage retiré par le serveur, puis texte échappé
    assert "Aucun message pour l&#39;instant" not in html


def test_refus_affiche_code_et_motif(client_console: TestClient) -> None:
    html = client_console.post(
        "/agent/executer", data={"mode": "transcript", "transcript": ""}
    ).text
    assert 'role="alert"' in html and "<code>validation_failed</code>" in html


def test_lot_de_huit_scenarios(client_console: TestClient) -> None:
    html = client_console.post("/agent/lot", data={"groupe": "qualification"}).text
    assert "Bilan :" in html and "sur 8 conformes" in html
    assert html.count('<th scope="row">SC-Q') == 8


def test_lot_interrompu_par_la_limite(client_console: TestClient) -> None:
    limiteur = LimiteurDebit([(60, 3)])  # une seule limite pour tout le lot
    api.dependency_overrides[get_limiteur] = lambda: limiteur
    html = client_console.post("/agent/lot", data={"groupe": "annexe_a"}).text
    assert "Lot interrompu au scénario SC-04" in html and "sur 8 conformes" in html


def test_messages_renvoyes_sont_filtres(client_console: TestClient) -> None:
    """La liste revient du formulaire : seuls les champs connus sont gardés et affichés."""
    faux = json.dumps([{"categorie": "personnel", "message": "<script>x</script>", "pirate": 1}])
    html = client_console.post(
        "/agent/lot", data={"groupe": "qualification", "messages": faux}
    ).text
    assert "<script>x</script>" not in html and "pirate" not in html


def test_refus_dans_un_lot_ne_l_interrompt_pas(client_console: TestClient) -> None:
    from muninn.llm.fournisseur import RefusContenu

    # premier scénario : qualification puis extraction bloquées, refus poli (D-73)
    f = FauxFournisseur(scenario=[RefusContenu("filtre"), RefusContenu("filtre")])
    api.dependency_overrides[get_fournisseur] = lambda: f
    html = client_console.post("/agent/lot", data={"groupe": "qualification"}).text
    assert "refus content_refused" in html and "Lot interrompu" not in html
    assert html.count('<th scope="row">SC-Q') == 8
