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
porter de chiffre (numéro de téléphone, numéro de rue), sauf une forme bruitée d'un nombre du
dialogue, à sa place, une fois par appel : « 000 » entendu pour « 00 » (un chiffre répété une
fois de plus ou de moins, même nombre de groupes ; un autre chiffre est refusé). Reste une
tolérance de cinq mots sans chiffre, nécessaire aux écarts de la transcription (homophones,
accords) : un prénom, un nom et une ville peuvent y tenir ; le risque est accepté par
le porteur et consigné (revue de sécurité de l'étape 6, mesure de CA-8 du 26 octobre 2026).

Les heures écrites « 8h » ou « 8h30 » par la transcription sont lues « 8 heures » ou « 8 heures
30 », comme dans les dialogues du jeu.
"""

import re
import unicodedata
from difflib import SequenceMatcher

from muninn.voix.contrat import Tour

RAPPEL_MIN = 0.9
PRECISION_MIN = 0.95
MOTS_EN_TROP_MAX = 5
_HEURE = re.compile(r"\b(\d{1,2})h(\d{2})?\b")


def mots(texte: str) -> list[str]:
    """Les mots d'un texte, en minuscules, sans accents ni ponctuation."""
    sans_accents = unicodedata.normalize("NFKD", texte.lower())
    simple = "".join(c for c in sans_accents if not unicodedata.combining(c))
    simple = _HEURE.sub(lambda m: f"{m.group(1)} heures {m.group(2) or ''}", simple)
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


def _repetition(court: str, long_: str) -> bool:
    """Vrai si `long_` est `court` avec un chiffre répété une fois de plus (« 00 » → « 000 »)."""
    return len(long_) == len(court) + 1 and any(
        long_[:i] + long_[i + 1 :] == court
        and (
            (i > 0 and long_[i - 1] == long_[i])
            or (i + 1 < len(long_) and long_[i + 1] == long_[i])
        )
        for i in range(len(long_))
    )


def _groupes_bruites(dits: list[str], entendus: list[str]) -> int | None:
    """Nombre de nombres dits entendus avec un chiffre répété en plus ou en moins, à leur place ;
    `None` si un mot diffère autrement (autre chiffre, autre mot, autre nombre de groupes)."""
    if len(dits) != len(entendus):
        return None
    bruites = 0
    for d, e in zip(dits, entendus, strict=True):
        if d == e:
            continue
        if not (d.isdigit() and e.isdigit()):
            return None
        court, long_ = sorted((d, e), key=len)
        if not _repetition(court, long_):
            return None
        bruites += 1
    return bruites


def chiffres_en_trop(entendus: list[Tour], dialogue: list[Tour]) -> bool:
    """Vrai si un mot entendu en trop (absent, répété ou déplacé) porte un chiffre. Seul bruit
    toléré, une fois par appel : un nombre du dialogue, à sa place, entendu avec un chiffre répété
    en plus ou en moins (« 00 » entendu « 000 », constaté sur SC-01). Revue de sécurité : un chiffre
    quelconque ajouté, ou plusieurs groupes touchés, composeraient un autre numéro."""
    dit = [m for t in dialogue for m in mots(t.texte)]
    entendu = [m for t in entendus for m in mots(t.texte)]
    tolere = 1
    for etiquette, i1, i2, j1, j2 in SequenceMatcher(
        None, dit, entendu, autojunk=False
    ).get_opcodes():
        if etiquette not in ("insert", "replace"):
            continue
        ajoutes = entendu[j1:j2]
        if not any(any(c.isdigit() for c in m) for m in ajoutes):
            continue
        bruites = _groupes_bruites(dit[i1:i2], ajoutes) if etiquette == "replace" else None
        if bruites is not None and bruites <= tolere:
            tolere -= bruites
            continue
        return True
    return False


def conforme_au_dialogue(entendus: list[Tour], dialogue: list[Tour]) -> bool:
    """Vrai si l'entendu reprend le dialogue du scénario, et rien d'autre."""
    rappel, precision, en_trop = fidelite(entendus, dialogue)
    return (
        rappel >= RAPPEL_MIN
        and precision >= PRECISION_MIN
        and en_trop <= MOTS_EN_TROP_MAX
        and not chiffres_en_trop(entendus, dialogue)
    )
