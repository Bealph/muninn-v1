"""Rafale d'appels de démonstration sur l'API (sprint 5, étapes 4 et 5 ; D-83, D-84).

Usage : `uv run python eval/production/rafale.py --profil nominal|derive [--nombre N] [--api URL]`.

L'état du service se lit sur la dernière heure, avec 20 dossiers au moins (D-83) : sans trafic,
l'écran « Qualité » dit « pas assez d'appels pour juger ». Une rafale joue des scénarios
synthétiques avec le vrai modèle (le modèle simulé est exclu des chiffres) :
- `nominal` : scénarios à adresse complète ou déductible (SC-01, SC-02, SC-07, SC-08) ; l'état
  attendu est « aucun seuil dépassé ». À relancer avant une démonstration : la fenêtre glisse,
  et l'écran redevient gris une heure après la rafale ;
- `derive` : la dérive simulée de D-84, des communes homonymes sans indice (SC-10), qui finissent
  toutes « à vérifier » ; l'alerte AL-01 s'allume dès que la part dépasse 20 % sur 20 dossiers.

Un appel toutes les 7 s au plus (la limite de l'API est de 10 par minute). Coût : environ
0,005 € par appel. Aucune donnée réelle : les scénarios sont ceux du jeu synthétique.
"""

import argparse
import sys
import time

import httpx

API = "https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
PROFILS = {"nominal": ["SC-01", "SC-02", "SC-07", "SC-08"], "derive": ["SC-10"]}
ESPACEMENT_S = 7.0
NOMBRE_MAX = 60


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--profil", choices=sorted(PROFILS), required=True)
    options.add_argument("--nombre", type=int, default=24)
    options.add_argument("--api", default=API)
    args = options.parse_args()
    if not 1 <= args.nombre <= NOMBRE_MAX:
        print(f"--nombre entre 1 et {NOMBRE_MAX}", file=sys.stderr)
        return 2
    client = httpx.Client(base_url=args.api, timeout=120)
    version = client.get("/version").json()
    print(f"API {version.get('environment')} {str(version.get('git_sha'))[:7]}, profil "
          f"{args.profil}, {args.nombre} appels")  # fmt: skip
    scenarios = PROFILS[args.profil]
    dossiers = a_verifier = echecs = 0
    cout = 0.0
    for i in range(args.nombre):
        debut = time.perf_counter()
        scenario = scenarios[i % len(scenarios)]
        r = client.post("/v1/demo/runs", json={"mode": "scenario", "scenario_id": scenario})
        if r.status_code != 200:
            echecs += 1
            print(f"{i + 1:>2} {scenario} : HTTP {r.status_code}")
        else:
            run = r.json()
            # « À vérifier » au sens d'AL-01 : `envelope.a_verifier`. `draft.needs_review` dit
            # seulement que l'extraction est incomplète (contrat), ce n'est pas la même chose.
            verifier = bool((run.get("envelope") or {}).get("a_verifier"))
            dossiers += run.get("issue") == "dossier"
            a_verifier += verifier
            etapes = run.get("steps") or []
            duree = etapes[0]["duree_ms"] if etapes else None
            cout += sum(float(e["details"].get("cout_micro_eur", 0)) for e in etapes[1:]) / 1e6
            print(f"{i + 1:>2} {scenario} : {run.get('issue')}"
                  f"{', à vérifier' if verifier else ''}, {duree} ms")  # fmt: skip
        time.sleep(max(0.0, ESPACEMENT_S - (time.perf_counter() - debut)))
    print(f"Bilan : {dossiers} dossiers, dont {a_verifier} à vérifier ; {echecs} échecs ; "
          f"coût du modèle {cout:.4f} €")  # fmt: skip
    time.sleep(16)  # les métriques sont gardées 15 s par l'API
    etat = client.get("/v1/demo/quality", params={"heures": 1}).json()["etat"]
    print(f"État de la dernière heure : {etat['titre']}. {etat['phrase']}")
    return 0 if echecs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
