"""État du service sur une base PostgreSQL réelle : échéance du jugement, historique des alertes,
coût du mois (sprint 5, étape 4 ; D-83). Demande `TEST_DATABASE_URL` ; ignoré sans elle, sauf en CI.

Scénario écrit dans `app.traitements` :
- il y a 2 h 40 à 2 h 05 : 22 dossiers, dont 11 « à vérifier » (50 %) : une alerte AL-01 passée ;
- il y a 40 à 19 minutes : 22 dossiers, dont 2 « à vérifier » (9 %) : état jugé, sous le seuil.
"""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import Engine, text

from muninn.core.config import get_settings
from muninn.db import roles
from muninn.traitements import enregistrement
from muninn.traitements.etat import historique, juge_jusqu_a
from muninn.traitements.metriques import cout_du_mois
from outils_base import base_migree, exiger_base, url_postgres

exiger_base()

MDP = {"api": "api-" + "a" * 28, "ingestion": "ingestion-" + "b" * 22,
       "traitements": "traitements-" + "c" * 20}  # fmt: skip


def _rafale(conn: psycopg.Connection, debut_min: int, a_verifier: int) -> None:
    """22 dossiers, un par minute et demie à partir de `debut_min` minutes avant maintenant."""
    for i in range(22):
        conn.execute(
            "INSERT INTO app.traitements (request_id, recu_le, route, scenario_id, issue,"
            " statut, a_verifier, duree_ms, duree_extraction_ms, cout_micro_eur)"
            " VALUES (%s, now() - make_interval(secs => %s), 'demo', 'SC-01', 'dossier',"
            " 'complete', %s, 3000, 2500, 5000)",
            [str(uuid.uuid4()), debut_min * 60 - i * 90, i < a_verifier],
        )


@pytest.fixture(scope="module")
def moteur_essai() -> Iterator[Engine]:
    with base_migree() as nom:
        roles.preparer_roles(url_postgres(nom), MDP)
        with psycopg.connect(url_postgres(nom), autocommit=True) as conn:
            _rafale(conn, 160, a_verifier=11)
            _rafale(conn, 40, a_verifier=2)
        p = conninfo_to_dict(exiger_base())
        url = (f"postgresql://{nom}_traitements:{MDP['traitements']}"
               f"@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{nom}")  # fmt: skip
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_URL_TRAITEMENTS", url)
            get_settings.cache_clear()
            enregistrement.moteur.cache_clear()
            m = enregistrement.moteur()
            assert m is not None
            yield m
            enregistrement.moteur.cache_clear()


def test_juge_jusqu_a_une_heure_apres_le_vingtieme_dossier(moteur_essai: Engine) -> None:
    limite = juge_jusqu_a(moteur_essai)
    assert limite is not None
    with moteur_essai.connect() as conn:
        vingtieme: datetime = conn.execute(text(
            "SELECT recu_le FROM app.traitements WHERE recu_le > now() - interval '1 hour'"
            " ORDER BY recu_le DESC OFFSET 19 LIMIT 1"
        )).scalar_one()  # fmt: skip
    assert limite == vingtieme + timedelta(hours=1)
    # Le 20e dossier le plus récent a environ 37 minutes : l'état reste jugé encore 23 minutes.
    reste = limite - datetime.now(UTC)
    assert timedelta(minutes=20) < reste < timedelta(minutes=26)


def test_historique_retrouve_l_alerte_passee(moteur_essai: Engine) -> None:
    episodes = historique(moteur_essai)
    al01 = [e for e in episodes if e.code == "AL-01"]
    assert len(al01) == 1, episodes
    e = al01[0]
    assert not e.en_cours
    # L'alerte commence quand la fenêtre d'une heure compte 20 dossiers dont plus de 20 % à
    # vérifier, et finit quand la seconde rafale, peu douteuse, fait passer la part sous 20 %.
    maintenant = datetime.now(UTC)
    assert maintenant - timedelta(hours=2, minutes=40) < e.debut < e.fin
    assert e.fin < maintenant - timedelta(minutes=19)
    # Pire point : la fenêtre tient les 11 dossiers douteux parmi 20, 21 ou 22, selon l'alignement
    # de la grille de 5 minutes sur la rafale.
    assert e.pire in {"55 % (11 sur 20)", "52 % (11 sur 21)", "50 % (11 sur 22)"}
    assert not [x for x in episodes if x.code != "AL-01"]


def test_cout_du_mois_et_projection(moteur_essai: Engine) -> None:
    # 44 traitements à 5 000 micro-euros : 0,22 €, s'ils sont tous dans le mois en cours.
    maintenant = datetime.now(UTC)
    c = cout_du_mois(moteur_essai, maintenant)
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    attendu = 0.22 if maintenant - timedelta(hours=3) > debut_mois else c.total_eur
    assert c.total_eur == pytest.approx(attendu)
    assert c.budget_eur == 60.0 and c.mois == f"{maintenant:%m/%Y}"
    # Le rythme se mesure depuis le premier traitement (il y a 2 h 40), pas depuis le 1er du mois.
    if c.depuis and c.depuis > debut_mois:
        assert maintenant - c.depuis == pytest.approx(
            timedelta(minutes=160), abs=timedelta(minutes=1)
        )
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1)
        rythme = c.total_eur / (maintenant - c.depuis).total_seconds()
        attendue = c.total_eur + rythme * (fin_mois - maintenant).total_seconds()
        assert c.projection_eur == pytest.approx(attendue, abs=0.01)


def test_al16_sur_la_duree_de_l_extraction(moteur_essai: Engine) -> None:
    from muninn.traitements.metriques import calculer

    m = calculer(moteur_essai, 1)
    # 22 dossiers de la seconde rafale : extraction de 2,5 s, traitement entier de 3 s.
    assert (m.extractions, m.extraction_p95_ms, m.latence_p95_ms) == (22, 2500, 3000)
