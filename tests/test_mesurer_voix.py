"""Benchmark C7 : les mesures d'un appel transcrit, calculées sans réseau."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from muninn.voix.contrat import Tour

SCRIPT = Path(__file__).resolve().parents[1] / "eval" / "c7" / "mesurer_voix.py"


@pytest.fixture(scope="module")
def m() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mesurer_voix", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DITS = [
    Tour("agent", "Bonjour, vous êtes en relation avec l'assistant automatique."),
    Tour("caller", "Mon numéro est le 06 99 00 00 01, j'habite au 12 rue des Lilas, 93100."),
]


def test_groupes_de_chiffres_regroupes(m: ModuleType) -> None:
    assert m.groupes_chiffres(DITS) == ["0699000001", "12", "93100"]


def test_chiffre_repete_compte_manquant_et_en_trop(m: ModuleType) -> None:
    """INC-09 : « 00 000 » entendu pour « 00 00 » rend un numéro faux, jamais exact."""
    entendus = [DITS[0], Tour("caller", DITS[1].texte.replace("00 00 01", "00 000 01"))]
    resultat = m.chiffres(entendus, DITS)
    assert resultat["groupes_dits"] == 3 and resultat["groupes_exacts"] == 2
    assert resultat["groupes_manquants"] == ["0699000001"]
    assert resultat["groupes_en_trop"] == ["06990000001"]


def test_locuteurs_inverses_comptes_faux(m: ModuleType) -> None:
    assert m.locuteurs(DITS, DITS) == 1.0
    inverses = [Tour("caller", DITS[0].texte), Tour("agent", DITS[1].texte)]
    assert m.locuteurs(inverses, DITS) == 0.0


def test_mesurer_un_appel_fidele(m: ModuleType) -> None:
    reponse = {
        "transcription": {
            "turns": [{"speaker": t.locuteur, "text": t.texte} for t in DITS],
            "transcription_ms": 4200,
            "audio_bytes": 60_000,
            "matches_scenario": True,
        },
        "issue": "dossier",
        "steps": [{"nom": "extraction", "details": {"cout_micro_eur": 4500}}],
    }
    ligne = m.mesurer(DITS, reponse)
    assert ligne["rappel"] == 1.0 and ligne["precision"] == 1.0 and ligne["mots_en_trop"] == 0
    assert ligne["locuteurs_justes"] == 1.0 and ligne["chiffres"]["groupes_exacts"] == 3
    assert ligne["transcription_ms"] == 4200 and ligne["cout_modele_micro_eur"] == 4500
    # Aucun texte entendu dans la preuve, seulement une empreinte.
    assert "turns" not in ligne and len(ligne["empreinte_entendu"]) == 16


def test_cout_synthese_comptee_une_seule_fois(m: ModuleType) -> None:
    ligne = {"caracteres": 1_000_000, "audio_s": 3600.0, "cout_modele_micro_eur": 0}
    premiere = m.cout_appel(ligne, premiere_synthese=True)
    suivante = m.cout_appel(ligne, premiere_synthese=False)
    assert premiere - suivante == pytest.approx(m.EUR_PAR_CARACTERE * 1_000_000)
    assert suivante == pytest.approx(m.EUR_PAR_HEURE_TRANSCRIPTION + m.EUR_PAR_EXTRACTION)


def test_synthese_globale_stabilite_et_seuils(m: ModuleType) -> None:
    base = {
        "scenario_id": "SC-01",
        "rappel": 0.98,
        "precision": 0.97,
        "locuteurs_justes": 1.0,
        "chiffres": {"groupes_dits": 3, "groupes_exacts": 2, "groupes_en_trop": ["1"]},
        "transcription_ms": 5000,
        "fidele_selon_api": True,
        "empreinte_entendu": "a",
    }
    lignes = [base, base | {"empreinte_entendu": "b", "precision": 0.90}, {"erreur": "x"}]
    s = m.synthese_globale(lignes)
    assert s["appels_mesures"] == 2 and s["appels_en_erreur"] == 1
    assert s["appels_sous_seuils_mots"] == 1 and s["scenarios_stables"] == 0
    assert s["groupes_chiffres_exacts"] == 4 and s["groupes_chiffres_en_trop"] == 2
