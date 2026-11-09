# V-2026-11-05-02 : démarchage téléphonique, les textes lus

| Champ                         | Valeur                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Date de lecture               | 2026-11-05                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Source                        | S13, Légifrance : article L. 223-1 du code de la consommation, version en vigueur depuis le 11 août 2026, <https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000051830285> ; décret n° 2026-662 du 23 juillet 2026, JORF n° 0172 du 25 juillet 2026, en vigueur le 11 août 2026 (article 5), <https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000054483939>                                                                                                                                                                                                                         |
| Entrée de collecte            | aucune : lecture à la main de S13, suite de la fiche V-2026-11-03-04 (recommandation R3 de S-2026-11-03)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Thème                         | Démarchage et téléphonie                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Vérifiée à la source primaire | Oui : L. 223-1 et décret n° 2026-662 lus sur Légifrance ; article liminaire du code (définition du consommateur), <https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000034072545>. Lue aussi : fiche de la CNIL « Prospection commerciale par téléphone (hors automate d'appel) : quelles sont les règles ? », datée du 10 juin 2026 mais citant le régime du 11 août, <https://cnil.fr/fr/prospection-commerciale-par-telephone-hors-automate-dappel-quelles-sont-les-regles>. Non lus : article 13 de la loi n° 2025-594 au JORF ; fiches de la DGCCRF (accès refusé, HTTP 403) |

## En clair

La loi interdit d'appeler un particulier pour lui proposer un service sans son accord préalable.
Rappeler un client qui vient de demander une intervention ne semble pas être de la prospection.
Mais pour les travaux d'économies d'énergie, d'énergies renouvelables ou d'adaptation du logement
(une pompe à chaleur, par exemple), le décret ne tolère ce rappel qu'à trois conditions :
l'artisan doit pouvoir prouver la demande du client, le rappeler sous cinq jours ouvrables, et
s'en tenir à ce qu'il a demandé. Relancer d'anciens clients exige leur accord ; pour ces
travaux-là, le texte l'interdit, sauf contrat en cours. Ce n'est pas un avis juridique.

## Résumé

L. 223-1, modifié par la loi n° 2025-594 du 30 juin 2025 et en vigueur depuis le 11 août 2026,
interdit de démarcher par téléphone un consommateur « qui n'a pas exprimé préalablement son
consentement ». L'interdiction ne s'applique pas à une sollicitation faite dans « l'exécution d'un
contrat en cours » et en rapport avec son objet (quatrième alinéa). Le cinquième alinéa interdit
toute prospection téléphonique pour les travaux d'économies d'énergie, d'énergies renouvelables
ou d'adaptation du logement au vieillissement ou au handicap, hors contrat en cours.

Le décret n° 2026-662, en vigueur le 11 août 2026, fixe le recueil du consentement (valable un an
au plus, sans reconduction tacite : article R. 223-1), sa preuve (conservée trois ans) et son
retrait, possible oralement. Son article R. 223-4 vise le cinquième alinéa : l'appel « en vue de
répondre à une demande d'information » du consommateur n'est pas une prospection si le
professionnel peut justifier la demande, si « l'appel est passé dans les cinq jours ouvrables
suivant la demande du consommateur », et s'il s'en tient aux biens ou services demandés ; les
justificatifs sont conservés trois ans. Le consommateur est une personne physique qui n'agit pas
pour son activité professionnelle (article liminaire) : un client professionnel sort de ce régime.

La fiche de la CNIL présente la règle des cinq jours sans la limiter à ces travaux : « Les appels
en réponse à une demande explicite d'information du consommateur sont toutefois autorisés sous
conditions strictes » ; « ils doivent se faire dans un délai de 5 jours ouvrables ».

## Impact sur Muninn

À prévoir avant tout usage réel, sans effet sur la V1, qui ne passe aucun appel. Muninn ne
démarche personne : l'artisan rappelle le client qui a appelé. Quand la demande porte sur des
travaux du cinquième alinéa (une pompe à chaleur chez un chauffagiste, par exemple), les trois
conditions de R. 223-4 s'appliquent. Un dépannage simple n'en relève pas, par interprétation ; le
cas limite est la panne qui débouche sur un remplacement par une pompe à chaleur.

Le dossier de Muninn décrit la demande et porte sa date de production (`created_at`, contrat
`DossierDraft` 1.1), quelques secondes après l'appel, et non la date de la demande elle-même. Il
ne montre pas d'échéance de rappel. Le serveur ne garde aucun dossier : le justificatif serait le
dossier daté, sur l'appareil de l'artisan, à qui l'obligation incombe ; le registre RGPD ne prévoit
pas de le garder trois ans, et garder la transcription irait contre la règle R3 de la passation.

La CNIL et le décret divergent sur la portée des cinq jours ; l'écart n'est pas tranché ici. Hors
de ces travaux, rappeler pour traiter la demande ne semble pas relever de la prospection, par
interprétation et sous réserve d'avis juridique. Relancer d'anciens clients, hors V1, demanderait
leur consentement selon R. 223-1 ; pour les travaux du cinquième alinéa, seule la relance dans un
contrat en cours (un contrat d'entretien, par exemple) resterait possible, à confirmer.

## Suite

Recommandations R1 et R2 de la synthèse S-2026-11-05 ; décision D-94 proposée.
