"""Tests du lanceur de l'image : le bon processus selon MUNINN_PROCESSUS."""

import pytest

from muninn.serveur import cible


def test_cible_api_et_console() -> None:
    assert cible("api") == "muninn.api.main:app"
    assert cible("console") == "muninn.console.main:app"


def test_cible_inconnue_refusee() -> None:
    with pytest.raises(SystemExit, match="MUNINN_PROCESSUS inconnu"):
        cible("autre")
