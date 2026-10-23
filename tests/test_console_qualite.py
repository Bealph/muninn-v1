"""Écran « Qualité » de la console (sprint 5, étape 4 ; V-10, TB-6), avec une API simulée.

L'API est remplacée par un transport httpx qui rend une réponse choisie : chaque état de l'écran
(tout va bien, alerte, pas assez d'appels, base indisponible) se rend sans base ni réseau.
"""

import html as html_
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from muninn.console.main import _graphique, heure_lisible, pluriel
from outils_qualite import DERNIER_ID, EPISODE, qualite, rendre_qualite


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
    assert "Prévenir la personne qui gère Muninn" in html


def test_pas_assez_d_appels(ecran: Ecran) -> None:
    html = ecran(qualite(total=5, dossiers=4, a_verifier=3, part_a_verifier=0.75, refus=0))
    assert 'class="etat insuffisant"' in html and "Aucun problème détecté depuis 24 heures" in html
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
    # Heure de Paris : UTC+2 le 23 octobre 2026 (heure d'été).
    assert (g["debut"], g["fin"]) == ("22/10 à 13:00", "23/10 à 12:59")
    assert _graphique(serie[2:], 24, maintenant) is None


def test_pluriel_a_la_francaise() -> None:
    assert [pluriel(n, "dossier", "dossiers") for n in (0, 1, 2)] == [
        "0 dossier", "1 dossier", "2 dossiers"
    ]  # fmt: skip


def test_etat_gris_dit_ce_qui_manque(ecran: Ecran) -> None:
    html = ecran(qualite(total=5, dossiers=4, a_verifier=1, part_a_verifier=0.25, refus=0))
    assert "(4 dossiers, il en faut 20) pour un contrôle complet" in html
    assert "4 dossiers sur les 20 nécessaires" in html and "4 dossiers mesurés sur les 20" in html


def test_echeance_du_jugement_affichee_si_juge(ecran: Ecran) -> None:
    juge = datetime.now(UTC).replace(hour=23, minute=45, second=0, microsecond=0)
    html = ecran(qualite(juge=juge))
    attendu = heure_lisible(juge.isoformat())  # date ajoutée si ce n'est plus le jour même
    assert f"l'état ne pourra plus être jugé après {attendu} (heure de Paris)" in html
    assert "Calculé le 23/10/2026 à 16:00 (heure de Paris)" in html


def test_historique_des_alertes(ecran: Ecran) -> None:
    html = ecran(qualite(episodes=[EPISODE]))
    assert "Alertes des dernières 24 heures" in html
    assert "22/10 à 16:05" in html and "22/10 à 16:50" in html  # heure de Paris
    assert "<td>Dossiers à vérifier</td>" in html and "45 % (10 sur 22)" in html
    assert "Aucune alerte sur les dernières 24 heures" in ecran(qualite())


def test_cartes_alignees_sur_les_alertes(ecran: Ecran) -> None:
    html = ecran(qualite(secours=2, part_secours=0.08))
    assert "Brouillons de secours" in html and "8 %" in html
    assert "Nouveaux essais de l'IA" in html and "Erreurs du service" not in html


def test_cout_du_mois_et_seuil_trace(ecran: Ecran) -> None:
    html = ecran(qualite())
    assert "Coût de l'IA sur le mois (10/2026)" in html and "1,2345 €" in html
    assert "environ 1,66 € sur le mois, soit 3 % du budget mensuel du projet (60 €)" in html
    assert "seuil : 20 %" in html


def test_actualisation_deduite_d_un_appel_recent(ecran: Ecran) -> None:
    recent = qualite()
    recent["dernier_appel"]["recu_le"] = datetime.now(UTC).isoformat()
    html = ecran(recent)
    assert "location.reload" in html and "un appel a eu lieu il y a moins de 10 minutes" in html
    # Un choix explicite l'emporte : décoché, pas d'actualisation.
    assert "location.reload" not in ecran(recent, chemin="/qualite?auto=0")


def test_volume_accorde_au_singulier(ecran: Ecran) -> None:
    html = ecran(qualite(total=1, dossiers=1, messages=0, a_verifier=0, part_a_verifier=0.0,
                         refus=0))  # fmt: skip
    assert "1 dossier mesuré sur les 20 nécessaires" in html and "1 dossiers" not in html


def test_details_techniques_replies_et_sans_jargon_en_tete(ecran: Ecran) -> None:
    html = ecran(qualite(a_verifier=10, part_a_verifier=0.4))
    tete, _, technique = html.partition('<details class="technique">')
    # Identifiants, version et codes d'alerte : seulement dans le bloc replié.
    for terme in ("AL-01", DERNIER_ID, "abc1234", "UTC"):
        assert terme not in tete, terme
    assert "AL-01 : dossiers à vérifier" in technique and DERNIER_ID in technique
    # Sous 20 dossiers, une heure est grisée sur le graphique de la part à vérifier.
    assert 'class="faible"' in html


def test_heure_de_paris() -> None:
    # 23 octobre 2026, heure d'été (UTC+2) ; 26 octobre, heure d'hiver (UTC+1).
    assert heure_lisible("2026-10-23T14:05:00+00:00").endswith("16:05")
    assert heure_lisible("2026-10-26T14:05:00+00:00") == "26/10 à 15:05"
