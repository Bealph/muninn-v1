"""Garde-fous de sortie (sprint 4, étape 7), pour toute sortie du modèle : dossier et message.

- **Fuite** : un texte qui contient le jeton témoin des consignes, ou un motif de secret ou de clé,
  est vidé ; le dossier devient « à vérifier ». La règle contre l'invention, dans l'évaluateur,
  couvre les valeurs qui ne sont ni dites, ni rendues par un outil.
- **Hors rôle** : la sortie est limitée au schéma fermé (sortie structurée stricte) ; dans les
  textes libres, les liens sont retirés et la syntaxe Markdown ou HTML est enlevée. L'affichage
  échappe en plus tout texte (écran « Agent », étape 8).

Les listes sont fermées et versionnées avec le code (empreinte d'évaluation). Rien n'est journalisé
ici : l'appelant journalise le garde-fou déclenché, jamais le texte.
"""

import re
from collections.abc import Callable
from typing import Any, Literal

from pydantic import ValidationError

from muninn.extraction.entree import nettoyer

GardeFouSortie = Literal["fuite", "hors_role"]

# Jeton témoin : présent dans chaque consigne, il ne doit jamais apparaître dans une sortie.
MOTIF_TEMOIN = re.compile(r"TEMOIN-[0-9a-f]{12}", re.IGNORECASE)
MOTIFS_SECRETS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(m)
    for m in (
        r"\bsk-[A-Za-z0-9_-]{16,}",  # clés d'API au format OpenAI et apparentés
        r"\bsk-ant-[A-Za-z0-9_-]{16,}",
        r"\bAKIA[0-9A-Z]{16}\b",  # AWS
        r"\bgh[pousr]_[A-Za-z0-9]{30,}",  # GitHub
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.",  # jeton JWT
        r"(?i)\b(?:AccountKey|SharedAccessKey|api[_-]?key|password|passwd|secret)\s*[=:]\s*\S+",
        r"(?i)\bmot de passe\s*[=:]\s*\S+",
        r"\b[0-9a-fA-F]{32,}\b",  # clé hexadécimale (Azure, par exemple)
    )
)
MOTIF_LIEN = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
MOTIF_LIEN_MARKDOWN = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MOTIF_BALISE = re.compile(r"<[^>]{0,200}>")
CARACTERES_BALISAGE = re.compile(r"[*`#|~<>\[\]{}]")
ESPACES = re.compile(r"[ \t]{2,}")


def fuite(texte: str) -> bool:
    return MOTIF_TEMOIN.search(texte) is not None or any(m.search(texte) for m in MOTIFS_SECRETS)


def _nettoyer_une_fois(texte: str) -> str:
    propre, _ = nettoyer(texte)  # caractères invisibles et de contrôle
    propre = MOTIF_LIEN_MARKDOWN.sub(r"\1", propre)
    propre = MOTIF_LIEN.sub("", propre)
    propre = MOTIF_BALISE.sub("", propre)
    propre = CARACTERES_BALISAGE.sub("", propre)
    return ESPACES.sub(" ", propre).strip()


def assainir(texte: str) -> tuple[str | None, set[GardeFouSortie]]:
    """Texte vidé s'il fuit ; sinon, sans lien ni balisage. Rend les garde-fous déclenchés.

    Le nettoyage est répété jusqu'à un point fixe, et la fuite cherchée à chaque tour : un jeton
    coupé par un caractère de balisage ou invisible est vu une fois recollé.
    """
    propre = texte
    while True:  # chaque tour raccourcit le texte, ou s'arrête : la boucle termine
        if fuite(propre):
            return None, {"fuite"}
        suivant = _nettoyer_une_fois(propre)
        if suivant == propre:
            break
        propre = suivant
    if propre == texte:
        return texte, set()
    return (propre or None), {"hors_role"}


def assainir_arbre(donnees: Any) -> tuple[Any, set[GardeFouSortie]]:
    """Applique `assainir` à chaque texte d'une sortie sérialisée (`model_dump`).

    Une valeur vidée garde la forme du contrat : `value` à null, confiance 0, origine nulle ; un
    élément de liste vidé est retiré ; une clé simple vidée passe à null.
    """
    declenches: set[GardeFouSortie] = set()

    def texte(valeur: str) -> str | None:
        propre, g = assainir(valeur)
        declenches.update(g)
        return propre

    def visiter(noeud: Any) -> Any:
        if isinstance(noeud, dict):
            if "confidence" in noeud and isinstance(noeud.get("value"), str):
                noeud = dict(noeud, value=texte(noeud["value"]))
                if noeud["value"] is None:
                    noeud["confidence"] = 0
                    if "origin" in noeud:
                        noeud["origin"] = None
            return {cle: visiter(v) for cle, v in noeud.items()}
        if isinstance(noeud, list):
            elements = [visiter(v) for v in noeud]
            return [e for e in elements if not _vide(e)]
        if isinstance(noeud, str):
            return texte(noeud)
        return noeud

    return visiter(donnees), declenches


def _vide(element: Any) -> bool:
    """Un élément de liste vidé : un texte nul, ou une action sans libellé."""
    if element is None:
        return True
    return isinstance(element, dict) and "libelle" in element and element["libelle"] is None


def appliquer(
    donnees: dict[str, Any],
    valider: Callable[[dict[str, Any]], Any],
    facultatifs: tuple[str, ...] = (),
) -> tuple[Any | None, set[GardeFouSortie]]:
    """Assainit une sortie et la revalide par son contrat.

    Un texte raccourci peut passer sous une longueur minimale du contrat : les champs
    `facultatifs` (nullables, recalculés par le serveur) sont alors mis à null et la validation
    refaite une fois. Si elle échoue encore, rend None : l'appelant se replie sur un brouillon de
    secours ; l'erreur n'est jamais journalisée avec sa valeur.
    """
    propre, declenches = assainir_arbre(donnees)
    try:
        return valider(propre), declenches
    except ValidationError:
        pass
    try:
        return valider(propre | dict.fromkeys(facultatifs)), declenches
    except ValidationError:
        return None, declenches
