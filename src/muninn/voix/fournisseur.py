"""Choix du fournisseur de voix selon la configuration (`VOIX_FOURNISSEUR`)."""

from muninn.core.config import Settings
from muninn.voix.contrat import FournisseurVoix


def construire_fournisseur_voix(reglages: Settings) -> FournisseurVoix:
    """Le faux par défaut ; Azure AI Speech si `VOIX_FOURNISSEUR=azure`.

    Le faux n'est admis qu'en local (tests, CI, poste) : il accepte du texte déguisé en audio, et
    une API publique déployée sans `13-voix.sh` le servirait (revue de sécurité de l'étape 6).
    Ailleurs, la configuration est tenue pour incomplète : `ValueError`, rendue en 503.
    """
    if reglages.voix_fournisseur == "faux":
        if reglages.environment != "local":
            raise ValueError("VOIX_FOURNISSEUR=azure est requis hors de l'environnement local.")
        from muninn.voix.faux import FauxFournisseurVoix

        return FauxFournisseurVoix()
    if not reglages.speech_endpoint:
        raise ValueError("SPEECH_ENDPOINT est requis quand VOIX_FOURNISSEUR=azure.")
    if not reglages.speech_resource_id:
        raise ValueError("SPEECH_RESOURCE_ID est requis quand VOIX_FOURNISSEUR=azure.")
    from muninn.voix.azure import FournisseurVoixAzure, jeton_entra

    return FournisseurVoixAzure(
        reglages.speech_region, reglages.speech_endpoint, reglages.speech_resource_id,
        jeton_entra(),
    )  # fmt: skip
