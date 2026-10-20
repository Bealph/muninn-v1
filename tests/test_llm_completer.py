"""Étape de conversation avec outils et sortie structurée (sprint 4, étape 2), sans réseau."""

import json
import logging
from typing import Any

import httpx
import pytest

from muninn.extraction.paquet import charger_paquet
from muninn.llm.fournisseur import (
    DelaiDepasse,
    ErreurFournisseur,
    FauxFournisseur,
    FournisseurAzure,
    RefusContenu,
    RequeteChat,
    cout_micro_eur,
    message_outil,
    reponse_faux,
)

TEXTE_SENSIBLE = "Paul Martin, 06 99 00 00 01, 12 rue des Lilas"


def _azure(gestionnaire: Any) -> FournisseurAzure:
    return FournisseurAzure(
        "https://exemple.services.ai.azure.com",
        lambda: {"Authorization": "Bearer jeton-de-test"},
        client=httpx.Client(transport=httpx.MockTransport(gestionnaire)),
    )


def _requete(**autres: Any) -> RequeteChat:
    paquet = charger_paquet()
    valeurs: dict[str, Any] = {
        "modele": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": paquet.consigne},
            {"role": "user", "content": TEXTE_SENSIBLE},
        ],
        "outils": paquet.outils,
        "schema_sortie": paquet.schema_sortie,
    }
    valeurs.update(autres)
    return RequeteChat(**valeurs)


def _reponse(message: dict[str, Any], raison: str = "stop", **autres: Any) -> httpx.Response:
    corps: dict[str, Any] = {
        "model": "gpt-5.4-mini",
        "choices": [{"message": message, "finish_reason": raison}],
        "usage": {"prompt_tokens": 1000, "completion_tokens": 200},
    }
    corps.update(autres)
    return httpx.Response(200, json=corps)


def test_corps_envoye_outils_et_sortie_structuree() -> None:
    recu: dict[str, Any] = {}

    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        recu.update(json.loads(requete.content))
        return _reponse({"role": "assistant", "content": "{}"})

    _azure(gestionnaire).completer(_requete())
    assert recu["model"] == "gpt-5.4-mini"
    assert recu["parallel_tool_calls"] is False
    assert {o["function"]["name"] for o in recu["tools"]} == {
        "chercher_communes",
        "chercher_terme_metier",
    }
    assert recu["response_format"]["type"] == "json_schema"
    assert recu["response_format"]["json_schema"]["strict"] is True
    assert recu["max_completion_tokens"] == 4000
    assert "temperature" not in recu


def test_sans_outils_ni_schema() -> None:
    recu: dict[str, Any] = {}

    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        recu.update(json.loads(requete.content))
        return _reponse({"role": "assistant", "content": "ok"})

    _azure(gestionnaire).completer(_requete(outils=None, schema_sortie=None))
    assert "tools" not in recu and "parallel_tool_calls" not in recu
    assert "response_format" not in recu


def test_appels_d_outils_lus_et_remis_dans_la_conversation() -> None:
    appel = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "chercher_communes",
            "arguments": '{"nom": "Vincennes", "code_postal": null}',
        },
    }
    r = _azure(
        lambda _: _reponse(
            {"role": "assistant", "content": None, "tool_calls": [appel]}, "tool_calls"
        )
    ).completer(_requete())
    assert r.raison_fin == "tool_calls"
    assert [(a.id, a.nom) for a in r.appels_outils] == [("call_1", "chercher_communes")]
    assert json.loads(r.appels_outils[0].arguments) == {"nom": "Vincennes", "code_postal": None}
    assert r.message_assistant()["tool_calls"][0]["function"]["name"] == "chercher_communes"


def test_jetons_et_cout() -> None:
    r = _azure(lambda _: _reponse({"role": "assistant", "content": "{}"})).completer(_requete())
    assert (r.jetons_entree, r.jetons_sortie) == (1000, 200)
    # 1000 × 0,726 + 200 × 4,3559 millionièmes d'euro
    assert (
        r.cout_micro_eur
        == round(1000 * 0.726 + 200 * 4.3559)
        == cout_micro_eur("gpt-5.4-mini", 1000, 200)
    )
    assert cout_micro_eur("modele-inconnu", 1000, 200) == 0


def test_refus_du_filtre_en_entree() -> None:
    corps = {
        "error": {"code": "content_filter", "message": "The response was filtered", "status": 400}
    }
    with pytest.raises(RefusContenu):
        _azure(lambda _: httpx.Response(400, json=corps)).completer(_requete())


def test_refus_du_filtre_en_sortie() -> None:
    with pytest.raises(RefusContenu):
        _azure(
            lambda _: _reponse({"role": "assistant", "content": None}, "content_filter")
        ).completer(_requete())


def test_une_autre_erreur_400_n_est_pas_un_refus() -> None:
    with pytest.raises(ErreurFournisseur) as erreur:
        _azure(
            lambda _: httpx.Response(400, json={"error": {"code": "invalid_request"}})
        ).completer(_requete())
    assert not isinstance(erreur.value, RefusContenu)


def test_detournement_annote_sans_blocage() -> None:
    """D-65 : en « annoter seulement », la réponse arrive, avec l'annotation lue par le serveur."""
    annotation = [
        {
            "prompt_index": 0,
            "content_filter_results": {"jailbreak": {"filtered": False, "detected": True}},
        }
    ]
    r = _azure(
        lambda _: _reponse({"role": "assistant", "content": "{}"}, prompt_filter_results=annotation)
    ).completer(_requete())
    assert r.detournement_detecte is True
    sans = _azure(lambda _: _reponse({"role": "assistant", "content": "{}"})).completer(_requete())
    assert sans.detournement_detecte is False


def test_delai_depasse() -> None:
    def gestionnaire(requete: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("trop long", request=requete)

    with pytest.raises(DelaiDepasse):
        _azure(gestionnaire).completer(_requete(delai_s=0.1))


@pytest.mark.parametrize(
    "reponse",
    [
        httpx.Response(500, text="panne"),
        httpx.Response(429, json={"error": {"code": "429"}}),
        httpx.Response(200, json={"rien": 1}),
    ],
)
def test_pannes(reponse: httpx.Response) -> None:
    with pytest.raises(ErreurFournisseur) as erreur:
        _azure(lambda _: reponse).completer(_requete())
    assert not isinstance(erreur.value, (RefusContenu, DelaiDepasse))


def test_refus_du_modele_rapporte() -> None:
    r = _azure(
        lambda _: _reponse({"role": "assistant", "content": None, "refusal": "Je ne peux pas."})
    ).completer(_requete())
    assert r.refus_modele == "Je ne peux pas."


def test_journaux_sans_contenu(caplog: pytest.LogCaptureFixture) -> None:
    """R4 : ni la transcription, ni la sortie, ni les arguments d'outils dans les journaux."""
    appel = {
        "id": "c",
        "type": "function",
        "function": {"name": "chercher_communes", "arguments": '{"nom": "Lilas-SECRET"}'},
    }
    reponses = iter(
        [
            _reponse({"role": "assistant", "content": None, "tool_calls": [appel]}, "tool_calls"),
            _reponse({"role": "assistant", "content": '{"nom": "SORTIE-SECRETE"}'}),
            httpx.Response(
                400, json={"error": {"code": "content_filter", "message": TEXTE_SENSIBLE}}
            ),
        ]
    )
    fournisseur = _azure(lambda _: next(reponses))
    with caplog.at_level(logging.DEBUG):
        fournisseur.completer(_requete())
        fournisseur.completer(_requete())
        with pytest.raises(RefusContenu):
            fournisseur.completer(_requete())
    journaux = "\n".join(r.getMessage() for r in caplog.records)
    assert "llm.etape" in journaux and "llm.refus" in journaux
    for secret in ("Paul Martin", "06 99", "Lilas", "SORTIE-SECRETE", "jeton-de-test"):
        assert secret not in journaux


def test_faux_fournisseur_programmable() -> None:
    faux = FauxFournisseur(
        scenario=[
            reponse_faux(appels=[("chercher_communes", {"nom": "Vincennes", "code_postal": None})]),
            RefusContenu("bloqué"),
            reponse_faux(contenu='{"ok": true}'),
        ]
    )
    premiere = faux.completer(_requete())
    assert (
        premiere.raison_fin == "tool_calls" and premiere.appels_outils[0].nom == "chercher_communes"
    )
    with pytest.raises(RefusContenu):
        faux.completer(_requete())
    assert faux.completer(_requete()).contenu == '{"ok": true}'
    assert faux.completer(_requete()).contenu == "{}"  # scénario épuisé : réponse vide
    assert len(faux.requetes) == 4
    assert faux.requetes[0].outils is not None


def test_message_outil_sans_nom() -> None:
    r = reponse_faux(appels=[("chercher_communes", {"nom": "Vincennes", "code_postal": None})])
    assert message_outil(r.appels_outils[0], '{"statut": "trouve"}') == {
        "role": "tool",
        "tool_call_id": "appel-1",
        "content": '{"statut": "trouve"}',
    }


def _azure_qui_dort(gestionnaire: Any, attentes: list[float]) -> FournisseurAzure:
    return FournisseurAzure(
        "https://exemple.services.ai.azure.com",
        lambda: {"Authorization": "Bearer jeton-de-test"},
        client=httpx.Client(transport=httpx.MockTransport(gestionnaire)),
        dormir=attentes.append,
    )


def test_limite_de_debit_reprise_puis_reussite() -> None:
    reponses = [httpx.Response(429, headers={"Retry-After": "3"}),
                _reponse({"role": "assistant", "content": "{}"})]  # fmt: skip
    attentes: list[float] = []
    r = _azure_qui_dort(lambda requete: reponses.pop(0), attentes).completer(_requete())
    assert r.contenu == "{}" and attentes == [3.0]


def test_limite_de_debit_reprise_bornee() -> None:
    attentes: list[float] = []
    azure = _azure_qui_dort(lambda r: httpx.Response(429, headers={"Retry-After": "60"}), attentes)
    with pytest.raises(ErreurFournisseur):
        azure.completer(_requete())
    assert attentes == [10.0, 10.0]  # deux reprises, attente plafonnée
