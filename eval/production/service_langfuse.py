"""Nom du service sur les traces Langfuse, avant et après le correctif d'INC-11 (PR n° 202).

Usage : `uv run python eval/production/service_langfuse.py`, depuis la racine du dépôt.
Lecture seule, par l'API publique de Langfuse : les traces les plus récentes, puis celles d'avant
le correctif (du 21 octobre, V-13, au 29 octobre 2026 à 16:56 UTC). Pour un échantillon (les cinq
plus récentes, puis une par jour), affiche la date, l'environnement et le `service.name` de la
ressource. Attendu : `muninn-api` après le correctif, `unknown_service` avant. Les clés viennent
des réglages de l'application et ne sont jamais affichées. Une pause sépare deux appels, et un
429 est repris après le délai indiqué par Langfuse. Résultat du 2 novembre 2026 :
`docs/v1/sprints/sprint-5/incidents/INC-11-service-inconnu-dans-langfuse.md`.
"""

import time
from typing import Any

import httpx

from muninn.core.config import get_settings


def lire(client: httpx.Client, chemin: str, params: dict[str, Any]) -> Any:
    """GET poli : une pause entre deux appels, et reprise après un 429 (Retry-After)."""
    for _ in range(6):
        time.sleep(1.5)
        reponse = client.get(chemin, params=params)
        if reponse.status_code != 429:
            return reponse.raise_for_status().json()
        attente = float(reponse.headers.get("Retry-After", "10"))
        print(f"   limite de débit de Langfuse : pause de {attente:.0f} s")
        time.sleep(attente)
    raise SystemExit("Langfuse limite toujours le débit : relancer dans quelques minutes.")


def chercher(objet: Any, cle: str) -> Any:
    """Première valeur de `cle` trouvée dans un objet JSON imbriqué."""
    if isinstance(objet, dict):
        if cle in objet:
            return objet[cle]
        for valeur in objet.values():
            trouve = chercher(valeur, cle)
            if trouve is not None:
                return trouve
    if isinstance(objet, list):
        for valeur in objet:
            trouve = chercher(valeur, cle)
            if trouve is not None:
                return trouve
    return None


def main() -> None:
    s = get_settings()
    if s.langfuse_public_key is None or s.langfuse_secret_key is None:
        print("Clés Langfuse absentes des réglages : rien à lire.")
        return
    client = httpx.Client(
        base_url=s.langfuse_base_url,
        auth=(s.langfuse_public_key.get_secret_value(), s.langfuse_secret_key.get_secret_value()),
        timeout=30,
    )
    projets = lire(client, "/api/public/projects", {})
    print("Projet :", [p.get("name") for p in projets.get("data", [])])

    recentes = lire(client, "/api/public/traces", {"limit": 50}).get("data", [])
    # Avant le correctif (fusion du 29 octobre, 16:56 UTC), jusqu'à V-13 (21 octobre).
    anciennes = lire(
        client,
        "/api/public/traces",
        {
            "limit": 50,
            "fromTimestamp": "2026-10-21T00:00:00Z",
            "toTimestamp": "2026-10-29T16:56:00Z",
        },
    ).get("data", [])
    lignes = recentes + anciennes
    print(f"Traces lues : {len(recentes)} récentes, {len(anciennes)} avant le correctif")
    # Échantillon : les 5 plus récentes, puis une par jour en remontant.
    vus: set[str] = set()
    echantillon = []
    for i, t in enumerate(lignes):
        jour = (t.get("timestamp") or "")[:10]
        if i < 5 or jour not in vus:
            echantillon.append(t)
            vus.add(jour)
    for t in echantillon:
        obs = lire(client, "/api/public/observations", {"traceId": t["id"], "limit": 5})
        services = {
            str(chercher(o.get("metadata"), "service.name")) for o in obs.get("data", [])
        } or {"aucune observation"}
        print(
            f"{t.get('timestamp', '?')[:19]}Z  env={t.get('environment', '?'):<14}"
            f" service.name={', '.join(sorted(services))}"
        )


if __name__ == "__main__":
    main()
