"""Normalisation des noms avant comparaison (phase 1, document 04, section 3.2).

N1 casse, N2 accents, N3 séparateurs, N5 abréviations. N4 (civilités) ne concerne que les noms
de personnes, absents des référentiels.
"""

import re
import unicodedata

SEPARATEURS = re.compile(r"[-'’‘ʼ.\s]+")
ABREVIATIONS = {"st": "saint", "ste": "sainte"}


def sans_accents(texte: str) -> str:
    """N2 : décomposition NFD, puis suppression des diacritiques."""
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def normaliser_nom(texte: str, *, abreviations: bool = True) -> str:
    """Applique N1, N2, N3 et, par défaut, N5 : « Saint-Étienne » et « ST ETIENNE » donnent
    « saint etienne »."""
    resultat = sans_accents(texte.lower())  # N1, N2
    resultat = SEPARATEURS.sub(" ", resultat).strip()  # N3
    if abreviations:  # N5
        resultat = " ".join(ABREVIATIONS.get(mot, mot) for mot in resultat.split(" "))
    return resultat
