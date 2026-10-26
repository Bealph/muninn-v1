"""Faux fournisseur de voix : déterministe, sans réseau, pour les tests, la CI et le local.

Un « extrait » est un préfixe fixe suivi du tour en JSON. La console renvoie les extraits mis
bout à bout : `transcrire` découpe donc la concaténation sur le préfixe, et rend les tours comme
le ferait la transcription réelle (phrases consécutives d'un même locuteur réunies en un tour).
Ce n'est pas du MP3 : seul ce faux sait le relire.
"""

import json

from muninn.voix.contrat import ErreurVoix, Tour

# Les octets nuls n'apparaissent jamais dans du JSON (ils y sont échappés) : le préfixe ne peut
# pas se confondre avec le contenu d'un tour.
PREFIXE = b"\x00MUNINN-FAUSSE-VOIX\x00"


class FauxFournisseurVoix:
    """Synthèse et transcription simulées ; même interface que le fournisseur Azure."""

    nom = "faux"

    def synthetiser(self, tour: Tour) -> bytes:
        corps = {"locuteur": tour.locuteur, "texte": tour.texte}
        return PREFIXE + json.dumps(corps, ensure_ascii=False).encode("utf-8")

    def transcrire(self, audio: bytes) -> list[Tour]:
        morceaux = audio.split(PREFIXE)
        if len(morceaux) < 2 or morceaux[0]:
            raise ErreurVoix("Audio illisible par le faux fournisseur.")
        tours: list[Tour] = []
        for morceau in morceaux[1:]:
            try:
                corps = json.loads(morceau.decode("utf-8"))
                locuteur, texte = corps["locuteur"], str(corps["texte"])
            except (ValueError, KeyError, TypeError) as exc:
                raise ErreurVoix("Audio illisible par le faux fournisseur.") from exc
            if locuteur not in ("agent", "caller"):
                raise ErreurVoix("Audio illisible par le faux fournisseur.")
            if tours and tours[-1].locuteur == locuteur:
                tours[-1] = Tour(locuteur, f"{tours[-1].texte} {texte}")
            else:
                tours.append(Tour(locuteur, texte))
        return tours
