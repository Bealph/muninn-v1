"""Écran « Qualité » rendu avec une API simulée (tests de l'écran et de son accessibilité)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi.testclient import TestClient

from muninn.api.agent import Qualite
from muninn.console.main import app as console
from muninn.console.main import get_client_api
from muninn.traitements.etat import Episode, evaluer
from muninn.traitements.metriques import Compte, CoutMois, DernierAppel, Metriques, Point

VERSION = {"version": "0.1.0", "git_sha": "abc1234", "environment": "production"}
HEURE = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
DERNIER_ID = "4d7f6794-0f42-44e8-8372-e90b3bd931a8"


EPISODE = Episode(
    code="AL-01",
    court="dossiers à vérifier",
    debut=datetime(2026, 10, 22, 14, 5, tzinfo=UTC),
    fin=datetime(2026, 10, 22, 14, 50, tzinfo=UTC),
    en_cours=False,
    pire="45 % (10 sur 22)",
)


def qualite(
    episodes: list[Episode] | None = None, juge: datetime | None = None, **valeurs: Any
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "fenetre_heures": 24, "total": 30, "dossiers": 25, "messages": 4, "traces": 0,
        "refus": 1, "taux_refus": 0.0333, "secours": 0, "relances": 1, "taux_erreur": 0.04,
        "part_secours": 0.0,
        "bornes": 0, "a_verifier": 3, "part_a_verifier": 0.12, "securite": 1,
        "non_controle": 1, "part_non_controle": 0.04, "latence_p50_ms": 2710,
        "latence_p95_ms": 5671, "cout_moyen_eur": 0.003232, "cout_total_eur": 0.0969,
        "dossiers_valides": 3, "champs_corriges": 4,
        "corrections_par_champ": [Compte(nom="client.adresse.code_postal", nombre=3),
                                  Compte(nom="client.nom", nombre=1)],
        "garde_fous": [Compte(nom="gaz", nombre=1), Compte(nom="invention", nombre=2)],
        "premier": datetime(2026, 10, 23, 8, tzinfo=UTC),
        "dernier": datetime(2026, 10, 23, 10, tzinfo=UTC),
        "dernier_appel": DernierAppel(
            request_id=DERNIER_ID, scenario_id="SC-10", issue="dossier", duree_ms=3766,
            recu_le=datetime(2026, 10, 1, 10, tzinfo=UTC),  # ancien : pas d'actualisation
        ),
        # Trois heures avec des appels sur les cinq dernières : deux heures creuses.
        "serie": [Point(heure=HEURE - timedelta(hours=h), total=10 - h, dossiers=8 - h,
                        a_verifier=h, refus=0, secours=0, latence_p95_ms=5000)
                  for h in (0, 1, 4)],
    }  # fmt: skip
    m = Metriques(**(base | valeurs))
    heure = Metriques(**(base | valeurs | {"fenetre_heures": 1}))
    cout = CoutMois(mois="10/2026", total_eur=1.2345, projection_eur=1.66, budget_eur=60.0,
                    part_budget=0.0277)  # fmt: skip
    return Qualite(
        **m.model_dump(),
        etat=evaluer(heure, juge, episodes),
        cout_mois=cout,
        calcule_le=datetime(2026, 10, 23, 14, 0, 12, tzinfo=UTC),
    ).model_dump(mode="json")


def rendre_qualite(
    corps: dict[str, Any] | None = None, statut: int = 200, chemin: str = "/qualite"
) -> tuple[str, list[httpx.Request]]:
    """L'écran rendu pour une réponse de l'API donnée (corps JSON, ou code d'erreur)."""
    demandes: list[httpx.Request] = []

    def repondre(requete: httpx.Request) -> httpx.Response:
        demandes.append(requete)
        if requete.url.path == "/version":
            return httpx.Response(200, json=VERSION)
        if statut != 200:
            return httpx.Response(statut, json={"code": "service_unavailable"})
        return httpx.Response(200, json=corps)

    client = httpx.Client(transport=httpx.MockTransport(repondre), base_url="http://api")
    console.dependency_overrides[get_client_api] = lambda: client
    try:
        return TestClient(console).get(chemin).text, demandes
    finally:
        console.dependency_overrides.pop(get_client_api, None)
