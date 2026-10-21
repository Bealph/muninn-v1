"""Accès au LLM derrière une interface de fournisseur (R8, D-32).

Deux fournisseurs : un faux, sans réseau, pour les tests et la CI ; un fournisseur Azure AI
Foundry, qui parle le format OpenAI v1 (`/openai/v1/chat/completions`) pour les deux modèles
retenus (D-44, D-45). Les journaux ne contiennent jamais le texte échangé (R4).

Deux usages :
- `repondre` : une question, une réponse en texte (écran d'essai de la console, sprint 2) ;
- `completer` : une conversation à plusieurs tours, avec appel d'outils et sortie structurée
  par schéma (agent d'extraction, sprint 4). Elle rend les jetons et le coût de l'appel, et
  distingue trois échecs : le refus du filtre de contenu, le délai dépassé, la panne.
"""

import json
import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from muninn.core.config import Settings

journal = logging.getLogger(__name__)

PORTEE_COGNITIVE_SERVICES = "https://cognitiveservices.azure.com/.default"
CONSIGNE_SYSTEME = (
    "Tu es Muninn, le secrétariat automatique d'un artisan. "
    "Réponds en français, en une ou deux phrases."
)

# Prix lus le 16 octobre 2026 dans l'API des prix Azure, zone de données UE, West Europe (banc
# d'essai T-06) : euros par million de jetons, en entrée et en sortie.
TARIFS_EUR_PAR_MILLION: dict[str, tuple[float, float]] = {
    "gpt-5.4-mini": (0.726, 4.3559),
    "mistral-medium-3-5": (1.50, 7.30),
}


@dataclass(frozen=True)
class ReponseLLM:
    """Réponse du LLM, avec ce qu'il faut pour la tracer sans exposer le contenu."""

    texte: str
    modele: str
    fournisseur: str
    duree_ms: int


@dataclass(frozen=True)
class AppelOutil:
    """Un appel d'outil demandé par le modèle ; `arguments` est le JSON brut, non validé."""

    id: str
    nom: str
    arguments: str


@dataclass(frozen=True)
class RequeteChat:
    """Une étape de conversation : messages au format OpenAI v1, outils, schéma de sortie."""

    modele: str
    messages: list[dict[str, Any]]
    outils: list[dict[str, Any]] | None = None
    schema_sortie: dict[str, Any] | None = None
    max_jetons_sortie: int = 4000
    delai_s: float = 30.0


@dataclass(frozen=True)
class ReponseChat:
    """Réponse d'une étape : contenu ou appels d'outils, et ce qu'il faut pour la mesurer."""

    contenu: str | None
    appels_outils: list[AppelOutil]
    raison_fin: str
    modele: str
    fournisseur: str
    duree_ms: int
    jetons_entree: int
    jetons_sortie: int
    cout_micro_eur: int
    detournement_detecte: bool = False
    refus_modele: str | None = None

    def message_assistant(self) -> dict[str, Any]:
        """Le message à remettre dans la conversation avant les réponses des outils."""
        message: dict[str, Any] = {"role": "assistant", "content": self.contenu}
        if self.appels_outils:
            message["tool_calls"] = [
                {
                    "id": a.id,
                    "type": "function",
                    "function": {"name": a.nom, "arguments": a.arguments},
                }
                for a in self.appels_outils
            ]
        return message


def message_outil(appel: AppelOutil, contenu: str) -> dict[str, Any]:
    """Réponse d'un outil, à la forme du schéma de référence : sans champ `name` (Microsoft Learn,
    référence REST v1, lue le 19 octobre 2026), contrairement au banc d'essai T-06."""
    return {"role": "tool", "tool_call_id": appel.id, "content": contenu}


class ErreurFournisseur(Exception):
    """Le fournisseur n'a pas pu répondre ; le message ne contient aucune donnée échangée."""


class DelaiDepasse(ErreurFournisseur):
    """Le modèle n'a pas répondu dans le délai de l'étape."""


class RefusContenu(ErreurFournisseur):
    """Le filtre de contenu du fournisseur a bloqué l'entrée ou la sortie (garde-fou, D-65)."""


def cout_micro_eur(modele: str, jetons_entree: int, jetons_sortie: int) -> int:
    """Coût d'un appel en millionièmes d'euro, au tarif connu du modèle (0 s'il est inconnu)."""
    entree, sortie = TARIFS_EUR_PAR_MILLION.get(modele, (0.0, 0.0))
    return round(jetons_entree * entree + jetons_sortie * sortie)


class FournisseurLLM(Protocol):
    """Contrat commun à tous les fournisseurs."""

    nom: str

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        """Envoie la question au modèle et rend sa réponse."""
        ...

    def completer(self, requete: RequeteChat) -> ReponseChat:
        """Envoie une étape de conversation et rend la réponse du modèle."""
        ...


@dataclass
class FauxFournisseur:
    """Répond sans réseau, de façon déterministe : pour les tests, la CI et le local hors ligne.

    `scenario` programme les réponses de `completer`, dans l'ordre : une `ReponseChat`, ou une
    exception à lever. Sans scénario, `completer` rend un contenu vide (« {} »). Les requêtes
    reçues sont gardées dans `requetes`, pour les tests.
    """

    scenario: Iterable[ReponseChat | Exception] = ()
    requetes: list[RequeteChat] = field(default_factory=list)
    nom: str = "faux"

    def __post_init__(self) -> None:
        self._suite = iter(self.scenario)

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        return ReponseLLM(
            texte=f"Réponse simulée ({len(question)} caractères reçus).",
            modele=modele,
            fournisseur=self.nom,
            duree_ms=0,
        )

    def completer(self, requete: RequeteChat) -> ReponseChat:
        self.requetes.append(requete)
        suivant = next(self._suite, None)
        if isinstance(suivant, Exception):
            raise suivant
        if suivant is not None:
            return suivant
        return reponse_faux(contenu="{}", modele=requete.modele)


def reponse_faux(
    contenu: str | None = None,
    appels: list[tuple[str, dict[str, Any]]] | None = None,
    modele: str = "faux",
    raison_fin: str | None = None,
) -> ReponseChat:
    """Construit une réponse programmée du faux fournisseur : un contenu, ou des appels d'outils."""
    appels_outils = [
        AppelOutil(id=f"appel-{i}", nom=nom, arguments=json.dumps(args, ensure_ascii=False))
        for i, (nom, args) in enumerate(appels or [], start=1)
    ]
    return ReponseChat(
        contenu=contenu,
        appels_outils=appels_outils,
        raison_fin=raison_fin or ("tool_calls" if appels_outils else "stop"),
        modele=modele,
        fournisseur="faux",
        duree_ms=0,
        jetons_entree=0,
        jetons_sortie=0,
        cout_micro_eur=0,
    )


# Reprise d'un appel limité (429) ou indisponible (503) : deux essais de plus au plus, attente
# plafonnée ; au-delà, l'erreur remonte et l'agent rend le brouillon de secours (D-29).
REPRISES_LIMITE = 2
ATTENTE_MAX_S = 10.0


class FournisseurAzure:
    """Azure AI Foundry, déploiement en zone de données UE (R5), API au format OpenAI v1."""

    nom = "azure"

    def __init__(
        self,
        endpoint: str,
        entetes_auth: Callable[[], dict[str, str]],
        client: httpx.Client | None = None,
        max_jetons: int = 300,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._url = endpoint.rstrip("/") + "/openai/v1/chat/completions"
        self._entetes_auth = entetes_auth
        self._client = client or httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0))
        self._max_jetons = max_jetons
        self._dormir = dormir

    def repondre(self, question: str, modele: str) -> ReponseLLM:
        corps = {
            "model": modele,
            "messages": [
                {"role": "system", "content": CONSIGNE_SYSTEME},
                {"role": "user", "content": question},
            ],
            "max_completion_tokens": self._max_jetons,
        }
        debut = time.perf_counter()
        try:
            reponse = self._client.post(self._url, json=corps, headers=self._entetes_auth())
        except httpx.HTTPError as exc:
            journal.warning("llm.echec modele=%s cause=%s", modele, type(exc).__name__)
            raise ErreurFournisseur("Le service du modèle est injoignable.") from exc
        duree_ms = round((time.perf_counter() - debut) * 1000)
        if reponse.status_code != 200:
            journal.warning(
                "llm.echec modele=%s statut=%s duree_ms=%s", modele, reponse.status_code, duree_ms
            )
            raise ErreurFournisseur(f"Le service du modèle a répondu {reponse.status_code}.")
        try:
            donnees = reponse.json()
            texte = str(donnees["choices"][0]["message"]["content"] or "")
            modele_servi = str(donnees.get("model", modele))
            usage = donnees.get("usage", {})
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            journal.warning("llm.echec modele=%s cause=reponse_illisible", modele)
            raise ErreurFournisseur("La réponse du modèle est illisible.") from exc
        journal.info(
            "llm.appel modele=%s duree_ms=%s jetons_entree=%s jetons_sortie=%s",
            modele_servi,
            duree_ms,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return ReponseLLM(texte=texte, modele=modele_servi, fournisseur=self.nom, duree_ms=duree_ms)

    def completer(self, requete: RequeteChat) -> ReponseChat:
        """Un appel au modèle, tracé dans Langfuse comme génération (V-13) : modèle, jetons, coût,
        durée, raison de fin ; messages et réponse sur données synthétiques seulement."""
        from muninn.observabilite import observation

        with observation("llm", "generation", model=requete.modele) as obs:
            try:
                r = self._completer(requete)
            except ErreurFournisseur as erreur:
                obs.maj(level="ERROR", status_message=type(erreur).__name__)
                raise
            obs.maj(
                usage_details={"input": r.jetons_entree, "output": r.jetons_sortie},
                cost_details={"total": r.cout_micro_eur / 1e6},
                metadata={
                    "raison_fin": r.raison_fin,
                    "duree_ms": r.duree_ms,
                    "appels_outils": len(r.appels_outils),
                    "detournement": r.detournement_detecte,
                },  # fmt: skip
                entree=requete.messages,
                sortie=r.contenu,
            )
            return r

    def _completer(self, requete: RequeteChat) -> ReponseChat:
        corps: dict[str, Any] = {
            "model": requete.modele,
            "messages": requete.messages,
            "max_completion_tokens": requete.max_jetons_sortie,
        }
        if requete.outils:
            corps["tools"] = requete.outils
            corps["parallel_tool_calls"] = False
        if requete.schema_sortie is not None:
            corps["response_format"] = {"type": "json_schema", "json_schema": requete.schema_sortie}
        modele = requete.modele
        debut = time.perf_counter()
        for essai in range(1, REPRISES_LIMITE + 2):
            try:
                reponse = self._client.post(
                    self._url,
                    json=corps,
                    headers=self._entetes_auth(),
                    timeout=httpx.Timeout(requete.delai_s, connect=5.0),
                )
            except httpx.TimeoutException as exc:
                journal.warning("llm.echec modele=%s cause=delai_depasse", modele)
                raise DelaiDepasse("Le modèle n'a pas répondu dans le délai.") from exc
            except httpx.HTTPError as exc:
                journal.warning("llm.echec modele=%s cause=%s", modele, type(exc).__name__)
                raise ErreurFournisseur("Le service du modèle est injoignable.") from exc
            if reponse.status_code not in (429, 503) or essai > REPRISES_LIMITE:
                break
            # Limite de débit ou indisponibilité passagère : reprise bornée, selon Retry-After.
            attente = min(_attente(reponse), ATTENTE_MAX_S)
            journal.warning(
                "llm.reprise modele=%s statut=%s essai=%s attente_s=%s",
                modele, reponse.status_code, essai, attente,
            )  # fmt: skip
            self._dormir(attente)
        duree_ms = round((time.perf_counter() - debut) * 1000)
        if reponse.status_code != 200:
            if reponse.status_code == 400 and _code_erreur(reponse) == "content_filter":
                journal.warning(
                    "llm.refus modele=%s cause=filtre_entree duree_ms=%s", modele, duree_ms
                )
                raise RefusContenu("Le filtre de contenu a bloqué la demande.")
            journal.warning(
                "llm.echec modele=%s statut=%s duree_ms=%s", modele, reponse.status_code, duree_ms
            )
            raise ErreurFournisseur(f"Le service du modèle a répondu {reponse.status_code}.")
        try:
            donnees = reponse.json()
            choix = donnees["choices"][0]
            message = choix["message"]
            raison_fin = str(choix.get("finish_reason") or "")
            appels = [
                AppelOutil(
                    id=str(a["id"]),
                    nom=str(a["function"]["name"]),
                    arguments=str(a["function"].get("arguments") or "{}"),
                )
                for a in message.get("tool_calls") or []
            ]
            usage = donnees.get("usage") or {}
            jetons_entree = int(usage.get("prompt_tokens") or 0)
            jetons_sortie = int(usage.get("completion_tokens") or 0)
            modele_servi = str(donnees.get("model") or modele)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            journal.warning("llm.echec modele=%s cause=reponse_illisible", modele)
            raise ErreurFournisseur("La réponse du modèle est illisible.") from exc
        if raison_fin == "content_filter":
            journal.warning("llm.refus modele=%s cause=filtre_sortie duree_ms=%s", modele, duree_ms)
            raise RefusContenu("Le filtre de contenu a bloqué la réponse.")
        detournement = _detournement_annote(donnees)
        cout = cout_micro_eur(modele, jetons_entree, jetons_sortie)
        journal.info(
            "llm.etape modele=%s duree_ms=%s jetons_entree=%s jetons_sortie=%s cout_micro_eur=%s "
            "raison_fin=%s appels_outils=%s detournement=%s",
            modele_servi,
            duree_ms,
            jetons_entree,
            jetons_sortie,
            cout,
            raison_fin,
            len(appels),
            detournement,
        )
        return ReponseChat(
            contenu=message.get("content"),
            appels_outils=appels,
            raison_fin=raison_fin,
            modele=modele_servi,
            fournisseur=self.nom,
            duree_ms=duree_ms,
            jetons_entree=jetons_entree,
            jetons_sortie=jetons_sortie,
            cout_micro_eur=cout,
            detournement_detecte=detournement,
            refus_modele=message.get("refusal"),
        )


def _attente(reponse: httpx.Response) -> float:
    """Attente demandée par le service (Retry-After, en secondes), 2 s à défaut."""
    try:
        return max(0.0, float(reponse.headers.get("Retry-After", "2")))
    except ValueError:
        return 2.0


def _code_erreur(reponse: httpx.Response) -> str | None:
    """Code d'erreur du fournisseur (`error.code`), sans jamais lire le reste du corps."""
    try:
        erreur = reponse.json().get("error") or {}
    except ValueError:
        return None
    code = erreur.get("code") if isinstance(erreur, dict) else None
    return str(code) if code is not None else None


def _detournement_annote(donnees: dict[str, Any]) -> bool:
    """Annotation du filtre réglé en « annoter seulement » (D-65) : tentative de détournement."""
    for resultat in donnees.get("prompt_filter_results") or []:
        jailbreak = (resultat.get("content_filter_results") or {}).get("jailbreak") or {}
        if jailbreak.get("detected") is True:
            return True
    return False


def _entetes_entra() -> Callable[[], dict[str, str]]:
    """Authentification sans secret : identité managée en Azure, az login en local."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    jeton = get_bearer_token_provider(
        DefaultAzureCredential(exclude_interactive_browser_credential=True),
        PORTEE_COGNITIVE_SERVICES,
    )
    return lambda: {"Authorization": f"Bearer {jeton()}"}


def construire_fournisseur(reglages: Settings) -> FournisseurLLM:
    """Choisit le fournisseur selon la configuration."""
    if reglages.llm_fournisseur == "faux":
        return FauxFournisseur()
    if not reglages.azure_ai_endpoint:
        raise ValueError("AZURE_AI_ENDPOINT est requis quand LLM_FOURNISSEUR=azure.")
    cle = reglages.azure_ai_api_key
    if cle is not None and cle.get_secret_value():
        valeur = cle.get_secret_value()
        entetes: Callable[[], dict[str, str]] = lambda: {"api-key": valeur}  # noqa: E731
    else:
        entetes = _entetes_entra()
    return FournisseurAzure(reglages.azure_ai_endpoint, entetes)
