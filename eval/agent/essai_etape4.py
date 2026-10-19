"""Essai bout en bout, agent puis évaluateur, avec le vrai modèle (sprint 4, étape 4).

Usage : `uv run python eval/agent/essai_etape4.py [--repetitions N]`. Authentification Entra ID du
poste (`az login`) ; référentiels de production en lecture seule. Scénarios de l'annexe A
(données synthétiques, R9), transcriptions du banc T-06. Vérifie, en local, ce que les critères
CA-1 à CA-4 attendent du brouillon (avenant de CA-2 par D-69). Ce n'est ni l'évaluation de V-08
(étape 9), ni la vérification sur Azure (étape 11). Résultat : `eval/agent/essai_etape4.json`.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from muninn.core.config import Settings
from muninn.extraction.evaluateur import (
    ACTION_GAZ,
    ContenuRefuse,
    Extraction,
    extraire_dossier,
    normaliser,
)
from muninn.extraction.outils import ClientReferentiels
from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import construire_fournisseur

DOSSIER = Path(__file__).parent
SCENARIOS = DOSSIER.parent / "t06" / "scenarios.json"
FOUNDRY = "https://adialloext-muninn1-resource.services.ai.azure.com"
API_REFERENTIELS = (
    "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
)
PLAFOND_MICRO_EUR = 500_000  # 0,50 €, dans le plafond du sprint (D-64)
METIERS = {"SC-02": "electricite", "SC-05": "chauffage", "SC-10": "chauffage"}
L01 = {"fuite sous evier", "fuite evier", "fuite sous l evier"}
L08 = {"fuite chauffe eau electrique", "fuite de chauffe eau electrique", "fuite chauffe eau"}


def verifier(scenario: str, x: Extraction) -> list[str]:
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


def main() -> None:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--repetitions", type=int, default=1)
    repetitions = arguments.parse_args().repetitions
    paquet = charger_paquet()
    fournisseur = construire_fournisseur(
        Settings(llm_fournisseur="azure", azure_ai_endpoint=FOUNDRY)
    )
    referentiels = ClientReferentiels(API_REFERENTIELS, delai_s=15)
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]

    lignes: list[dict[str, Any]] = []
    cout = 0
    for repetition in range(1, repetitions + 1):
        for s in scenarios:
            if cout >= PLAFOND_MICRO_EUR:
                sys.exit(f"Plafond atteint : {cout / 1e6:.4f} €")
            metier = METIERS.get(s["id"], "plomberie")
            try:
                x = extraire_dossier(
                    s["transcription"], paquet, fournisseur, referentiels, metier, "2026-10-19"
                )  # type: ignore[arg-type]
            except ContenuRefuse:
                lignes.append(
                    {"scenario": s["id"], "repetition": repetition, "resultat": "refus du filtre"}
                )
                print(f"{s['id']} r{repetition} : refus du filtre de contenu (D-65)")
                continue
            cout += x.agent.cout_micro_eur if x.agent else 0
            ecarts = verifier(s["id"], x)
            lignes.append(
                {
                    "scenario": s["id"],
                    "repetition": repetition,
                    "resultat": "conforme" if not ecarts else "ecarts",
                    "ecarts": ecarts,
                    "statut": x.brouillon.provenance.extraction_status,
                    "motifs": x.enveloppe.motifs,
                    "garde_fous": x.enveloppe.garde_fous,
                    "outils": [a.nom for a in x.agent.appels_outils] if x.agent else [],
                    "cout_micro_eur": x.agent.cout_micro_eur if x.agent else 0,
                    "duree_ms": x.agent.duree_ms if x.agent else 0,
                }
            )
            print(
                f"{s['id']} r{repetition} : {'conforme' if not ecarts else ecarts} ; "
                f"motifs {x.enveloppe.motifs}"
            )

    synthese = {
        "date": "2026-10-19",
        "paquet": paquet.prompt_version,
        "conformes": sum(x["resultat"] == "conforme" for x in lignes),
        "refus_du_filtre": sum(x["resultat"] == "refus du filtre" for x in lignes),
        "extractions": len(lignes),
        "cout_total_eur": round(cout / 1e6, 4),
        "lignes": lignes,
    }
    (DOSSIER / "essai_etape4.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"\nConformes : {synthese['conformes']}/{len(lignes)} ; "
        f"refus du filtre : {synthese['refus_du_filtre']} ; "
        f"coût {synthese['cout_total_eur']} €"
    )


if __name__ == "__main__":
    main()
