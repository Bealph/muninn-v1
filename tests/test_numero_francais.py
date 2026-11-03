"""Numéro français : « +33 » suivi de 9 chiffres (benchmark C7, SC-02)."""

import pytest

from muninn.extraction.contrat import numero_plausible
from muninn.traitements.revue import _telephone


@pytest.mark.parametrize(
    ("numero", "attendu"),
    [
        ("+33699000002", True),
        ("+336990000002", False),  # onze chiffres en national : un zéro répété
        ("+3369900000", False),  # huit chiffres après « +33 »
        ("+33099000002", False),  # pas de zéro après « +33 »
        ("+4915112345678", True),  # numéro étranger : motif E.164 seul
        ("0699000002", False),  # format national, pas E.164
    ],
)
def test_numero_plausible(numero: str, attendu: bool) -> None:
    assert numero_plausible(numero) is attendu


def test_correction_de_l_artisan_suit_la_regle() -> None:
    assert _telephone("06 99 00 00 02").value == "+33699000002"
    with pytest.raises(ValueError, match="numéro invalide"):
        _telephone("06 99 00 000 02")
    with pytest.raises(ValueError, match="numéro invalide"):
        _telephone("+336990000002")
