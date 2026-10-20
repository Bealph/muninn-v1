"""Essai de la qualification avec le vrai modèle : CA-7 en local (sprint 4, étape 6).

Usage : `uv run python eval/qualification/essai_etape6.py [--repetitions N]`. Authentification
Entra ID du poste (`az login`) ; référentiels de production en lecture seule. Dialogues figés
`eval/qualification/scenarios.json` (données synthétiques, R9). CA-7 : SC-Q1, SC-Q2, SC-Q5 et
SC-Q6 donnent un message avec la catégorie, le nom dit et le numéro présenté ; SC-Q3, SC-Q4 et
SC-Q8 un dossier, jamais un message ; SC-Q7 l'urgence de sécurité. SC-Q3, SC-Q4 et SC-Q7 :
3 fois sur 3. Ce n'est pas la vérification sur Azure (étape 11). Résultat :
`eval/qualification/essai_etape6.json`.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from muninn.core.config import Settings
from muninn.demo.verification import verifier_qualification
from muninn.extraction.evaluateur import ContenuRefuse
from muninn.extraction.outils import ClientReferentiels
from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import construire_fournisseur
from muninn.qualification.qualificateur import (
    charger_paquet_qualification,
    traiter_appel,
)

DOSSIER = Path(__file__).parent
SCENARIOS = DOSSIER / "scenarios.json"
FOUNDRY = "https://adialloext-muninn1-resource.services.ai.azure.com"
API_REFERENTIELS = (
    "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
)
PLAFOND_MICRO_EUR = 500_000  # 0,50 €, dans le plafond du sprint (D-64)


def main() -> None:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--repetitions", type=int, default=3)
    repetitions = arguments.parse_args().repetitions
    paquet_q, paquet_x = charger_paquet_qualification(), charger_paquet()
    fournisseur = construire_fournisseur(
        Settings(llm_fournisseur="azure", azure_ai_endpoint=FOUNDRY)
    )
    referentiels = ClientReferentiels(API_REFERENTIELS, delai_s=15)
    jeu = json.loads(SCENARIOS.read_text(encoding="utf-8"))

    lignes: list[dict[str, Any]] = []
    cout = 0
    for repetition in range(1, repetitions + 1):
        for s in jeu["scenarios"]:
            if cout >= PLAFOND_MICRO_EUR:
                sys.exit(f"Plafond atteint : {cout / 1e6:.4f} €")
            try:
                t = traiter_appel(
                    s["transcription"], paquet_q, paquet_x, fournisseur, referentiels,
                    "plomberie", "2026-10-20", s["numero_presente"],
                )  # fmt: skip
            except ContenuRefuse:
                lignes.append({"scenario": s["id"], "repetition": repetition, "resultat": "refus"})
                print(f"{s['id']} r{repetition} : refus du filtre de contenu")
                continue
            q = t.qualification
            cout_ligne = (q.cout_micro_eur if q else 0) + (
                t.extraction.agent.cout_micro_eur if t.extraction and t.extraction.agent else 0
            )
            cout += cout_ligne
            ecarts = verifier_qualification(s["attendu"], t)
            lignes.append(
                {
                    "scenario": s["id"],
                    "repetition": repetition,
                    "resultat": "conforme" if not ecarts else "ecarts",
                    "ecarts": ecarts,
                    "issue": "message" if t.message else "dossier" if t.extraction else "trace",
                    "categorie": q.categorie if q else None,
                    "categorie_modele": q.categorie_modele if q else None,
                    "confiance": q.confiance if q else None,
                    "regle": q.regle if q else None,
                    "garde_fous": sorted(t.garde_fous)
                    + (t.extraction.enveloppe.garde_fous if t.extraction else []),
                    "cout_micro_eur": cout_ligne,
                }
            )
            print(
                f"{s['id']} r{repetition} : {'conforme' if not ecarts else ecarts} ; "
                f"{q.categorie_modele if q else '-'} -> {q.categorie if q else '-'} "
                f"({q.confiance if q else '-'}, regle {q.regle if q else '-'})"
            )

    synthese = {
        "date": "2026-10-20",
        "dialogues": jeu["version"],
        "paquet": paquet_q.prompt_version,
        "conformes": sum(x["resultat"] == "conforme" for x in lignes),
        "executions": len(lignes),
        "refus_du_filtre": sum(x["resultat"] == "refus" for x in lignes),
        "cout_total_eur": round(cout / 1e6, 4),
        "lignes": lignes,
    }
    (DOSSIER / "essai_etape6.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"\nConformes : {synthese['conformes']}/{len(lignes)} ; "
        f"refus du filtre : {synthese['refus_du_filtre']} ; coût {synthese['cout_total_eur']} €"
    )


if __name__ == "__main__":
    main()
