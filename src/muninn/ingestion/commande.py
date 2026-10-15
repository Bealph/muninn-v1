"""Commande `muninn-ingestion` : rejoue le pipeline, en entier ou pour une source.

Usage : `muninn-ingestion tout`, ou une source : `cog`, `codes-postaux`, `api-geo`.
Une source inchangée (même empreinte que la version servie) ne crée aucune version. Code de
sortie 1 si une version échoue à ses contrôles bloquants.
"""

import argparse
import sys
from collections.abc import Callable

import httpx

from muninn.ingestion import api_geo, codes_postaux, cog
from muninn.ingestion.telechargement import client_http, telecharger
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


ETAPES: dict[str, Callable[[Connexion, httpx.Client], Resultat]] = {
    "cog": ingerer_cog,
    "codes-postaux": ingerer_codes_postaux,
    "api-geo": ingerer_api_geo,
}


def afficher(resultat: Resultat) -> None:
    if resultat.statut == "inchange":
        print(
            f"{resultat.jeu} : inchangée, même empreinte que la version servie"
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
    parser.add_argument("source", choices=["tout", *ETAPES])
    args = parser.parse_args(argv)
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
