# Sprint 5 : les traitements enregistrés

Étape 1 de la checklist (V-09, V-10 ; D-82, D-85). Code : `src/muninn/traitements/`, migration
`src/muninn/db/migrations/versions/0003_traitements.py`, rôles `src/muninn/db/roles.py` ; tests :
`tests/test_enregistrement.py`, `tests/test_traitements_base.py` ; mise en production :
`infra/azure/08-traitements.sh`.

## 1. Ce qui est enregistré

| Table             | Contenu                                                                                                       | Contenu de l'appel ?                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `app.traitements` | Une ligne par appel : route, issue, refus, catégorie, statut, motifs, garde-fous, outils, jetons, coût, durée | Non : codes, nombres et booléens      |
| `app.dossiers`    | Le brouillon et son enveloppe ; état « brouillon » puis « validé » ; scénarios seulement                      | Oui : valeurs extraites, synthétiques |
| `app.messages`    | Le message d'un fournisseur ou d'un proche ; scénarios seulement                                              | Oui : synthétique                     |
| `app.corrections` | Le champ corrigé et la date (étape 2)                                                                         | Non : jamais la valeur                |

**Seuls les scénarios du jeu synthétique laissent leur contenu en base** (D-82). Un texte libre, tapé
dans l'écran « Agent » ou envoyé à l'extraction, peut contenir de vraies données personnelles : il ne
laisse que sa ligne de mesures. Relevé par la revue de sécurité automatique du commit, corrigé avant
la fusion, et testé (`test_un_texte_libre_ne_laisse_que_ses_mesures`).

Jamais la transcription, jamais l'audio : un test vérifie qu'aucune réplique du scénario n'apparaît
en base. Conservation de 30 jours : une ligne de `app.traitements` supprimée emporte son dossier, son
message et ses corrections ; purge au plus une fois par heure par processus, et par la commande
`muninn-purge`.

## 2. Qui écrit

- Rôle de groupe `<base>_app`, créé par la migration : lecture et écriture sur le seul schéma `app`.
- Rôle de connexion `<base>_traitements`, créé par la tâche des données quand son mot de passe est
  fourni ; délai de 5 s par requête.
- Le rôle de l'API (`<base>_api`) reste en lecture seule par défaut et ne voit pas le schéma `app`.

Vérifié par les tests : le rôle des traitements écrit dans `app`, ne lit pas les référentiels et ne
crée pas de table ; le rôle de l'API ne lit pas `app`.

## 3. Ce qui ne doit jamais arriver, et ce qui est prévu

| Situation                                | Comportement                                                                            |
| ---------------------------------------- | --------------------------------------------------------------------------------------- |
| `DATABASE_URL_TRAITEMENTS` absente       | L'appel est traité, rien n'est enregistré                                               |
| Base injoignable ou erreur d'écriture    | L'appel est traité ; `traitements.echec request_id=… erreur=…` journalisé, sans contenu |
| Refus (entrée vide, trop longue, filtre) | Une ligne `issue = refus` avec son code, pour le taux de refus                          |

## 4. Mise en production

1. Fusion et livraison du code : sans l'adresse du rôle, l'API traite les appels sans les
   enregistrer ; aucune coupure.
2. Le porteur lance `bash infra/azure/08-traitements.sh` (R10) : mot de passe, tâche des données
   (migration, rôle), puis adresse donnée à l'API avec une révision contrôlée.
3. Vérification : `bash infra/azure/consulter-base.sh production --traitements`.
