"""Vitrine de l'audit RGAA de la console (C10), tirée de `docs/v1/accessibilite/`.

Lit le rapport (`rapport.md` : couche « En clair », cadrage, méthode, corrections, parcours au
lecteur d'écran, remarques, limites), la grille après corrections (`grille.md` : taux, 106 critères
sur 5 écrans, verdict d'avant) et le parcours NVDA joué (`scenario-nvda.md`), puis écrit
`vitrine.html` : le modèle `vitrine_modele.html` avec la charte commune (`infra/vitrine/`) et les
données en JSON. Aucune saisie à la main.

L'analyse du Markdown (sections, listes, tableaux, segments en ligne) est celle de la vitrine du
benchmark (`infra/benchmark/vitrine.py`) : le texte n'est jamais interprété comme du HTML.

Bibliothèque standard seulement. Usage : `python infra/accessibilite/vitrine.py [--sortie FICHIER]`.
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = RACINE / "docs" / "v1" / "accessibilite"
MODELE = Path(__file__).with_name("vitrine_modele.html")
DEPOT = "https://github.com/Bealph/Muninn/blob/main/docs/v1/accessibilite/"
ECRANS = ("Accueil", "Référentiels", "Agent", "Démonstration", "Qualité")


def _charger(nom: str, chemin: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nom, chemin)
    if spec is None or spec.loader is None:
        raise ImportError(chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_md = _charger("vitrine_benchmark", RACINE / "infra" / "benchmark" / "vitrine.py")
seg = _md.seg
cellules = _md.cellules


def rangs(texte: str, entete: str) -> list[list[str]]:
    """Les lignes (sans en-tête ni séparateur) du premier tableau dont l'en-tête commence ainsi."""
    lignes = texte.split("\n")
    debut = next(i for i, x in enumerate(lignes) if x.startswith("| " + entete))
    resultat = []
    for x in lignes[debut + 2 :]:
        if not x.startswith("|"):
            break
        resultat.append(cellules(x))
    return resultat


def taux(grille: str) -> dict[str, Any]:
    """Les taux avant et après corrections, et par écran (section « Taux » de la grille)."""
    lignes = {r[0]: r for r in rangs(grille, "Mesure ")}
    avant = lignes["Avant, rectifié (9.1 Qualité)"]
    apres = lignes["Après corrections"]

    def compte(r: list[str]) -> dict[str, int]:
        c, nc, na = (int(x) for x in r[1].split("/"))
        return {"c": c, "nc": nc, "na": na}

    return {
        "avant": {"global": avant[2], "moyen": avant[3], **compte(avant),
                  "ecrans": dict(zip(ECRANS, avant[4:9], strict=True))},
        "apres": {"global": apres[2], "moyen": apres[3], **compte(apres),
                  "ecrans": dict(zip(ECRANS, apres[4:9], strict=True))},
        "initial": lignes["Avant, audit initial"][2],
    }  # fmt: skip


def criteres(grille: str) -> list[dict[str, Any]]:
    """Les 106 critères, par thématique : verdict par écran, verdict d'avant, preuve."""
    corps = grille.split("\n## Grille après corrections", 1)[1]
    resultat = []
    theme = ""
    for ligne in corps.split("\n"):
        titre = re.match(r"### (\d+)\. (.+)", ligne)
        if titre:
            theme = f"{titre.group(1)}. {titre.group(2)}"
            continue
        m = re.match(r"\| (\d+\.\d+) ", ligne)
        if not m:
            continue
        c = cellules(ligne)
        numero, _, intitule = c[0].partition(" ")
        resultat.append({
            "theme": theme, "numero": numero, "titre": intitule,
            "verdicts": dict(zip(ECRANS, c[1:6], strict=True)),
            "avant": c[6], "preuve": seg(c[7]),
        })  # fmt: skip
    return resultat


def parcours(texte: str) -> dict[str, Any]:
    """Le parcours NVDA joué : étapes et champs de la fin du scénario."""
    # Deux tableaux d'étapes : le parcours, puis le complément ciblé.
    debuts = [m.start() for m in re.finditer(r"\n\| N° ", texte)]
    tableaux = [rangs(texte[i:], "N° ") for i in debuts]
    etapes = [{"n": r[0], "ecran": r[1], "action": seg(r[2]), "attendu": seg(r[3]), "observe": r[4]}
              for t in tableaux for r in t]  # fmt: skip
    champs = {r[0]: r[1] for r in rangs(texte, "Champ ")}
    return {"etapes": etapes, "champs": champs}


def donnees(dossier: Path = DOSSIER) -> dict[str, Any]:
    rapport = (dossier / "rapport.md").read_text(encoding="utf-8")
    grille = (dossier / "grille.md").read_text(encoding="utf-8")
    s = _md.sections(rapport)
    clair = _md.en_clair(s.get("En clair", ""))
    corrections = [
        {"criteres": r[0], "ecrans": r[1], "defaut": seg(r[2]), "correction": seg(r[3])}
        for r in rangs(s["Corrections"], "Critère(s)")
    ]
    liste = criteres(grille)
    return {
        "clair": clair,
        "cadrage": _md.blocs(s["Cadrage"]),
        "methode": _md.blocs(s["Échantillon et méthode"]),
        "resultats": [b for b in _md.blocs(s["Résultats"]) if b["type"] != "tableau"],
        "corrections": corrections,
        "corrections_fin": [b for b in _md.blocs(s["Corrections"]) if b["type"] != "tableau"],
        "nvda": {"texte": _md.blocs(s["Parcours au lecteur d'écran"]),
                 **parcours((dossier / "scenario-nvda.md").read_text(encoding="utf-8"))},
        "remarques": _md.blocs(s["Remarques hors taux"]),
        "limites": _md.blocs(s["Limites"]),
        "taux": taux(grille),
        "criteres": liste,
        "themes": list(dict.fromkeys(c["theme"] for c in liste)),
        "ecrans": list(ECRANS),
        "depot": DEPOT,
    }  # fmt: skip


def page(d: dict[str, Any], modele: Path = MODELE) -> str:
    """La page autonome : charte commune et données insérées (`infra/vitrine/assemblage.py`)."""
    return str(_md.page(d, modele))


def main(argv: list[str]) -> int:
    options = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    options.add_argument("--sortie", type=Path, default=DOSSIER / "vitrine.html")
    args = options.parse_args(argv)
    args.sortie.write_text(page(donnees()), encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    print(args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
