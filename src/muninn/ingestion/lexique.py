"""Lexique métier : collecte des termes et construction d'une version (sprint 3, étapes 4 et 5).

Sources : une catégorie du Wiktionnaire (SRC-12, page web) ; Wikidata s'y ajoute à l'étape 5.
Chaque terme garde sa source, sa référence (titre de page) et sa licence. Seul le titre est
repris, jamais la définition : l'attribution se fait par le lien vers la page (registre des
sources du sprint 3, § 2).

La V1 retire la relecture humaine du lexique (dossier V1, V-04) : un terme est accepté ou écarté
par des règles écrites ci-dessous. La version construite reste `candidate` ; elle n'est publiée
qu'avec un rapport d'évaluation (US-48, critère 4), à l'étape 7.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote

from muninn.ingestion.normalisation import normaliser_nom
from muninn.ingestion.telechargement import FichierRecu
from muninn.ingestion.versions import Connexion, Resultat, valeur

METIER = "plomberie"
CATEGORIE = "Catégorie:Lexique_en_français_de_la_plomberie"
URL_WIKTIONNAIRE = "https://fr.wiktionary.org/wiki/" + quote(CATEGORIE)
LONGUEUR_MAX = 80  # contrainte de `ref.lexicon_terms.term`


@dataclass(frozen=True)
class Terme:
    terme: str
    source_id: str  # SRC-11, SRC-12 ou manual
    source_ref: str  # titre de page ou identifiant Wikidata
    licence: str
    categorie: str = "other"


class PagesDeCategorie(HTMLParser):
    """Titres des pages listées dans le bloc `mw-pages` d'une page de catégorie MediaWiki.

    Les liens hors de ce bloc (catégories parentes, navigation) sont ignorés.
    """

    def __init__(self) -> None:
        super().__init__()
        self.titres: list[str] = []
        self.profondeur = 0  # profondeur des `div` depuis l'entrée dans `mw-pages`

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributs = dict(attrs)
        if tag == "div":
            if self.profondeur:
                self.profondeur += 1
            elif attributs.get("id") == "mw-pages":
                self.profondeur = 1
        elif tag == "a" and self.profondeur and attributs.get("title"):
            href = attributs.get("href") or ""
            if href.startswith("/wiki/"):
                self.titres.append(str(attributs["title"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.profondeur:
            self.profondeur -= 1


def lire_wiktionnaire(contenu: bytes) -> list[Terme]:
    analyseur = PagesDeCategorie()
    analyseur.feed(contenu.decode("utf-8"))
    if not analyseur.titres:
        raise ValueError("Wiktionnaire : aucune page trouvée dans le bloc mw-pages")
    return [
        Terme(titre, "SRC-12", titre, "CC-BY-SA-4.0")
        for titre in analyseur.titres
        if ":" not in titre  # pages d'un autre espace de noms (Catégorie:, Annexe:)
    ]


def url_de(terme: Terme) -> str | None:
    """Adresse de la page source d'un terme : l'attribution exigée par la licence."""
    if terme.source_id == "SRC-12":
        return "https://fr.wiktionary.org/wiki/" + quote(terme.source_ref.replace(" ", "_"))
    if terme.source_id == "SRC-11":
        return "https://www.wikidata.org/wiki/" + terme.source_ref
    return None


def selectionner(termes: list[Terme]) -> tuple[list[Terme], list[dict[str, str]]]:
    """Règles d'acceptation de la V1 : longueur bornée, un seul terme par forme normalisée.

    Le premier terme d'une forme normalisée est gardé ; les suivants sont écartés et cités au
    rapport (« eaux vannes » et « eaux-vannes » ont la même forme).
    """
    gardes: dict[str, Terme] = {}
    ecartes: list[dict[str, str]] = []
    for terme in termes:
        forme = normaliser_nom(terme.terme, abreviations=False)
        if not forme or len(terme.terme) > LONGUEUR_MAX:
            ecartes.append({"terme": terme.terme, "motif": "longueur hors bornes"})
        elif forme in gardes:
            ecartes.append(
                {"terme": terme.terme, "motif": f"même forme que « {gardes[forme].terme} »"}
            )
        else:
            gardes[forme] = terme
    return list(gardes.values()), ecartes


def empreinte(termes: list[Terme]) -> str:
    """Empreinte du contenu du lexique : deux collectes identiques donnent la même."""
    lignes = sorted(f"{t.source_id}\t{t.source_ref}\t{t.terme}\t{t.licence}" for t in termes)
    return hashlib.sha256("\n".join(lignes).encode("utf-8")).hexdigest()


def construire(conn: Connexion, termes: list[Terme], sources: list[dict[str, Any]]) -> Resultat:
    """Construit une version `candidate` du lexique, sauf si son contenu n'a pas changé."""
    gardes, ecartes = selectionner(termes)
    signature = empreinte(gardes)
    derniere = conn.execute(
        "SELECT id, report->>'empreinte' FROM ref.trade_lexicons WHERE trade = %s"
        " ORDER BY id DESC LIMIT 1",
        [METIER],
    ).fetchone()
    if derniere is not None and derniere[1] == signature:
        return Resultat(jeu=f"lexique {METIER}", statut="inchange", version_id=int(derniere[0]))

    maintenant = datetime.now(UTC)
    rang = valeur(
        conn,
        "SELECT count(*) + 1 FROM ref.trade_lexicons WHERE trade = %s AND version LIKE %s",
        [METIER, f"{maintenant:%Y.%m}.%"],
    )
    rapport = {
        "empreinte": signature,
        "sources": sources,
        "termes_ecartes": ecartes,
        "regles": "V1 : acceptation par règles (longueur, forme unique), sans relecture humaine",
        "attribution": "titres repris, définitions non reprises ; lien vers chaque page",
    }
    with conn.transaction():
        lexique = int(
            valeur(
                conn,
                "INSERT INTO ref.trade_lexicons (trade, version, status, report)"
                " VALUES (%s, %s, 'candidate', %s) RETURNING id",
                [METIER, f"{maintenant:%Y.%m}.{rang}", json.dumps(rapport, ensure_ascii=False)],
            )
        )
        with conn.cursor().copy(
            "COPY ref.lexicon_terms (lexicon_id, term, term_normalized, category, source_id,"
            " source_ref, license, review_status) FROM STDIN"
        ) as copie:
            for t in gardes:
                copie.write_row(
                    [
                        lexique,
                        t.terme,
                        normaliser_nom(t.terme, abreviations=False),
                        t.categorie,
                        t.source_id,
                        t.source_ref,
                        t.licence,
                        "accepted",
                    ]
                )
    return Resultat(
        jeu=f"lexique {METIER}",
        statut="candidate",
        version_id=lexique,
        lues=len(termes),
        chargees=len(gardes),
        rejetees=len(ecartes),
    )


def source_rapport(fichier: FichierRecu, nombre: int) -> dict[str, Any]:
    return {
        "source_id": "SRC-12",
        "url": fichier.url,
        "date_source": fichier.date_source.isoformat() if fichier.date_source else None,
        "recupere_le": fichier.recupere_le.isoformat(),
        "sha256": fichier.sha256.hex(),
        "termes": nombre,
        "licence": "CC BY-SA 4.0 (ou GFDL)",
    }
