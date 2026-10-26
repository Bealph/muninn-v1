"""Planche de CA-8 pour la soutenance (`ca8.svg`, et `ca8.png` avec `--png`).

Même style que les planches de `infra/azure/schemas/` (classe `Planche` de son générateur). Les
chiffres viennent des trois preuves `../preuves/etape-6-ca8*.json` du 26 octobre 2026 ; la fiche
qui les commente est `../ca8-soutenance.md`.

Usage : `uv run python docs/v1/sprints/sprint-5/ca8/generer.py [--png]`.
"""

import importlib.util
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[4]
_spec = importlib.util.spec_from_file_location(
    "planches", RACINE / "infra/azure/schemas/generer.py"
)
if _spec is None or _spec.loader is None:
    raise ImportError("générateur des planches introuvable")
planches = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(planches)


def planche() -> "planches.Planche":
    p = planches.Planche(0, "CA-8 : la voix, mesurée sur la production",
                         bandeau="MUNINN · CRITÈRES D'ACCEPTATION · V1",
                         repere="3 mesures · 21 parcours")  # fmt: skip
    # Colonne 1 : ce que CA-8 exige, élément par élément.
    p.groupe(40, 160, 470, 720, "Ce que CA-8 exige")
    exigences = [
        (["Appel synthétisé à deux voix", "21 parcours · lecture testée à l'écran"], "fonce"),
        (["Agent et appelant distingués", "21 sur 21"], "fonce"),
        (["45 s au plus après l'appel (D-74)", "de 3,9 à 17,4 s"], "fonce"),
        (["Aucun audio sur disque (TC-10)", "prouvé par les tests de l'API"], "fonce"),
        (["Dossier de SC-01 = attendu de CA-1", "téléphone manquant · 0 sur 3, 3 fois"], "rouge"),
    ]
    for i, (lignes, style) in enumerate(exigences):
        p.boite(70, 215 + i * 128, 410, 100, lignes, style)
    # Colonne 2 : pourquoi le téléphone manque.
    p.groupe(560, 160, 480, 720, "Pourquoi le téléphone manque")
    chaine = [
        (["Dit par l'appelant", "06 99 00 00 01 (tranche fictive, R9)"], "clair"),
        (["Voix Azure", "3 façons de lire essayées, 2 fois"], "gris"),
        (["Transcription Azure", "06 99 00 000 01 · à chaque passage"], "gris"),
        (["11 chiffres", "numéro invalide, non retenu"], "rouge"),
        (["Dossier sans numéro dicté", "rien d'inventé : comportement sûr"], "vif"),
    ]
    for i, (lignes, style) in enumerate(chaine):
        y = 215 + i * 128
        p.boite(590, y, 420, 100, lignes, style)
        if i:
            p.fleche((800, y - 28), (800, y - 2))
    # Colonne 3 : ce qui aurait fait réussir la mesure sans améliorer Muninn.
    p.groupe(1090, 160, 470, 460, "Écarté : ajuster le système au test")
    ecartes = [
        ["Réécrire « 000 » en « 00 »", "pour ce seul numéro"],
        ["Souffler le numéro", "à la transcription"],
        ["Changer le numéro", "impossible : tranche fictive (R9)"],
    ]
    for i, lignes in enumerate(ecartes):
        p.boite(1120, 215 + i * 128, 410, 100, lignes, "clair")
    p.boite(1090, 650, 470, 230, ["Démonstration : 4 sur 4", "SC-Q4, SC-04, SC-Q1, SC-10",
                                  "conformes à l'attendu", "et transcription jugée fidèle",
                                  "(3e mesure, production 74b1e55)"], "vif")  # fmt: skip
    p.note(910, "CA-8 : non atteint sur le téléphone. Limite de la transcription, mesurée,"
                " documentée (INC-09) et assumée.")  # fmt: skip
    return p


def main() -> int:
    svg = ICI / "ca8.svg"
    svg.write_text(planche().svg("ca8"), encoding="utf-8", newline="\n")
    if "--png" in sys.argv[1:]:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        with sync_playwright() as pw:
            navigateur = pw.chromium.launch()
            page = navigateur.new_page(device_scale_factor=2)
            page.set_content("<!doctype html><html><body style='margin:0;background:#fff'>"
                             f"{svg.read_text(encoding='utf-8')}</body></html>")  # fmt: skip
            page.locator("svg").screenshot(path=str(ICI / "ca8.png"))
            navigateur.close()
    print("ca8.svg" + (" et ca8.png" if "--png" in sys.argv[1:] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
