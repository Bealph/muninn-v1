"""Point d'entrée de la console de démonstration (ADR-09 : processus séparé de l'API).

La console ne parle qu'à l'API, jamais directement au LLM.
"""

import json
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

import httpx
from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from muninn import __version__
from muninn.core.config import get_settings

app = FastAPI(title="Muninn console", version=__version__)
gabarits = Jinja2Templates(directory=Path(__file__).parent / "templates")


def date_lisible(valeur: str) -> str:
    """Date lisible : « 15/10/2026 à 14:12 UTC » pour un instant, « 01/10/2026 » pour une date."""
    try:
        instant = datetime.fromisoformat(valeur)
    except (TypeError, ValueError):
        return str(valeur)
    if len(valeur) <= 10:
        return f"{instant:%d/%m/%Y}"
    return f"{instant.astimezone(UTC):%d/%m/%Y à %H:%M} UTC"


gabarits.env.filters["date_lisible"] = date_lisible

# Champs que l'artisan peut corriger avant de valider (V-09, CA-5), dans l'ordre de l'écran.
CHAMPS_CORRIGEABLES = (
    "client.nom",
    "client.prenom",
    "client.telephone",
    "client.adresse.rue",
    "client.adresse.code_postal",
    "client.adresse.commune",
    "demande.objet_court",
    "demande.urgence",
)


def valeurs_corrigeables(brouillon: dict[str, Any]) -> dict[str, str]:
    """Valeur actuelle de chaque champ corrigeable, en texte ; vide si absente."""
    vus: dict[str, str] = {}
    for chemin in CHAMPS_CORRIGEABLES:
        noeud: Any = brouillon
        for cle in chemin.split("."):
            noeud = noeud.get(cle) if isinstance(noeud, dict) else None
        valeur = noeud.get("value") if isinstance(noeud, dict) else noeud
        vus[chemin] = "" if valeur is None else str(valeur)
    return vus


gabarits.env.globals["origine_json"] = lambda d: json.dumps(
    valeurs_corrigeables(d), ensure_ascii=False
)


def get_client_api() -> Iterator[httpx.Client]:
    """Client HTTP vers l'API ; remplacé dans les tests par un client branché sur l'API."""
    with httpx.Client(
        base_url=get_settings().api_base_url, timeout=httpx.Timeout(40.0, connect=5.0)
    ) as client:
        yield client


ClientAPI = Annotated[httpx.Client, Depends(get_client_api)]


def _version_api(client: httpx.Client) -> dict[str, Any]:
    try:
        reponse = client.get("/version")
        reponse.raise_for_status()
        donnees: dict[str, Any] = reponse.json()
        return donnees
    except (httpx.HTTPError, ValueError):
        return {"version": "injoignable", "git_sha": "injoignable", "environment": "inconnu"}


def _page(request: Request, client: httpx.Client, **contexte: Any) -> HTMLResponse:
    settings = get_settings()
    return gabarits.TemplateResponse(
        request,
        "accueil.html",
        {
            "api": _version_api(client),
            "console": {"version": __version__, "git_sha": settings.git_sha},
            "page": "accueil",
            "question": "",
            "modele": "A",
            **contexte,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que le processus répond."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def accueil(request: Request, client: ClientAPI) -> HTMLResponse:
    """Page d'essai : version livrée et formulaire d'appel au LLM."""
    return _page(request, client)


@app.post("/essai", response_class=HTMLResponse)
def essai(
    request: Request,
    client: ClientAPI,
    question: Annotated[str, Form(min_length=1, max_length=500)],
    modele: Annotated[str, Form(pattern="^[AB]$")] = "A",
) -> HTMLResponse:
    """Transmet la question à l'API et affiche la réponse du LLM."""
    resultat: dict[str, Any] | None = None
    erreur: str | None = None
    try:
        reponse = client.post("/llm/essai", json={"question": question, "modele": modele})
        if reponse.status_code == 200:
            resultat = reponse.json()
        else:
            erreur = str(reponse.json().get("detail", f"Erreur {reponse.status_code}."))
    except (httpx.HTTPError, ValueError):
        erreur = "L'API est injoignable."
    return _page(
        request, client, question=question, modele=modele, resultat=resultat, erreur=erreur
    )


METIERS = ("plomberie", "chauffage", "electricite", "serrurerie", "autre")
LIBELLES = {
    "trouve": "Réponse tirée des données",
    "hors_corpus": "Refus : hors des données",
    "hors_perimetre": "Refus : hors du périmètre",
    "incoherent": "Nom et code postal incohérents",
}
TRANCHES = {
    "NN": "non employeur",
    "00": "0 salarié",
    "employer": "employeur",
    "empty": "non renseignée",
}
FORMES = {"ei": "entrepreneur individuel", "sarl": "SARL", "sas": "SAS", "other": "autre"}


def _page_referentiels(request: Request, **contexte: Any) -> HTMLResponse:
    valeurs: dict[str, Any] = {
        "page": "referentiels",
        "metiers": METIERS,
        "libelles": LIBELLES,
        "tranches": TRANCHES,
        "formes": FORMES,
        "nom": "",
        "code_postal": "",
        "mot": "",
        "metier": "plomberie",
        "metier_marche": "plomberie",
        "resultat": None,
        "rappel": None,
        "nationaux": None,
        "erreur": None,
    }
    return gabarits.TemplateResponse(request, "referentiels.html", valeurs | contexte)


def _interroger(appel: Callable[[], httpx.Response]) -> tuple[dict[str, Any] | None, str | None]:
    """Appelle l'API ; rend sa réponse, ou un message d'erreur lisible."""
    try:
        reponse = appel()
        donnees: dict[str, Any] = reponse.json()
    except (httpx.HTTPError, ValueError):
        return None, "L'API est injoignable."
    if reponse.status_code == 200:
        return donnees, None
    detail = donnees.get("detail", f"Erreur {reponse.status_code}.")
    if isinstance(detail, list):  # erreur de validation : premier message, en clair
        message = str(detail[0].get("msg", "valeur invalide")).removeprefix("Value error, ")
        detail = "Entrée refusée : " + message
    return None, str(detail)


@app.get("/referentiels", response_class=HTMLResponse)
def referentiels(request: Request) -> HTMLResponse:
    """Écran des référentiels (D-57) : questions aux données, sources citées, refus motivés."""
    return _page_referentiels(request)


@app.post("/referentiels/commune", response_class=HTMLResponse)
def referentiels_commune(
    request: Request,
    client: ClientAPI,
    nom: Annotated[str, Form(max_length=120)] = "",
    code_postal: Annotated[str, Form(max_length=5)] = "",
) -> HTMLResponse:
    corps = {k: v.strip() for k, v in (("nom", nom), ("code_postal", code_postal)) if v.strip()}
    resultat, erreur = _interroger(lambda: client.post("/v1/referentiels/communes", json=corps))
    rappel = " ; ".join(
        f"{libelle} « {valeur} »"
        for libelle, valeur in (("commune", nom.strip()), ("code postal", code_postal.strip()))
        if valeur
    )
    return _page_referentiels(
        request,
        nom=nom,
        code_postal=code_postal,
        resultat=resultat,
        erreur=erreur,
        rappel=rappel or "aucune valeur",
    )


@app.post("/referentiels/terme", response_class=HTMLResponse)
def referentiels_terme(
    request: Request,
    client: ClientAPI,
    mot: Annotated[str, Form(min_length=1, max_length=80)],
    metier: Annotated[str, Form(max_length=40)] = "plomberie",
) -> HTMLResponse:
    corps = {"mot": mot, "metier": metier}
    resultat, erreur = _interroger(lambda: client.post("/v1/referentiels/termes", json=corps))
    return _page_referentiels(
        request,
        mot=mot,
        metier=metier,
        resultat=resultat,
        erreur=erreur,
        rappel=f"mot « {mot} », métier {metier}",
    )


@app.get("/referentiels/marche", response_class=HTMLResponse)
def referentiels_marche(
    request: Request, client: ClientAPI, metier: Annotated[str, Query(max_length=40)]
) -> HTMLResponse:
    resultat, erreur = _interroger(
        lambda: client.get(f"/v1/referentiels/marche/{quote(metier, safe='')}")
    )
    nationaux = (
        [c for c in resultat["comptages"] if c["department_code"] == "FR"] if resultat else None
    )
    return _page_referentiels(
        request,
        metier_marche=metier,
        resultat=resultat,
        nationaux=nationaux,
        erreur=erreur,
        rappel=f"marché, métier {metier}",
    )


# --- Écran « Agent » (D-62, sprint 4, étape 8) -------------------------------------------------

DELAI_EXECUTION_S = 90.0  # une exécution appelle le modèle plusieurs fois, plus les outils
MESSAGES_GARDES = 10
REFUS_DU_SCENARIO = ("content_refused", "content_unprocessable", "validation_failed")
GROUPES = {
    "annexe_a": "Annexe A : extraction du dossier",
    "qualification": "Qualification des appels (CA-7)",
    "perimetre": "Périmètre d'accès (P4, modèle simulé)",
}
CATEGORIES = {
    "demande_service": "demande de service",
    "indetermine": "indéterminé",
    "fournisseur": "fournisseur",
    "personnel": "personnel",
    "autre": "autre (démarchage, erreur)",
}
GARDE_FOUS = {
    "gaz": "gaz : urgence de sécurité, orientation en tête",
    "sante": "santé : information retirée",
    "invention": "invention : valeur non dite retirée",
    "detournement": "détournement suspecté",
    "fuite": "fuite : texte vidé",
    "hors_role": "hors rôle : lien ou balisage retiré",
}
MOTIFS = {
    "extraction_incomplete": "extraction incomplète",
    "brouillon_de_secours": "brouillon de secours",
    "commune_ambigue": "commune ambiguë",
    "code_postal_ambigu": "code postal ambigu",
    "incoherent": "commune et code postal incohérents",
    "commune_inconnue": "commune inconnue",
    "non_controle": "contrôle impossible",
    "invention_retiree": "invention retirée",
    "detournement_suspect": "détournement suspect",
    "champ_incertain": "champ clé incertain",
    "choix_sans_indice": "choix entre homonymes sans indice",
    "qualification_indeterminee": "qualification indéterminée",
    "fuite_retiree": "fuite retirée",
}
CHAMPS_MESSAGE = (
    "categorie",
    "nom_appelant",
    "societe",
    "numero_rappel",
    "numero_dicte",
    "message",
    "rappel_souhaite",
    "securite",
    "recu_le",
)


def _scenarios(client: httpx.Client) -> list[dict[str, Any]]:
    """Liste des scénarios, demandée à l'API (la console ne parle qu'à l'API)."""
    donnees, _ = _interroger(lambda: client.get("/v1/demo/scenarios"))
    return list(donnees["scenarios"]) if donnees else []


def _messages_recus(brut: str) -> list[dict[str, Any]]:
    """Messages des exécutions précédentes, renvoyés par le formulaire : rien n'est stocké."""
    try:
        valeur = json.loads(brut) if brut else []
    except ValueError:
        return []
    if not isinstance(valeur, list):
        return []
    return [{k: m.get(k) for k in CHAMPS_MESSAGE} for m in valeur if isinstance(m, dict)][
        :MESSAGES_GARDES
    ]


def _executer(
    client: httpx.Client, corps: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Une exécution de `/v1/demo/runs` ; rend la réponse, ou l'erreur au format du contrat."""
    try:
        reponse = client.post("/v1/demo/runs", json=corps, timeout=DELAI_EXECUTION_S)
        donnees: dict[str, Any] = reponse.json()
    except (httpx.HTTPError, ValueError):
        return None, {"code": "api_unreachable", "message": "L'API est injoignable."}
    if reponse.status_code == 200:
        return donnees, None
    return None, {
        "code": donnees.get("code", f"http_{reponse.status_code}"),
        "message": donnees.get("message", f"Erreur {reponse.status_code}."),
        "request_id": donnees.get("request_id"),
        "retry_after_s": donnees.get("retry_after_s"),
    }


def _message_resume(run: dict[str, Any]) -> dict[str, Any] | None:
    m = run.get("message")
    return {k: m.get(k) for k in CHAMPS_MESSAGE} if m else None


def _page_agent(request: Request, client: httpx.Client, **contexte: Any) -> HTMLResponse:
    messages: list[dict[str, Any]] = contexte.pop("messages", [])
    valeurs: dict[str, Any] = {
        "page": "agent",
        "scenarios": _scenarios(client),
        "groupes": GROUPES,
        "categories": CATEGORIES,
        "garde_fous": GARDE_FOUS,
        "motifs": MOTIFS,
        "metiers": METIERS,
        "mode": "scenario",
        "scenario_id": "SC-01",
        "transcript": "",
        "trade": "plomberie",
        "caller_number": "",
        "run": None,
        "revue": None,
        "erreur": None,
        "lot": None,
        "messages": messages,
        "messages_json": json.dumps(messages, ensure_ascii=False),
    }
    return gabarits.TemplateResponse(request, "agent.html", valeurs | contexte)


@app.get("/agent", response_class=HTMLResponse)
def agent(request: Request, client: ClientAPI) -> HTMLResponse:
    """Écran « Agent » : un scénario ou un texte, et tout ce que l'agent et le serveur ont fait."""
    return _page_agent(request, client)


@app.post("/agent/executer", response_class=HTMLResponse)
def agent_executer(
    request: Request,
    client: ClientAPI,
    mode: Annotated[str, Form(pattern="^(scenario|transcript)$")] = "scenario",
    scenario_id: Annotated[str, Form(max_length=40)] = "",
    transcript: Annotated[str, Form(max_length=8000)] = "",
    trade: Annotated[str, Form(max_length=40)] = "plomberie",
    caller_number: Annotated[str, Form(max_length=20)] = "",
    messages: Annotated[str, Form(max_length=20_000)] = "",
) -> HTMLResponse:
    """Une exécution : scénario du jeu synthétique, ou transcription saisie."""
    corps: dict[str, Any] = {"mode": mode}
    if mode == "scenario":
        corps["scenario_id"] = scenario_id
    else:
        corps |= {"transcript": transcript, "trade": trade}
        if caller_number.strip():
            corps["caller_number"] = caller_number.strip()
    run, erreur = _executer(client, corps)
    recus = _messages_recus(messages)
    if run and (resume := _message_resume(run)):
        recus = [resume, *recus][:MESSAGES_GARDES]
    return _page_agent(
        request, client, run=run, erreur=erreur, messages=recus, mode=mode,
        scenario_id=scenario_id, transcript=transcript, trade=trade, caller_number=caller_number,
    )  # fmt: skip


@app.post("/agent/valider", response_class=HTMLResponse)
def agent_valider(
    request: Request,
    client: ClientAPI,
    draft_id: Annotated[str, Form(pattern=r"^[0-9a-f-]{36}$")],
    origine: Annotated[str, Form(max_length=4000)],
    scenario_id: Annotated[str, Form(max_length=40)] = "",
    messages: Annotated[str, Form(max_length=20_000)] = "",
    nom: Annotated[str, Form(alias="client.nom", max_length=120)] = "",
    prenom: Annotated[str, Form(alias="client.prenom", max_length=120)] = "",
    telephone: Annotated[str, Form(alias="client.telephone", max_length=120)] = "",
    rue: Annotated[str, Form(alias="client.adresse.rue", max_length=120)] = "",
    code_postal: Annotated[str, Form(alias="client.adresse.code_postal", max_length=120)] = "",
    commune: Annotated[str, Form(alias="client.adresse.commune", max_length=120)] = "",
    objet: Annotated[str, Form(alias="demande.objet_court", max_length=120)] = "",
    urgence: Annotated[str, Form(alias="demande.urgence", max_length=20)] = "",
) -> HTMLResponse:
    """Validation par l'artisan : seuls les champs modifiés partent, avec leur nouvelle valeur."""
    saisis = dict(zip(CHAMPS_CORRIGEABLES, (nom, prenom, telephone, rue, code_postal, commune,
                                            objet, urgence), strict=True))  # fmt: skip
    try:
        avant = json.loads(origine)
    except ValueError:
        avant = {}
    if not isinstance(avant, dict):
        avant = {}
    corriges = [
        c for c in CHAMPS_CORRIGEABLES if saisis[c].strip() != str(avant.get(c, "")).strip()
    ]
    corps: dict[str, Any] = {
        "decision": "validated_with_corrections" if corriges else "validated",
        "corrected_fields": corriges,
        "values": {c: saisis[c].strip() or None for c in corriges},
    }
    recus = _messages_recus(messages)
    try:
        reponse = client.post(f"/v1/demo/runs/{draft_id}/review", json=corps,
                              timeout=DELAI_EXECUTION_S)  # fmt: skip
        donnees: dict[str, Any] = reponse.json()
    except (httpx.HTTPError, ValueError):
        erreur: dict[str, Any] = {"code": "api_unreachable", "message": "L'API est injoignable."}
        return _page_agent(request, client, erreur=erreur, messages=recus, scenario_id=scenario_id)
    if reponse.status_code != 200:
        erreur = {
            "code": donnees.get("code", f"http_{reponse.status_code}"),
            "message": donnees.get("message", f"Erreur {reponse.status_code}."),
            "request_id": donnees.get("request_id"),
        }
        return _page_agent(request, client, erreur=erreur, messages=recus, scenario_id=scenario_id)
    return _page_agent(request, client, revue=donnees, messages=recus, scenario_id=scenario_id)


@app.post("/agent/lot", response_class=HTMLResponse)
def agent_lot(
    request: Request,
    client: ClientAPI,
    groupe: Annotated[str, Form(pattern="^(annexe_a|qualification)$")],
    messages: Annotated[str, Form(max_length=20_000)] = "",
) -> HTMLResponse:
    """Joue les 8 scénarios d'un groupe, l'un après l'autre, et rend le bilan de conformité."""
    lignes: list[dict[str, Any]] = []
    recus = _messages_recus(messages)
    arret: dict[str, Any] | None = None
    du_groupe = [s for s in _scenarios(client) if s["groupe"] == groupe]
    for s in du_groupe:
        run, erreur = _executer(client, {"mode": "scenario", "scenario_id": s["id"]})
        if run is None and erreur and erreur["code"] in REFUS_DU_SCENARIO:
            # Un refus est le résultat du scénario, pas une panne : le lot continue.
            lignes.append(
                {
                    "id": s["id"],
                    "libelle": s["libelle"],
                    "issue": "refus",
                    "categorie": None,
                    "conformite": {"compliant": False, "gaps": [f"refus {erreur['code']}"]},
                    "garde_fous": [],
                    "cout": 0,
                    "duree": 0,
                }
            )
            continue
        if run is None:
            arret = (erreur or {}) | {"scenario": s["id"]}
            break
        if resume := _message_resume(run):
            recus = [resume, *recus][:MESSAGES_GARDES]
        q = run.get("qualification") or {}
        cout = (q.get("cost_micro_eur") or 0) + ((run.get("run") or {}).get("cost_micro_eur") or 0)
        lignes.append(
            {
                "id": s["id"],
                "libelle": s["libelle"],
                "issue": run["issue"],
                "categorie": q.get("categorie"),
                "conformite": run.get("conformity") or {},
                "garde_fous": run.get("guardrails", []),
                "cout": cout,
                "duree": run.get("latency_ms", 0),
            }
        )
    lot = {
        "groupe": groupe,
        "lignes": lignes,
        "conformes": sum(bool(ligne["conformite"].get("compliant")) for ligne in lignes),
        "total": len(du_groupe),
        "cout": sum(ligne["cout"] for ligne in lignes),
        "arret": arret,
    }
    return _page_agent(request, client, lot=lot, messages=recus)


# Écran « Qualité » (sprint 5, étape 4 ; V-10, TB-6) : l'état du service en mots, puis les
# chiffres d'une période, tirés de la base par l'API. Aucun contenu d'appel : des nombres, des
# codes et des noms de champs, rendus en français pour un lecteur non développeur.
PERIODES = {1: "la dernière heure", 24: "les dernières 24 heures", 168: "les 7 derniers jours",
            720: "les 30 derniers jours"}  # fmt: skip
NOMS_CHAMPS = {
    "client.nom": "Nom du client",
    "client.prenom": "Prénom du client",
    "client.telephone": "Téléphone du client",
    "client.adresse.rue": "Rue",
    "client.adresse.code_postal": "Code postal",
    "client.adresse.commune": "Commune",
    "demande.objet_court": "Objet de la demande",
    "demande.urgence": "Urgence",
}
NOMS_GARDE_FOUS = {
    "gaz": "Odeur de gaz : orientation vers les secours",
    "sante": "Danger pour la santé : orientation vers les secours",
    "invention": "Information que l'appelant n'a pas donnée, retirée du dossier",
    "detournement": "Tentative de manipuler l'assistant, bloquée",
    "fuite": "Consigne interne de l'assistant qui allait apparaître, retirée",
    "hors_role": "Réponse sans rapport avec le dépannage, retirée",
}
NOMS_ISSUES = {"dossier": "un dossier", "message": "un message pour l'artisan",
               "trace": "un appel sans contenu (numéro et heure seulement)",
               "refus": "un appel écarté avant traitement"}  # fmt: skip


def pluriel(n: int, singulier: str, pluriel_: str) -> str:
    """« 1 dossier », « 3 dossiers », « 0 dossier » : accord du nom au nombre, en français."""
    return f"{n} {singulier if n <= 1 else pluriel_}"


gabarits.env.globals["pluriel"] = pluriel


def _graphique(
    serie: list[dict[str, Any]], heures: int, maintenant: datetime | None = None
) -> dict[str, Any] | None:
    """Barres par heure (appels traités, dont « à vérifier »), sur toute la période : une heure
    sans appel garde sa place, pour que la largeur dise le temps. SVG simple, sans script."""
    if not serie:
        return None
    fin = (maintenant or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    debut = fin - timedelta(hours=heures - 1)
    par_heure = {datetime.fromisoformat(p["heure"]).astimezone(UTC): p for p in serie}
    par_heure = {h: p for h, p in par_heure.items() if debut <= h <= fin}
    if not par_heure:
        return None
    haut = max(p["total"] for p in par_heure.values()) or 1
    largeur = 600 / heures
    barres = []
    for i in range(heures):
        heure = debut + timedelta(hours=i)
        p = par_heure.get(heure)
        if p is None or not p["total"]:
            continue
        barres.append({
            "x": round(i * largeur, 2), "w": round(max(largeur * 0.85, 0.6), 2),
            "h_total": round(p["total"] / haut * 120, 1),
            "h_verifier": round(p["a_verifier"] / haut * 120, 1),
            "titre": f"{heure:%d/%m à %H:00} UTC : {pluriel(p['total'], 'appel', 'appels')}, "
            f"{pluriel(p['a_verifier'], 'dossier à vérifier', 'dossiers à vérifier')}",
        })  # fmt: skip
    if not barres:
        return None
    return {
        "barres": barres, "haut": haut,
        "debut": f"{debut:%d/%m à %H:00}", "fin": f"{fin:%d/%m à %H:59}",
    }  # fmt: skip


@app.get("/qualite", response_class=HTMLResponse)
def qualite(
    request: Request,
    client: ClientAPI,
    heures: Annotated[int, Query()] = 24,
    auto: Annotated[int, Query(ge=0, le=1)] = 0,
) -> HTMLResponse:
    """Écran « Qualité » : le service va-t-il bien ? puis les chiffres de la période choisie."""
    if heures not in PERIODES:
        heures = 24
    q, erreur = None, None
    try:
        reponse = client.get("/v1/demo/quality", params={"heures": heures})
        if reponse.status_code == 200:
            q = reponse.json()
        elif reponse.status_code == 503:
            erreur = "Les chiffres sont indisponibles : la base des traitements ne répond pas."
        else:
            erreur = f"Les chiffres sont indisponibles (erreur {reponse.status_code})."
    except (httpx.HTTPError, ValueError):
        erreur = "L'API est injoignable."
    settings = get_settings()
    return gabarits.TemplateResponse(
        request,
        "qualite.html",
        {
            "page": "qualite", "q": q, "erreur": erreur, "heures": heures, "auto": auto,
            "periodes": PERIODES, "noms_champs": NOMS_CHAMPS,
            "noms_garde_fous": NOMS_GARDE_FOUS, "noms_issues": NOMS_ISSUES,
            "graphique": _graphique(q["serie"], heures) if q else None,
            "api": _version_api(client),
            "console": {"version": __version__, "git_sha": settings.git_sha},
        },
    )  # fmt: skip
