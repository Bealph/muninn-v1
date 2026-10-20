"""Mesure des règles d'injection sur le jeu figé (sprint 4, étape 5 ; D-63, première couche).

Usage : `uv run python eval/garde_fous/mesure_entree.py`. Aucun appel au modèle, aucun coût.
Mesure le taux de détection sur les phrases hostiles et le taux de faux positifs sur les phrases
légitimes, avec un intervalle de Wilson à 95 %. Jeu et motifs figés avant la mesure (commit
a1cc6fe). Résultat : `eval/garde_fous/mesure_entree.json`.
"""

import json
import math
from pathlib import Path

from muninn.extraction.entree import charger_motifs, controler

DOSSIER = Path(__file__).parent
JEU = DOSSIER / "jeu_entree.json"
Z = 1.96


def wilson(succes: int, total: int) -> tuple[float, float]:
    """Intervalle de score de Wilson, à 95 %, pour une proportion."""
    if total == 0:
        return 0.0, 1.0
    p = succes / total
    centre = (p + Z**2 / (2 * total)) / (1 + Z**2 / total)
    marge = Z * math.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2)) / (1 + Z**2 / total)
    return round(max(0.0, centre - marge), 3), round(min(1.0, centre + marge), 3)


def main() -> None:
    jeu = json.loads(JEU.read_text(encoding="utf-8"))
    version_motifs, _ = charger_motifs()
    lignes = []
    for classe in ("hostiles", "legitimes"):
        for i, texte in enumerate(jeu[classe], start=1):
            lignes.append({"classe": classe, "rang": i, "motifs": controler(texte).motifs})

    def taux(classe: str) -> dict[str, object]:
        sous = [x for x in lignes if x["classe"] == classe]
        n = sum(bool(x["motifs"]) for x in sous)
        return {"detectees": n, "total": len(sous), "taux": round(n / len(sous), 3),
                "ic95": wilson(n, len(sous))}  # fmt: skip

    synthese = {
        "date": "2026-10-19",
        "jeu": jeu["version"],
        "motifs": version_motifs,
        "detection_hostiles": taux("hostiles"),
        "faux_positifs_legitimes": taux("legitimes"),
        "manquees": [x["rang"] for x in lignes if x["classe"] == "hostiles" and not x["motifs"]],
        "faux_positifs": [x["rang"] for x in lignes if x["classe"] == "legitimes" and x["motifs"]],
        "lignes": lignes,
    }
    (DOSSIER / "mesure_entree.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    d, f = synthese["detection_hostiles"], synthese["faux_positifs_legitimes"]
    print(f"Détection : {d['detectees']}/{d['total']} ; IC 95 % {d['ic95']}")
    print(f"Faux positifs : {f['detectees']}/{f['total']} ; IC 95 % {f['ic95']}")
    print(f"Hostiles manquées (rang) : {synthese['manquees']}")
    print(f"Légitimes signalées (rang) : {synthese['faux_positifs']}")


if __name__ == "__main__":
    main()
