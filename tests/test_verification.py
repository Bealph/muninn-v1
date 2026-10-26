"""Contrôles du texte des critères reportés dans `muninn.demo.verification` (sprint 5, étape 7).

Jusqu'au sprint 4, seul le script de production les faisait (`complements`). Chaque test part d'un
brouillon valide de SC-01 et vérifie qu'une seule faute ajoute exactement l'écart attendu.
"""

from typing import Any

from muninn.demo.verification import verifier_annexe_a
from muninn.extraction.contrat import Controles, DossierDraft, TexteCourt
from muninn.extraction.evaluateur import CandidateCommune, Enveloppe, Extraction, ProvenanceChamp
from test_extraction_contrat import dossier_sc01

ENTENDU = ProvenanceChamp(origine="entendu", auteur="agent")
NON_CONTROLE = {"status": "not_checked", "reason": "no_value", "referential": None}


def extraction(b: DossierDraft, candidates: list[CandidateCommune] | None = None) -> Extraction:
    enveloppe = Enveloppe(
        provenance={"client.adresse.commune": ENTENDU, "client.adresse.code_postal": ENTENDU},
        departement=None, candidates=candidates or [], a_verifier=True, motifs=[], garde_fous=[],
    )  # fmt: skip
    return Extraction(brouillon=b, enveloppe=enveloppe, agent=None)


def reference() -> DossierDraft:
    return DossierDraft.model_validate(dossier_sc01())


def nouveaux_ecarts(scenario: str, faute: Extraction, juste: Extraction) -> set[str]:
    return set(verifier_annexe_a(scenario, faute)) - set(verifier_annexe_a(scenario, juste))


def avec(b: DossierDraft, **champs: Any) -> DossierDraft:
    return b.model_copy(update=champs)


def test_sc01_exige_le_nom_martin() -> None:
    b = reference()
    assert b.client.nom.value and b.client.nom.value.lower() == "martin"
    client = b.client.model_copy(update={"nom": TexteCourt(value="Dupont", confidence=0.9)})
    assert nouveaux_ecarts("SC-01", extraction(avec(b, client=client)), extraction(b)) == {
        "nom Martin"
    }


def test_sc05_exige_un_objet_de_la_liste_l05() -> None:
    b = reference()

    def objet(texte: str) -> DossierDraft:
        court = TexteCourt(value=texte, confidence=0.9)
        return avec(b, demande=b.demande.model_copy(update={"objet_court": court}))

    juste, faute = objet("Chaudière en panne"), objet("Fuite sous évier")
    assert nouveaux_ecarts("SC-05", extraction(faute), extraction(juste)) == {"objet L-05"}


def test_sc05_et_sc07_exigent_commune_et_code_postal_verifies() -> None:
    b = reference()
    assert b.checks.commune.status == b.checks.code_postal.status == "verified"
    non_controles = Controles.model_validate({
        "client.telephone": b.checks.telephone.model_dump(),
        "client.adresse.code_postal": NON_CONTROLE,
        "client.adresse.commune": NON_CONTROLE | {"insee_code": None, "match": None,
                                                  "heard_value": None},
    })  # fmt: skip
    faute = extraction(avec(b, checks=non_controles))
    for scenario in ("SC-05", "SC-07"):
        assert "commune et code postal verifies" in nouveaux_ecarts(
            scenario, faute, extraction(b)
        ), scenario


def test_sc10_exige_code_postal_et_departement_des_candidates() -> None:
    b = reference()
    completes = [
        CandidateCommune(code_insee="28267", nom="Montreuil", departement="28",
                         codes_postaux=["28500"]),
        CandidateCommune(code_insee="85148", nom="Montreuil", departement="85",
                         codes_postaux=["85200"]),
        CandidateCommune(code_insee="93048", nom="Montreuil", departement="93",
                         codes_postaux=["93100"]),
    ]  # fmt: skip
    incompletes = [*completes[:2], completes[2].model_copy(update={"codes_postaux": []})]
    assert nouveaux_ecarts("SC-10", extraction(b, incompletes), extraction(b, completes)) == {
        "candidates avec code postal et departement"
    }
