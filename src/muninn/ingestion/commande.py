"""Commande `muninn-ingestion` : rejoue le pipeline, en entier ou pour une source.

Usage : `muninn-ingestion tout`, ou une étape : `cog`, `codes-postaux`, `api-geo`, `lexique`.
`muninn-ingestion lexique-secours` réécrit l'instantané de secours du lexique, sans base.
Une source inchangée (même empreinte que la version servie) ne crée aucune version. Code de
sortie 1 si une version échoue à ses contrôles bloquants.
"""

import argparse
import sys
from collections.abc import Callable

import httpx

from muninn.ingestion import api_geo, codes_postaux, cog, lexique
from muninn.ingestion.telechargement import FichierRecu, client_http, telecharger
from muninn.ingestion.versions import Connexion, Resultat, charger, connecter, version_publiee


def ingerer_cog(conn: Connexion, client: httpx.Client) -> Resultat:
    fichier = telecharger(cog.URL, client)
    return charger(
        conn,
        jeu=cog.JEU,
        source_id=cog.SOURCE,
        fichier=fichier,
        date_source=cog.date_source(fichier),
        lecture=cog.lire(fichier.contenu),
        inserer=cog.inserer,
        controler=cog.controler,
    )


def ingerer_codes_postaux(conn: Connexion, client: httpx.Client) -> Resultat:
    servie = version_publiee(conn, cog.JEU)
    if servie is None:
        raise RuntimeError("Codes postaux : aucune version du COG publiée ; lancer d'abord `cog`")
    codes = {
        str(ligne[0])
        for ligne in conn.execute(
            "SELECT DISTINCT insee_code FROM ref.communes WHERE version_id = %s", [servie[0]]
        )
    }
    fichier = telecharger(codes_postaux.URL, client)
    lecture = codes_postaux.lire(fichier.contenu, codes)
    return charger(
        conn,
        jeu=codes_postaux.JEU,
        source_id=codes_postaux.SOURCE,
        fichier=fichier,
        date_source=codes_postaux.date_source(fichier),
        lecture=lecture,
        inserer=codes_postaux.inserer,
        controler=codes_postaux.controleur(lecture, servie[0]),
    )


def ingerer_api_geo(conn: Connexion, client: httpx.Client) -> Resultat:
    servie = version_publiee(conn, cog.JEU)
    if servie is None:
        raise RuntimeError("API Géo : aucune version du COG publiée ; lancer d'abord `cog`")
    communes_cog = {
        str(code): str(nom)
        for code, nom in conn.execute(
            "SELECT insee_code, name FROM ref.communes"
            " WHERE version_id = %s AND commune_type = 'COM'",
            [servie[0]],
        )
    }
    codes = version_publiee(conn, codes_postaux.JEU)
    fichier = telecharger(api_geo.URL, client)
    lecture = api_geo.lire(fichier.contenu)
    return charger(
        conn,
        jeu=api_geo.JEU,
        source_id=api_geo.SOURCE,
        fichier=fichier,
        date_source=api_geo.date_source(fichier),
        lecture=lecture,
        inserer=api_geo.inserateur(communes_cog),
        controler=api_geo.controleur(lecture.lignes, codes[0] if codes else None),
    )


SOURCES_LEXIQUE: dict[str, tuple[str, Callable[[bytes], list[lexique.Terme]]]] = {
    "SRC-12": (lexique.URL_WIKTIONNAIRE, lexique.lire_wiktionnaire),
    "SRC-11": (lexique.URL_WIKIDATA, lexique.lire_wikidata),
}


def collecter_lexique(
    client: httpx.Client,
) -> dict[str, tuple[list[lexique.Terme], FichierRecu]]:
    """Collecte chaque source du lexique ; une erreur sur une source est levée telle quelle."""
    collectes = {}
    for source_id, (url, lire) in SOURCES_LEXIQUE.items():
        fichier = telecharger(url, client)
        collectes[source_id] = (lire(fichier.contenu), fichier)
    return collectes


def ingerer_lexique(conn: Connexion, client: httpx.Client) -> Resultat:
    """Collecte les sources du lexique ; une source qui ne répond pas passe par le secours."""
    termes: list[lexique.Terme] = []
    sources = []
    for source_id, (url, lire) in SOURCES_LEXIQUE.items():
        try:
            fichier = telecharger(url, client)
            recus = lire(fichier.contenu)
            sources.append(lexique.source_rapport(source_id, fichier, len(recus)))
        except (httpx.HTTPError, ValueError, KeyError) as erreur:
            recus, rapport = lexique.lire_secours(source_id, f"{type(erreur).__name__}: {erreur}")
            sources.append(rapport)
            print(f"   {source_id} indisponible, instantané de secours utilisé : {erreur}")
        termes.extend(recus)
    return lexique.construire(conn, termes, sources)


ETAPES: dict[str, Callable[[Connexion, httpx.Client], Resultat]] = {
    "cog": ingerer_cog,
    "codes-postaux": ingerer_codes_postaux,
    "api-geo": ingerer_api_geo,
    "lexique": ingerer_lexique,
}


def afficher(resultat: Resultat) -> None:
    if resultat.statut == "inchange":
        print(
            f"{resultat.jeu} : inchangée, même empreinte que la dernière version"
            f" ({resultat.version_id}) ; aucune version créée"
        )
        return
    print(
        f"{resultat.jeu} : {resultat.statut} (version {resultat.version_id}) ; lues"
        f" {resultat.lues}, chargées {resultat.chargees}, filtrées {resultat.filtrees},"
        f" rejetées {resultat.rejetees}"
    )
    for controle in resultat.controles:
        etat = "ok" if controle.reussi else ("ÉCHEC" if controle.bloquant else "à relire")
        print(f"   {controle.cas} {etat} : {controle.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="muninn-ingestion", description=__doc__)
    parser.add_argument("source", choices=["tout", *ETAPES, "lexique-secours"])
    args = parser.parse_args(argv)
    if args.source == "lexique-secours":  # sans base : réécrit l'instantané de secours
        with client_http() as client:
            lexique.ecrire_secours(collecter_lexique(client))
        print(f"Instantané écrit : {lexique.FICHIER_SECOURS}")
        return 0
    etapes = list(ETAPES) if args.source == "tout" else [args.source]
    echec = False
    with connecter() as conn, client_http() as client:
        for nom in etapes:
            resultat = ETAPES[nom](conn, client)
            afficher(resultat)
            echec = echec or resultat.statut == "failed"
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
