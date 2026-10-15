"""Chargement en base des fichiers (sprint 3, étape 2) : versions, rejets, rejeu, publication.

Passe par la commande `muninn-ingestion`, avec un téléchargement remplacé par des fichiers de
test : aucun appel réseau.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Any, cast

import pytest

from muninn.core.config import get_settings
from muninn.ingestion import api_geo, codes_postaux, cog, commande
from muninn.ingestion.telechargement import FichierRecu
from outils_base import base_migree, connecter, exiger_base, url_postgres

exiger_base()

ENTETE_COG = (
    '"TYPECOM","COM","REG","DEP","CTCD","ARR","TNCC","NCC","NCCENR","LIBELLE","CAN","COMPARENT"'
)
COG_V1 = "\n".join(
    [
        ENTETE_COG,
        '"COM","01001","84","01","","","5","","","L\'Abergement-Clémenciat","",""',
        '"COM","75056","11","75","","","0","","","Paris","",""',
        '"ARM","75101","11","75","","","0","","","Paris 1er Arrondissement","","75056"',
        '"COMD","01015","84","","","","0","","","Arbignieu","","01001"',
    ]
).encode("utf-8")
COG_V2 = COG_V1 + b'\n"COM","01002","84","01","","","5","","","L\'Abergement-de-Varey","",""'
COG_ORPHELINE = COG_V1 + b'\n"COMD","01099","84","","","","0","","","Orpheline","","01098"'
CP = "\r\n".join(
    [
        "#Code_commune_INSEE;Nom_de_la_commune;Code_postal;Libellé_d_acheminement;Ligne_5",
        "01001;L ABERGEMENT CLEMENCIAT;01400;L ABERGEMENT CLEMENCIAT;",
        "75101;PARIS 01;75001;PARIS;",
        "98714;BORA BORA;98730;ANAU;BORA BORA",
        "99999;INCONNUE;99999;INCONNUE;",
    ]
).encode("iso-8859-1")
GEO = (
    '[{"code": "01001", "nom": "L\'Abergement-Clémenciat", "codesPostaux": ["01400"]},'
    ' {"code": "75056", "nom": "Paris", "codesPostaux": ["75001"]},'
    ' {"code": "98714", "nom": "Bora-Bora", "codesPostaux": ["98730"]}]'
).encode()
TOUT = {cog.URL: COG_V1, codes_postaux.URL: CP, api_geo.URL: GEO}


@pytest.fixture
def base(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    with base_migree() as nom:
        monkeypatch.setenv("DATABASE_URL", url_postgres(nom))
        monkeypatch.setenv("GIT_SHA", "test")
        get_settings.cache_clear()
        yield nom
    get_settings.cache_clear()


def servir(monkeypatch: pytest.MonkeyPatch, fichiers: dict[str, bytes]) -> None:
    """Remplace le téléchargement : chaque adresse rend le contenu donné."""

    def faux(url: str, client: Any = None) -> FichierRecu:
        return FichierRecu(
            url=url,
            url_finale=url,
            contenu=fichiers[url],
            date_source=date(2026, 10, 8) if url == codes_postaux.URL else None,
            recupere_le=datetime.now(UTC),
        )

    monkeypatch.setattr(commande, "telecharger", faux)


def versions(base: str) -> list[tuple[Any, ...]]:
    with connecter(base) as conn:
        return conn.execute(
            "SELECT dataset, status, rows_read, rows_loaded, rows_filtered, rows_rejected,"
            " source_date FROM ref.dataset_versions ORDER BY id"
        ).fetchall()


def test_chargement_complet(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    servir(monkeypatch, TOUT)
    assert commande.main(["tout"]) == 0
    assert versions(base) == [
        ("communes", "published", 4, 4, 0, 0, date(2026, 1, 1)),
        ("postal_codes", "published", 4, 2, 1, 1, date(2026, 10, 8)),
        ("geo_api_communes", "published", 3, 3, 0, 0, datetime.now(UTC).date()),
    ]
    with connecter(base) as conn:
        assert conn.execute(
            "SELECT name, name_normalized FROM ref.communes WHERE insee_code = '01001'"
        ).fetchone() == ("L'Abergement-Clémenciat", "l abergement clemenciat")
        assert conn.execute(
            "SELECT line_number, reason_code FROM ref.load_rejections"
        ).fetchall() == [(5, "unknown_commune")]
        assert conn.execute("SELECT postal_code FROM ref.postal_codes ORDER BY 1").fetchall() == [
            ("01400",),
            ("75001",),
        ]
        rapport = conn.execute(
            "SELECT report FROM ref.dataset_versions WHERE dataset = 'postal_codes'"
        ).fetchone()
    assert rapport is not None
    donnees = cast(dict[str, Any], rapport[0])
    controles = {c["cas"]: c for c in donnees["controles"]}
    assert controles["VD-01"]["reussi"]
    assert controles["VD-08"]["reussi"]  # Paris couverte par son arrondissement


def test_rejeu_sans_doublon(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    servir(monkeypatch, TOUT)
    assert commande.main(["tout"]) == 0
    assert commande.main(["tout"]) == 0
    assert len(versions(base)) == 3  # second passage : sources inchangées, aucune version


def test_nouvelle_version_remplace_la_servie(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    servir(monkeypatch, {cog.URL: COG_V1})
    assert commande.main(["cog"]) == 0
    servir(monkeypatch, {cog.URL: COG_V2})
    assert commande.main(["cog"]) == 0
    assert [(v[0], v[1], v[3]) for v in versions(base)] == [
        ("communes", "retired", 4),
        ("communes", "published", 5),
    ]


def test_echec_de_controle_garde_la_version_servie(
    base: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    servir(monkeypatch, {cog.URL: COG_V1})
    assert commande.main(["cog"]) == 0
    servir(monkeypatch, {cog.URL: COG_ORPHELINE})
    assert commande.main(["cog"]) == 1  # VD-11 : commune déléguée sans parent existant
    assert [(v[1], v[3]) for v in versions(base)] == [("published", 4), ("failed", 5)]


def test_erreur_en_cours_de_chargement_ne_laisse_rien(
    base: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    servir(monkeypatch, {cog.URL: COG_V1})
    assert commande.main(["cog"]) == 0

    def panne(*_: Any) -> None:
        raise RuntimeError("panne simulée pendant l'écriture")

    servir(monkeypatch, {cog.URL: COG_V2})
    monkeypatch.setattr(cog, "inserer", panne)
    with pytest.raises(RuntimeError, match="panne simulée"):
        commande.main(["cog"])
    assert [(v[1], v[3]) for v in versions(base)] == [("published", 4)]


def test_codes_postaux_exigent_un_cog_publie(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    servir(monkeypatch, {codes_postaux.URL: CP})
    with pytest.raises(RuntimeError, match="COG"):
        commande.main(["codes-postaux"])


def test_api_geo_enregistre_les_ecarts(base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    servir(monkeypatch, TOUT)
    assert commande.main(["tout"]) == 0
    with connecter(base) as conn:
        assert conn.execute(
            "SELECT insee_code, gap_type, geo_api_name FROM ref.commune_source_gaps"
        ).fetchall() == [("98714", "absent_from_cog", "Bora-Bora")]
