"""Les deux outils de l'agent, en lecture seule, par l'API des référentiels (D-37, A-6).

L'agent n'a accès à aucune base : chaque outil appelle un point de l'API des référentiels. Ne
part vers l'outil que le strict nécessaire : un nom de commune et un code postal, ou un mot et un
métier ; jamais le nom du client ni la transcription (dossier V1, § 3.1). Un outil inconnu, des
arguments illisibles ou un outil indisponible donnent une réponse d'erreur au modèle, jamais une
exception : l'agent garde la main.

Chaque appel rend deux choses : le texte compact remis au modèle, et ce que le serveur retient
pour ses propres contrôles (communes et termes rendus, règle contre l'invention, D-37).
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from muninn.observabilite import tracer

journal = logging.getLogger(__name__)

NOMS_OUTILS = frozenset({"chercher_communes", "chercher_terme_metier"})
# Nom composé dont le complément suit un article ou une préposition : « X-la-Y », « X-sous-Y ».
MOTIF_NOM_COMPOSE = re.compile(r"^(.+?)[- ](?:la|le|les|sous|sur|lès|lez|en)[- ].+$", re.IGNORECASE)
OUTIL_INCONNU = {"erreur": "outil inconnu ; outils : chercher_communes, chercher_terme_metier"}


@dataclass(frozen=True)
class CommuneRendue:
    """Une commune rendue par un outil pendant l'extraction (données publiques du COG)."""

    code_insee: str
    nom: str
    departement: str
    codes_postaux: tuple[str, ...]


@dataclass
class ResultatOutil:
    """Résultat d'un appel : le texte pour le modèle, et ce que garde le serveur."""

    nom: str
    statut: str
    contenu: str
    duree_ms: int
    communes: list[CommuneRendue] = field(default_factory=list)
    terme: str | None = None


class Referentiels(Protocol):
    """Accès en lecture aux référentiels : l'API en production, un double dans les tests."""

    def communes(self, corps: dict[str, str]) -> dict[str, Any]: ...

    def termes(self, corps: dict[str, str]) -> dict[str, Any]: ...


class ClientReferentiels:
    """Client HTTP de l'API des référentiels, avec un délai par appel (dossier V1, § 3.4)."""

    def __init__(self, url: str, delai_s: float = 5.0, client: httpx.Client | None = None) -> None:
        self._url = url.rstrip("/")
        self._client = client or httpx.Client(timeout=httpx.Timeout(delai_s, connect=2.0))

    def _post(self, chemin: str, corps: dict[str, str]) -> dict[str, Any]:
        reponse = self._client.post(f"{self._url}{chemin}", json=corps)
        reponse.raise_for_status()
        donnees: dict[str, Any] = reponse.json()
        return donnees

    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        return self._post("/v1/referentiels/communes", corps)

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        return self._post("/v1/referentiels/termes", corps)


def _texte(valeur: object) -> str | None:
    return valeur.strip() if isinstance(valeur, str) and valeur.strip() else None


@tracer(
    lambda referentiels, nom, arguments_json: nom if nom in NOMS_OUTILS else "outil_inconnu",
    "tool",
    lambda r: {"statut": r.statut, "duree_ms": r.duree_ms, "communes": len(r.communes)},
)
def executer_outil(referentiels: Referentiels, nom: str, arguments_json: str) -> ResultatOutil:
    """Exécute un appel d'outil demandé par le modèle ; ne lève jamais d'exception."""
    debut = time.perf_counter()

    def resultat(statut: str, contenu: dict[str, Any], **autres: Any) -> ResultatOutil:
        duree = round((time.perf_counter() - debut) * 1000)
        journal.info(
            "agent.outil nom=%s statut=%s duree_ms=%s",
            nom if nom in NOMS_OUTILS else "inconnu",
            statut,
            duree,
        )
        return ResultatOutil(
            nom=nom,
            statut=statut,
            contenu=json.dumps(contenu, ensure_ascii=False),
            duree_ms=duree,
            **autres,
        )

    if nom not in NOMS_OUTILS:
        return resultat(
            "outil_inconnu",
            OUTIL_INCONNU,
        )
    try:
        arguments = json.loads(arguments_json or "{}")
        if not isinstance(arguments, dict):
            raise ValueError
    except ValueError:
        return resultat("arguments_illisibles", {"erreur": "arguments illisibles"})

    try:
        if nom == "chercher_communes":
            corps = {k: v for k in ("nom", "code_postal") if (v := _texte(arguments.get(k)))}
            if not corps:
                return resultat(
                    "arguments_illisibles", {"erreur": "donner un nom de commune ou un code postal"}
                )
            donnees = referentiels.communes(corps)
            principal = None
            if donnees.get("statut") == "hors_corpus" and "nom" in corps:
                # Nom usuel non officiel (« X-la-Y », « X-sous-Y ») : aucune commune ne le porte ;
                # l'outil cherche le nom principal et le dit. Le complément dit reste un indice.
                trouve = MOTIF_NOM_COMPOSE.match(corps["nom"])
                if trouve:
                    principal = trouve.group(1)
                    secours = referentiels.communes(corps | {"nom": principal})
                    if secours.get("candidates"):
                        donnees = secours
                    else:
                        principal = None
            communes = [
                CommuneRendue(
                    code_insee=str(c["code_insee"]),
                    nom=str(c["nom"]),
                    departement=str(c["departement"]),
                    codes_postaux=tuple(str(cp) for cp in c.get("codes_postaux") or []),
                )
                for c in donnees.get("candidates") or []
            ]
            contenu = {
                "statut": donnees.get("statut"),
                "candidates": [
                    {
                        "nom": c.nom,
                        "code_insee": c.code_insee,
                        "departement": c.departement,
                        "codes_postaux": list(c.codes_postaux),
                    }
                    for c in communes
                ],
            }
            if principal:
                contenu["nom_principal"] = principal
                contenu["note"] = "aucune commune ne porte le nom dit : candidates du nom principal"
            return resultat(str(donnees.get("statut")), contenu, communes=communes)

        mot, metier = _texte(arguments.get("mot")), _texte(arguments.get("metier"))
        if not mot or not metier:
            return resultat("arguments_illisibles", {"erreur": "donner un mot et un métier"})
        donnees = referentiels.termes({"mot": mot, "metier": metier})
        terme = (donnees.get("terme") or {}).get("terme")
        contenu = {
            "statut": donnees.get("statut"),
            "terme": terme,
            "similarite": (donnees.get("terme") or {}).get("similarite"),
        }
        return resultat(str(donnees.get("statut")), contenu, terme=terme)
    except httpx.TimeoutException:
        return resultat("delai_depasse", {"erreur": "référentiel indisponible (délai dépassé)"})
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return resultat("indisponible", {"erreur": "référentiel indisponible"})
    except Exception as erreur:  # noqa: BLE001 (l'agent garde la main, quelle que soit la panne)
        journal.warning("agent.outil_erreur type=%s", type(erreur).__name__)
        return resultat("indisponible", {"erreur": "référentiel indisponible"})
