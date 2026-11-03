"""Assemblage commun des vitrines de Muninn (veille, benchmark) : une page autonome.

Le modèle d'une vitrine porte trois marques : `/*CHARTE*/` dans sa feuille de style, remplacée par
`charte.css` ; `/*COMMUN_JS*/` dans son script, remplacée par `commun.js` ; `/*DONNEES*/` dans un
`<script type="application/json">`, remplacée par les données en JSON. Une marque de charte ou de
script absente est tolérée (modèle de test) ; la marque des données est obligatoire et unique.
"""

import json
import re
from pathlib import Path
from typing import Any

ICI = Path(__file__).resolve().parent
MARQUE = "/*DONNEES*/"

Segment = dict[str, Any]
_EN_LIGNE = r"`([^`]+)`|\[([^\]]+)\]\((https://[^)\s]+)\)|<(https://[^>\s]+)>"


def segments(texte: str, gras: bool = False) -> list[Segment]:
    """Markdown en ligne -> segments : texte, `code`, [lien](https://…), <https://…>, et
    **gras** si `gras`. Le texte n'est jamais interprété comme du HTML ; seuls les liens en
    `https://` sont gardés."""
    motif = re.compile(_EN_LIGNE + (r"|\*\*([^*]+)\*\*" if gras else ""))
    resultat: list[Segment] = []
    position = 0
    for m in motif.finditer(texte):
        if m.start() > position:
            resultat.append({"t": texte[position : m.start()]})
        if m.group(1) is not None:
            resultat.append({"code": m.group(1)})
        elif m.group(2) is not None:
            resultat.append({"a": m.group(2), "href": m.group(3)})
        elif m.group(4) is not None:
            resultat.append({"a": m.group(4), "href": m.group(4)})
        else:
            # Le gras peut contenir du code ou un lien : ses segments sont découpés à leur tour.
            resultat.append({"b": segments(m.group(5))})
        position = m.end()
    if position < len(texte):
        resultat.append({"t": texte[position:]})
    return resultat


def page(d: dict[str, Any], modele: Path) -> str:
    texte = modele.read_text(encoding="utf-8")
    if texte.count(MARQUE) != 1:
        raise ValueError(f"le modèle doit contenir {MARQUE} une seule fois")
    texte = texte.replace("/*CHARTE*/", (ICI / "charte.css").read_text(encoding="utf-8"))
    texte = texte.replace("/*COMMUN_JS*/", (ICI / "commun.js").read_text(encoding="utf-8"))
    # « < », « > » et « & » échappés : le JSON ne peut ni fermer la balise <script> qui le
    # porte, ni ouvrir un « <!-- » qui ferait avaler le script suivant par l'analyseur HTML.
    charge = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    charge = charge.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return texte.replace(MARQUE, charge)
