"""Répétition technique de la démo sur la console de production (sprint 5, étape 10).

Usage : `uv run python eval/production/repetition_demo.py --repetition N [--scenarios SC-04 ...]
[--sonnerie-courte]`. Pour chaque scénario, l'écran « Démonstration » de production est joué dans
Chromium, comme le ferait la personne qui présente : choix du scénario, « Lancer l'appel »,
sonnerie, conversation jouée (son actif, sans sortie audio), chaîne animée, résultat. Sont
relevés la durée totale vue de l'écran (du clic au résultat), le verdict CA-8 affiché par l'écran
et l'issue, et une capture de la page entière (plan B de la démo).

Ce n'est pas la répétition orale : celle-ci, chronométrée par la personne qui présente, mesure le
discours. Celle-ci mesure ce que la production met à jouer chaque séquence.
Playwright est utilisé comme bibliothèque, sur une adresse fixée ; jamais le serveur MCP.
Preuve : `docs/v1/sprints/sprint-5/preuves/etape-10-repetition-<N>.json` et ses captures, sans
contenu d'appel autre que les scénarios synthétiques.
"""

import argparse
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

CONSOLE = "https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io"
PREUVES = Path(__file__).resolve().parents[2] / "docs/v1/sprints/sprint-5/preuves"
RESULTAT = re.compile(r"(Dossier|Message|Trace) prêt[e]? en ([0-9]+(?:,[0-9])?) s")
DELAI_MAX_S = 240


def jouer(page, scenario: str, sonnerie_courte: bool) -> dict[str, object]:  # type: ignore[no-untyped-def]
    page.goto(f"{CONSOLE}/demonstration", wait_until="networkidle")
    page.check(f'input[name="scenario"][value="{scenario}"]')
    if sonnerie_courte:
        page.uncheck("#reel")
    debut = time.perf_counter()
    page.click("#lancer")
    page.wait_for_function(
        "() => /(prêt|prête) en /.test(document.getElementById('chrono').textContent)"
        " || document.getElementById('erreur').textContent.trim() !== ''",
        timeout=DELAI_MAX_S * 1000,
    )
    total_s = round(time.perf_counter() - debut, 1)
    chrono = page.inner_text("#chrono")
    erreur = page.inner_text("#erreur").strip()
    m = RESULTAT.search(chrono)
    return {
        "scenario": scenario,
        "sonnerie_s": 3 if sonnerie_courte else 15,
        "duree_ecran_s": total_s,
        "issue": m.group(1).lower() if m else None,
        "apres_fin_appel_s": float(m.group(2).replace(",", ".")) if m else None,
        "ca8_respecte": "respecté" in chrono,
        "erreur_affichee": bool(erreur),
    }


def main() -> int:
    options = argparse.ArgumentParser()
    options.add_argument("--repetition", type=int, required=True)
    options.add_argument("--scenarios", nargs="+", default=["SC-04", "SC-10"])
    options.add_argument("--sonnerie-courte", action="store_true")
    args = options.parse_args()
    lignes = []
    with sync_playwright() as p:
        navigateur = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        page = navigateur.new_page(viewport={"width": 1440, "height": 1000})
        for scenario in args.scenarios:
            ligne = jouer(page, scenario, args.sonnerie_courte)
            # La chaîne rejoue les étapes en 5 à 6 s après le résultat : capture de l'écran final.
            page.wait_for_timeout(8000)
            capture = PREUVES / f"etape-10-repetition-{args.repetition}-{scenario}.png"
            page.screenshot(path=str(capture), full_page=True)
            ligne["capture"] = capture.name
            lignes.append(ligne)
            print(json.dumps(ligne, ensure_ascii=False))
        navigateur.close()
    preuve = {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "console": CONSOLE,
        "repetition": args.repetition,
        "nature": "répétition technique : écran joué par Chromium, sans discours",
        "lignes": lignes,
    }
    chemin = PREUVES / f"etape-10-repetition-{args.repetition}.json"
    chemin.write_text(json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(lg["issue"] and not lg["erreur_affichee"] for lg in lignes) else 1


if __name__ == "__main__":
    sys.exit(main())
