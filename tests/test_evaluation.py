"""Harnais d'évaluation V-08 (sprint 4, étape 9), sans réseau ni modèle réel."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from muninn.evaluation import harnais
from muninn.evaluation.mesures import comparer, controler_conformite, percentile, wilson
from muninn.extraction.contrat import (
    Action,
    CodePostal,
    DossierDraft,
    Telephone,
    TexteCourt,
    TexteLong,
)
from muninn.extraction.evaluateur import ACTION_GAZ, Enveloppe, Extraction
from muninn.llm.fournisseur import FauxFournisseur
from test_extraction_contrat import dossier_sc01

JEU = json.loads(
    (Path(__file__).parents[1] / "eval" / "v08" / "jeu.json").read_text(encoding="utf-8")
)
SCENARIOS = {s["id"]: s for s in JEU["scenarios"]}


def brouillon(**champs: Any) -> DossierDraft:
    """Brouillon valide de SC-01 (tests du contrat), champs remplacés pour le test."""
    vides: dict[str, Any] = dict.fromkeys(
        ("nom", "telephone", "origin", "code_postal", "commune", "objet")
    )
    c = vides | {"description": None, "urgence": "non_precise", "actions": []} | champs
    b = DossierDraft.model_validate(dossier_sc01())

    def court(v: str | None) -> TexteCourt:
        return TexteCourt(value=v, confidence=0.9 if v else 0)

    adresse = b.client.adresse.model_copy(
        update={"rue": court(None), "code_postal": CodePostal(value=c["code_postal"],
                confidence=0.9 if c["code_postal"] else 0), "commune": court(c["commune"])}
    )  # fmt: skip
    client = b.client.model_copy(update={
        "nom": court(c["nom"]), "prenom": court(None), "adresse": adresse,
        "telephone": Telephone(value=c["telephone"], confidence=0.9 if c["telephone"] else 0,
                               origin=c["origin"]),
    })  # fmt: skip
    demande = b.demande.model_copy(update={
        "objet_court": court(c["objet"]), "urgence": c["urgence"],
        "description": TexteLong(value=c["description"], confidence=0.9 if c["description"] else 0),
        "disponibilites_client": [],
    })  # fmt: skip
    actions = [Action.model_validate(a) for a in c["actions"]]
    return b.model_copy(update={"client": client, "demande": demande, "actions": actions,
                                "cle_humaine": None})  # fmt: skip


def extraction(b: DossierDraft, a_verifier: bool = False) -> Extraction:
    enveloppe = Enveloppe(provenance={}, departement=None, candidates=[], a_verifier=a_verifier,
                          motifs=[], garde_fous=[])  # fmt: skip
    return Extraction(brouillon=b, enveloppe=enveloppe, agent=None)


def test_wilson_et_percentile() -> None:
    assert wilson(18, 20) == (0.699, 0.972)  # valeurs de la phase 1, document 04, § 4.4
    assert percentile([100, 200, 300, 400], 0.5) == 200 and percentile([], 0.95) == 0


def test_comparaison_normalisee_et_invention() -> None:
    v = SCENARIOS["T15"]["verite"]  # nom attendu nul
    b = brouillon(nom="Syndic", telephone="+33639981015", origin="caller_id", code_postal="06000",
                  commune="nice", objet="Clé cassée dans la serrure")  # fmt: skip
    r = comparer(v, b)
    assert r["nom"] == {"exact": False, "invente": True, "absent_attendu": True}
    assert r["commune"]["exact"] and r["objet"]["exact"] and r["telephone"]["exact"]


def test_conformite_medicale_et_refus() -> None:
    sante = brouillon(description="Panne, cliente enceinte.", urgence="urgent")
    assert "terme de santé : enceinte" in controler_conformite(SCENARIOS["C01"], extraction(sante))
    refus = brouillon(telephone="+33639982005", origin="caller_id",
                      actions=[{"type": "rappeler", "libelle": "Rappeler"}])  # fmt: skip
    assert controler_conformite(SCENARIOS["C05"], extraction(refus)) == []
    assert controler_conformite(SCENARIOS["C05"], None) == ["aucun brouillon (refus)"]


def test_conformite_gaz() -> None:
    gaz = brouillon(urgence="securite", actions=[ACTION_GAZ.model_dump()])
    assert controler_conformite(SCENARIOS["C03"], extraction(gaz)) == []
    assert controler_conformite(SCENARIOS["C04"], extraction(gaz)) == ["urgence de sécurité à tort"]


class ReferentielsHorsLigne:
    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        raise httpx.ConnectError("hors ligne")


def test_campagne_avec_le_faux_modele(tmp_path: Path) -> None:
    """Le faux modèle rend « {} » : tout est hors schéma ; la campagne va au bout, verdict échec."""
    rapport, code = harnais.executer(FauxFournisseur, ReferentielsHorsLigne(), tmp_path)
    assert code == 1 and rapport["verdict"] == "echec"
    assert (
        rapport["test"]["global"]["total"] == 120 and len(rapport["bloquants"]["conformite"]) == 15
    )
    assert len(rapport["bloquants"]["qualification"]) == 9
    assert list(tmp_path.glob("*.json"))


def test_sans_acces_au_modele_non_mesure(tmp_path: Path) -> None:
    def sans_acces() -> FauxFournisseur:
        raise PermissionError

    rapport, code = harnais.executer(sans_acces, ReferentielsHorsLigne(), tmp_path)
    assert code == 2 and rapport["verdict"] == "non_mesure"


def test_plafond(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(harnais, "PLAFOND_MICRO_EUR", 0)
    rapport, code = harnais.executer(FauxFournisseur, ReferentielsHorsLigne(), tmp_path)
    assert code == 2 and "plafond" in rapport["raisons"][0]


def test_racines_de_l_objet() -> None:
    from muninn.evaluation.mesures import contient_racines

    assert contient_racines("Ballon d’eau chaude fuit", [["ballon", "fui"]])
    assert contient_racines("Tableau disjoncte four", [["disjonct"]])
    assert not contient_racines("prises salon", [["prise", "panne"], ["prise", "marche"]])
    assert not contient_racines("fuite", [])
