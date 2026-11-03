"""Vitrine de la veille (C6) : une page web autonome tirée des fichiers de `docs/veille/`.

Lit le registre (`sources.md`), la collecte la plus récente (`collecte/*.md`), les fiches
(`fiches/V-*.md`), la dernière synthèse (`syntheses/S-*.md`) et le glossaire (`glossaire.md`),
puis écrit `docs/veille/vitrine.html` : le modèle `vitrine_modele.html` avec les données en JSON.
Aucune saisie à la main : la page se régénère après chaque collecte.

Le texte venu des flux externes n'est jamais interprété comme du HTML : les passages en ligne
(code, liens) sont découpés ici en segments typés, que la page assemble avec `textContent` ; seuls
les liens en `https://` sont gardés.

Bibliothèque standard seulement. Usage : `python infra/veille/vitrine.py [--sortie FICHIER]`.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
VEILLE = RACINE / "docs" / "veille"
MODELE = Path(__file__).with_name("vitrine_modele.html")
MARQUE = "/*DONNEES*/"

Segment = dict[str, str]


def segments(texte: str) -> list[Segment]:
    """Markdown en ligne -> segments : texte, `code`, [lien](https://…) ou <https://…>."""
    motif = re.compile(r"`([^`]+)`|\[([^\]]+)\]\((https://[^)\s]+)\)|<(https://[^>\s]+)>")
    resultat: list[Segment] = []
    position = 0
    for m in motif.finditer(texte):
        if m.start() > position:
            resultat.append({"t": texte[position : m.start()]})
        if m.group(1) is not None:
            resultat.append({"code": m.group(1)})
        elif m.group(2) is not None:
            resultat.append({"a": m.group(2), "href": m.group(3)})
        else:
            resultat.append({"a": m.group(4), "href": m.group(4)})
        position = m.end()
    if position < len(texte):
        resultat.append({"t": texte[position:]})
    return resultat


def cellules(ligne: str) -> list[str]:
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def tableau(lignes: list[str]) -> list[list[str]]:
    """Les lignes d'un tableau Markdown, sans l'en-tête ni la ligne de séparation."""
    rangs = [cellules(x) for x in lignes if x.startswith("|")]
    return [r for r in rangs[1:] if not set("".join(r)) <= set("-: ")]


def sections(texte: str, niveau: str = "## ") -> dict[str, str]:
    """Le corps de chaque section d'un niveau donné, titre -> texte."""
    resultat: dict[str, str] = {}
    titre = ""
    for ligne in texte.split("\n"):
        if ligne.startswith(niveau):
            titre = ligne[len(niveau) :].strip()
            resultat[titre] = ""
        elif titre:
            resultat[titre] += ligne + "\n"
    return {k: v.strip() for k, v in resultat.items()}


def paragraphes(texte: str) -> list[str]:
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", texte) if p.strip()]


def puces(texte: str) -> list[str]:
    """Les éléments d'une liste à puces, lignes de continuation comprises."""
    elements: list[str] = []
    for ligne in texte.split("\n"):
        if ligne.startswith("- "):
            elements.append(ligne[2:].strip())
        elif elements and ligne.startswith("  "):
            elements[-1] += " " + ligne.strip()
    return elements


def lire_sources(chemin: Path) -> list[dict[str, str]]:
    sources = []
    for r in tableau(chemin.read_text(encoding="utf-8").split("\n")):
        if len(r) < 7 or not r[0].startswith("S"):
            continue
        lien = re.search(r"<(https://[^>]+)>", r[6])
        sources.append({
            "code": r[0], "nom": r[1], "theme": r[2], "type": r[3], "fiabilite": r[4],
            "frequence": r[5], "acces": "main" if r[6].startswith("À la main") else "flux",
            "lien": lien.group(1) if lien else "",
        })  # fmt: skip
    return sources


def lire_collecte(chemin: Path, themes: dict[str, str]) -> dict[str, Any]:
    texte = chemin.read_text(encoding="utf-8")
    entete = re.search(r"Nouveautés des (\d+) derniers jours, (\d+) au total", texte)
    retirees = re.search(r"règle d'exclusion du poste : (\d+)", texte)
    entrees: list[dict[str, str]] = []
    injoignables: list[str] = []
    code = ""
    for ligne in texte.split("\n"):
        titre = re.match(r"## (S\d+) ", ligne)
        if titre:
            code = titre.group(1)
            continue
        if ligne.startswith("Source injoignable") and code:
            injoignables.append(code)
        m = re.match(r"- (\d{4}-\d{2}-\d{2}) · \[(.*)\]\((https://[^)\s]+)\)$", ligne)
        if m and code:
            entrees.append({
                "id": f"entree-{len(entrees) + 1}", "date": m.group(1), "titre": m.group(2),
                "lien": m.group(3), "source": code, "theme": themes.get(code, ""), "fiche": "",
            })  # fmt: skip
    return {
        "fichier": chemin.name,
        "date": chemin.name[:10],
        "jours": int(entete.group(1)) if entete else 0,
        "total": len(entrees),
        "retirees": int(retirees.group(1)) if retirees else 0,
        "injoignables": injoignables,
        "entrees": entrees,
    }


def lire_fiche(chemin: Path) -> dict[str, Any]:
    texte = chemin.read_text(encoding="utf-8")
    titre = texte.split("\n", 1)[0].lstrip("# ").strip()
    ident, _, libelle = titre.partition(" : ")
    champs = {r[0]: r[1] for r in tableau(texte.split("\n")) if len(r) >= 2}
    verification = champs.get("Vérifiée à la source primaire", "")
    corps = sections(texte)
    entree = re.search(r"<(https://[^>]+)>", champs.get("Entrée de collecte", ""))
    return {
        "id": ident.lower(),
        "code": ident,
        "titre": libelle,
        "lecture": champs.get("Date de lecture", ""),
        "source": segments(champs.get("Source", "")),
        "theme": champs.get("Thème", ""),
        "verification": re.split(r"[ ,:;]", verification, maxsplit=1)[0] if verification else "",
        "verification_detail": segments(verification),
        "entree": entree.group(1) if entree else "",
        "resume": [segments(p) for p in paragraphes(corps.get("Résumé", ""))],
        "impact": [segments(p) for p in paragraphes(corps.get("Impact sur Muninn", ""))],
        "suite": [segments(p) for p in paragraphes(corps.get("Suite", ""))],
        "en_clair": [segments(p) for p in paragraphes(corps.get("En clair", ""))],
    }


def lire_synthese(chemin: Path) -> dict[str, Any]:
    texte = chemin.read_text(encoding="utf-8")
    titre = texte.split("\n", 1)[0].lstrip("# ").strip()
    debut = paragraphes(texte.split("\n## ", 1)[0].split("\n", 1)[1])
    corps = sections(texte)
    clair = {}
    for p in puces(corps.get("En clair", "")):
        cle, _, valeur = p.partition(" : ")
        clair[cle.strip()] = valeur.strip()
    recommandations = []
    for r in tableau(corps.get("Recommandations", "").split("\n")):
        if len(r) >= 5 and r[0].startswith("R"):
            recommandations.append({
                "n": r[0], "fiche": r[1], "information": segments(r[2]), "impact": segments(r[3]),
                "recommandation": segments(r[4]), "en_clair": clair.get(r[0], ""),
            })  # fmt: skip
    raisonnements = {
        k.split(" ", 1)[0]: {"titre": k, "paragraphes": [segments(p) for p in paragraphes(v)]}
        for k, v in corps.items()
        if re.match(r"R\d+ ", k)
    }
    return {
        "titre": titre,
        "chapeau": [segments(p) for p in debut[:1]],
        "periode": [segments(p) for p in debut[1:]],
        "chapeau_clair": clair.get("Chapeau", ""),
        "recommandations": recommandations,
        "raisonnements": raisonnements,
        "rien": [segments(p) for p in puces(corps.get("Ce qui ne change rien", ""))],
        "limites": [segments(p) for p in puces(corps.get("Limites", ""))],
        "sources_citees": [segments(p) for p in puces(corps.get("Sources citées", ""))],
    }


def lire_glossaire(chemin: Path) -> list[dict[str, str]]:
    if not chemin.exists():
        return []
    rangs = tableau(chemin.read_text(encoding="utf-8").split("\n"))
    return [{"terme": r[0], "definition": r[1]} for r in rangs if len(r) >= 2]


def themes_du_readme(chemin: Path) -> list[str]:
    corps = sections(chemin.read_text(encoding="utf-8")).get("Thèmes", "")
    return [r[0] for r in tableau(corps.split("\n")) if r]


def cle_collecte(chemin: Path) -> tuple[str, int]:
    periode = re.search(r"-(\d+)j\.md$", chemin.name)
    return chemin.name[:10], int(periode.group(1)) if periode else 0


def donnees(veille: Path = VEILLE) -> dict[str, Any]:
    sources = lire_sources(veille / "sources.md")
    themes_par_source = {s["code"]: s["theme"] for s in sources}
    # La collecte la plus récente ; à date égale, celle de la plus longue période (30j avant 7j).
    candidates = list((veille / "collecte").glob("*.md"))
    if not candidates:
        raise SystemExit("Aucune collecte dans docs/veille/collecte : lancer collecter.py.")
    recente = max(candidates, key=cle_collecte)
    collecte = lire_collecte(recente, themes_par_source)
    fiches = [lire_fiche(p) for p in sorted((veille / "fiches").glob("V-*.md"))]
    for f in fiches:
        for e in collecte["entrees"]:
            if f["entree"] and e["lien"] == f["entree"]:
                e["fiche"] = f["id"]
    syntheses = sorted((veille / "syntheses").glob("S-*.md"))
    return {
        "themes": themes_du_readme(veille / "README.md"),
        "sources": sources,
        "collecte": collecte,
        "fiches": fiches,
        "synthese": lire_synthese(syntheses[-1]) if syntheses else None,
        "glossaire": lire_glossaire(veille / "glossaire.md"),
    }


def page(d: dict[str, Any], modele: Path = MODELE) -> str:
    texte = modele.read_text(encoding="utf-8")
    if texte.count(MARQUE) != 1:
        raise ValueError(f"le modèle doit contenir {MARQUE} une seule fois")
    # « < », « > » et « & » échappés : le JSON ne peut ni fermer la balise <script> qui le
    # porte, ni ouvrir un « <!-- » qui ferait avaler le script suivant par l'analyseur HTML.
    charge = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    charge = charge.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return texte.replace(MARQUE, charge)


def main(argv: list[str]) -> int:
    options = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    options.add_argument("--sortie", type=Path, default=VEILLE / "vitrine.html")
    args = options.parse_args(argv)
    args.sortie.write_text(page(donnees()), encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    print(args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
