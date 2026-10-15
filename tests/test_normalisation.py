"""Normalisation des noms (phase 1, document 04, section 3.2 ; plan de tests, TU-03).

Exemples écrits avant le code : au moins cinq par règle.
"""

import pytest

from muninn.ingestion.normalisation import normaliser_nom

EXEMPLES = [
    # N1 : casse
    ("PARIS", "paris"),
    ("Lyon", "lyon"),
    ("MaRsEiLLe", "marseille"),
    ("NANTES", "nantes"),
    ("bordeaux", "bordeaux"),
    # N2 : accents
    ("Évreux", "evreux"),
    ("Clémenciat", "clemenciat"),
    ("Pézenas", "pezenas"),
    ("Châlons", "chalons"),
    ("Lœuilly", "lœuilly"),  # la ligature n'est pas un diacritique : gardée
    # N3 : séparateurs
    ("L'Abergement-Clémenciat", "l abergement clemenciat"),
    ("L’Haÿ-les-Roses", "l hay les roses"),
    ("  Bourg   en  Bresse ", "bourg en bresse"),
    ("Saint-Jean-de-Luz", "saint jean de luz"),
    ("Châtillon-s.-Chalaronne", "chatillon s chalaronne"),
    # N5 : abréviations, mot entier seulement
    ("ST ETIENNE", "saint etienne"),
    ("Ste-Maxime", "sainte maxime"),
    ("ST DENIS", "saint denis"),
    ("LA STE BAUME", "la sainte baume"),
    ("Stains", "stains"),
]


@pytest.mark.parametrize(("entree", "attendu"), EXEMPLES)
def test_normaliser_nom(entree: str, attendu: str) -> None:
    assert normaliser_nom(entree) == attendu


def test_sans_abreviations() -> None:
    assert normaliser_nom("ST ETIENNE", abreviations=False) == "st etienne"


def test_officiel_et_la_poste_se_rejoignent() -> None:
    """Le nom officiel du COG et le nom de La Poste, sans accents ni tirets, se rejoignent."""
    assert normaliser_nom("L'Abergement-Clémenciat") == normaliser_nom("L ABERGEMENT CLEMENCIAT")
    assert normaliser_nom("Saint-Étienne") == normaliser_nom("ST ETIENNE")
