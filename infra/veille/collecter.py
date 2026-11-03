"""Collecte de la veille (C6) : lit les flux du registre et écrit les nouveautés à trier.

Entrée : `docs/veille/sources.opml` (les flux de `docs/veille/sources.md`). Sortie : un fichier
Markdown daté, `docs/veille/collecte/AAAA-MM-JJ.md`, une section par source, une ligne par
nouveauté (date, titre, lien), du plus récent au plus ancien. Une nouveauté est retenue si elle
date de la période demandée ; pour les flux à fort volume (arXiv), seulement si son titre contient
un des mots-clés de la veille. Une source injoignable est signalée dans le fichier, sans arrêter
la collecte. Le tri (ce qui devient une fiche) reste un travail humain : `docs/veille/README.md`.

Bibliothèque standard seulement. Les flux sont des données externes : réponse limitée à 5 Mo, XML
lu par `xml.etree` (expat récent : expansions d'entités bornées).
Usage : `python infra/veille/collecter.py [--jours 7] [--sortie docs/veille/collecte]`.
"""

import argparse
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
OPML = RACINE / "docs" / "veille" / "sources.opml"
SORTIE = RACINE / "docs" / "veille" / "collecte"
TAILLE_MAX = 5 * 1024 * 1024
ATOM = "{http://www.w3.org/2005/Atom}"
# Flux à fort volume : seules les entrées dont le titre contient un de ces mots sont gardées.
FILTRES = {
    "rss.arxiv.org": (
        "information extraction", "structured output", "hallucinat", "speech recognition",
        "asr", "french", "tool call", "tool use", "tool-use", "function call",
        "llm-as-a-judge", "llm judge", "slot filling", "dialogue state", "named entity",
    ),
}  # fmt: skip


def lire_opml(chemin: Path) -> list[tuple[str, str]]:
    """Les flux du registre : (nom, adresse), dans l'ordre du fichier."""
    racine = ET.parse(chemin).getroot()  # noqa: S314 : fichier versionné du dépôt
    return [
        (o.get("text", ""), o.get("xmlUrl", "")) for o in racine.iter("outline") if o.get("xmlUrl")
    ]


def quand(texte: str | None) -> datetime | None:
    """Date d'un flux : RFC 822 (RSS) ou ISO 8601 (Atom) ; None si illisible."""
    if not texte:
        return None
    texte = texte.strip()
    for lire in (parsedate_to_datetime, datetime.fromisoformat):
        try:
            d = lire(texte)
        except (TypeError, ValueError, IndexError):
            continue
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    return None


def entrees(xml: bytes) -> list[tuple[datetime | None, str, str]]:
    """(date, titre, lien) de chaque entrée d'un flux RSS 2.0 ou Atom."""
    # Flux externe : expat récent borne les expansions d'entités et ignore les entités externes
    # (test_veille.py le vérifie) ; aucune dépendance de plus pour defusedxml.
    racine = ET.fromstring(xml)  # noqa: S314
    resultat = []
    for item in racine.iter("item"):  # RSS
        resultat.append((
            quand(item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date")),
            " ".join((item.findtext("title") or "").split()),
            (item.findtext("link") or "").strip(),
        ))  # fmt: skip
    for entree in racine.iter(f"{ATOM}entry"):  # Atom
        lien = entree.find(f"{ATOM}link[@rel='alternate']")
        if lien is None:
            lien = entree.find(f"{ATOM}link")
        resultat.append((
            quand(entree.findtext(f"{ATOM}published") or entree.findtext(f"{ATOM}updated")),
            " ".join((entree.findtext(f"{ATOM}title") or "").split()),
            lien.get("href", "") if lien is not None else "",
        ))  # fmt: skip
    return resultat


def retenir(
    adresse: str, lignes: list[tuple[datetime | None, str, str]], depuis: datetime
) -> list[tuple[datetime, str, str]]:
    """Les entrées de la période, filtrées par mots-clés pour les flux à fort volume."""
    mots = next((m for hote, m in FILTRES.items() if hote in adresse), None)
    gardees = []
    for d, titre, lien in lignes:
        if d is None or d < depuis or not titre:
            continue
        if mots and not any(m in titre.lower() for m in mots):
            continue
        gardees.append((d, titre, lien))
    return sorted(gardees, key=lambda e: e[0], reverse=True)


def exclure(
    lignes: list[tuple[datetime, str, str]], mots: tuple[str, ...]
) -> tuple[list[tuple[datetime, str, str]], int]:
    """Retire les entrées dont le titre contient un mot exclu ; rend le reste et le nombre retiré.

    Les mots viennent de `VEILLE_EXCLUSIONS` (séparés par des virgules), réglée sur le poste et
    jamais versionnée : une règle du dépôt interdit certains noms dans les fichiers suivis. Le
    fichier de collecte dit combien d'entrées ont été retirées.
    """
    if not mots:
        return lignes, 0
    gardees = [e for e in lignes if not any(m in e[1].lower() for m in mots)]
    return gardees, len(lignes) - len(gardees)


def telecharger(adresse: str) -> bytes:
    # Adresse lue dans le registre versionné, en https (contrôlé par test_veille.py).
    requete = urllib.request.Request(adresse, headers={"User-Agent": "veille-muninn/1.0"})  # noqa: S310
    with urllib.request.urlopen(requete, timeout=30) as reponse:  # noqa: S310
        contenu: bytes = reponse.read(TAILLE_MAX + 1)
    if len(contenu) > TAILLE_MAX:
        raise ValueError("réponse de plus de 5 Mo")
    return contenu


def rendre(
    jour: date,
    jours: int,
    resultats: list[tuple[str, list[tuple[datetime, str, str]] | str]],
    retirees: int = 0,
) -> str:
    """Le fichier de collecte : une section par source, nouveautés ou erreur."""
    total = sum(len(r) for _, r in resultats if not isinstance(r, str))
    lignes = [
        f"# Collecte de veille du {jour.isoformat()}",
        "",
        f"Nouveautés des {jours} derniers jours, {total} au total, à trier : une information "
        "n'est retenue (fiche dans `../fiches/`) que si elle peut changer un choix, une mesure "
        "ou une obligation de Muninn. Produit par `infra/veille/collecter.py`.",
    ]
    if retirees:
        lignes += ["", f"Entrées retirées par la règle d'exclusion du poste : {retirees}."]
    for nom, r in resultats:
        lignes += ["", f"## {nom}", ""]
        if isinstance(r, str):
            lignes.append(f"Source injoignable : {r}")
        elif not r:
            lignes.append("Rien de nouveau.")
        else:
            lignes += [f"- {d.date().isoformat()} · [{t}]({lien})" for d, t, lien in r]
    return "\n".join(lignes) + "\n"


def main(argv: list[str]) -> int:
    options = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    options.add_argument("--jours", type=int, default=7)
    options.add_argument("--sortie", type=Path, default=SORTIE)
    args = options.parse_args(argv)
    maintenant = datetime.now(UTC)
    depuis = maintenant - timedelta(days=args.jours)
    mots = tuple(
        m.strip().lower() for m in os.environ.get("VEILLE_EXCLUSIONS", "").split(",") if m.strip()
    )
    resultats: list[tuple[str, list[tuple[datetime, str, str]] | str]] = []
    retirees = 0
    for nom, adresse in lire_opml(OPML):
        try:
            gardees, n = exclure(retenir(adresse, entrees(telecharger(adresse)), depuis), mots)
        except Exception as erreur:  # noqa: BLE001 : une source en échec ne bloque pas les autres
            resultats.append((nom, f"{type(erreur).__name__}"))
            continue
        resultats.append((nom, gardees))
        retirees += n
    args.sortie.mkdir(parents=True, exist_ok=True)
    fichier = args.sortie / f"{maintenant.date().isoformat()}.md"
    texte = rendre(maintenant.date(), args.jours, resultats, retirees)
    fichier.write_text(texte, encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    print(f"{fichier.relative_to(RACINE) if fichier.is_relative_to(RACINE) else fichier}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
