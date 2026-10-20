"""Vérifications des scénarios, partagées par les essais (`eval/`) et l'écran « Agent ».

- `verifier_annexe_a` : ce que les critères CA-1 à CA-4 attendent du brouillon (annexe A, avenant
  de CA-2 par D-69), déplacé de `eval/agent/essai_etape4.py` sans changement de règle.
- `verifier_qualification` : CA-7, déplacé de `eval/qualification/essai_etape6.py`.
- `verifier_perimetre` : le scénario P4 (outil hors liste refusé, borne d'appels atteinte).
"""

from typing import Any

from muninn.extraction.entree import normaliser
from muninn.extraction.evaluateur import ACTION_GAZ, Extraction
from muninn.qualification.qualificateur import Traitement

L01 = {"fuite sous evier", "fuite evier", "fuite sous l evier"}
L08 = {"fuite chauffe eau electrique", "fuite de chauffe eau electrique", "fuite chauffe eau"}


def verifier_annexe_a(scenario: str, x: Extraction) -> list[str]:
    """Écarts au regard de l'annexe A et des critères ; vide si conforme."""
    b, e = x.brouillon, x.enveloppe
    a = b.client.adresse
    commune, code = normaliser(a.commune.value or ""), a.code_postal.value
    ecarts: list[str] = []

    def exiger(condition: bool, nom: str) -> None:
        if not condition:
            ecarts.append(nom)

    if scenario == "SC-01":
        exiger(commune == "montreuil" and code == "93100", "commune et code")
        exiger(
            b.checks.commune.status == b.checks.code_postal.status == "verified", "statuts verifies"
        )
        exiger(e.provenance["client.adresse.commune"].origine == "entendu", "provenance entendu")
        exiger(b.client.telephone.value == "+33699000001", "telephone")
        exiger(normaliser(b.demande.objet_court.value or "") in L01, "objet L-01")
        exiger(b.demande.urgence == "urgent", "urgence")
    elif scenario == "SC-02":
        exiger(code == "94300" and b.checks.code_postal.status == "verified", "code 94300 verifie")
        exiger(e.provenance["client.adresse.code_postal"].origine == "deduit", "code deduit")
        exiger(b.demande.urgence == "normal", "urgence")
    elif scenario == "SC-03":
        exiger(commune == "bagnolet" and code == "93100", "valeurs gardees")
        exiger(b.checks.commune.status == "mismatch", "incoherent")
        exiger(e.a_verifier, "a verifier")
    elif scenario == "SC-04":
        exiger(b.demande.urgence == "securite", "urgence securite")
        exiger(b.demande.rdv_propose is None, "rdv vide")
        exiger(bool(b.actions) and b.actions[0] == ACTION_GAZ, "orientation en tete")
    elif scenario == "SC-05":
        exiger(commune == "montreuil" and code == "93100", "commune et code")
        exiger(b.demande.urgence == "normal", "urgence")
        exiger("diabet" not in normaliser(b.model_dump_json()), "aucun terme de sante")
    elif scenario == "SC-07":
        exiger(b.checks.commune.insee_code == "93048" and code == "93100", "93048 et 93100")
        exiger(e.provenance["client.adresse.commune"].origine == "deduit", "commune deduite")
        exiger(e.provenance["client.adresse.code_postal"].origine == "deduit", "code deduit")
    elif scenario == "SC-08":
        exiger(normaliser(b.demande.objet_court.value or "") in L08, "objet L-08")
    elif scenario == "SC-10":
        exiger(commune == "montreuil" and code is None, "Montreuil garde, code vide")
        exiger(
            {c.code_insee for c in e.candidates} == {"28267", "85148", "93048"}, "trois candidates"
        )
        exiger(e.a_verifier, "a verifier")
    return ecarts


def verifier_qualification(attendu: dict[str, Any], t: Traitement) -> list[str]:
    """Écarts au regard de CA-7 ; vide si conforme."""
    ecarts: list[str] = []

    def exiger(condition: bool, nom: str) -> None:
        if not condition:
            ecarts.append(nom)

    m, x = t.message, t.extraction
    if attendu.get("issue") == "message":
        exiger(m is not None and x is None, "message sans dossier")
        if m is not None:
            exiger(m.categorie == attendu["categorie"], f"categorie {attendu['categorie']}")
            exiger(attendu["nom_contient"] in normaliser(m.nom_appelant or ""), "nom dit")
            exiger(m.numero_rappel == attendu["numero_rappel"], "numero presente")
    if attendu.get("issue") == "dossier":
        exiger(x is not None and m is None, "dossier, jamais un message")
    if attendu.get("a_verifier"):
        exiger(x is not None and x.enveloppe.a_verifier, "a verifier")
    if attendu.get("securite"):
        securite = (m is not None and m.securite) or (
            x is not None and x.brouillon.demande.urgence == "securite"
        )
        exiger(securite, "urgence de securite")
    return ecarts


def verifier_perimetre(t: Traitement) -> list[str]:
    """P4 : l'outil hors liste est refusé, la borne d'appels arrête la boucle."""
    x = t.extraction
    if x is None or x.agent is None:
        return ["dossier attendu"]
    ecarts = []
    if not any(a.nom == "lire_base" and a.statut == "outil_inconnu" for a in x.agent.appels_outils):
        ecarts.append("outil hors liste refuse")
    if not x.agent.borne_atteinte:
        ecarts.append("borne atteinte")
    return ecarts


def verifier(groupe: str, scenario_id: str, attendu: dict[str, Any], t: Traitement) -> list[str]:
    """Écarts d'un scénario de l'écran « Agent » ; vide si conforme."""
    if groupe == "qualification":
        return verifier_qualification(attendu, t)
    if groupe == "perimetre":
        return verifier_perimetre(t)
    if t.extraction is None:
        return ["dossier attendu"]
    return verifier_annexe_a(scenario_id, t.extraction)
