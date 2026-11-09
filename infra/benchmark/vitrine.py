"""Vitrine du benchmark C7 : une page web autonome tirée de `docs/v1/benchmark-services-ia/`.

Lit le rapport (`rapport.md` : réponse courte, couche « En clair », lecture « Selon le
référentiel », règles, mesure, grilles des trois catégories, écarts, limites), la mesure la plus
récente (`mesures/azure-speech-*.json`) et la liste des relevés, puis écrit `vitrine.html` : le
modèle `vitrine_modele.html` avec la charte commune des vitrines (`infra/vitrine/`) et les
données en JSON. Aucune saisie à la main : la page se régénère après chaque modification du
rapport.

Le texte du rapport n'est jamais interprété comme du HTML : les passages en ligne (code, liens,
gras) sont découpés en segments typés, que la page assemble avec `textContent`.

Bibliothèque standard seulement. Usage : `python infra/benchmark/vitrine.py [--sortie FICHIER]`.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = RACINE / "docs" / "v1" / "benchmark-services-ia"
MODELE = Path(__file__).with_name("vitrine_modele.html")
DEPOT = "https://github.com/Bealph/Muninn/blob/main/docs/v1/benchmark-services-ia/"
CATEGORIES = (
    ("transcription", "Transcription", "transcription.md"),
    ("synthese", "Synthèse vocale", "synthese-vocale.md"),
    ("telephonie", "Téléphonie", "telephonie.md"),
)


def _charger_assemblage() -> ModuleType:
    chemin = RACINE / "infra" / "vitrine" / "assemblage.py"
    spec = importlib.util.spec_from_file_location("vitrine_assemblage", chemin)
    if spec is None or spec.loader is None:
        raise ImportError(chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_assemblage = _charger_assemblage()
Segment = dict[str, str]


def seg(texte: str) -> list[Segment]:
    return list(_assemblage.segments(texte, gras=True))


def cellules(ligne: str) -> list[str]:
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def sections(texte: str) -> dict[str, str]:
    """Le corps de chaque section de niveau 2, titre -> texte (titre sans son numéro)."""
    resultat: dict[str, str] = {}
    titre = ""
    for ligne in texte.split("\n"):
        if ligne.startswith("## "):
            titre = re.sub(r"^\d+\.\s*", "", ligne[3:].strip())
            resultat[titre] = ""
        elif titre:
            resultat[titre] += ligne + "\n"
    return resultat


def etat(texte: str) -> str:
    """Couleur d'une cellule de verdict ou de critère éliminatoire : satisfait, sous réserve, non
    satisfait (« non établi », « contradictoire » : règle de la section 2 du rapport), ou neutre."""
    t = texte.lower()
    if re.match(
        r"(non|écarté|fermé|pas de|aucun|autorisé en préversion|contradictoire)", t
    ) or re.search(r"non (établi|listé|trouvé)", t):
        return "non"
    if "sous réserve" in t or "sous condition" in t or re.match(r"(préversion|extrait)", t):
        return "partie"
    if re.match(r"(établi|oui|1er|2e|3e|tenu)", t):
        return "oui"
    return ""


def colorer(ligne: list[str]) -> bool:
    """Seuls le verdict et les critères éliminatoires sont colorés ; un critère principal ou
    rapporté « non publié » n'est pas un échec."""
    critere = ligne[0].lower()
    return "éliminatoire" in critere or critere.startswith("verdict")


def blocs(corps: str) -> list[dict[str, Any]]:
    """Paragraphes, listes et tableaux d'un corps de section, lus ligne par ligne. Une puce peut
    porter une sous-liste (« - » en retrait de deux espaces) et un paragraphe de suite (texte en
    retrait après une ligne vide)."""
    resultat: list[dict[str, Any]] = []
    courant: dict[str, Any] | None = None  # bloc en cours : paragraphe, liste ou tableau
    vide = False
    for ligne in corps.strip().split("\n"):
        if not ligne.strip():
            vide = True
            if courant is not None and courant["type"] != "liste":
                courant = None
            continue
        if ligne.startswith("|"):
            if courant is None or courant["type"] != "tableau":
                courant = {"type": "tableau", "rangs": []}
                resultat.append(courant)
            courant["rangs"].append(cellules(ligne))
        elif ligne.startswith("- ") or re.match(r"\d+\. ", ligne):
            ordonnee = not ligne.startswith("- ")
            if courant is None or courant["type"] != "liste" or courant["ordonnee"] != ordonnee:
                courant = {"type": "liste", "ordonnee": ordonnee, "items": []}
                resultat.append(courant)
            texte = re.sub(r"^(- |\d+\. )", "", ligne).strip()
            courant["items"].append({"texte": texte, "sous": [], "suite": []})
        elif ligne.startswith("  ") and courant is not None and courant["type"] == "liste":
            item = courant["items"][-1]
            texte = ligne.strip()
            if texte.startswith("- "):
                item["sous"].append(texte[2:].strip())
            elif vide or item["suite"]:
                if vide:
                    item["suite"].append(texte)
                else:
                    item["suite"][-1] += " " + texte
            elif item["sous"]:
                item["sous"][-1] += " " + texte
            else:
                item["texte"] += " " + texte
        elif courant is not None and courant["type"] == "p" and not vide:
            courant["texte"] += " " + ligne.strip()
        else:
            courant = {"type": "p", "texte": ligne.strip()}
            resultat.append(courant)
        vide = False
    return [_rendre(b) for b in resultat]


def _rendre(b: dict[str, Any]) -> dict[str, Any]:
    """Un bloc lu, mis en segments typés pour la page."""
    if b["type"] == "p":
        return {"type": "p", "s": seg(b["texte"])}
    if b["type"] == "liste":
        return {
            "type": "liste",
            "ordonnee": b["ordonnee"],
            "items": [
                {"s": seg(i["texte"]), "sous": [seg(s) for s in i["sous"]],
                 "suite": [seg(s) for s in i["suite"]]}
                for i in b["items"]
            ],
        }  # fmt: skip
    rangs = b["rangs"]
    lignes = [r for r in rangs[1:] if not set("".join(r)) <= set("-: ")]
    return {
        "type": "tableau", "entetes": rangs[0],
        "lignes": [
            [{"s": seg(c), "e": etat(c) if i and colorer(r) else ""} for i, c in enumerate(r)]
            for r in lignes
        ],
    }  # fmt: skip


def en_clair(corps: str) -> dict[str, str]:
    """Les puces « Clé : texte » de la section « En clair »."""
    resultat: dict[str, str] = {}
    for item in blocs(corps):
        if item["type"] != "liste":
            continue
        for i in item["items"]:
            texte = "".join(s.get("t", "") or s.get("code", "") or s.get("a", "") or s.get("b", "")
                            for s in i["s"])  # fmt: skip
            cle, _, valeur = texte.partition(" : ")
            resultat[cle.strip()] = valeur.strip()
    return resultat


def parties(corps: str) -> dict[str, Any]:
    """Une section découpée par ses titres de niveau 3 : l'introduction, puis chaque partie."""
    morceaux = re.split(r"^### (.+)$", corps, flags=re.M)
    return {
        "intro": blocs(morceaux[0]) if morceaux[0].strip() else [],
        "parties": [
            {"titre": morceaux[i].strip(), "blocs": blocs(morceaux[i + 1])}
            for i in range(1, len(morceaux), 2)
        ],
    }


def mesure_recente(dossier: Path) -> dict[str, Any]:
    fichiers = sorted((dossier / "mesures").glob("azure-speech-*.json"))
    if not fichiers:
        raise SystemExit("Aucune mesure dans mesures/ : lancer eval/c7/mesurer_voix.py.")
    d = json.loads(fichiers[-1].read_text(encoding="utf-8"))
    return {
        "fichier": fichiers[-1].name, "date": d["date"], "passages": d["passages"],
        "cout": d["cout_estime_eur"], "resultats": d["resultats"],
    }  # fmt: skip


def donnees(dossier: Path = DOSSIER) -> dict[str, Any]:
    texte = (dossier / "rapport.md").read_text(encoding="utf-8")
    titre = texte.split("\n", 1)[0].lstrip("# ").strip()
    en_tete = texte.split("\n## ", 1)[0].split("\n", 1)[1]
    s = sections(texte)
    clair = en_clair(s.get("En clair", ""))
    reponse = []
    for b in blocs(s.get("Réponse courte", "")):
        if b["type"] == "tableau":
            for ligne in b["lignes"]:
                categorie = "".join(x.get("t", "") for x in ligne[0]["s"])
                reponse.append({
                    "categorie": categorie, "recommandation": ligne[1]["s"],
                    "condition": ligne[2]["s"], "clair": clair.get(categorie, ""),
                })  # fmt: skip
    categories: list[dict[str, Any]] = []
    for ident, nom, releve in CATEGORIES:
        corps = blocs(s.get(nom, ""))
        grille = next((b for b in corps if b["type"] == "tableau"), None)
        categories.append({
            "id": ident, "titre": nom, "grille": grille,
            "blocs": [b for b in corps if b is not grille], "releve": DEPOT + "releves/" + releve,
        })  # fmt: skip
    titre_mesure = next(k for k in s if k.startswith("Mesure du service en place"))
    decisions = sorted(set(re.findall(r"\(D-\d+\)", texte)))
    return {
        "titre": titre,
        "en_tete": [seg(" ".join(p.split())) for p in re.split(r"\n\s*\n", en_tete) if p.strip()],
        "chapeau_clair": clair.get("Chapeau", ""),
        "mesure_clair": clair.get("Mesure", ""),
        "reponse": reponse,
        "referentiel": parties(s.get("Selon le référentiel", "")),
        "regles": blocs(s.get("Règles d'application de la grille", "")),
        "mesure": {
            "titre": titre_mesure,
            "blocs": blocs(s[titre_mesure]),
            **mesure_recente(dossier),
        },
        "categories": categories,
        "ecarts": blocs(s.get("Écarts au protocole", "")),
        "limites": blocs(s.get("Limites", "")),
        "decisions": [d.strip("()") for d in decisions],
        "services": sum(len(c["grille"]["entetes"]) - 1 for c in categories if c["grille"]),
        "depot": DEPOT,
    }


def page(d: dict[str, Any], modele: Path = MODELE) -> str:
    """La page autonome : charte commune et données insérées (`infra/vitrine/assemblage.py`)."""
    return str(_assemblage.page(d, modele))


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
