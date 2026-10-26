"""Fidélité d'un appel joué à son scénario (étape 6) : est-ce bien le dialogue synthétique ?

`POST /v1/demo/voice/call` reçoit un audio quelconque : rien n'empêche d'y envoyer un vrai
enregistrement en le présentant comme un scénario du jeu. Le contenu n'est donc tenu pour
synthétique, et stocké comme tel (P-03), que si ce qui a été entendu reprend le dialogue du
scénario, et rien d'autre : sinon, seules les mesures sont enregistrées, comme pour un texte
libre, et le dossier ne peut pas être corrigé.

La comparaison porte sur les mots, sans accents ni ponctuation (la transcription rend « A
Montreuil » pour « À Montreuil », « souci? » pour « souci ? »), alignés dans l'ordre (plus longue
suite commune, `difflib`) : un mot du dialogue ne compte qu'une fois et qu'à sa place, si bien que
répéter ou réordonner des mots du dialogue (« 06 », « 12 »…) ne compose pas un autre numéro.
- rappel : part des mots du dialogue retrouvés, dans l'ordre, dans ce qui a été entendu ;
- précision : part des mots entendus alignés sur le dialogue ;
- mots en trop : entendus mais non alignés (absents, répétés ou déplacés).
La précision et le plafond de mots en trop ferment la porte à un enregistrement réel glissé au
milieu du dialogue ; le rappel, à un audio sans rapport. Le plafond est absolu, pas en pourcentage :
une part du dialogue, même petite, suffirait à un nom et un numéro. Aucun mot en trop ne peut
porter de chiffre (numéro de téléphone, numéro de rue). Reste une tolérance de trois mots sans
chiffre, nécessaire aux écarts de la transcription : un prénom et un nom peuvent y tenir ; le
risque est accepté et consigné (revue de sécurité de l'étape 6).
"""

import re
import unicodedata
from difflib import SequenceMatcher

from muninn.voix.contrat import Tour

RAPPEL_MIN = 0.9
PRECISION_MIN = 0.95
MOTS_EN_TROP_MAX = 3


def mots(texte: str) -> list[str]:
    """Les mots d'un texte, en minuscules, sans accents ni ponctuation."""
    sans_accents = unicodedata.normalize("NFKD", texte.lower())
    simple = "".join(c for c in sans_accents if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", simple)


def alignement(entendus: list[Tour], dialogue: list[Tour]) -> tuple[int, int, list[str]]:
    """Nombre de mots dits, nombre de mots entendus alignés dans l'ordre, et mots en trop."""
    dit = [m for t in dialogue for m in mots(t.texte)]
    entendu = [m for t in entendus for m in mots(t.texte)]
    alignes: set[int] = set()
    for bloc in SequenceMatcher(None, dit, entendu, autojunk=False).get_matching_blocks():
        alignes.update(range(bloc.b, bloc.b + bloc.size))
    return len(dit), len(alignes), [m for i, m in enumerate(entendu) if i not in alignes]


def fidelite(entendus: list[Tour], dialogue: list[Tour]) -> tuple[float, float, int]:
    """Rappel, précision et nombre de mots en trop de l'entendu par rapport au dialogue."""
    nb_dit, communs, restes = alignement(entendus, dialogue)
    nb_entendu = communs + len(restes)
    rappel = communs / nb_dit if nb_dit else 0.0
    precision = communs / nb_entendu if nb_entendu else 0.0
    return rappel, precision, len(restes)


def chiffres_en_trop(entendus: list[Tour], dialogue: list[Tour]) -> bool:
    """Vrai si un mot entendu en trop (absent, répété ou déplacé) porte un chiffre."""
    return any(any(c.isdigit() for c in m) for m in alignement(entendus, dialogue)[2])


def conforme_au_dialogue(entendus: list[Tour], dialogue: list[Tour]) -> bool:
    """Vrai si l'entendu reprend le dialogue du scénario, et rien d'autre."""
    rappel, precision, en_trop = fidelite(entendus, dialogue)
    return (
        rappel >= RAPPEL_MIN
        and precision >= PRECISION_MIN
        and en_trop <= MOTS_EN_TROP_MAX
        and not chiffres_en_trop(entendus, dialogue)
    )
