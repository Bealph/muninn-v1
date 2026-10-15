"""Lecture et nettoyage des fichiers sources (sprint 3, étape 2 ; cas VD de la phase 1)."""

import pytest

from muninn.ingestion import api_geo, codes_postaux, cog, lexique

ENTETE_COG = (
    '"TYPECOM","COM","REG","DEP","CTCD","ARR","TNCC","NCC","NCCENR","LIBELLE","CAN","COMPARENT"'
)


def ligne_cog(type_: str, code: str, dep: str, libelle: str, parent: str = "") -> str:
    return f'"{type_}","{code}","84","{dep}","","","0","","","{libelle}","","{parent}"'


def fichier_cog(*lignes: str) -> bytes:
    return "\n".join([ENTETE_COG, *lignes]).encode("utf-8")


ENTETE_CP = "#Code_commune_INSEE;Nom_de_la_commune;Code_postal;Libellé_d_acheminement;Ligne_5"


def fichier_cp(*lignes: str, encodage: str = "iso-8859-1") -> bytes:
    return "\r\n".join([ENTETE_CP, *lignes]).encode(encodage)


def test_cog_garde_rejette_et_compte() -> None:
    lecture = cog.lire(
        fichier_cog(
            ligne_cog("COM", "01001", "01", "L'Abergement-Clémenciat"),
            ligne_cog("COM", "2A004", "2A", "Ajaccio"),
            ligne_cog("COMD", "01015", "", "Arbignieu", "01015"),
            ligne_cog("COMD", "01016", "", "Sans parent"),  # parent manquant
            ligne_cog("COM", "01001", "01", "Doublon"),  # (type, code) déjà vu
            ligne_cog("XXX", "01002", "01", "Type inconnu"),
            ligne_cog("COM", "1002", "01", "Code sur 4 chiffres"),
            ligne_cog("COM", "01003", "", "Commune sans département"),
        )
    )
    assert [c.code for c in lecture.lignes] == ["01001", "2A004", "01015"]
    assert [(r.ligne, r.motif) for r in lecture.rejets] == [
        (5, "missing_field"),
        (6, "duplicate"),
        (7, "bad_format"),
        (8, "bad_format"),
        (9, "missing_field"),
    ]
    assert lecture.lues == len(lecture.lignes) + len(lecture.rejets) + lecture.filtrees
    assert lecture.lignes[0].nom == "L'Abergement-Clémenciat"  # VD-10 : nom officiel accentué


def test_cog_entete_inattendu() -> None:
    with pytest.raises(ValueError, match="en-tête"):
        cog.lire(b'"COM","LIBELLE"\n"01001","X"')


def test_codes_postaux_zeros_filtre_et_rejets() -> None:
    lecture = codes_postaux.lire(
        fichier_cp(
            "01001;L ABERGEMENT CLEMENCIAT;01400;L ABERGEMENT CLEMENCIAT;",
            "98714;BORA BORA;98730;ANAU;BORA BORA",  # collectivité d'outre-mer : filtrée
            "99138;MONACO;98000;MONACO;",  # Monaco : filtré
            "99999;INCONNUE;99999;INCONNUE;",  # absente du COG : rejetée
            "01001;L ABERGEMENT CLEMENCIAT;01400;L ABERGEMENT CLEMENCIAT;",  # doublon
            "01002;L ABERGEMENT DE VAREY;1640;L ABERGEMENT DE VAREY;",  # code sur 4 chiffres
            "01004;AMBERIEU EN BUGEY;01500;;",  # libellé vide
            "01004;AMBERIEU EN BUGEY;01500",  # colonne manquante
        ),
        communes_cog={"01001", "01002", "01004"},
    )
    assert [(c.code_postal, c.code_commune) for c in lecture.lignes] == [("01400", "01001")]
    assert lecture.filtrees == 2
    assert [r.motif for r in lecture.rejets] == [
        "unknown_commune",
        "duplicate",
        "bad_format",
        "missing_field",
        "bad_format",
    ]
    assert lecture.lues == 8 == len(lecture.lignes) + len(lecture.rejets) + lecture.filtrees
    assert lecture.lignes[0].code_postal.startswith("0")  # VD-01 : zéro initial gardé


def test_codes_postaux_libelles_d_acheminement_distincts_gardes() -> None:
    """Une commune avec plusieurs libellés d'acheminement n'est pas un doublon (VD-05)."""
    lecture = codes_postaux.lire(
        fichier_cp("01001;X;01400;LIBELLE A;", "01001;X;01400;LIBELLE B;"),
        communes_cog={"01001"},
    )
    assert len(lecture.lignes) == 2
    assert lecture.rejets == []


def test_codes_postaux_fichier_en_utf8_refuse() -> None:
    """VD-02 : un fichier en UTF-8 lu en ISO-8859-1 donne un en-tête faux, donc un arrêt."""
    with pytest.raises(ValueError, match="en-tête"):
        codes_postaux.lire(fichier_cp("01001;X;01400;X;", encodage="utf-8"), {"01001"})


def test_api_geo_lecture_et_ecarts() -> None:
    contenu = (
        '[{"code": "01001", "nom": "L\'Abergement-Clémenciat", "codesPostaux": ["01400"]},'
        ' {"code": "98714", "nom": "Bora-Bora", "codesPostaux": ["98730"]},'
        ' {"code": "01002", "nom": "Autre nom", "codesPostaux": []},'
        ' {"code": "01001", "nom": "Doublon"},'
        ' {"nom": "Sans code"},'
        ' {"code": "1003", "nom": "Code sur 4 chiffres"}]'
    ).encode()
    lecture = api_geo.lire(contenu)
    assert [c.code for c in lecture.lignes] == ["01001", "98714", "01002"]
    assert [(r.ligne, r.motif) for r in lecture.rejets] == [
        (4, "duplicate"),
        (5, "missing_field"),
        (6, "bad_format"),
    ]
    cog_servi = {
        "01001": "L'Abergement-Clémenciat",
        "01002": "L'Abergement-de-Varey",
        "01004": "Ambérieu-en-Bugey",
    }
    assert api_geo.ecarts(lecture.lignes, cog_servi) == [
        ("98714", "absent_from_cog", "Bora-Bora"),
        ("01004", "absent_from_geo_api", None),
        ("01002", "name_differs", "Autre nom"),
    ]


PAGE_CATEGORIE = """<html><body>
<div id="mw-subcategories"><a href="/wiki/Cat%C3%A9gorie:Autre" title="Catégorie:Autre">x</a></div>
<div id="mw-pages"><h2>Pages</h2><div class="mw-content-ltr"><div class="mw-category">
<ul><li><a href="/wiki/cumulus" title="cumulus">cumulus</a></li>
<li><a href="/wiki/eaux_vannes" title="eaux vannes">eaux vannes</a></li>
<li><a href="/wiki/eaux-vannes" title="eaux-vannes">eaux-vannes</a></li>
<li><a href="/wiki/Annexe:X" title="Annexe:X">annexe</a></li></ul></div></div></div>
<div id="catlinks"><a href="/wiki/Cat%C3%A9gorie:Plomberie" title="Catégorie:Plomberie">p</a></div>
</body></html>"""


def test_wiktionnaire_lit_seulement_le_bloc_des_pages() -> None:
    termes = lexique.lire_wiktionnaire(PAGE_CATEGORIE.encode("utf-8"))
    assert [t.terme for t in termes] == ["cumulus", "eaux vannes", "eaux-vannes"]
    assert {(t.source_id, t.licence) for t in termes} == {("SRC-12", "CC-BY-SA-4.0")}


def test_wiktionnaire_page_sans_bloc_refusee() -> None:
    with pytest.raises(ValueError, match="mw-pages"):
        lexique.lire_wiktionnaire(b"<html><body><p>vide</p></body></html>")


def test_lexique_une_forme_un_terme_et_attribution() -> None:
    termes = lexique.lire_wiktionnaire(PAGE_CATEGORIE.encode("utf-8"))
    gardes, ecartes = lexique.selectionner(termes)
    assert [t.terme for t in gardes] == ["cumulus", "eaux vannes"]
    assert ecartes == [{"terme": "eaux-vannes", "motif": "même forme que « eaux vannes »"}]
    assert lexique.url_de(gardes[1]) == "https://fr.wiktionary.org/wiki/eaux_vannes"
    assert lexique.empreinte(gardes) == lexique.empreinte(list(reversed(gardes)))
