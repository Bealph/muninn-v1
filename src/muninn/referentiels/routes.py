"""API des référentiels (sprint 3, V-05) : réponses ancrées dans les données, sources citées.

Chaque réponse porte un statut :
- `trouve` : la réponse vient des données, chaque valeur avec la table et la clé qui l'attestent ;
- `hors_corpus` : rien dans les données ne répond (commune inconnue, mot sous le seuil) ;
- `hors_perimetre` : la question sort de ce que la V1 couvre (métier sans lexique publié) ;
- `incoherent` : nom et code postal donnés ensemble, mais aucune commune ne les accorde.
Un refus ne contient jamais de valeur inventée. Une entrée mal formée est refusée en 422.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Any, Literal
from urllib.parse import quote

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from muninn.api.limites import LimiteurDebit
from muninn.core.config import get_settings
from muninn.referentiels import depot
from muninn.referentiels.seuil import SEUIL_LEXIQUE

journal = logging.getLogger(__name__)
routeur = APIRouter(prefix="/v1/referentiels", tags=["référentiels"])
Statut = Literal["trouve", "hors_corpus", "hors_perimetre", "incoherent"]
METIERS = ("plomberie", "chauffage", "electricite", "serrurerie", "autre")


@lru_cache
def get_limiteur_referentiels() -> LimiteurDebit:
    """Limite globale des lectures : les points sont publics en démonstration (D-57)."""
    s = get_settings()
    return LimiteurDebit([(60, s.referentiels_limite_minute), (86_400, s.referentiels_limite_jour)])


def limiter(limiteur: Annotated[LimiteurDebit, Depends(get_limiteur_referentiels)]) -> None:
    attente = limiteur.reserver()
    if attente is not None:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de demandes : réessayer dans {attente} s.",
            headers={"Retry-After": str(attente)},
        )


@contextmanager
def ouvrir() -> Iterator[depot.Connexion]:
    """Connexion de lecture ; toute erreur de base devient un 503 sans détail technique.

    Couvre une base indisponible, un délai dépassé, ou des schémas pas encore installés.
    """
    try:
        with depot.connecter() as conn:
            yield conn
    except (depot.BaseIndisponible, psycopg.Error) as erreur:
        journal.warning("referentiels.base_en_erreur type=%s", type(erreur).__name__)
        raise HTTPException(status_code=503, detail="Base des référentiels indisponible.") from (
            erreur
        )


def exiger(version: depot.Version | None, jeu: str) -> depot.Version:
    if version is None:
        raise HTTPException(status_code=503, detail=f"Référentiel « {jeu} » non chargé.")
    return version


class QuestionCommune(BaseModel):
    model_config = ConfigDict(extra="forbid")  # contrat : aucun champ non prévu
    nom: str | None = Field(default=None, min_length=1, max_length=120)
    code_postal: str | None = Field(default=None, pattern=r"^[0-9]{5}$")

    @model_validator(mode="after")
    def au_moins_une_valeur(self) -> "QuestionCommune":
        if self.nom is None and self.code_postal is None:
            raise ValueError("donner un nom de commune, un code postal, ou les deux")
        return self


class Candidate(BaseModel):
    nom: str
    code_insee: str
    departement: str
    codes_postaux: list[str]
    via: str
    references: list[dict[str, str]]


class ReponseCommunes(BaseModel):
    statut: Statut
    motif: str
    candidates: list[Candidate]
    sources: list[dict[str, Any]]


@routeur.post("/communes", dependencies=[Depends(limiter)])
def communes(question: QuestionCommune) -> ReponseCommunes:
    """Communes candidates pour un nom, un code postal, ou les deux (outil `chercher_communes`)."""
    with ouvrir() as conn:
        version_communes = exiger(depot.version_publiee(conn, "communes"), "communes")
        version_codes = exiger(depot.version_publiee(conn, "postal_codes"), "codes postaux")
        trouvees, accord = depot.chercher_communes(
            conn, version_communes, version_codes, question.nom, question.code_postal
        )
    sources = [
        version_communes.citation("ref.communes"),
        version_codes.citation("ref.postal_codes"),
    ]
    candidates = [Candidate(**vars(c)) for c in trouvees]
    if not candidates:
        return ReponseCommunes(
            statut="hors_corpus",
            motif="Aucune commune de ce nom ou de ce code postal dans le COG 2026 et la base"
            " officielle des codes postaux. Aucune valeur n'est proposée.",
            candidates=[],
            sources=sources,
        )
    if not accord:
        return ReponseCommunes(
            statut="incoherent",
            motif=f"Aucune commune de ce nom n'a le code postal {question.code_postal} :"
            " les communes du nom sont listées avec leurs codes postaux.",
            candidates=candidates,
            sources=sources,
        )
    if question.nom is not None and question.code_postal is not None:
        candidates = [c for c in candidates if question.code_postal in c.codes_postaux]
    nombre = len(candidates)
    motif = "Une commune correspond." if nombre == 1 else f"{nombre} communes correspondent."
    return ReponseCommunes(statut="trouve", motif=motif, candidates=candidates, sources=sources)


class QuestionTerme(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mot: str = Field(min_length=1, max_length=80)
    metier: str = Field(min_length=1, max_length=40)


class Terme(BaseModel):
    terme: str
    similarite: float
    categorie: str
    source_id: str
    reference: str
    url: str | None
    licence: str
    references: list[dict[str, str]]


class ReponseTerme(BaseModel):
    statut: Statut
    motif: str
    seuil: float
    terme: Terme | None
    sources: list[dict[str, Any]]


def url_terme(source_id: str, reference: str) -> str | None:
    if source_id == "SRC-12":
        return "https://fr.wiktionary.org/wiki/" + quote(reference.replace(" ", "_"))
    if source_id == "SRC-11":
        return "https://www.wikidata.org/wiki/" + reference
    return None


def citer_source_du_lexique(
    metier: str, lexique: depot.LexiquePublie, source: dict[str, Any]
) -> dict[str, Any]:
    """Cite une source réelle du lexique (Wiktionnaire ou Wikidata), telle que collectée.

    En mode secours, la date est celle de l'instantané versionné, et le mode est dit.
    """
    source_id = str(source["source_id"])
    date_collecte = source.get("recupere_le") or source.get("instantane_du") or ""
    return {
        "jeu": f"lexique {metier}",
        "source_id": source_id,
        **depot.SOURCES[source_id],
        "url": source.get("url"),
        "date_source": source.get("date_source") or date_collecte[:10] or None,
        "charge_le": lexique.publie_le.isoformat(),
        "version": lexique.version,
        "table": "ref.lexicon_terms",
        "mode": source.get("mode", "collecte"),
        "attribution": "titres de pages et libellés repris, définitions non reprises",
    }


@routeur.post("/termes", dependencies=[Depends(limiter)])
def termes(question: QuestionTerme) -> ReponseTerme:
    """Terme du lexique le plus proche d'un mot, pour un métier (outil `chercher_terme_metier`)."""
    if question.metier not in METIERS:
        return ReponseTerme(
            statut="hors_perimetre",
            motif=f"Métier inconnu ; métiers de Muninn : {', '.join(METIERS)}.",
            seuil=SEUIL_LEXIQUE,
            terme=None,
            sources=[],
        )
    with ouvrir() as conn:
        lexique = depot.lexique_publie(conn, question.metier)
        if lexique is None:
            return ReponseTerme(
                statut="hors_perimetre",
                motif=f"Aucun lexique publié pour le métier « {question.metier} » en V1.",
                seuil=SEUIL_LEXIQUE,
                terme=None,
                sources=[],
            )
        meilleur = depot.terme_le_plus_proche(conn, lexique.id, question.mot)
    sources = [
        citer_source_du_lexique(question.metier, lexique, s)
        for s in lexique.rapport.get("sources", [])
    ]
    similarite = round(float(meilleur["similarite"]), 3) if meilleur else 0.0
    if meilleur is None or similarite < SEUIL_LEXIQUE:
        return ReponseTerme(
            statut="hors_corpus",
            motif=f"Aucun terme du lexique n'atteint le seuil de similarité ({SEUIL_LEXIQUE}) :"
            f" meilleure similarité {similarite}. Aucun terme n'est proposé.",
            seuil=SEUIL_LEXIQUE,
            terme=None,
            sources=sources,
        )
    terme = Terme(
        terme=meilleur["term"],
        similarite=similarite,
        categorie=meilleur["category"],
        source_id=meilleur["source_id"],
        reference=meilleur["source_ref"],
        url=url_terme(meilleur["source_id"], meilleur["source_ref"]),
        licence=depot.SOURCES[meilleur["source_id"]]["licence"],
        references=[
            {"table": "ref.lexicon_terms", "cle": f"id {meilleur['id']}"},
            {"table": "ref.trade_lexicons", "cle": f"version {lexique.version}"},
        ],
    )
    return ReponseTerme(
        statut="trouve",
        motif=f"Terme trouvé, similarité {similarite} pour un seuil de {SEUIL_LEXIQUE}.",
        seuil=SEUIL_LEXIQUE,
        terme=terme,
        sources=sources,
    )


class ReponseMarche(BaseModel):
    statut: Statut
    motif: str
    metier: str
    comptages: list[dict[str, Any]]
    sources: list[dict[str, Any]]


@routeur.get("/marche/{metier}", dependencies=[Depends(limiter)])
def marche(metier: str) -> ReponseMarche:
    """Établissements actifs d'un métier, par département, après secret statistique (Sirene)."""
    if metier not in METIERS or metier == "autre":
        return ReponseMarche(
            statut="hors_perimetre",
            motif="Métier hors de la tête de pont : plomberie, chauffage, electricite, serrurerie.",
            metier=metier,
            comptages=[],
            sources=[],
        )
    with ouvrir() as conn:
        execution = depot.execution_sirene(conn)
        if execution is None:
            raise HTTPException(status_code=503, detail="Agrégats Sirene non chargés.")
        lignes = depot.comptages_sirene(conn, execution["id"], metier)
    source = {
        "jeu": "sirene",
        "source_id": "SRC-01",
        **depot.SOURCES["SRC-01"],
        "url": execution["source_url"],
        "date_source": execution["stock_date"].isoformat(),
        "charge_le": execution["published_at"].isoformat(),
        "version": execution["id"],
        "table": "market.sirene_counts",
        "secret_statistique": f"seuil de {execution['small_cell_threshold']} ;"
        " ZZ : cellules regroupées ; FR : total national",
    }
    return ReponseMarche(
        statut="trouve",
        motif=f"{len(lignes)} cellules, stock Sirene du {execution['stock_date'].isoformat()}.",
        metier=metier,
        comptages=lignes,
        sources=[source],
    )
