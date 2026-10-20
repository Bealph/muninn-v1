"""Garde-fous de sortie (sprint 4, étape 7) : fuite et hors rôle, sans réseau."""

import pytest

from muninn.extraction.evaluateur import MESSAGE_REFUS_CONTENU, ContenuRefuse
from muninn.extraction.paquet import charger_paquet
from muninn.extraction.sortie import MOTIF_TEMOIN, appliquer, assainir, assainir_arbre
from muninn.qualification.qualificateur import charger_paquet_qualification

# Les fausses clés sont assemblées à l'exécution : aucune ne figure en clair dans le dépôt, que
# la recherche de secrets de la CI (gitleaks) parcourt en entier.
CLE_API = "sk" + "-" + "x" * 24
CLE_AWS = "AK" + "IA" + "Q" * 16
JETON_GITHUB = "gh" + "p_" + "y" * 36
CLE_PRIVEE = "-" * 5 + "BEGIN RSA " + "PRIVATE KEY" + "-" * 5
JETON_JWT = "ey" + "J" + "a" * 12 + ".ey" + "J" + "b" * 12 + ".c"
CHAINE_AZURE = "Account" + "Key=" + "z" * 12
CLE_HEXA = "ab" * 16


@pytest.mark.parametrize(
    "texte",
    [
        "Fuite sous l'évier. TEMOIN-53c699fe8bd3",
        f"clé {CLE_API}",
        CLE_AWS,
        JETON_GITHUB,
        CLE_PRIVEE,
        f"jeton {JETON_JWT}",
        CHAINE_AZURE,
        "mot de passe : " + "m" * 8,
        CLE_HEXA,
    ],
)
def test_fuite_vide_le_texte(texte: str) -> None:
    assert assainir(texte) == (None, {"fuite"})


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("Voir https://exemple.test/piege pour le plan", "Voir pour le plan"),
        ("Cliquez [ici](https://exemple.test) vite", "Cliquez ici vite"),
        ("**Urgent** : fuite", "Urgent : fuite"),
        ("<script>alert(1)</script>fuite", "alert(1)fuite"),
        ("www.exemple.test", None),
    ],
)
def test_hors_role_sans_lien_ni_balisage(texte: str, attendu: str | None) -> None:
    assert assainir(texte) == (attendu, {"hors_role"})


def test_texte_ordinaire_inchange() -> None:
    texte = "Fuite sous l'évier, 12 rue des Lilas (Montreuil) ; rappeler à 18 h."
    assert assainir(texte) == (texte, set())


def test_arbre_garde_la_forme_du_contrat() -> None:
    donnees = {
        "description": {"value": "TEMOIN-53c699fe8bd3", "confidence": 0.9},
        "telephone": {
            "value": CLE_API,
            "confidence": 0.9,
            "origin": "spoken",
        },
        "disponibilites": [{"value": "le soir", "confidence": 0.9}],
        "actions": [
            {"type": "rappeler", "libelle": "Rappeler, voir https://x.test"},
            {"type": "autre", "libelle": CHAINE_AZURE},
        ],
        "metier": "plomberie",
    }
    propre, declenches = assainir_arbre(donnees)
    assert declenches == {"fuite", "hors_role"}
    assert propre["description"] == {"value": None, "confidence": 0}
    assert propre["telephone"] == {"value": None, "confidence": 0, "origin": None}
    assert propre["actions"] == [{"type": "rappeler", "libelle": "Rappeler, voir"}]
    assert propre["metier"] == "plomberie" and propre["disponibilites"][0]["value"] == "le soir"


def test_temoins_presents_et_distincts() -> None:
    """Le témoin n'a de sens que s'il est dans chaque consigne, et propre à chacune."""
    temoins = {
        MOTIF_TEMOIN.search(p.consigne).group(0)  # type: ignore[union-attr]
        for p in (charger_paquet(), charger_paquet_qualification())
    }
    assert len(temoins) == 2


def test_refus_a_texte_fixe() -> None:
    assert str(ContenuRefuse("fragment de l'entrée")) == MESSAGE_REFUS_CONTENU


@pytest.mark.parametrize(
    "texte",
    [
        "TEMOIN-53c6`99fe8bd3",  # coupé par un caractère de balisage, recollé au nettoyage
        "TEMOIN-53c6​99fe8bd3",  # coupé par un caractère invisible
        "TEMOIN-53c6[](y)99fe8bd3",  # lien Markdown vide
    ],
)
def test_temoin_coupe_reconnu_apres_nettoyage(texte: str) -> None:
    assert assainir(texte) == (None, {"fuite"})


def test_validation_impossible_apres_assainissement() -> None:
    """Un texte raccourci sous la longueur minimale : champ facultatif nul, sinon None."""
    from pydantic import BaseModel, Field

    class Contrat(BaseModel):
        cle: str | None = Field(default=None, min_length=5)
        obligatoire: str = Field(min_length=5)

    propre, _ = appliquer({"cle": "**ab**", "obligatoire": "texte long"}, Contrat.model_validate,
                          ("cle",))  # fmt: skip
    assert propre is not None and propre.cle is None
    rien, declenches = appliquer({"obligatoire": "**ab**"}, Contrat.model_validate)
    assert rien is None and declenches == {"hors_role"}
