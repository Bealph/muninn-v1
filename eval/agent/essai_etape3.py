"""Essai de l'agent avec le vrai modèle (sprint 4, étape 3) : l'outil attendu est-il appelé ?

Usage : `uv run python eval/agent/essai_etape3.py [--repetitions N] [--date AAAA-MM-JJ]
[--resultat nom.json]`. Authentification Entra ID
du poste (`az login`) ; outils sur l'API des référentiels de production, en lecture seule.
Scénarios de l'annexe A du dossier V1 (données synthétiques, R9), transcriptions du banc T-06.
Ce n'est pas l'évaluation de V-08 (étape 9) : seulement une vérification de la boucle, plafonnée.
Résultat : `eval/agent/essai_etape3.json` par défaut (aucune donnée réelle). SC-10 : la commune
entendue est gardée (avenant D-69 de CA-2), le code postal reste vide.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from muninn.core.config import Settings
from muninn.extraction.agent import extraire
from muninn.extraction.outils import ClientReferentiels
from muninn.extraction.paquet import charger_paquet
from muninn.ingestion.normalisation import normaliser_nom
from muninn.llm.fournisseur import construire_fournisseur

DOSSIER = Path(__file__).parent
SCENARIOS = DOSSIER.parent / "t06" / "scenarios.json"
FOUNDRY = "https://adialloext-muninn1-resource.services.ai.azure.com"
API_REFERENTIELS = (
    "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
)
PLAFOND_MICRO_EUR = 500_000  # 0,50 €, dans le plafond du sprint (D-64)

# Scénario : métier de l'artisan, outil attendu, valeurs attendues (annexe A ; None = vide).
ATTENDUS: dict[str, tuple[str, str, dict[str, str | None]]] = {
    "SC-02": ("electricite", "chercher_communes", {"code_postal": "94300", "commune": "vincennes"}),
    "SC-07": ("plomberie", "chercher_communes", {"code_postal": "93100", "commune": "montreuil"}),
    "SC-08": ("plomberie", "chercher_terme_metier", {}),
    "SC-10": ("chauffage", "chercher_communes", {"code_postal": None, "commune": "montreuil"}),
}


def main() -> None:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--repetitions", type=int, default=3)
    arguments.add_argument("--date", default="2026-10-19")
    arguments.add_argument("--resultat", default="essai_etape3.json")
    args = arguments.parse_args()
    repetitions = args.repetitions

    paquet = charger_paquet()
    fournisseur = construire_fournisseur(
        Settings(llm_fournisseur="azure", azure_ai_endpoint=FOUNDRY)
    )
    referentiels = ClientReferentiels(
        API_REFERENTIELS, delai_s=float(paquet.parametres["delai_outil_s"]) + 10
    )
    transcriptions = {
        s["id"]: s["transcription"]
        for s in json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]
    }

    lignes: list[dict[str, Any]] = []
    cout_total = 0
    for repetition in range(1, repetitions + 1):
        for scenario, (metier, outil, valeurs) in ATTENDUS.items():
            if cout_total >= PLAFOND_MICRO_EUR:
                sys.exit(f"Plafond atteint : {cout_total / 1e6:.4f} €")
            r = extraire(
                transcriptions[scenario], paquet, fournisseur, referentiels, args.date, metier
            )
            cout_total += r.cout_micro_eur
            outils = [a.nom for a in r.appels_outils]
            adresse = r.sortie.client.adresse if r.sortie else None
            obtenu = {
                "code_postal": adresse.code_postal.value if adresse else None,
                "commune": normaliser_nom(adresse.commune.value, abreviations=False)
                if adresse and adresse.commune.value
                else None,
            }
            ecarts = [cle for cle, attendu in valeurs.items() if obtenu[cle] != attendu]
            ligne = {
                "scenario": scenario,
                "repetition": repetition,
                "statut": r.statut,
                "outils": outils,
                "outil_attendu_appele": outil in outils,
                "valeurs_conformes": r.statut == "complete" and not ecarts,
                "ecarts": ecarts,
                "etapes": r.etapes,
                "jetons_entree": r.jetons_entree,
                "jetons_sortie": r.jetons_sortie,
                "cout_micro_eur": r.cout_micro_eur,
                "duree_ms": r.duree_ms,
            }
            lignes.append(ligne)
            print(
                f"{scenario} r{repetition} : {r.statut} ; outils {outils} ; "
                f"outil attendu {'oui' if ligne['outil_attendu_appele'] else 'NON'} ; "
                f"valeurs {'ok' if ligne['valeurs_conformes'] else ecarts} ; "
                f"{r.duree_ms / 1000:.1f} s ; {r.cout_micro_eur / 1e6:.4f} €"
            )

    synthese = {
        "date": args.date,
        "paquet": paquet.prompt_version,
        "modele": paquet.model_id,
        "extractions": len(lignes),
        "outil_attendu_appele": sum(x["outil_attendu_appele"] for x in lignes),
        "valeurs_conformes": sum(x["valeurs_conformes"] for x in lignes),
        "cout_total_eur": round(cout_total / 1e6, 4),
        "lignes": lignes,
    }
    (DOSSIER / args.resultat).write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"\nOutil attendu appelé : {synthese['outil_attendu_appele']}/{len(lignes)} ; "
        f"valeurs conformes : {synthese['valeurs_conformes']}/{len(lignes)} ; "
        f"coût {synthese['cout_total_eur']} €"
    )


if __name__ == "__main__":
    main()
