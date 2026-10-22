"""Vérification de CA-5 sur la révision active d'Azure (sprint 5, étape 2 ; V-09, D-86).

Usage : `uv run python eval/production/verifier_ca5.py [--api URL]`. Trois fois : SC-03 joué sur
l'API de production (commune « incohérent »), puis le code postal corrigé en « 93170 » et le
dossier validé en une requête (`POST /v1/demo/runs/{draft_id}/review`). Attendu (CA-5) : la
commune et le code postal passent « vérifié », le dossier est « validé », le champ corrigé est
cité. La table des corrections et les journaux se contrôlent à part (`consulter-base.sh
--traitements`, Log Analytics), sans afficher de valeur.
Preuve : `docs/v1/sprints/sprint-5/preuves/etape-2-ca-5.json`, sans contenu.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

API = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
PREUVE = Path(__file__).resolve().parents[2] / "docs/v1/sprints/sprint-5/preuves/etape-2-ca-5.json"
ESPACEMENT_S = 7.0  # 10 appels par minute au plus, limite de l'API
CP = "client.adresse.code_postal"


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--api", default=API)
    args = options.parse_args()
    client = httpx.Client(base_url=args.api, timeout=120)
    version = client.get("/version").json()
    lignes = []
    for execution in range(1, 4):
        debut = time.perf_counter()
        run = client.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": "SC-03"}).json()
        avant = (run.get("draft") or {}).get("checks", {})
        draft_id = (run.get("draft") or {}).get("draft_id")
        time.sleep(max(0.0, ESPACEMENT_S - (time.perf_counter() - debut)))
        debut = time.perf_counter()
        r = client.post(f"/v1/demo/runs/{draft_id}/review", json={
            "decision": "validated_with_corrections", "corrected_fields": [CP],
            "values": {CP: "93170"},
        })  # fmt: skip
        corps = r.json()
        apres = (corps.get("draft") or {}).get("checks", {})
        ecarts = []
        if run.get("review_available") is not True:
            ecarts.append("dossier non enregistré")
        if (avant.get("client.adresse.commune") or {}).get("status") != "mismatch":
            ecarts.append("commune non incohérente avant correction")
        if r.status_code != 200 or corps.get("state") != "validated":
            ecarts.append(f"validation {r.status_code} {corps.get('code', '')}".strip())
        for champ in ("client.adresse.commune", CP):
            if (apres.get(champ) or {}).get("status") != "verified":
                ecarts.append(f"{champ} non vérifié après correction")
        if corps.get("corrected_fields") != [CP]:
            ecarts.append("champ corrigé non cité")
        lignes.append({
            "execution": execution, "request_id": run.get("request_id"), "draft_id": draft_id,
            "statut_revue": r.status_code, "conforme": not ecarts, "ecarts": ecarts,
            "statuts_avant": {k: (v or {}).get("status") for k, v in avant.items()},
            "statuts_apres": {k: (v or {}).get("status") for k, v in apres.items()},
        })  # fmt: skip
        print(f"CA-5 r{execution} : {'conforme' if not ecarts else 'ECART ' + str(ecarts)}")
        time.sleep(max(0.0, ESPACEMENT_S - (time.perf_counter() - debut)))
    preuve = {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "api": args.api,
        "version_servie": version,
        "bilan": f"{sum(lg['conforme'] for lg in lignes)}/{len(lignes)}",
        "lignes": lignes,
    }
    PREUVE.parent.mkdir(parents=True, exist_ok=True)
    PREUVE.write_text(json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nBilan :", preuve["bilan"], "; version servie :", version.get("git_sha", "")[:7])
    return 0 if all(lg["conforme"] for lg in lignes) else 1


if __name__ == "__main__":
    sys.exit(main())
