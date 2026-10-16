"""Règles du contrat que le JSON Schema n'exprime pas (contrat d'API, § 3.3 et § 3.4, fin).

- règle 1 : un champ est « à vérifier » si sa confiance est sous 0,7 ou s'il est manquant ;
- règle 2 : un champ `mismatch` ou `not_checked` a sa confiance ramenée à 0,6 au plus ;
- règle 5 : `champs_manquants` liste exactement les chemins des champs à confiance dont la
  valeur est nulle ; `rdv_propose`, `actions` et `cle_humaine` n'y figurent jamais.

Le serveur recalcule `champs_manquants` à partir des valeurs : il ne reprend pas la liste du
modèle. `verifier_regles` sert de garde finale avant toute émission d'un brouillon.
"""

from muninn.extraction.contrat import (
    CHEMINS_CHAMPS,
    Client,
    Demande,
    DossierDraft,
)

SEUIL_A_VERIFIER = 0.7  # [H : seuil recalibré par ADR-08], contrat § 3.3, règle 1
PLAFOND_CONTROLE = 0.6  # [H : ADR-08], contrat § 3.3, règle 2
JAMAIS_MANQUANTS = frozenset({"demande.rdv_propose", "actions", "cle_humaine"})


def valeurs_a_confiance(client: Client, demande: Demande) -> dict[str, tuple[object, float]]:
    """Chemin, valeur et confiance de chaque champ qui porte une confiance."""
    return {
        "client.nom": (client.nom.value, client.nom.confidence),
        "client.prenom": (client.prenom.value, client.prenom.confidence),
        "client.telephone": (client.telephone.value, client.telephone.confidence),
        "client.adresse.rue": (client.adresse.rue.value, client.adresse.rue.confidence),
        "client.adresse.code_postal": (
            client.adresse.code_postal.value,
            client.adresse.code_postal.confidence,
        ),
        "client.adresse.commune": (
            client.adresse.commune.value,
            client.adresse.commune.confidence,
        ),
        "demande.objet_court": (demande.objet_court.value, demande.objet_court.confidence),
        "demande.description": (demande.description.value, demande.description.confidence),
    }


def calculer_champs_manquants(client: Client, demande: Demande) -> list[str]:
    """Règle 5 : les chemins des champs à confiance dont la valeur est nulle, dans l'ordre."""
    nuls = {c for c, (valeur, _) in valeurs_a_confiance(client, demande).items() if valeur is None}
    return [c for c in CHEMINS_CHAMPS if c in nuls]


def plafonner(confiance: float, statut: str) -> float:
    """Règle 2 : un champ incohérent ou non contrôlé reste « à vérifier »."""
    if statut in ("mismatch", "not_checked"):
        return min(confiance, PLAFOND_CONTROLE)
    return confiance


def champs_a_verifier(dossier: DossierDraft) -> list[str]:
    """Règle 1 : chemins des champs à confiance sous le seuil ou manquants."""
    manquants = set(dossier.champs_manquants)
    return [
        chemin
        for chemin, (_, confiance) in valeurs_a_confiance(dossier.client, dossier.demande).items()
        if confiance < SEUIL_A_VERIFIER or chemin in manquants
    ]


def verifier_regles(dossier: DossierDraft) -> list[str]:
    """Rend les règles violées (vide si le brouillon est conforme) ; jamais une valeur."""
    ecarts: list[str] = []
    attendus = calculer_champs_manquants(dossier.client, dossier.demande)
    if sorted(dossier.champs_manquants) != sorted(attendus):
        ecarts.append("regle_5_champs_manquants")
    if JAMAIS_MANQUANTS & set(dossier.champs_manquants):
        ecarts.append("regle_5_chemin_interdit")
    adresse = dossier.client.adresse
    for confiance, statut in (
        (adresse.code_postal.confidence, dossier.checks.code_postal.status),
        (adresse.commune.confidence, dossier.checks.commune.status),
    ):
        if statut in ("mismatch", "not_checked") and confiance > PLAFOND_CONTROLE:
            ecarts.append("regle_2_plafond")
    if (adresse.code_postal.value is None) != (dossier.checks.code_postal.reason == "no_value"):
        ecarts.append("regle_4_code_postal")
    if (adresse.commune.value is None) != (dossier.checks.commune.reason == "no_value"):
        ecarts.append("regle_4_commune")
    if (dossier.client.telephone.value is None) != (dossier.checks.telephone.reason == "no_value"):
        ecarts.append("regle_4_telephone")
    return ecarts
