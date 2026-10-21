"""Vérification de CA-2, CA-3, CA-4 et CA-7 sur la révision active d'Azure (sprint 4, étape 11).

Usage : `uv run python eval/production/verifier_criteres.py`. Appelle l'API de production
(`POST /v1/demo/runs`), 3 exécutions par scénario, en respectant la limite de débit (10 appels par
minute). Le verdict de chaque exécution vient du serveur (`conformity`, mêmes vérifications que les
essais : `muninn.demo.verification`). Preuve :
`docs/v1/sprints/sprint-4/preuves/etape-11-criteres.json`, sans contenu (identifiants, verdicts,
durées, révision servie).
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

API = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
CRITERES = {
    "CA-2": ["SC-07", "SC-10"],
    "CA-3": ["SC-04"],
    "CA-4": ["SC-05"],
    "CA-7": [f"SC-Q{i}" for i in range(1, 9)],
}
EXECUTIONS = 3
ESPACEMENT_S = 7.0  # 10 appels par minute au plus, limite de l'API
PREUVE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "v1"
    / "sprints"
    / "sprint-4"
    / "preuves"
    / "etape-11-criteres.json"
)


def main() -> None:
    client = httpx.Client(base_url=API, timeout=120)
    version = client.get("/version").json()
    lignes = []
    for execution in range(1, EXECUTIONS + 1):
        for critere, scenarios in CRITERES.items():
            for sid in scenarios:
                debut = time.perf_counter()
                r = client.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": sid})
                corps = r.json()
                conformite = corps.get("conformity") or {}
                q = corps.get("qualification") or {}
                lignes.append({
                    "critere": critere, "scenario": sid, "execution": execution,
                    "statut_http": r.status_code, "request_id": corps.get("request_id"),
                    "conforme": bool(conformite.get("compliant")), "ecarts": conformite.get("gaps"),
                    "issue": corps.get("issue"), "categorie": q.get("categorie"),
                    "garde_fous": corps.get("guardrails"), "latence_ms": corps.get("latency_ms"),
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
        for c in CRITERES
    }
    preuve = {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "api": API,
        "version_servie": version,
        "executions_par_scenario": EXECUTIONS,
        "bilan": bilan,
        "lignes": lignes,
    }
    PREUVE.parent.mkdir(parents=True, exist_ok=True)
    PREUVE.write_text(json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nBilan :", bilan, "; version servie :", version.get("git_sha", "")[:7])
    sys.exit(0 if all(lg["conforme"] for lg in lignes) else 1)


if __name__ == "__main__":
    main()
