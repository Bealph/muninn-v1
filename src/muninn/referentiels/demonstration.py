"""Commande `muninn-questions` : rejoue le jeu de questions de démonstration contre une API.

Usage : `muninn-questions https://<api>` (ou `http://127.0.0.1:8000` en local). Pour chaque
question : le statut attendu, les valeurs attendues dans la réponse, la source qui doit être
citée. Code de sortie 1 au premier écart : sert de contrôle après un chargement en production.
"""

import json
import sys
from pathlib import Path
from typing import Any

import httpx

FICHIER = Path(__file__).parent / "questions_demonstration.json"


def questions() -> list[dict[str, Any]]:
    resultat: list[dict[str, Any]] = json.loads(FICHIER.read_text(encoding="utf-8"))["questions"]
    return resultat


def poser(client: httpx.Client, question: dict[str, Any]) -> dict[str, Any]:
    if question["point"] == "marche":
        reponse = client.get(f"/v1/referentiels/marche/{question['corps']['metier']}")
    else:
        reponse = client.post(f"/v1/referentiels/{question['point']}", json=question["corps"])
    reponse.raise_for_status()
    donnees: dict[str, Any] = reponse.json()
    return donnees


def ecarts(question: dict[str, Any], reponse: dict[str, Any]) -> list[str]:
    """Ce qui manque à la réponse pour être celle attendue."""
    trouves = []
    if reponse.get("statut") != question["statut"]:
        trouves.append(f"statut {reponse.get('statut')} au lieu de {question['statut']}")
    texte = json.dumps(reponse, ensure_ascii=False)
    trouves += [f"« {v} » absent" for v in question["contient"] if v not in texte]
    sources = {s.get("source_id") for s in reponse.get("sources", [])}
    if question["source"] is not None and question["source"] not in sources:
        trouves.append(f"source {question['source']} non citée")
    return trouves


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    adresse = (argv if argv is not None else sys.argv[1:])[0]
    echecs = 0
    with httpx.Client(base_url=adresse, timeout=httpx.Timeout(60.0)) as client:
        for q in questions():
            trouves = ecarts(q, poser(client, q))
            echecs += bool(trouves)
            etat = "ok" if not trouves else "ÉCART : " + " ; ".join(trouves)
            print(
                f"{q['id']} {q['nature']:<26} {json.dumps(q['corps'], ensure_ascii=False)} : {etat}"
            )
    print(f"{len(questions()) - echecs} sur {len(questions())} conformes")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
