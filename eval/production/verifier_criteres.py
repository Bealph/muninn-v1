"""Vérification des critères du contrat sur la révision active d'Azure (sprint 4, étapes 11, 12).

Usage : `uv run python eval/production/verifier_criteres.py [--criteres CA-1 ...] [--preuve nom]`
(par défaut, CA-2, CA-3, CA-4 et CA-7, étape 11). Appelle l'API de production
(`POST /v1/demo/runs`), 3 exécutions par scénario, en respectant la limite de débit (10 appels par
minute). Le verdict de chaque exécution vient du serveur (`conformity`, mêmes vérifications que les
essais : `muninn.demo.verification`), complété ici par ce que le texte des critères exige et que
cette vérification ne contrôle pas (`complements`) : nom de SC-01, objet et statuts de SC-05,
statuts de SC-07, code postal et département des candidates de SC-10. CA-1 exige aussi le
dossier en 30 s au plus, mesurées côté client, du lancement à la réponse. Preuve :
`docs/v1/sprints/sprint-4/preuves/`, sans contenu (identifiants, verdicts, durées, révision servie).
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from muninn.extraction.entree import normaliser

API = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
CRITERES = {
    "CA-1": ["SC-01"],
    "CA-2": ["SC-07", "SC-10"],
    "CA-3": ["SC-04"],
    "CA-4": ["SC-05"],
    "CA-7": [f"SC-Q{i}" for i in range(1, 9)],
}
L05 = {"chaudiere en panne", "panne chaudiere", "panne de chaudiere"}  # dossier V1, annexe A
PAR_DEFAUT = ["CA-2", "CA-3", "CA-4", "CA-7"]  # étape 11
DUREE_MAX_MS = {"CA-1": 30_000}
EXECUTIONS = 3
ESPACEMENT_S = 7.0  # 10 appels par minute au plus, limite de l'API
PREUVES = Path(__file__).resolve().parents[2] / "docs" / "v1" / "sprints" / "sprint-4" / "preuves"


def statuts(checks: object, chemin: str = "") -> dict[str, str]:
    """Statut de chaque contrôle du brouillon, par chemin."""
    if not isinstance(checks, dict):
        return {}
    trouves = {chemin: checks["status"]} if isinstance(checks.get("status"), str) else {}
    for cle, valeur in checks.items():
        trouves |= statuts(valeur, f"{chemin}.{cle}".strip("."))
    return trouves


def complements(sid: str, corps: dict) -> list[str]:
    """Écarts au texte des critères non couverts par la vérification du serveur ; noms seuls."""
    d = corps.get("draft") or {}
    s = statuts(d.get("checks"))
    adresse = ("client.adresse.commune", "client.adresse.code_postal")
    ecarts = []
    nom = ((d.get("client") or {}).get("nom") or {}).get("value") or ""
    if sid == "SC-01" and normaliser(nom) != "martin":
        ecarts.append("nom Martin")
    if sid == "SC-05":
        objet = normaliser(((d.get("demande") or {}).get("objet_court") or {}).get("value") or "")
        if objet not in L05:
            ecarts.append("objet L-05")
        if any(v != "not_checked" for k, v in s.items() if k not in adresse):
            ecarts.append("statut hors commune et code postal")
    if sid in ("SC-05", "SC-07") and any(s.get(k) != "verified" for k in adresse):
        ecarts.append("commune et code postal verifies")
    candidates = (corps.get("envelope") or {}).get("candidates") or []
    if sid == "SC-10" and not all(
        c.get("codes_postaux") and c.get("departement") for c in candidates
    ):
        ecarts.append("candidates avec code postal et departement")
    return ecarts


def main() -> None:
    options = argparse.ArgumentParser()
    options.add_argument("--criteres", nargs="+", choices=list(CRITERES), default=PAR_DEFAUT)
    options.add_argument("--preuve", default="etape-11-criteres.json")
    args = options.parse_args()
    criteres = {c: CRITERES[c] for c in args.criteres}
    client = httpx.Client(base_url=API, timeout=120)
    version = client.get("/version").json()
    lignes = []
    for execution in range(1, EXECUTIONS + 1):
        for critere, scenarios in criteres.items():
            for sid in scenarios:
                debut = time.perf_counter()
                r = client.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": sid})
                duree_client_ms = round((time.perf_counter() - debut) * 1000)
                corps = r.json()
                conformite = corps.get("conformity") or {}
                ecarts = list(conformite.get("gaps") or []) + complements(sid, corps)
                if duree_client_ms > DUREE_MAX_MS.get(critere, duree_client_ms):
                    ecarts.append(f"duree {duree_client_ms} ms")
                q = corps.get("qualification") or {}
                lignes.append({
                    "critere": critere, "scenario": sid, "execution": execution,
                    "statut_http": r.status_code, "request_id": corps.get("request_id"),
                    "conforme": bool(conformite.get("compliant")) and not ecarts, "ecarts": ecarts,
                    "issue": corps.get("issue"), "categorie": q.get("categorie"),
                    "garde_fous": corps.get("guardrails"), "latence_ms": corps.get("latency_ms"),
                    "duree_client_ms": duree_client_ms,
                    "code_erreur": corps.get("code"),
                })  # fmt: skip
                etat = (
                    "conforme"
                    if lignes[-1]["conforme"]
                    else f"ECART {lignes[-1]['ecarts'] or corps.get('code')}"
                )
                print(f"{critere} {sid} r{execution} : {etat}")
                time.sleep(max(0.0, ESPACEMENT_S - (time.perf_counter() - debut)))
    bilan = {
        c: f"{sum(lg['conforme'] for lg in lignes if lg['critere'] == c)}/"
        f"{sum(1 for lg in lignes if lg['critere'] == c)}"
        for c in criteres
    }
    preuve = {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "api": API,
        "version_servie": version,
        "executions_par_scenario": EXECUTIONS,
        "bilan": bilan,
        "lignes": lignes,
    }
    preuve_chemin = PREUVES / args.preuve
    preuve_chemin.parent.mkdir(parents=True, exist_ok=True)
    preuve_chemin.write_text(
        json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\nBilan :", bilan, "; version servie :", version.get("git_sha", "")[:7])
    sys.exit(0 if all(lg["conforme"] for lg in lignes) else 1)


if __name__ == "__main__":
    main()
