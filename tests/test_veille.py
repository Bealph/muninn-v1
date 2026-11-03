"""Collecte de la veille (C6) : flux RSS et Atom, période et mots-clés, sans réseau."""

import importlib.util
import pyexpat
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
COLLECTER = RACINE / "infra" / "veille" / "collecter.py"
OPML = RACINE / "docs" / "veille" / "sources.opml"
REGISTRE = RACINE / "docs" / "veille" / "sources.md"

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Nouveau  service</title><link>https://exemple.org/a</link>
<pubDate>Mon, 02 Nov 2026 10:00:00 GMT</pubDate></item>
<item><title>Ancien</title><link>https://exemple.org/b</link>
<pubDate>Mon, 05 Oct 2026 10:00:00 GMT</pubDate></item>
<item><title>Sans date</title><link>https://exemple.org/c</link></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>t</title>
<entry><title>v4.16.0</title><link rel="alternate" href="https://exemple.org/v416"/>
<updated>2026-11-01T08:00:00Z</updated></entry>
</feed>"""


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("collecter", COLLECTER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DEPUIS = datetime(2026, 10, 27, tzinfo=UTC)


def test_rss_periode_et_dates() -> None:
    m = module()
    gardees = m.retenir("https://exemple.org/rss", m.entrees(RSS), DEPUIS)
    assert [(t, lien) for _, t, lien in gardees] == [("Nouveau service", "https://exemple.org/a")]


def test_atom_lien_et_date() -> None:
    m = module()
    gardees = m.retenir("https://github.com/x/releases.atom", m.entrees(ATOM), DEPUIS)
    assert gardees == [
        (datetime(2026, 11, 1, 8, tzinfo=UTC), "v4.16.0", "https://exemple.org/v416")
    ]


def test_arxiv_filtre_par_mots_cles() -> None:
    m = module()
    lignes = [
        (datetime(2026, 11, 2, tzinfo=UTC), "Evaluating LLM agents on tool use", "a"),
        (datetime(2026, 11, 2, tzinfo=UTC), "Morphology of Old Norse verbs", "b"),
    ]
    gardees = m.retenir("https://rss.arxiv.org/rss/cs.CL", lignes, DEPUIS)
    assert [t for _, t, _ in gardees] == ["Evaluating LLM agents on tool use"]


def test_rendu_signale_une_source_injoignable() -> None:
    m = module()
    texte = m.rendre(
        date(2026, 11, 3),
        7,
        [("S04 Langfuse", [(datetime(2026, 11, 1, tzinfo=UTC), "v4.16.0", "https://e/v")]),
         ("S11 CNIL", "URLError"), ("S14 W3C", [])],
    )  # fmt: skip
    assert "# Collecte de veille du 2026-11-03" in texte
    assert "- 2026-11-01 · [v4.16.0](https://e/v)" in texte
    assert "Source injoignable : URLError" in texte and "Rien de nouveau." in texte


def test_les_flux_sont_ceux_du_registre_en_https() -> None:
    """L'OPML et le registre ne divergent pas : chaque flux y figure, en https."""
    flux = module().lire_opml(OPML)
    registre = REGISTRE.read_text(encoding="utf-8")
    assert len(flux) == 11
    for nom, adresse in flux:
        assert adresse.startswith("https://"), nom
        assert adresse in registre, nom


def test_expat_borne_les_expansions_d_entites() -> None:
    """`xml.etree` n'est sûr face au « billion laughs » qu'avec expat 2.4.1 ou plus récent."""
    assert pyexpat.version_info >= (2, 4, 1)
    bombe = (
        b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaaaaaaaa">'
        + b"".join(
            f'<!ENTITY {chr(98 + i)} "{("&" + chr(97 + i) + ";") * 10}">'.encode() for i in range(7)
        )
        + b"]><r>&h;</r>"
    )
    try:
        ET.fromstring(bombe)  # noqa: S314 : c'est l'objet du test
    except ET.ParseError:
        return
    raise AssertionError("expansion d'entités non bornée")


def test_exclusion_comptee_et_jamais_versionnee() -> None:
    """Les mots exclus viennent du poste ; le fichier dit combien d'entrées ont été retirées."""
    m = module()
    lignes = [
        (datetime(2026, 11, 2, tzinfo=UTC), "Nouveau modèle Zeta", "a"),
        (datetime(2026, 11, 2, tzinfo=UTC), "Mise à jour de Container Apps", "b"),
    ]
    gardees, n = m.exclure(lignes, ("zeta",))
    assert [t for _, t, _ in gardees] == ["Mise à jour de Container Apps"] and n == 1
    assert m.exclure(lignes, ())[1] == 0
    texte = m.rendre(date(2026, 11, 3), 7, [("S01", gardees)], n)
    assert "Entrées retirées par la règle d'exclusion du poste : 1." in texte
    assert "VEILLE_EXCLUSIONS" in COLLECTER.read_text(encoding="utf-8")
