"""Format d'erreur du contrat (contrat d'API, § 2.8), identifiant de requête, `no-store`.

S'applique aux routes de l'agent (`/v1/extract`, `/v1/demo`) ; les routes antérieures gardent
leur format, que la console lit déjà. Toute réponse porte `X-Request-Id`. Le message d'erreur est
un texte fixe associé au code : il ne contient jamais un fragment de l'entrée (TA-38) ; `details`
donne le chemin du champ fautif, jamais sa valeur.
"""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

PREFIXES_AGENT = ("/v1/extract", "/v1/demo")
MESSAGES = {
    "validation_failed": "La requête ne respecte pas le contrat.",
    "content_refused": (
        "La demande n'a pas pu être traitée : son contenu a été bloqué par le filtre de modération."
    ),
    "content_unprocessable": "Aucun contenu exploitable : la demande ne peut pas être traitée.",
    "rate_limited": "Trop de demandes : réessayer plus tard.",
    "scenario_not_found": "Scénario inconnu.",
    "draft_not_found": "Dossier inconnu, ou purgé.",
    "conflict": "Ce dossier a déjà été validé.",
    "service_unavailable": "Le service est momentanément indisponible.",
    # Voix simulée (étape 6, D-50).
    "voice_unavailable": "Le service de voix est momentanément indisponible.",
    "audio_too_large": "L'enregistrement dépasse la taille admise.",
    "unsupported_media_type": "Type de contenu non pris en charge : audio/mpeg attendu.",
    "request_timeout": "L'enregistrement n'a pas été reçu à temps.",
}
# Types d'erreur de Pydantic vers les codes fermés du contrat (§ 2.8, `details[].issue`).
ISSUES = {
    "missing": "required",
    "string_too_long": "too_long",
    "too_long": "too_long",
    "extra_forbidden": "unknown_field",
    "greater_than_equal": "out_of_range",
    "less_than_equal": "out_of_range",
}


class DetailErreur(BaseModel):
    field: str
    issue: str


class Erreur(BaseModel):
    """Corps de toute réponse 4xx ou 5xx des routes de l'agent."""

    code: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    message: str
    request_id: str
    details: list[DetailErreur] | None = None
    retry_after_s: int | None = None


class ErreurAPI(Exception):
    def __init__(
        self,
        statut: int,
        code: str,
        details: list[DetailErreur] | None = None,
        retry_after_s: int | None = None,
    ) -> None:
        super().__init__(code)
        self.statut, self.code, self.details, self.retry_after_s = (
            statut,
            code,
            details,
            retry_after_s,
        )


def identifiant(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


def reponse_erreur(request: Request, erreur: ErreurAPI) -> JSONResponse:
    corps = Erreur(
        code=erreur.code,
        message=MESSAGES[erreur.code],
        request_id=identifiant(request),
        details=erreur.details,
        retry_after_s=erreur.retry_after_s,
    )
    entetes = {"Retry-After": str(erreur.retry_after_s)} if erreur.retry_after_s else None
    return JSONResponse(
        corps.model_dump(exclude_none=True), status_code=erreur.statut, headers=entetes
    )


def installer(app: FastAPI) -> None:
    """Identifiant de requête, `no-store` et format d'erreur des routes de l'agent."""

    @app.middleware("http")
    async def identifier(
        request: Request, suivant: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = str(uuid.uuid4())
        reponse = await suivant(request)
        reponse.headers["X-Request-Id"] = request.state.request_id
        if request.url.path.startswith(PREFIXES_AGENT):
            reponse.headers["Cache-Control"] = "no-store"
        return reponse

    @app.exception_handler(ErreurAPI)
    async def erreur_api(request: Request, erreur: ErreurAPI) -> JSONResponse:
        return reponse_erreur(request, erreur)

    @app.exception_handler(RequestValidationError)
    async def validation(request: Request, erreur: RequestValidationError) -> Response:
        if not request.url.path.startswith(PREFIXES_AGENT):
            return await request_validation_exception_handler(request, erreur)
        details = [
            DetailErreur(
                field=".".join(str(p) for p in e.get("loc", ())),
                issue=ISSUES.get(str(e.get("type", "")), "bad_format"),
            )
            for e in erreur.errors()[:50]
        ]
        return reponse_erreur(request, ErreurAPI(422, "validation_failed", details))
