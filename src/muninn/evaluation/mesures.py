"""Comparaison d'un brouillon à la vérité terrain, et contrôles des cas bloquants (sans réseau).

Règles du dossier V1 (§ 6) et de la phase 1 (document 04, § 3.3) : nom et commune comparés après
normalisation ; code postal à l'égalité ; téléphone au format +33 ; objet dans la liste acceptée ;
urgence à l'égalité. Un champ attendu nul est exact s'il est resté vide ; une valeur à sa place est
une invention (VE-12).
"""

import math
from typing import Any

from muninn.extraction.contrat import DossierDraft
from muninn.extraction.entree import normaliser
from muninn.extraction.evaluateur import ACTION_GAZ, Extraction

CHAMPS = ("nom", "telephone", "code_postal", "commune", "objet", "urgence")
Z = 1.96


def wilson(succes: int, total: int) -> tuple[float, float]:
    """Intervalle de score de Wilson à 95 % (phase 1, document 04, § 4.4)."""
    if total == 0:
        return 0.0, 1.0
    p = succes / total
    centre = (p + Z**2 / (2 * total)) / (1 + Z**2 / total)
    marge = Z * math.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2)) / (1 + Z**2 / total)
    return round(max(0.0, centre - marge), 3), round(min(1.0, centre + marge), 3)


def valeurs(b: DossierDraft) -> dict[str, str | None]:
    return {
        "nom": b.client.nom.value,
        "telephone": b.client.telephone.value,
        "code_postal": b.client.adresse.code_postal.value,
        "commune": b.client.adresse.commune.value,
        "objet": b.demande.objet_court.value,
        "urgence": b.demande.urgence,
    }


def contient_racines(texte: str, ensembles: list[list[str]]) -> bool:
    """Vrai si, pour l'un des ensembles, chaque racine commence un mot du texte (oracle v2)."""
    mots = normaliser(texte).split()
    return any(all(any(m.startswith(r) for m in mots) for r in e) for e in ensembles if e)


def comparer(verite: dict[str, Any], b: DossierDraft) -> dict[str, dict[str, Any]]:
    """Par champ : exact ou non, et si une valeur a été inventée à la place d'un champ absent."""
    v = valeurs(b)
    attendus = {
        "nom": verite["nom"],
        "telephone": verite["telephone"],
        "code_postal": verite["code_postal"],
        "commune": verite["commune"],
        "objet": verite["objet_dans"] or None,
        "urgence": verite["urgence"],
    }
    resultat: dict[str, dict[str, Any]] = {}
    for champ, attendu in attendus.items():
        obtenu = v[champ]
        if attendu is None:
            exact, invente = obtenu is None, obtenu is not None
        elif champ in ("nom", "commune"):
            exact, invente = obtenu is not None and normaliser(obtenu) == normaliser(attendu), False
        elif champ == "objet":
            liste = {normaliser(o) for o in attendu}
            exact = obtenu is not None and (
                normaliser(obtenu) in liste
                or contient_racines(obtenu, verite.get("objet_racines") or [])
            )
            invente = False
        else:
            exact, invente = obtenu == attendu, False
        resultat[champ] = {"exact": exact, "invente": invente, "absent_attendu": attendu is None}
    return resultat


def textes(b: DossierDraft) -> str:
    """Tous les textes libres du brouillon, normalisés (VE-13, VE-20)."""
    morceaux = [
        b.demande.objet_court.value,
        b.demande.description.value,
        b.cle_humaine,
        *(a.libelle for a in b.actions),
        *(d.value for d in b.demande.disponibilites_client),
    ]
    return " " + normaliser(" ".join(m for m in morceaux if m)) + " "


def controler_conformite(s: dict[str, Any], x: Extraction | None) -> list[str]:
    """Écarts d'un cas de conformité, à tolérance nulle ; vide si conforme."""
    if x is None:
        return ["aucun brouillon (refus)"]
    b, c, v = x.brouillon, s.get("controles", {}), s["verite"]
    ecarts: list[str] = []
    texte = textes(b)
    for terme in c.get("termes_interdits", []):
        if f" {normaliser(terme)} " in texte:
            ecarts.append(f"terme de santé : {terme}")
    for terme in c.get("termes_promesse", []):
        if normaliser(terme) in texte:
            ecarts.append(f"promesse : {terme}")
    if c.get("action_gaz_en_tete"):
        if b.demande.urgence != "securite" or b.demande.rdv_propose is not None:
            ecarts.append("urgence de sécurité")
        if not b.actions or b.actions[0] != ACTION_GAZ:
            ecarts.append("orientation gaz en tête")
    if "urgence_differente_de" in c and b.demande.urgence == c["urgence_differente_de"]:
        ecarts.append("urgence de sécurité à tort")
    if c.get("refus"):
        vals = valeurs(b)
        if b.client.telephone.origin != "caller_id" or vals["telephone"] != v["telephone"]:
            ecarts.append("numéro présenté")
        if any(vals[k] is not None for k in ("nom", "code_postal", "commune", "objet")):
            ecarts.append("champ rempli malgré le refus")
        if [a.type for a in b.actions] != ["rappeler"]:
            ecarts.append("une seule action « rappeler »")
    if c.get("a_verifier") and not x.enveloppe.a_verifier:
        ecarts.append("à vérifier")
    if not c.get("refus") and "urgence_differente_de" not in c:
        if b.demande.urgence != v["urgence"]:
            ecarts.append(f"urgence {v['urgence']}")
    return ecarts


def percentile(valeurs_ms: list[int], q: float) -> int:
    """Percentile par rang le plus proche ; sur 20 valeurs, une estimation grossière (dite)."""
    if not valeurs_ms:
        return 0
    ordre = sorted(valeurs_ms)
    return ordre[min(len(ordre) - 1, max(0, math.ceil(q * len(ordre)) - 1))]
