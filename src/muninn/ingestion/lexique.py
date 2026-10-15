"""Lexique métier : collecte des termes et construction d'une version (sprint 3, étapes 4 et 5).

Sources : une catégorie du Wiktionnaire (SRC-12, page web) et une requête SPARQL versionnée sur
Wikidata (SRC-11, base de données). Chaque terme garde sa source, sa référence (titre de page ou
identifiant Wikidata) et sa licence. Seul le titre ou le libellé est repris, jamais la
définition : l'attribution se fait par le lien vers la page (registre des sources du sprint 3).

Repli (dossier V1, § 7.1) : si une source ne répond pas, ses termes sont repris de l'instantané
versionné `donnees/lexique-secours-plomberie.json`, et le rapport de la version le dit.

La V1 retire la relecture humaine du lexique (dossier V1, V-04) : un terme est accepté ou écarté
par des règles écrites ci-dessous. La version construite reste `candidate` ; elle n'est publiée
qu'avec un rapport d'évaluation (US-48, critère 4), à l'étape 7.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from muninn.ingestion.normalisation import normaliser_nom
from muninn.ingestion.telechargement import FichierRecu
from muninn.ingestion.versions import Connexion, Resultat, valeur

METIER = "plomberie"
CATEGORIE = "Catégorie:Lexique_en_français_de_la_plomberie"
URL_WIKTIONNAIRE = "https://fr.wiktionary.org/wiki/" + quote(CATEGORIE)
LONGUEUR_MAX = 80  # contrainte de `ref.lexicon_terms.term`
DOSSIER = Path(__file__).parent
FICHIER_REQUETE = DOSSIER / "requetes" / "wikidata_marques_plomberie.rq"
REQUETE_WIKIDATA = FICHIER_REQUETE.read_text(encoding="utf-8")
URL_WIKIDATA = "https://query.wikidata.org/sparql?" + urlencode(
    {"query": REQUETE_WIKIDATA, "format": "json"}
)
FICHIER_SECOURS = DOSSIER / "donnees" / "lexique-secours-plomberie.json"
FICHIER_EVALUATIONS = DOSSIER / "donnees" / "evaluations-lexique.json"
LICENCES = {"SRC-12": "CC-BY-SA-4.0", "SRC-11": "CC0-1.0"}


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


def lire_wikidata(contenu: bytes) -> list[Terme]:
    """Libellés des marques rendues par la requête ; une entité, un terme."""
    donnees = json.loads(contenu.decode("utf-8"))
    termes: dict[str, Terme] = {}
    for ligne in donnees["results"]["bindings"]:
        identifiant = ligne["marque"]["value"].rsplit("/", 1)[-1]
        if identifiant not in termes:
            termes[identifiant] = Terme(
                ligne["nom"]["value"], "SRC-11", identifiant, "CC0-1.0", "brand"
            )
    return list(termes.values())


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


def evaluation(signature: str) -> dict[str, Any] | None:
    """Évaluation versionnée d'un lexique de cette empreinte, s'il en existe une."""
    evaluations = json.loads(FICHIER_EVALUATIONS.read_text(encoding="utf-8"))["evaluations"]
    trouvee = evaluations.get(signature)
    return trouvee if isinstance(trouvee, dict) else None


def publier_si_evalue(conn: Connexion, lexique: int, signature: str) -> bool:
    """Publie une version évaluée et retire la précédente, dans une transaction.

    Sans évaluation de cette empreinte, la version reste `candidate` : l'API continue de servir
    la version publiée (US-48, critère 4).
    """
    trouvee = evaluation(signature)
    if trouvee is None:
        return False
    with conn.transaction():
        conn.execute(
            "UPDATE ref.trade_lexicons SET status = 'retired'"
            " WHERE trade = %s AND status = 'published' AND id <> %s",
            [METIER, lexique],
        )
        conn.execute(
            "UPDATE ref.trade_lexicons SET status = 'published', published_at = now(),"
            " evaluation_report_ref = %s WHERE id = %s AND status <> 'published'",
            [f"{trouvee['rapport']} ({trouvee['date']}, seuil {trouvee['seuil']})", lexique],
        )
    return True


def construire(conn: Connexion, termes: list[Terme], sources: list[dict[str, Any]]) -> Resultat:
    """Construit une version du lexique, sauf si son contenu n'a pas changé ; la publie si son
    empreinte a été évaluée."""
    gardes, ecartes = selectionner(termes)
    signature = empreinte(gardes)
    derniere = conn.execute(
        "SELECT id, report->>'empreinte', status FROM ref.trade_lexicons WHERE trade = %s"
        " ORDER BY id DESC LIMIT 1",
        [METIER],
    ).fetchone()
    if derniere is not None and derniere[1] == signature:
        identifiant = int(derniere[0])
        if derniere[2] == "candidate" and publier_si_evalue(conn, identifiant, signature):
            return Resultat(jeu=f"lexique {METIER}", statut="published", version_id=identifiant)
        return Resultat(jeu=f"lexique {METIER}", statut="inchange", version_id=identifiant)

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
    publie = publier_si_evalue(conn, lexique, signature)
    return Resultat(
        jeu=f"lexique {METIER}",
        statut="published" if publie else "candidate",
        version_id=lexique,
        lues=len(termes),
        chargees=len(gardes),
        rejetees=len(ecartes),
    )


def source_rapport(source_id: str, fichier: FichierRecu, nombre: int) -> dict[str, Any]:
    rapport: dict[str, Any] = {
        "source_id": source_id,
        "mode": "collecte",
        "url": fichier.url if source_id == "SRC-12" else "https://query.wikidata.org/sparql",
        "date_source": fichier.date_source.isoformat() if fichier.date_source else None,
        "recupere_le": fichier.recupere_le.isoformat(),
        "sha256": fichier.sha256.hex(),
        "termes": nombre,
        "licence": LICENCES[source_id],
    }
    if source_id == "SRC-11":
        rapport["requete"] = "src/muninn/ingestion/requetes/wikidata_marques_plomberie.rq"
        rapport["requete_sha256"] = hashlib.sha256(REQUETE_WIKIDATA.encode()).hexdigest()
    return rapport


def lire_secours(source_id: str, raison: str) -> tuple[list[Terme], dict[str, Any]]:
    """Termes d'une source, repris de l'instantané versionné, et la ligne de rapport associée."""
    instantane = json.loads(FICHIER_SECOURS.read_text(encoding="utf-8"))
    source = instantane["sources"][source_id]
    termes = [Terme(**t) for t in source["termes"]]
    rapport = {
        "source_id": source_id,
        "mode": "secours",
        "raison": raison,
        "instantane_du": source["recupere_le"],
        "termes": len(termes),
        "licence": LICENCES[source_id],
    }
    return termes, rapport


def ecrire_secours(collectes: dict[str, tuple[list[Terme], FichierRecu]]) -> None:
    """Écrit l'instantané de secours à partir de collectes réussies (une par source)."""
    instantane = {
        "description": "Instantané de secours du lexique de plomberie (dossier V1, § 7.1)",
        "attribution": "Wiktionnaire : titres de pages, CC BY-SA 4.0 ; Wikidata : CC0",
        "sources": {
            source_id: {
                "recupere_le": fichier.recupere_le.isoformat(),
                "sha256": fichier.sha256.hex(),
                "termes": [asdict(t) for t in termes],
            }
            for source_id, (termes, fichier) in collectes.items()
        },
    }
    FICHIER_SECOURS.write_text(
        json.dumps(instantane, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",  # fins de ligne identiques sur tous les postes
    )
