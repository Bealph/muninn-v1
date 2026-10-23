"""Vérification des traces sur Azure (sprint 5, étape 3 ; D-40, D-87, OB-1, OB-2).

Usage : `uv run python eval/production/verifier_traces.py [--reponse ENV=FICHIER ...]`.
Pour chaque environnement : SC-10 joué sur l'API (l'agent y appelle `chercher_communes`), puis
les traces de l'appel lues dans Application Insights (`az monitor app-insights query`, compte
Azure du poste). Attendu :
1. arbre complet : une racine `appel`, chaque autre étape a pour parent une étape de l'appel ;
   `outil` est fille d'`agent` ; les étapes de `steps` sont toutes présentes ;
2. rôle `<environnement>.muninn-api` ;
3. attributs : seulement ceux de la liste blanche (OB-2), un texte n'étant qu'un code court ;
4. durées : celles de la trace égales à celles de `steps`, à 5 ms près.
`--reponse` réutilise la réponse d'un appel déjà fait (JSON de `/v1/demo/runs`) au lieu d'en
jouer un nouveau. Preuve : `docs/v1/sprints/sprint-5/preuves/etape-3-traces.json`, sans contenu.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from muninn.telemetrie import ATTRIBUTS_AUTORISES

GROUPE = "adialloRG"
COMPOSANT = "appi-muninn"
API = {
    "preproduction": "https://ca-muninn-api-preprod.graybeach-70019748.francecentral.azurecontainerapps.io",
    "production": "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io",
}
PREUVE = (
    Path(__file__).resolve().parents[2] / "docs/v1/sprints/sprint-5/preuves/etape-3-traces.json"
)
CODE = re.compile(r"[A-Za-z0-9_.,\-]{1,80}")
TOLERANCE_MS = 5
ATTENTE_S = 600  # délai d'ingestion d'Application Insights : quelques minutes


def requete(request_id: str) -> str:
    # `request_id` vient de la réponse de l'API (UUID) : contrôlé avant d'entrer dans la requête.
    if not re.fullmatch(r"[0-9a-f-]{36}", request_id):
        raise ValueError("request_id inattendu")
    return (
        "let op = dependencies | where name == 'appel'"
        f" and tostring(customDimensions['muninn.request_id']) == '{request_id}'"
        " | project operation_Id;"
        " dependencies | where operation_Id in (op)"
        " | project name, id, operation_ParentId, operation_Id, duration, cloud_RoleName,"
        " customDimensions"
    )


def lire_traces(request_id: str) -> list[dict[str, Any]]:
    az = shutil.which("az")
    if az is None:
        raise RuntimeError("az introuvable")
    # Entrée maîtrisée : az trouvé par `shutil.which`, requête construite ci-dessus.
    sortie = subprocess.run(  # noqa: S603
        [az, "monitor", "app-insights", "query", "-g", GROUPE, "--app", COMPOSANT,
         "--analytics-query", requete(request_id), "-o", "json"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout  # fmt: skip
    table = json.loads(sortie)["tables"][0]
    noms = [c["name"] for c in table["columns"]]
    lignes = [dict(zip(noms, r, strict=True)) for r in table["rows"]]
    for ligne in lignes:
        if isinstance(ligne["customDimensions"], str):
            ligne["customDimensions"] = json.loads(ligne["customDimensions"])
    return lignes


def controler(env: str, reponse: dict[str, Any], spans: list[dict[str, Any]]) -> dict[str, object]:
    ecarts: list[str] = []
    etapes = reponse["steps"]
    par_id = {s["id"]: s for s in spans}
    racines = [s for s in spans if s["name"] == "appel"]
    if len(racines) != 1:
        ecarts.append(f"racines appel : {len(racines)}")
    racine = racines[0] if racines else None
    # 1. Arbre complet.
    for s in spans:
        if s is racine:
            if s["operation_ParentId"] != s["operation_Id"]:
                ecarts.append("la racine a un parent")
        elif s["operation_ParentId"] not in par_id:
            ecarts.append(f"{s['name']} : parent absent")
    parents = {s["name"]: par_id.get(s["operation_ParentId"], {}).get("name") for s in spans}
    if parents.get("outil") != "agent":
        ecarts.append(f"outil a pour parent {parents.get('outil')}")
    if sorted(e["nom"] for e in etapes) != sorted(s["name"] for s in spans):
        ecarts.append("étapes de la trace différentes de steps")
    # 2. Rôle de l'environnement.
    roles = {s["cloud_RoleName"] for s in spans}
    if roles != {f"{env}.muninn-api"}:
        ecarts.append(f"rôles {sorted(roles)}")
    # 3. Liste blanche, codes courts seulement.
    for s in spans:
        for cle, valeur in s["customDimensions"].items():
            if cle not in ATTRIBUTS_AUTORISES:
                ecarts.append(f"{s['name']} : attribut {cle} hors liste blanche")
            elif not CODE.fullmatch(str(valeur)):
                ecarts.append(f"{s['name']} : valeur de {cle} qui n'est pas un code")
    # 4. Durées.
    durees = {}
    for e in etapes:
        trace = next((s["duration"] for s in spans if s["name"] == e["nom"]), None)
        durees[e["nom"]] = {"steps_ms": e["duree_ms"], "trace_ms": trace}
        if trace is None or abs(float(trace) - e["duree_ms"]) > TOLERANCE_MS:
            ecarts.append(f"{e['nom']} : durée {trace} contre {e['duree_ms']}")
    return {
        "environnement": env,
        "request_id": reponse["request_id"],
        "operation_id": racine["operation_Id"] if racine else None,
        "conforme": not ecarts,
        "ecarts": ecarts,
        "arbre": parents,
        "roles": sorted(roles),
        "durees": durees,
        "attributs_vus": sorted({k for s in spans for k in s["customDimensions"]}),
    }


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--reponse", action="append", default=[], help="ENV=FICHIER")
    args = options.parse_args()
    deja = dict(r.split("=", 1) for r in args.reponse)
    lignes = []
    for env, url in API.items():
        client = httpx.Client(base_url=url, timeout=120)
        version = client.get("/version").json()
        if env in deja:
            reponse = json.loads(Path(deja[env]).read_text(encoding="utf-8"))
        else:
            corps = {"mode": "scenario", "scenario_id": "SC-10"}
            reponse = client.post("/v1/demo/runs", json=corps).json()
        attendues = len(reponse["steps"])
        fin = time.monotonic() + ATTENTE_S
        spans = lire_traces(reponse["request_id"])
        while len(spans) < attendues and time.monotonic() < fin:
            time.sleep(30)
            spans = lire_traces(reponse["request_id"])
        ligne = controler(env, reponse, spans)
        ligne["git_sha"] = version.get("git_sha")
        lignes.append(ligne)
        print(env, "conforme" if ligne["conforme"] else f"écarts : {ligne['ecarts']}")
    bilan = sum(bool(lg["conforme"]) for lg in lignes)
    PREUVE.parent.mkdir(parents=True, exist_ok=True)
    PREUVE.write_text(json.dumps({
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "composant": COMPOSANT,
        "scenario": "SC-10",
        "bilan": f"{bilan}/{len(lignes)}",
        "tolerance_duree_ms": TOLERANCE_MS,
        "lignes": lignes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # fmt: skip
    return 0 if bilan == len(lignes) else 1


if __name__ == "__main__":
    sys.exit(main())
