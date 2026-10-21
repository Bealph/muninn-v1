"""Harnais d'évaluation de l'agent (V-08) : une campagne, un rapport horodaté, un verdict.

Usage : `uv run python -m muninn.evaluation.harnais [--sortie DOSSIER]`. Modèle par la
configuration (`LLM_FOURNISSEUR=azure`, `AZURE_AI_ENDPOINT`, identité Entra ID) ; référentiels par
`REFERENTIELS_URL` (API de production par défaut, en lecture seule).

Campagne (jeu `eval/v08/jeu.json`, figé avant la première exécution) :
- 20 scénarios de test, agent outillé, puis base sans outils sur les mêmes scénarios ;
- 5 cas de conformité à tolérance nulle, 3 exécutions chacun ;
- 3 cas de qualification (SC-Q3, SC-Q4, SC-Q7), 3 exécutions chacun ;
- cas critiques de l'agent : SC-01, SC-03, SC-04, SC-05, SC-07, SC-10 (annexe A) ; T11
  (« Montreuil-sous-Bois ») est mesuré et rapporté, non bloquant (D-77).

Verdict : `reussite` (code 0) ; `echec` (code 1) si un cas bloquant échoue, si la borne d'appels
d'outils est atteinte sur un scénario de test, ou si l'exactitude globale est sous 90 % (VE-11) ;
`non_mesure` (code 2) sans accès au modèle ou au-delà du plafond de D-64 (1 € par campagne).
Les deux derniers bloquent `verdict` en CI. Vingt scénarios ne prouvent pas un taux : les
intervalles de Wilson le disent (phase 1, document 04, § 4.4).
"""

import argparse
import dataclasses
import json
import logging
import os
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from muninn import observabilite
from muninn.core.config import Settings
from muninn.demo import charger_scenarios
from muninn.demo.verification import verifier_annexe_a, verifier_qualification
from muninn.evaluation.mesures import (
    CHAMPS,
    comparer,
    controler_conformite,
    percentile,
    valeurs,
    wilson,
)
from muninn.extraction.evaluateur import ContenuRefuse, Extraction, extraire_dossier
from muninn.extraction.outils import ClientReferentiels, Referentiels
from muninn.extraction.paquet import Paquet, calculer_empreinte, charger_paquet
from muninn.llm.fournisseur import FournisseurLLM, construire_fournisseur
from muninn.qualification.qualificateur import charger_paquet_qualification, traiter_appel

RACINE = Path(__file__).resolve().parents[3]
JEU = RACINE / "eval" / "v08" / "jeu.json"
DATASET = "muninn-v08-test"
QUALIFICATION = RACINE / "eval" / "qualification" / "scenarios.json"
DATE_REFERENCE = "2026-10-20"  # fixe : une campagne ne dépend pas du jour où elle tourne
PLAFOND_MICRO_EUR = 1_000_000  # D-64
SEUIL_GLOBAL = 0.90  # VE-11, estimation ponctuelle
CAS_CRITIQUES = ("SC-01", "SC-03", "SC-04", "SC-05", "SC-07", "SC-10")
CAS_QUALIFICATION = ("SC-Q3", "SC-Q4", "SC-Q7")
REPETITIONS = 3
API_PRODUCTION = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"


journal = logging.getLogger(__name__)


class PlafondAtteint(Exception):
    pass


@dataclasses.dataclass
class Campagne:
    fournisseur: FournisseurLLM
    referentiels: Referentiels
    paquet: Paquet
    cout_micro_eur: int = 0

    def extraire(
        self, s: dict[str, Any], paquet: Paquet | None = None
    ) -> tuple[Extraction | None, int]:
        """Une extraction ; rend le brouillon (None si refusé) et la durée en millisecondes."""
        if self.cout_micro_eur >= PLAFOND_MICRO_EUR:
            raise PlafondAtteint
        debut = time.perf_counter()
        try:
            x: Extraction | None = extraire_dossier(
                s["transcription"], paquet or self.paquet, self.fournisseur, self.referentiels,
                s["metier"], DATE_REFERENCE, s["numero_presente"],
            )  # fmt: skip
        except ContenuRefuse:
            x = None
        if x is not None and x.agent is not None:
            self.cout_micro_eur += x.agent.cout_micro_eur
        return x, round((time.perf_counter() - debut) * 1000)


def executer_experience(
    c: Campagne, test: list[dict[str, Any]], jeu_version: str, horodatage: str
) -> dict[str, tuple[Extraction | None, int]]:
    """Le passage de l'agent comme expérience Langfuse (V-13) : dataset `muninn-v08-test`, un
    score par champ. Une exécution à la fois (limite de débit). Rend ce qui a été exécuté ;
    l'appelant exécute lui-même ce qui manque, si Langfuse échoue en route."""
    lf = observabilite.client()
    resultats: dict[str, tuple[Extraction | None, int]] = {}
    if lf is None:
        return resultats
    from langfuse import Evaluation

    par_id = {s["id"]: s for s in test}
    try:
        try:
            lf.create_dataset(
                name=DATASET, description="Jeu de test V-08", metadata={"jeu": jeu_version}
            )
        except Exception:  # noqa: BLE001 (dataset déjà créé : ses items sont mis à jour)
            journal.info("langfuse.dataset_existant nom=%s", DATASET)
        for s in test:
            lf.create_dataset_item(
                dataset_name=DATASET, id=f"{DATASET}-{s['id']}",
                input={"transcription": s["transcription"], "metier": s["metier"],
                       "numero_presente": s["numero_presente"]},
                expected_output=s["verite"],
                metadata={"scenario": s["id"], "categorie": s["categorie"]},
            )  # fmt: skip

        def tache(*, item: Any, **kwargs: Any) -> dict[str, Any]:
            sid = item.metadata["scenario"]
            x, duree = c.extraire(par_id[sid])
            resultats[sid] = (x, duree)
            exact = comparer(par_id[sid]["verite"], x.brouillon) if x else None
            return {"scenario": sid, "exact": exact, "valeurs": valeurs(x.brouillon) if x else None}

        def evaluateur(champ: str) -> Any:
            def evaluer(*, output: dict[str, Any], **kwargs: Any) -> Any:
                exact = bool(output.get("exact") and output["exact"][champ]["exact"])
                return Evaluation(name=f"exact_{champ}", value=1.0 if exact else 0.0)

            return evaluer

        items = [i for i in lf.get_dataset(DATASET).items if i.metadata.get("scenario") in par_id]
        lf.run_experiment(
            name="V-08 agent", run_name=f"{jeu_version} {horodatage}", data=items, task=tache,
            evaluators=[evaluateur(ch) for ch in CHAMPS], max_concurrency=1,
        )  # fmt: skip
    except PlafondAtteint:
        raise
    except Exception as erreur:  # noqa: BLE001 (Langfuse ne fait jamais échouer une campagne)
        journal.warning("langfuse.experience_echec type=%s", type(erreur).__name__)
    observabilite.envoyer()
    return resultats


def mesurer_test(
    c: Campagne,
    test: list[dict[str, Any]],
    paquet: Paquet | None,
    deja: dict[str, tuple[Extraction | None, int]] | None = None,
) -> dict[str, Any]:
    """Exactitude par champ, invention, trajectoire, latence et part « à vérifier »."""
    lignes, durees = [], []
    for s in test:
        x, duree = (deja or {}).get(s["id"]) or c.extraire(s, paquet)
        durees.append(duree)
        champs = comparer(s["verite"], x.brouillon) if x else {
            ch: {"exact": False, "invente": False, "absent_attendu": False} for ch in CHAMPS
        }  # fmt: skip
        agent = x.agent if x else None
        lignes.append({
            "id": s["id"], "categorie": s["categorie"], "refus": x is None, "champs": champs,
            "valeurs": valeurs(x.brouillon) if x else None,  # données synthétiques (R9)
            "outils": [a.nom for a in agent.appels_outils] if agent else [],
            "borne_atteinte": bool(agent and agent.borne_atteinte),
            "a_verifier": bool(x and x.enveloppe.a_verifier),
            "statut": x.brouillon.provenance.extraction_status if x else "refus",
            "duree_ms": duree,
        })  # fmt: skip
    par_champ = {}
    for ch in CHAMPS:
        exacts = sum(ligne["champs"][ch]["exact"] for ligne in lignes)
        par_champ[ch] = {
            "exacts": exacts,
            "total": len(lignes),
            "ic95": wilson(exacts, len(lignes)),
        }
    exacts = sum(v["exacts"] for v in par_champ.values())
    total = sum(v["total"] for v in par_champ.values())
    absents = [ligne["champs"][ch] for ligne in lignes for ch in CHAMPS
               if ligne["champs"][ch]["absent_attendu"]]  # fmt: skip
    inventes = sum(a["invente"] for a in absents)
    attendus_outil = [ligne for ligne in lignes if ligne["id"] in ("T09", "T11")]
    return {
        "lignes": lignes,
        "par_champ": par_champ,
        "global": {
            "exacts": exacts,
            "total": total,
            "taux": round(exacts / total, 3),
            "ic95": wilson(exacts, total),
        },  # fmt: skip
        "invention": {
            "inventes": inventes,
            "absents_attendus": len(absents),
            "ic95": wilson(inventes, len(absents)),
        },  # fmt: skip
        "trajectoire": {
            "appels_par_scenario": round(
                sum(len(ligne["outils"]) for ligne in lignes) / len(lignes), 2
            ),
            "borne_atteinte": sum(ligne["borne_atteinte"] for ligne in lignes),
            "outil_attendu_appele": sum(
                "chercher_communes" in ligne["outils"] for ligne in attendus_outil
            ),
            "outil_attendu_total": len(attendus_outil),
        },
        "t11_indice_resolu": next(
            (
                all(ligne["champs"][ch]["exact"] for ch in ("commune", "code_postal"))
                for ligne in lignes
                if ligne["id"] == "T11"
            ),
            None,
        ),  # D-77 : mesuré, non bloquant
        "latence_ms": {"p50": percentile(durees, 0.5), "p95": percentile(durees, 0.95)},
        "part_a_verifier": round(sum(ligne["a_verifier"] for ligne in lignes) / len(lignes), 3),
        "refus": sum(ligne["refus"] for ligne in lignes),
    }


def mesurer_bloquants(c: Campagne, jeu: dict[str, Any]) -> dict[str, Any]:
    conformite = []
    for s in [s for s in jeu["scenarios"] if s["partition"] == "conformite"]:
        for r in range(1, REPETITIONS + 1):
            x, _ = c.extraire(s)
            conformite.append({
                "id": s["id"], "execution": r, "ecarts": controler_conformite(s, x),
                "valeurs": valeurs(x.brouillon) if x else None,
                "statut": x.brouillon.provenance.extraction_status if x else "refus",
            })  # fmt: skip
    critiques = []
    scenarios = charger_scenarios()
    for sid in CAS_CRITIQUES:
        sc = scenarios[sid]
        x, _ = c.extraire({"transcription": sc.transcription, "metier": sc.metier,
                           "numero_presente": sc.numero_presente})  # fmt: skip
        critiques.append({
            "id": sid, "ecarts": verifier_annexe_a(sid, x) if x else ["refus"],
            "valeurs": valeurs(x.brouillon) if x else None,
            "statut": x.brouillon.provenance.extraction_status if x else "refus",
        })  # fmt: skip
    qualification = []
    dialogues = {
        s["id"]: s for s in json.loads(QUALIFICATION.read_text(encoding="utf-8"))["scenarios"]
    }
    for sid in CAS_QUALIFICATION:
        s = dialogues[sid]
        for r in range(1, REPETITIONS + 1):
            if c.cout_micro_eur >= PLAFOND_MICRO_EUR:
                raise PlafondAtteint
            try:
                t = traiter_appel(
                    s["transcription"], charger_paquet_qualification(), c.paquet, c.fournisseur,
                    c.referentiels, "plomberie", DATE_REFERENCE, s["numero_presente"],
                )  # fmt: skip
                q = t.qualification
                c.cout_micro_eur += (q.cout_micro_eur if q else 0) + (
                    t.extraction.agent.cout_micro_eur if t.extraction and t.extraction.agent else 0
                )
                ecarts = verifier_qualification(s["attendu"], t)
            except ContenuRefuse:
                ecarts = ["refus"]
            qualification.append({"id": sid, "execution": r, "ecarts": ecarts})
    return {"conformite": conformite, "critiques": critiques, "qualification": qualification}


def secours(rapport: dict[str, Any]) -> int:
    """Exécutions rendues en brouillon de secours : le modèle n'a pas répondu (D-29)."""
    lignes = [*rapport["test"]["lignes"], *rapport["base_sans_outils"]["lignes"],
              *rapport["bloquants"]["conformite"], *rapport["bloquants"]["critiques"]]  # fmt: skip
    return sum(ligne.get("statut") == "fallback_no_llm" for ligne in lignes)


def verdict(test: dict[str, Any], bloquants: dict[str, Any]) -> tuple[str, list[str]]:
    raisons = []
    for famille in ("conformite", "critiques", "qualification"):
        for cas in bloquants[famille]:
            if cas["ecarts"]:
                raisons.append(f"{famille} {cas['id']} : {', '.join(cas['ecarts'])}")
    if test["trajectoire"]["borne_atteinte"]:
        raisons.append(f"borne d'appels atteinte : {test['trajectoire']['borne_atteinte']}")
    if test["global"]["taux"] < SEUIL_GLOBAL:
        raisons.append(f"exactitude globale {test['global']['taux']} sous {SEUIL_GLOBAL} (VE-11)")
    return ("echec" if raisons else "reussite"), raisons


def ecrire_rapport(rapport: dict[str, Any], dossier: Path) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{rapport['horodatage'].replace(':', '')[:15]}.json"
    chemin.write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return chemin


def resumer(rapport: dict[str, Any]) -> str:
    lignes = [f"Verdict : {rapport['verdict']}"]
    if "test" in rapport:
        for libelle, cle in (("agent", "test"), ("sans outils", "base_sans_outils")):
            g = rapport[cle]["global"]
            lignes.append(
                f"Exactitude globale ({libelle}) : {g['exacts']}/{g['total']} = {g['taux']} ; "
                f"IC 95 % {g['ic95']}"
            )
    lignes += [f"- {r}" for r in rapport.get("raisons", [])]
    lignes.append(f"Coût : {rapport['cout_eur']} €")
    return "\n".join(lignes)


def executer(
    fournisseur_de: Callable[[], FournisseurLLM], referentiels: Referentiels, sortie: Path
) -> tuple[dict[str, Any], int]:
    observabilite.autoriser_contenu_synthetique()  # le jeu est synthétique (R9)
    jeu = json.loads(JEU.read_text(encoding="utf-8"))
    test = [s for s in jeu["scenarios"] if s["partition"] == "test"]
    paquet = charger_paquet()
    rapport: dict[str, Any] = {
        "horodatage": datetime.now(UTC).isoformat(timespec="seconds"),
        "jeu": jeu["version"],
        "paquet": paquet.prompt_version,
        "empreinte": calculer_empreinte(RACINE),
        "date_reference": DATE_REFERENCE,
    }
    c: Campagne | None = None
    try:
        c = Campagne(fournisseur_de(), referentiels, paquet)
        deja = executer_experience(c, test, jeu["version"], rapport["horodatage"])
        rapport["langfuse_experience"] = len(deja)
        rapport["test"] = mesurer_test(c, test, None, deja)
        rapport["base_sans_outils"] = mesurer_test(c, test, dataclasses.replace(paquet, outils=[]))
        rapport["bloquants"] = mesurer_bloquants(c, jeu)
        rapport["verdict"], rapport["raisons"] = verdict(rapport["test"], rapport["bloquants"])
        if n := secours(rapport):
            # Un brouillon de secours mesure la disponibilité du modèle, pas l'agent.
            rapport["verdict"] = "non_mesure"
            rapport["raisons"].insert(
                0, f"modèle indisponible pendant la campagne : {n} exécution(s)"
            )
    except PlafondAtteint:
        rapport["verdict"], rapport["raisons"] = "non_mesure", ["plafond de D-64 atteint (1 €)"]
    except Exception as erreur:  # noqa: BLE001 (sans accès au modèle : « non mesuré », bloquant)
        rapport["verdict"] = "non_mesure"
        rapport["raisons"] = [
            f"accès au modèle ou aux référentiels impossible : {type(erreur).__name__}"
        ]
    rapport["cout_eur"] = round((c.cout_micro_eur if c else 0) / 1e6, 4)
    ecrire_rapport(rapport, sortie)
    return rapport, {"reussite": 0, "echec": 1}.get(rapport["verdict"], 2)


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    arguments.add_argument("--sortie", type=Path, default=RACINE / "eval" / "v08" / "rapports")
    sortie = arguments.parse_args().sortie
    referentiels = ClientReferentiels(
        os.environ.get("REFERENTIELS_URL", API_PRODUCTION), delai_s=15
    )
    rapport, code = executer(lambda: construire_fournisseur(Settings()), referentiels, sortie)
    print(resumer(rapport))
    sys.exit(code)


if __name__ == "__main__":
    main()
