"""Benchmark C7 : mesure d'Azure AI Speech, le service en place (protocole, section 5).

Usage : `uv run python eval/c7/mesurer_voix.py [--api URL] [--passages N] [--plafond EUR]`.

Protocole : `docs/v1/benchmark-services-ia/protocole.md`, versionné avant la mesure. Pour chaque
passage, chacun des 16 scénarios qui ont un dialogue est synthétisé (`/v1/demo/voice/synthesis`,
gardé en mémoire par l'API après la première demande), puis l'enregistrement est envoyé à
`/v1/demo/voice/call`, qui le transcrit (transcription rapide, deux locuteurs) avant l'extraction.
Mesures par appel : rappel et précision des mots (`voix.fidelite`), groupes de chiffres rendus à
l'identique et chiffres en trop, part des mots alignés attribués au bon locuteur, délai de la
transcription. Le programme s'arrête avant de dépasser le plafond de coût.

Preuve : `docs/v1/benchmark-services-ia/mesures/azure-speech-<date>.json` ; ni audio, ni texte
entendu, sauf les mots en trop et les groupes de chiffres en écart, tous issus du jeu
synthétique (noms et numéros fictifs, R9).
"""

import argparse
import hashlib
import importlib.util
import json
import re
import statistics
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx

from muninn.demo import PERIMETRE, charger_scenarios
from muninn.voix.contrat import TYPE_AUDIO, Tour, decouper
from muninn.voix.fidelite import alignement, fidelite, mots

RACINE = Path(__file__).resolve().parents[2]
MESURES = RACINE / "docs/v1/benchmark-services-ia/mesures"
PASSAGES = 3
PLAFOND_EUR = 2.0
ESPACEMENT_S = 10.0  # protocole : un appel toutes les 10 s au moins, jamais en parallèle
# Prix publics, West Europe, API officielle des prix, lus le 3 novembre 2026 (protocole, section 6).
EUR_PAR_CARACTERE = 13.4656 / 1e6  # synthèse neuronale standard
# Transcription rapide, plus la séparation des locuteurs comptée par prudence (non vérifiée).
EUR_PAR_HEURE_TRANSCRIPTION = 0.3232 + 0.2693
# Modèle A, mesure du 29 octobre ; remplacé par le coût rendu par les étapes s'il existe.
EUR_PAR_EXTRACTION = 0.0045
SEUIL_RAPPEL, SEUIL_PRECISION, SEUIL_TRANSCRIPTION_MS = 0.90, 0.95, 30_000
_CHIFFRES = re.compile(r"\d+")


def _charger(nom: str, chemin: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nom, chemin)
    if spec is None or spec.loader is None:
        raise ImportError(chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Cadence, assemblage des extraits, codes d'erreur : ceux, déjà testés, de la vérification de CA-8.
ca8 = _charger("verifier_ca8", RACINE / "eval/production/verifier_ca8.py")


def groupes_chiffres(tours: list[Tour]) -> list[str]:
    """Les nombres d'un dialogue, ceux qui se suivent regroupés (« 06 99 00 00 01 » → un groupe)."""
    groupes: list[str] = []
    for tour in tours:
        precedent_chiffre = False
        for mot in mots(tour.texte):
            if _CHIFFRES.fullmatch(mot):
                if precedent_chiffre:
                    groupes[-1] += mot
                else:
                    groupes.append(mot)
                precedent_chiffre = True
            else:
                precedent_chiffre = False
    return groupes


def chiffres(entendus: list[Tour], dits: list[Tour]) -> dict[str, Any]:
    """Groupes de chiffres dits rendus à l'identique (T3), et groupes entendus en trop."""
    dit, entendu = Counter(groupes_chiffres(dits)), Counter(groupes_chiffres(entendus))
    exacts = sum((dit & entendu).values())
    return {
        "groupes_dits": sum(dit.values()),
        "groupes_exacts": exacts,
        "groupes_manquants": sorted((dit - entendu).elements()),
        "groupes_en_trop": sorted((entendu - dit).elements()),
    }


def locuteurs(entendus: list[Tour], dits: list[Tour]) -> float:
    """Part des mots alignés (dits et entendus) attribués au même locuteur (T2)."""
    dit = [(m, t.locuteur) for t in dits for m in mots(t.texte)]
    entendu = [(m, t.locuteur) for t in entendus for m in mots(t.texte)]
    paires = SequenceMatcher(None, [m for m, _ in dit], [m for m, _ in entendu], autojunk=False)
    alignes = justes = 0
    for bloc in paires.get_matching_blocks():
        for k in range(bloc.size):
            alignes += 1
            justes += dit[bloc.a + k][1] == entendu[bloc.b + k][1]
    return justes / alignes if alignes else 0.0


def mesurer(dits: list[Tour], reponse: dict[str, Any]) -> dict[str, Any]:
    """Les mesures d'un appel dont la transcription a été rendue ; nombres et écarts seulement."""
    transcription = reponse.get("transcription") or {}
    entendus = [Tour(t["speaker"], t["text"]) for t in transcription.get("turns") or []]
    rappel, precision, en_trop = fidelite(entendus, dits)
    _, _, restes = alignement(entendus, dits)
    etapes = reponse.get("steps") or []
    cout_modele = sum(
        float(e.get("details", {}).get("cout_micro_eur", 0)) for e in etapes if e["nom"] != "appel"
    )
    return {
        "transcription_ms": transcription.get("transcription_ms"),
        "audio_octets": transcription.get("audio_bytes"),
        "tours_dits": len(dits),
        "tours_entendus": len(entendus),
        "rappel": round(rappel, 4),
        "precision": round(precision, 4),
        "mots_en_trop": en_trop,
        "mots_en_trop_liste": restes,
        "locuteurs_justes": round(locuteurs(entendus, dits), 4),
        "chiffres": chiffres(entendus, dits),
        "fidele_selon_api": bool(transcription.get("matches_scenario")),
        "issue": reponse.get("issue"),
        "cout_modele_micro_eur": round(cout_modele),
        # Empreinte du texte entendu, pour la stabilité entre passages sans garder le texte.
        "empreinte_entendu": hash_texte(entendus),
    }


def hash_texte(tours: list[Tour]) -> str:
    texte = "\n".join(f"{t.locuteur}:{' '.join(mots(t.texte))}" for t in tours)
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()[:16]


def cout_appel(ligne: dict[str, Any], premiere_synthese: bool) -> float:
    """Coût estimé d'un appel : synthèse (la première fois seulement), transcription, modèle."""
    synthese = int(ligne.get("caracteres", 0)) * EUR_PAR_CARACTERE if premiere_synthese else 0.0
    secondes = float(ligne.get("audio_s", 0.0))
    modele = int(ligne.get("cout_modele_micro_eur", 0)) / 1e6 or EUR_PAR_EXTRACTION
    return synthese + secondes / 3600 * EUR_PAR_HEURE_TRANSCRIPTION + modele


def synthese_globale(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    """Les résultats agrégés, lus contre les seuils du protocole."""
    ok = [lg for lg in lignes if "rappel" in lg]
    if not ok:
        return {"appels_mesures": 0}
    delais = [lg["transcription_ms"] for lg in ok if lg.get("transcription_ms") is not None]
    dits = sum(lg["chiffres"]["groupes_dits"] for lg in ok)
    exacts = sum(lg["chiffres"]["groupes_exacts"] for lg in ok)
    par_scenario: dict[str, set[str]] = {}
    for lg in ok:
        par_scenario.setdefault(lg["scenario_id"], set()).add(lg["empreinte_entendu"])
    return {
        "appels_mesures": len(ok),
        "appels_en_erreur": len(lignes) - len(ok),
        "rappel_median": statistics.median(lg["rappel"] for lg in ok),
        "rappel_min": min(lg["rappel"] for lg in ok),
        "precision_mediane": statistics.median(lg["precision"] for lg in ok),
        "precision_min": min(lg["precision"] for lg in ok),
        "appels_sous_seuils_mots": sum(
            lg["rappel"] < SEUIL_RAPPEL or lg["precision"] < SEUIL_PRECISION for lg in ok
        ),
        "locuteurs_justes_median": statistics.median(lg["locuteurs_justes"] for lg in ok),
        "locuteurs_justes_min": min(lg["locuteurs_justes"] for lg in ok),
        "groupes_chiffres_dits": dits,
        "groupes_chiffres_exacts": exacts,
        "groupes_chiffres_en_trop": sum(len(lg["chiffres"]["groupes_en_trop"]) for lg in ok),
        "transcription_ms_median": statistics.median(delais) if delais else None,
        "transcription_ms_max": max(delais) if delais else None,
        "appels_au_dela_30_s": sum(d > SEUIL_TRANSCRIPTION_MS for d in delais),
        "scenarios_stables": sum(len(e) == 1 for e in par_scenario.values()),
        "scenarios": len(par_scenario),
        "fideles_selon_api": sum(lg["fidele_selon_api"] for lg in ok),
    }


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--api", default=ca8.API)
    options.add_argument("--passages", type=int, default=PASSAGES)
    options.add_argument("--plafond", type=float, default=PLAFOND_EUR)
    args = options.parse_args()
    if not 1 <= args.passages <= 3 or not 0 < args.plafond <= PLAFOND_EUR:
        print("--passages entre 1 et 3, --plafond entre 0 et 2 €", file=sys.stderr)
        return 2
    # Le modèle simulé n'a pas de dialogue : l'API le refuse (`scenario_parle`).
    scenarios = {k: v for k, v in charger_scenarios().items() if k != PERIMETRE}
    client = httpx.Client(base_url=args.api, timeout=120)
    version = client.get("/version").json()
    print(
        f"API {version.get('environment')} {str(version.get('git_sha'))[:7]} ; "
        f"{len(scenarios)} scénarios x {args.passages} passages ; plafond {args.plafond} €"
    )
    cadence = ca8.Cadence(espacement=ESPACEMENT_S)
    lignes: list[dict[str, Any]] = []
    deja_synthetises: set[str] = set()
    cout = 0.0
    arret = ""
    for passage in range(1, args.passages + 1):
        for sid, scenario in scenarios.items():
            dits = decouper(scenario.transcription)
            ligne: dict[str, Any] = {"passage": passage, "scenario_id": sid}
            caracteres = sum(len(t.texte) for t in dits)
            prevu = (0 if sid in deja_synthetises else caracteres * EUR_PAR_CARACTERE) + (
                caracteres / 15 / 3600 * EUR_PAR_HEURE_TRANSCRIPTION + EUR_PAR_EXTRACTION
            )
            if cout + prevu > args.plafond:
                arret = f"plafond atteint avant {sid}, passage {passage}"
                break
            cadence.attendre()
            debut = time.perf_counter()
            r = client.post("/v1/demo/voice/synthesis", json={"scenario_id": sid})
            synthese_ms = round((time.perf_counter() - debut) * 1000)
            if r.status_code != 200:
                lignes.append(ligne | {"erreur": f"synthèse {ca8.code_erreur(r)}"})
                continue
            audio = ca8.assembler(r.json()["turns"])
            premiere = sid not in deja_synthetises
            deja_synthetises.add(sid)
            ligne |= {
                "caracteres": caracteres,
                "audio_s": round(len(audio) / ca8.OCTETS_PAR_SECONDE, 1),
                # Seule la première demande synthétise ; les suivantes lisent la mémoire de l'API.
                "synthese_ms": synthese_ms if premiere else None,
            }
            cadence.attendre()
            debut = time.perf_counter()
            r = client.post("/v1/demo/voice/call", params={"scenario_id": sid}, content=audio,
                            headers={"Content-Type": TYPE_AUDIO})  # fmt: skip
            ligne["appel_ms"] = round((time.perf_counter() - debut) * 1000)
            if r.status_code != 200:
                ligne["erreur"] = f"appel {ca8.code_erreur(r)}"
            else:
                ligne |= mesurer(dits, r.json())
            cout += cout_appel(ligne, premiere)
            lignes.append(ligne)
            erreur = f"  {ligne['erreur']}" if "erreur" in ligne else ""
            print(
                f"{passage} {sid} : rappel {ligne.get('rappel')}, précision "
                f"{ligne.get('precision')}, {ligne.get('transcription_ms')} ms, "
                f"cumul {cout:.3f} €{erreur}"
            )
        if arret:
            break
    MESURES.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC)
    sortie = MESURES / f"azure-speech-{date:%Y-%m-%d-%H%M}.json"
    contenu = {
        "date": date.isoformat(timespec="seconds"),
        "api": args.api,
        "environnement": version.get("environment"),
        "git_sha": version.get("git_sha"),
        "protocole": "docs/v1/benchmark-services-ia/protocole.md, section 5",
        "passages": args.passages,
        "espacement_s": ESPACEMENT_S,
        "seuils": {
            "rappel": SEUIL_RAPPEL,
            "precision": SEUIL_PRECISION,
            "transcription_ms": SEUIL_TRANSCRIPTION_MS,
        },  # fmt: skip
        "arret": arret or None,
        "cout_estime_eur": round(cout, 4),
        "resultats": synthese_globale(lignes),
        "lignes": lignes,
    }
    sortie.write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"écrit : {sortie.relative_to(RACINE)} ; coût estimé {cout:.3f} €")
    return 0 if not arret and all("erreur" not in lg for lg in lignes) else 1


if __name__ == "__main__":
    sys.exit(main())
