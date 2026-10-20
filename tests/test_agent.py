"""Agent d'extraction et sa boucle bornée (sprint 4, étape 3), sans réseau ni modèle réel."""

import json
import logging
from typing import Any

import httpx
import pytest

from muninn.extraction.agent import extraire, normaliser_sortie
from muninn.extraction.outils import ClientReferentiels, executer_outil
from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import (
    DelaiDepasse,
    ErreurFournisseur,
    FauxFournisseur,
    RefusContenu,
    ReponseChat,
    reponse_faux,
)

TRANSCRIPTION = (
    "Bonjour, Claire Petit, une prise qui grésille, 4 rue de Fontenay à Vincennes, 06 99 00 00 02."
)


def sortie(code_postal: str | None = "94300", commune: str | None = "Vincennes") -> str:
    def champ(valeur: str | None, confiance: float = 0.95) -> dict[str, Any]:
        return {"value": valeur, "confidence": confiance if valeur is not None else 0}

    return json.dumps(
        {
            "client": {
                "nom": champ("Petit"),
                "prenom": champ("Claire"),
                "telephone": {"value": "+33699000002", "confidence": 0.95, "origin": "spoken"},
                "adresse": {
                    "rue": champ("4 rue de Fontenay"),
                    "code_postal": champ(code_postal),
                    "commune": champ(commune),
                },
            },
            "demande": {
                "objet_court": champ("prise qui grésille"),
                "description": champ("Une prise électrique grésille."),
                "metier": "electricite",
                "urgence": "normal",
                "disponibilites_client": [],
            },
            "cle_humaine": "Petit, Vincennes, prise qui grésille",
            "actions": [{"type": "rappeler", "libelle": "Rappeler la cliente"}],
            "champs_manquants": [],
        },
        ensure_ascii=False,
    )


class FauxReferentiels:
    """Double de l'API des référentiels : garde les corps reçus."""

    def __init__(self) -> None:
        self.recus: list[tuple[str, dict[str, str]]] = []

    def communes(self, corps: dict[str, str]) -> dict[str, Any]:
        self.recus.append(("communes", corps))
        return {
            "statut": "trouve",
            "candidates": [
                {
                    "nom": "Vincennes",
                    "code_insee": "94080",
                    "departement": "94",
                    "codes_postaux": ["94300"],
                }
            ],
        }

    def termes(self, corps: dict[str, str]) -> dict[str, Any]:
        self.recus.append(("termes", corps))
        return {"statut": "trouve", "terme": {"terme": "chauffe-eau électrique", "similarite": 0.8}}


def lancer(
    scenario: list[ReponseChat | Exception], referentiels: FauxReferentiels | None = None
) -> Any:
    fournisseur = FauxFournisseur(scenario=scenario)
    refs = referentiels or FauxReferentiels()
    resultat = extraire(
        TRANSCRIPTION, charger_paquet(), fournisseur, refs, "2026-10-19", "electricite"
    )
    return resultat, fournisseur, refs


def appel_communes(**args: Any) -> ReponseChat:
    return reponse_faux(appels=[("chercher_communes", {"nom": None, "code_postal": None, **args})])


def test_reponse_directe() -> None:
    r, fournisseur, _ = lancer([reponse_faux(contenu=sortie())])
    assert r.statut == "complete" and r.tentatives == 1 and r.etapes == 1
    assert r.sortie is not None and r.sortie.client.adresse.code_postal.value == "94300"
    requete = fournisseur.requetes[0]
    assert requete.outils is not None and requete.schema_sortie is not None
    assert requete.messages[0]["role"] == "system"
    assert requete.messages[1]["content"].count("<transcription>") == 1


def test_outil_puis_reponse_et_communes_rendues() -> None:
    r, fournisseur, refs = lancer([appel_communes(nom="Vincennes"), reponse_faux(contenu=sortie())])
    assert r.statut == "complete" and r.etapes == 2
    assert [a.nom for a in r.appels_outils] == ["chercher_communes"]
    assert r.communes_rendues[0].codes_postaux == ("94300",)
    # Seuls le nom ou le code postal partent vers l'outil ; un champ nul n'est pas transmis.
    assert refs.recus == [("communes", {"nom": "Vincennes"})]
    # La réponse de l'outil revient au modèle, liée à l'appel, sans champ `name`.
    message = fournisseur.requetes[1].messages[-1]
    assert (
        message["role"] == "tool" and message["tool_call_id"] == "appel-1" and "name" not in message
    )
    assert json.loads(message["content"])["candidates"][0]["code_insee"] == "94080"


def test_terme_metier_retenu() -> None:
    appel = reponse_faux(
        appels=[("chercher_terme_metier", {"mot": "cumulus", "metier": "plomberie"})]
    )
    r, _, refs = lancer([appel, reponse_faux(contenu=sortie())])
    assert r.termes_rendus == ["chauffe-eau électrique"]
    assert refs.recus == [("termes", {"mot": "cumulus", "metier": "plomberie"})]


def test_outil_inconnu_refuse_sans_arreter_l_agent() -> None:
    inconnu = reponse_faux(appels=[("supprimer_dossier", {"id": 1})])
    r, fournisseur, refs = lancer([inconnu, reponse_faux(contenu=sortie())])
    assert r.statut == "complete"
    assert r.appels_outils[0].statut == "outil_inconnu"
    assert refs.recus == []
    assert "outil inconnu" in fournisseur.requetes[1].messages[-1]["content"]


def test_borne_de_six_appels() -> None:
    scenario: list[ReponseChat | Exception] = [appel_communes(nom="Montreuil") for _ in range(7)]
    scenario.append(reponse_faux(contenu=sortie()))
    r, fournisseur, refs = lancer(scenario)
    assert len(r.appels_outils) == 6 and len(refs.recus) == 6
    assert r.borne_atteinte is True
    # Après la borne, le modèle doit conclure sans outil.
    assert fournisseur.requetes[-1].outils is None
    assert r.statut == "complete"


def test_relance_unique_puis_reponse_conforme() -> None:
    r, fournisseur, _ = lancer(
        [reponse_faux(contenu='{"client": "pas un objet"}'), reponse_faux(contenu=sortie())]
    )
    assert r.statut == "complete" and r.tentatives == 2
    relance = fournisseur.requetes[1].messages[-1]
    assert relance["role"] == "user" and "client" in relance["content"]
    assert "pas un objet" not in relance["content"]  # le chemin du champ, jamais sa valeur
    assert fournisseur.requetes[1].outils is None


def test_deux_sorties_hors_schema_donnent_un_brouillon_partiel() -> None:
    r, _, _ = lancer([reponse_faux(contenu="pas du JSON"), reponse_faux(contenu="{}")])
    assert r.statut == "partial_after_retry" and r.tentatives == 2 and r.sortie is None


def test_refus_du_modele_traite_comme_hors_schema() -> None:
    refus = ReponseChat(
        contenu=None,
        appels_outils=[],
        raison_fin="stop",
        modele="m",
        fournisseur="faux",
        duree_ms=0,
        jetons_entree=0,
        jetons_sortie=0,
        cout_micro_eur=0,
        refus_modele="Je ne peux pas.",
    )
    r, _, _ = lancer([refus, reponse_faux(contenu=sortie())])
    assert r.statut == "complete" and r.tentatives == 2


@pytest.mark.parametrize(
    ("erreur", "statut"),
    [
        (RefusContenu("bloqué"), "content_refused"),
        (DelaiDepasse("lent"), "fallback_no_llm"),
        (ErreurFournisseur("panne"), "fallback_no_llm"),
    ],
)
def test_echecs_du_fournisseur(erreur: Exception, statut: str) -> None:
    r, _, _ = lancer([erreur])
    assert r.statut == statut and r.sortie is None


def test_panne_apres_un_appel_d_outil() -> None:
    r, _, _ = lancer([appel_communes(nom="Vincennes"), ErreurFournisseur("panne")])
    assert r.statut == "fallback_no_llm" and len(r.appels_outils) == 1


def test_arguments_d_outil_illisibles() -> None:
    assert (
        executer_outil(FauxReferentiels(), "chercher_communes", "pas du json").statut
        == "arguments_illisibles"
    )
    assert (
        executer_outil(FauxReferentiels(), "chercher_communes", '{"nom": "  "}').statut
        == "arguments_illisibles"
    )
    assert (
        executer_outil(FauxReferentiels(), "chercher_terme_metier", '{"mot": "x"}').statut
        == "arguments_illisibles"
    )


def test_referentiels_indisponibles() -> None:
    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lent", request=requete)

    client = ClientReferentiels(
        "http://api", client=httpx.Client(transport=httpx.MockTransport(gestionnaire))
    )
    assert (
        executer_outil(client, "chercher_communes", '{"nom": "Vincennes"}').statut
        == "delai_depasse"
    )
    erreur = ClientReferentiels(
        "http://api",
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))),
    )
    assert (
        executer_outil(erreur, "chercher_communes", '{"nom": "Vincennes"}').statut == "indisponible"
    )


def test_client_referentiels_appelle_l_api() -> None:
    recu: dict[str, Any] = {}

    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        recu["url"], recu["corps"] = str(requete.url), json.loads(requete.content)
        return httpx.Response(200, json={"statut": "hors_corpus", "candidates": []})

    client = ClientReferentiels(
        "http://api/", client=httpx.Client(transport=httpx.MockTransport(gestionnaire))
    )
    r = executer_outil(client, "chercher_communes", '{"nom": "Gotham", "code_postal": null}')
    assert recu == {"url": "http://api/v1/referentiels/communes", "corps": {"nom": "Gotham"}}
    assert r.statut == "hors_corpus" and r.communes == []


def test_cumul_des_jetons_et_du_cout() -> None:
    def avec_cout(reponse: ReponseChat) -> ReponseChat:
        return ReponseChat(
            **{**reponse.__dict__, "jetons_entree": 100, "jetons_sortie": 10, "cout_micro_eur": 50}
        )

    r, _, _ = lancer(
        [avec_cout(appel_communes(nom="Vincennes")), avec_cout(reponse_faux(contenu=sortie()))]
    )
    assert (r.jetons_entree, r.jetons_sortie, r.cout_micro_eur) == (200, 20, 100)


def test_journaux_sans_contenu(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        lancer(
            [
                appel_communes(nom="Vincennes"),
                reponse_faux(contenu="pas du JSON"),
                reponse_faux(contenu=sortie()),
            ]
        )
    journaux = "\n".join(r.getMessage() for r in caplog.records)
    assert "agent.fin" in journaux and "agent.outil" in journaux
    for secret in ("Claire", "Petit", "Fontenay", "06 99", "Vincennes", "grésille"):
        assert secret not in journaux


def test_normalisation_benigne_d_une_valeur_nulle() -> None:
    """Numéro absent : confiance et origine remises à vide ; aucune valeur créée ni modifiée."""
    donnees = json.loads(sortie())
    donnees["client"]["telephone"] = {"value": None, "confidence": 0.4, "origin": "caller_id"}
    donnees["client"]["nom"] = {"value": "Petit", "confidence": 0.3}
    normaliser_sortie(donnees)
    assert donnees["client"]["telephone"] == {"value": None, "confidence": 0, "origin": None}
    assert donnees["client"]["nom"] == {"value": "Petit", "confidence": 0.3}
    r, _, _ = lancer(
        [reponse_faux(contenu=json.dumps(json.loads(sortie()) | {"client": donnees["client"]}))]
    )
    assert r.statut == "complete" and r.tentatives == 1


def test_panne_imprevue_d_un_referentiel_ne_leve_pas() -> None:
    """Toute panne d'un référentiel, même hors httpx, donne « indisponible » (D-29)."""
    from muninn.extraction.outils import executer_outil

    class EnPanne:
        def communes(self, corps: dict[str, str]) -> dict[str, object]:
            raise ConnectionError

        def termes(self, corps: dict[str, str]) -> dict[str, object]:
            raise OSError

    r = executer_outil(EnPanne(), "chercher_communes", '{"nom": "Montreuil", "code_postal": null}')
    assert r.statut == "indisponible"
