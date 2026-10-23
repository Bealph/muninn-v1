"""État du service sur la dernière heure : les trois règles de D-83, seuils et volumes minimaux."""

from typing import Any

import pytest

from muninn.traitements.etat import evaluer
from muninn.traitements.metriques import Metriques


def metriques(**valeurs: Any) -> Metriques:
    base: dict[str, Any] = {
        "fenetre_heures": 1, "total": 0, "dossiers": 0, "messages": 0, "traces": 0, "refus": 0,
        "taux_refus": None, "secours": 0, "relances": 0, "taux_erreur": None, "bornes": 0,
        "part_secours": None, "a_verifier": 0, "part_a_verifier": None, "securite": 0,
        "non_controle": 0,
        "part_non_controle": None, "latence_p50_ms": None, "latence_p95_ms": None,
        "extraction_p50_ms": None,
        "cout_moyen_eur": 0.0, "cout_total_eur": 0.0, "dossiers_valides": 0,
        "champs_corriges": 0, "corrections_par_champ": [], "garde_fous": [], "premier": None,
        "dernier": None, "dernier_appel": None, "serie": [],
    }  # fmt: skip
    base |= valeurs
    # Par défaut, chaque dossier a sa durée d'extraction, égale à `latence_p95_ms` au 95e centile.
    base.setdefault("extractions", base["dossiers"])
    base.setdefault("extraction_p95_ms", base["latence_p95_ms"])
    if base["dossiers"]:
        base["part_a_verifier"] = base["a_verifier"] / base["dossiers"]
    return Metriques(**base)


def niveaux(m: Metriques) -> dict[str, str]:
    return {r.code: r.niveau for r in evaluer(m).regles}


def test_aucun_appel_pas_assez_pour_juger() -> None:
    e = evaluer(metriques())
    assert e.niveau == "insuffisant" and e.titre == "Pas assez d'appels pour juger"
    assert set(niveaux(metriques()).values()) == {"insuffisant"}


def test_etat_gris_dit_combien_il_manque() -> None:
    e = evaluer(metriques(total=14, dossiers=12, messages=2))
    assert e.phrase.startswith("12 dossiers sur la dernière heure, il en faut 20 pour juger.")
    assert [(r.volume, r.unite_volume) for r in e.regles] == [
        (12, "dossiers"), (12, "dossiers"), (12, "dossiers mesurés")
    ]  # fmt: skip


def test_service_nominal_tout_va_bien() -> None:
    m = metriques(total=30, dossiers=30, a_verifier=3, latence_p95_ms=6000)
    e = evaluer(m)
    assert e.niveau == "ok" and e.titre == "Aucun seuil dépassé"
    assert "Non jugé" not in e.phrase
    assert niveaux(m) == {"AL-01": "ok", "AL-04": "ok", "AL-16": "ok"}


@pytest.mark.parametrize(("a_verifier", "attendu"), [(4, "ok"), (5, "alerte")])
def test_al01_seuil_de_20_pour_cent(a_verifier: int, attendu: str) -> None:
    # 4 sur 20 : 20 % pile, dans la norme ; 5 sur 20 : 25 %, au-dessus.
    m = metriques(total=20, dossiers=20, a_verifier=a_verifier, latence_p95_ms=5000)
    assert niveaux(m)["AL-01"] == attendu
    assert evaluer(m).niveau == attendu


def test_al01_ne_conclut_pas_sous_20_dossiers() -> None:
    # 10 sur 19, plus de la moitié : pas d'alerte, le volume ne permet pas de juger.
    m = metriques(total=19, dossiers=19, a_verifier=10)
    assert niveaux(m)["AL-01"] == "insuffisant"


@pytest.mark.parametrize(("secours", "attendu"), [(1, "ok"), (2, "alerte")])
def test_al04_brouillons_de_secours(secours: int, attendu: str) -> None:
    # 1 sur 20 : 5 % pile ; 2 sur 20 : 10 %.
    m = metriques(total=20, dossiers=20, secours=secours, latence_p95_ms=5000)
    assert niveaux(m)["AL-04"] == attendu


@pytest.mark.parametrize(("p95", "attendu"), [(20000, "ok"), (20001, "alerte")])
def test_al16_duree_au_95e_centile(p95: int, attendu: str) -> None:
    m = metriques(total=25, dossiers=25, latence_p95_ms=p95)
    assert niveaux(m)["AL-16"] == attendu


def test_al16_ne_compte_que_les_dossiers_mesures() -> None:
    # Refus et messages n'ont pas d'extraction ; 15 dossiers ne suffisent pas.
    m = metriques(total=25, refus=10, dossiers=15, latence_p95_ms=30000)
    assert niveaux(m)["AL-16"] == "insuffisant"
    # La durée de la qualification n'entre plus dans AL-16 : seul compte le 95e centile de
    # l'extraction (SLO-05).
    m = metriques(total=25, dossiers=25, latence_p95_ms=30000, extraction_p95_ms=8000)
    assert niveaux(m)["AL-16"] == "ok"


def test_alerte_nomme_les_regles_depassees() -> None:
    m = metriques(total=20, dossiers=20, a_verifier=10, secours=5, latence_p95_ms=5000)
    e = evaluer(m)
    assert e.niveau == "alerte"
    assert "dossiers à vérifier (AL-01), brouillons de secours (AL-04)" in e.phrase
    assert "AL-16" not in e.phrase and "Prévenir l'exploitant" in e.phrase


def test_regle_non_jugee_dite_meme_si_rien_ne_depasse() -> None:
    # Juste après la migration 0004 : 25 dossiers, dont 15 seulement ont leur durée d'extraction.
    # AL-01 et AL-04 se jugent, AL-16 non ; l'écran le dit au lieu d'annoncer que tout est vérifié.
    m = metriques(total=25, dossiers=25, a_verifier=1, latence_p95_ms=5000, extractions=15)
    e = evaluer(m)
    assert e.niveau == "ok"
    assert e.phrase.endswith("Non jugé faute d'appels : temps de préparation.")
