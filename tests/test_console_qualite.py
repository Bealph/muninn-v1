"""Écran « Qualité » de la console (sprint 5, étape 4 ; V-10, TB-6), avec une API simulée.

L'API est remplacée par un transport httpx qui rend une réponse choisie : chaque état de l'écran
(tout va bien, alerte, pas assez d'appels, base indisponible) se rend sans base ni réseau.
"""

import html as html_
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from muninn.console.main import _graphique, pluriel
from outils_qualite import DERNIER_ID, qualite, rendre_qualite


class Ecran:
    """Rend l'écran et garde les requêtes faites à l'API simulée ; texte désenchappé."""

    demandes: list[httpx.Request]

    def __call__(
        self, corps: dict[str, Any] | None = None, statut: int = 200, chemin: str = "/qualite"
    ) -> str:
        brut, self.demandes = rendre_qualite(corps, statut, chemin)
        # Texte désenchappé : Jinja rend l'apostrophe en « &#39; ».
        return html_.unescape(brut)


@pytest.fixture
def ecran() -> Ecran:
    return Ecran()


def test_tout_va_bien_en_mots(ecran: Ecran) -> None:
    html = ecran(qualite())
    assert 'aria-current="page">Qualité' in html
    assert "Aucun seuil dépassé" in html and "Sous le seuil" in html
    # Les chiffres de la période, en clair.
    assert "Les chiffres sur les dernières 24 heures" in html
    assert "12 %" in html and "2,7 s" in html and "5,7 s" in html and "0,0032 €" in html
    # Noms de champs et protections en français, jamais le code brut seul.
    assert "Code postal" in html and "Odeur de gaz" in html
    assert "client.adresse.code_postal" not in html
    assert DERNIER_ID in html and "SC-10" in html


def test_alerte_en_rouge_avec_la_regle(ecran: Ecran) -> None:
    html = ecran(qualite(a_verifier=10, part_a_verifier=0.4))
    assert 'class="etat alerte"' in html and "Alerte" in html
    assert "AL-01" in html and "Seuil dépassé" in html
    assert "Prévenir l'exploitant" in html


def test_pas_assez_d_appels(ecran: Ecran) -> None:
    html = ecran(qualite(total=5, dossiers=4, a_verifier=3, part_a_verifier=0.75, refus=0))
    assert 'class="etat insuffisant"' in html and "Pas assez d'appels pour juger" in html
    # Les trois quarts « à vérifier », mais sur 4 dossiers : pas d'alerte.
    assert "Seuil dépassé" not in html


def test_base_indisponible(ecran: Ecran) -> None:
    html = ecran(statut=503)
    assert 'role="alert"' in html and "base des traitements ne répond pas" in html


def test_periode_choisie_transmise_a_l_api(ecran: Ecran) -> None:
    html = ecran(qualite(fenetre_heures=168), chemin="/qualite?heures=168")
    assert "Les chiffres sur les 7 derniers jours" in html
    assert any(d.url.params.get("heures") == "168" for d in ecran.demandes)


def test_periode_inconnue_ramenee_a_24_heures(ecran: Ecran) -> None:
    ecran(qualite(), chemin="/qualite?heures=5")
    assert any(d.url.params.get("heures") == "24" for d in ecran.demandes)


def test_actualisation_seulement_si_demandee(ecran: Ecran) -> None:
    assert "location.reload" not in ecran(qualite())
    assert "location.reload" in ecran(qualite(), chemin="/qualite?auto=1")


def test_graphique_garde_la_place_des_heures_creuses() -> None:
    maintenant = datetime(2026, 10, 23, 10, 40, tzinfo=UTC)
    serie = [
        {"heure": "2026-10-23T10:00:00Z", "total": 4, "a_verifier": 1},
        {"heure": "2026-10-23T05:00:00Z", "total": 2, "a_verifier": 0},
        {"heure": "2026-10-21T10:00:00Z", "total": 9, "a_verifier": 9},  # hors des 24 heures
    ]
    g = _graphique(serie, 24, maintenant)
    assert g is not None
    # 24 cases de 25 unités : 10 h est la dernière, 5 h la dix-neuvième ; l'heure hors période
    # est ignorée, y compris pour l'échelle (la plus haute barre compte 4 appels).
    assert [b["x"] for b in g["barres"]] == [450.0, 575.0]
    assert g["haut"] == 4
    assert (g["debut"], g["fin"]) == ("22/10 à 11:00", "23/10 à 10:59")
    assert _graphique(serie[2:], 24, maintenant) is None


def test_pluriel_a_la_francaise() -> None:
    assert [pluriel(n, "dossier", "dossiers") for n in (0, 1, 2)] == [
        "0 dossier", "1 dossier", "2 dossiers"
    ]  # fmt: skip
