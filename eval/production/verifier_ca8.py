"""Vérification de CA-8 sur Azure : la voix simulée (sprint 5, étape 6 ; D-50, D-74, D-88, V-12).

Usage : `uv run python eval/production/verifier_ca8.py [--api URL] [--passages N]`.

Protocole, fixé avant toute mesure. Chaque parcours suit celui de l'écran « Démonstration »
(`docs/v1/sprints/sprint-5/contrat-voix.md`) sur l'API (production par défaut) :
1. `POST /v1/demo/voice/synthesis` : un extrait MP3 par tour ;
2. les extraits mis bout à bout forment l'enregistrement de l'appel joué (comme la console) ;
3. `POST /v1/demo/voice/call?scenario_id=…`, corps brut `audio/mpeg`. La durée de cette requête,
   mesurée côté client (envoi de l'enregistrement → réponse lue), est celle de CA-8 : de la fin de
   l'appel joué à la réponse, 45 s au plus (avenant D-74). La sonnerie et la lecture des extraits
   ne sont pas rejouées : elles précèdent la mesure et n'en changent rien.

Un parcours est conforme si, à la fois : les deux requêtes rendent 200 ; la durée est de 45 s au
plus ; l'issue est celle de l'attendu du scénario (`dossier`, ou `message` pour SC-Q1) ;
`conformity.compliant` est vrai ; la première étape après la racine `appel` est `transcription` ;
la transcription est fidèle au dialogue synthétisé : même suite de locuteurs (CA-8 : « la
transcription distingue l'agent et l'appelant »), et 85 % au moins des mots dits retrouvés (mots
sans accents ni ponctuation, nombres regroupés, comptés avec leurs répétitions).

Scénarios : SC-01, le scénario de CA-8, joué `--passages` fois (3 par défaut : « 3 sur 3 » dit
que le résultat se répète, pas qu'il a réussi une fois) ; puis une fois chacun des quatre
scénarios de la démonstration (SC-Q4, SC-04, SC-Q1, SC-10), pour couvrir le plus long dialogue
(17 tours), un message, une urgence de sécurité et une commune ambiguë.

Un appel toutes les 7 s au plus (limite de l'API : 10 par minute, synthèse et appel compris).
Coût affiché avant et après : synthèse 13,20 € par million de caractères, transcription rapide
0,32 € par heure (API officielle des prix de Microsoft, 26 octobre 2026, West Europe), plus le
modèle de langage (coût rendu par les étapes). Pour les sept parcours : environ 0,07 € de voix
(3 472 caractères, débit de parole supposé de 15 caractères par seconde), plus environ 0,035 €
de modèle (0,005 € par appel, mesuré par `rafale.py`), soit environ 0,10 €.
Preuve : `docs/v1/sprints/sprint-5/preuves/etape-6-ca8.json` : identifiants, durées, verdicts ;
ni audio, ni texte entendu ou dit. Ce script ne vérifie pas l'absence d'audio côté serveur
(TC-10) : c'est le rôle des tests de l'API.
"""

import argparse
import base64
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from muninn.demo import charger_scenarios
from muninn.voix.contrat import TYPE_AUDIO, decouper

API = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
PREUVE = Path(__file__).resolve().parents[2] / "docs/v1/sprints/sprint-5/preuves/etape-6-ca8.json"
SCENARIO_CA8 = "SC-01"
PASSAGES = 3
DEMONSTRATION = ["SC-Q4", "SC-04", "SC-Q1", "SC-10"]
SEUIL_MS = 45_000  # CA-8, avenant D-74
SEUIL_MOTS = 0.85
ESPACEMENT_S = 7.0
EUR_PAR_CARACTERE = 13.20 / 1e6  # synthèse neuronale
EUR_PAR_SECONDE_AUDIO = 0.32 / 3600  # transcription rapide
OCTETS_PAR_SECONDE = 48_000 / 8  # audio-24khz-48kbitrate-mono-mp3 (FORMAT_SYNTHESE)
CARACTERES_PAR_SECONDE = 15  # débit de parole supposé, pour l'estimation avant les appels
CODE = re.compile(r"[A-Za-z0-9_.\-]{1,80}")


def mots(texte: str) -> list[str]:
    """Les mots d'un texte, sans accents ni ponctuation, en minuscules ; les nombres qui se
    suivent sont regroupés (« 06 99 00 00 01 » et « 0699000001 » donnent le même mot)."""
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c)
    )
    resultat: list[str] = []
    for mot in re.findall(r"[a-z0-9]+", sans_accents.lower()):
        if mot.isdigit() and resultat and resultat[-1].isdigit():
            resultat[-1] += mot
        else:
            resultat.append(mot)
    return resultat


def taux_mots(dits: list[str], entendus: list[str]) -> float:
    """Part des mots dits retrouvés dans ce qui a été entendu, répétitions comprises."""
    reference = Counter(m for t in dits for m in mots(t))
    if not reference:
        return 0.0
    entendu = Counter(m for t in entendus for m in mots(t))
    return sum((reference & entendu).values()) / sum(reference.values())


def assembler(tours: list[dict[str, Any]]) -> bytes:
    """L'enregistrement de l'appel joué : les extraits MP3 mis bout à bout, comme la console."""
    return b"".join(base64.b64decode(t["audio_base64"], validate=True) for t in tours)


def etape_en_tete(etapes: list[dict[str, Any]]) -> str | None:
    """Nom de la première étape après la racine `appel` (attendu : `transcription`)."""
    return next((e["nom"] for e in etapes if e["nom"] != "appel"), None)


def code_erreur(r: httpx.Response) -> str:
    """`HTTP 503 voice_unavailable` : statut et code d'erreur du contrat, jamais le message."""
    try:
        code = str(r.json().get("code", ""))
    except (ValueError, AttributeError):
        code = ""
    return f"HTTP {r.status_code}" + (f" {code}" if CODE.fullmatch(code) else "")


class Cadence:
    """Un appel toutes les `espacement` secondes au plus (limite de débit de l'API)."""

    def __init__(
        self,
        espacement: float = ESPACEMENT_S,
        horloge: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self.espacement, self.horloge, self.dormir = espacement, horloge, dormir
        self.dernier: float | None = None

    def attendre(self) -> None:
        if self.dernier is not None:
            reste = self.dernier + self.espacement - self.horloge()
            if reste > 0:
                self.dormir(reste)
        self.dernier = self.horloge()


def controler(
    issue_attendue: str,
    synthese: dict[str, Any],
    reponse: dict[str, Any],
    duree_ms: int,
) -> dict[str, object]:
    """Verdict d'un parcours dont les deux requêtes ont rendu 200 ; nombres et codes seulement."""
    ecarts: list[str] = []
    dits = synthese["turns"]
    entendus = (reponse.get("transcription") or {}).get("turns") or []
    etapes = reponse.get("steps") or []
    if duree_ms > SEUIL_MS:
        ecarts.append(f"durée {duree_ms} ms au-delà de {SEUIL_MS}")
    if reponse.get("issue") != issue_attendue:
        ecarts.append(f"issue {reponse.get('issue')} au lieu de {issue_attendue}")
    conformite = reponse.get("conformity") or {}
    if not conformite.get("compliant"):
        ecarts.append("non conforme à l'attendu du scénario")
    en_tete = etape_en_tete(etapes)
    if en_tete != "transcription":
        ecarts.append(f"première étape {en_tete} au lieu de transcription")
    locuteurs = [t["speaker"] for t in dits] == [t["speaker"] for t in entendus]
    if not locuteurs:
        ecarts.append("locuteurs entendus différents des locuteurs dits")
    taux = taux_mots([t["text"] for t in dits], [t["text"] for t in entendus])
    if taux < SEUIL_MOTS:
        ecarts.append(f"mots retrouvés {taux:.2f} sous {SEUIL_MOTS}")
    # Jugement de l'API elle-même (`voix.fidelite`) : s'il refuse un appel joué tel quel, ses
    # seuils sont trop stricts pour la vraie transcription, et la correction du dossier se perd.
    fidele = bool((reponse.get("transcription") or {}).get("matches_scenario"))
    if not fidele:
        ecarts.append("transcription jugée non fidèle au scénario par l'API")
    transcription: dict[str, Any] = next((e for e in etapes if e["nom"] == "transcription"), {})
    cout_modele = sum(
        float(e.get("details", {}).get("cout_micro_eur", 0)) for e in etapes if e["nom"] != "appel"
    )
    return {
        "request_id": reponse.get("request_id"),
        "duree_appel_ms": duree_ms,
        "latence_serveur_ms": reponse.get("latency_ms"),
        "transcription_ms": transcription.get("duree_ms"),
        "etape_en_tete": en_tete,
        "issue": reponse.get("issue"),
        "issue_attendue": issue_attendue,
        "conforme_attendu": bool(conformite.get("compliant")),
        # Libellés des vérifications du jeu synthétique (« a verifier »…), sans donnée réelle.
        "ecarts_attendu": list(conformite.get("gaps", [])),
        "tours_dits": len(dits),
        "tours_entendus": len(entendus),
        "locuteurs_identiques": locuteurs,
        "taux_mots": round(taux, 3),
        "fidele_au_scenario": fidele,
        "cout_modele_micro_eur": round(cout_modele),
        "conforme": not ecarts,
        "ecarts": ecarts,
    }


def jouer(
    client: httpx.Client,
    scenario_id: str,
    issue_attendue: str,
    cadence: Cadence,
    horloge: Callable[[], float] = time.perf_counter,
) -> dict[str, object]:
    """Un parcours complet : synthèse, enregistrement, appel ; la ligne de la preuve."""
    ligne: dict[str, object] = {"scenario_id": scenario_id}
    cadence.attendre()
    r = client.post("/v1/demo/voice/synthesis", json={"scenario_id": scenario_id})
    if r.status_code != 200:
        return ligne | {"conforme": False, "ecarts": [f"synthèse {code_erreur(r)}"]}
    synthese = r.json()
    audio = assembler(synthese["turns"])
    ligne |= {
        "caracteres_synthetises": sum(len(t["text"]) for t in synthese["turns"]),
        "audio_octets": len(audio),
        "audio_s": round(len(audio) / OCTETS_PAR_SECONDE, 1),
    }
    cadence.attendre()
    debut = horloge()
    r = client.post(
        "/v1/demo/voice/call",
        params={"scenario_id": scenario_id},
        content=audio,
        headers={"Content-Type": TYPE_AUDIO},
    )
    duree_ms = round((horloge() - debut) * 1000)
    if r.status_code != 200:
        return ligne | {
            "duree_appel_ms": duree_ms,
            "conforme": False,
            "ecarts": [f"appel {code_erreur(r)}"],
        }
    return ligne | controler(issue_attendue, synthese, r.json(), duree_ms)


def cout_eur(lignes: list[dict[str, Any]]) -> dict[str, float]:
    """Coût estimé des parcours joués : synthèse, transcription, modèle de langage."""
    synthese = sum(int(lg.get("caracteres_synthetises", 0)) for lg in lignes) * EUR_PAR_CARACTERE
    secondes = sum(float(lg.get("audio_s", 0)) for lg in lignes)
    modele = sum(int(lg.get("cout_modele_micro_eur", 0)) for lg in lignes) / 1e6
    transcription = secondes * EUR_PAR_SECONDE_AUDIO
    return {
        "synthese": round(synthese, 4),
        "transcription": round(transcription, 4),
        "modele": round(modele, 4),
        "total": round(synthese + transcription + modele, 4),
    }


def estimation_eur(dialogues: list[str]) -> float:
    """Coût de synthèse et de transcription estimé avant les appels (modèle non compté)."""
    caracteres = sum(len(t.texte) for d in dialogues for t in decouper(d))
    return caracteres * EUR_PAR_CARACTERE + (
        caracteres / CARACTERES_PAR_SECONDE * EUR_PAR_SECONDE_AUDIO
    )


def bilan(lignes: list[dict[str, Any]], passages_ca8: int) -> dict[str, str]:
    ca8 = lignes[:passages_ca8]
    demo = lignes[passages_ca8:]
    return {
        "ca8": f"{sum(bool(lg['conforme']) for lg in ca8)}/{len(ca8)}",
        "demonstration": f"{sum(bool(lg['conforme']) for lg in demo)}/{len(demo)}",
    }


def preuve(
    lignes: list[dict[str, Any]], passages_ca8: int, api: str, version: dict[str, Any]
) -> dict[str, object]:
    return {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "api": api,
        "environnement": version.get("environment"),
        "git_sha": version.get("git_sha"),
        "critere": "CA-8, avenant D-74 : de la fin de l'appel joué à la réponse",
        "protocole": {
            "scenario_ca8": SCENARIO_CA8,
            "passages_ca8": passages_ca8,
            "demonstration": DEMONSTRATION,
            "seuil_ms": SEUIL_MS,
            "seuil_mots": SEUIL_MOTS,
            "espacement_s": ESPACEMENT_S,
            "mesure": "côté client, durée de POST /v1/demo/voice/call",
        },
        "bilan": bilan(lignes, passages_ca8),
        "cout_estime_eur": cout_eur(lignes),
        "lignes": lignes,
    }


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--api", default=API)
    options.add_argument("--passages", type=int, default=PASSAGES)
    args = options.parse_args()
    if not 1 <= args.passages <= 5:
        print("--passages entre 1 et 5", file=sys.stderr)
        return 2
    scenarios = charger_scenarios()
    plan = [SCENARIO_CA8] * args.passages + DEMONSTRATION
    client = httpx.Client(base_url=args.api, timeout=120)
    version = client.get("/version").json()
    avant = estimation_eur([scenarios[s].transcription for s in plan])
    print(f"API {version.get('environment')} {str(version.get('git_sha'))[:7]} ; "
          f"{len(plan)} parcours ; coût estimé (voix seule) {avant:.3f} €")  # fmt: skip
    cadence = Cadence()
    lignes: list[dict[str, Any]] = []
    for i, scenario_id in enumerate(plan, start=1):
        issue = str(scenarios[scenario_id].attendu.get("issue", "dossier"))
        ligne = jouer(client, scenario_id, issue, cadence)
        ligne["passage"] = i
        lignes.append(ligne)
        verdict = "conforme" if ligne["conforme"] else f"écarts : {ligne['ecarts']}"
        print(f"{i} {scenario_id} : {ligne.get('duree_appel_ms')} ms, {verdict}")
    PREUVE.parent.mkdir(parents=True, exist_ok=True)
    contenu = preuve(lignes, args.passages, args.api, version)
    PREUVE.write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resultat, cout = bilan(lignes, args.passages), cout_eur(lignes)
    print(f"CA-8 ({SCENARIO_CA8}) : {resultat['ca8']} ; démonstration : "
          f"{resultat['demonstration']} ; coût estimé {cout['total']:.4f} €")  # fmt: skip
    return 0 if all(lg["conforme"] for lg in lignes) else 1


if __name__ == "__main__":
    sys.exit(main())
