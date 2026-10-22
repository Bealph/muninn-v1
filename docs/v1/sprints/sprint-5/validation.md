# Sprint 5 : correction et validation par l'artisan

Étape 2 de la checklist (V-09, CA-5 ; D-86). Code : `src/muninn/traitements/revue.py`, route
`POST /v1/demo/runs/{draft_id}/review` (`src/muninn/api/agent.py`), formulaire de l'écran « Agent »
et route `/agent/valider` (`src/muninn/console/`) ; tests : `tests/test_revue_base.py`,
`tests/test_accessibilite.py` ; vérification en production : `eval/production/verifier_ca5.py`.

## 1. Le parcours

1. Un scénario est traité : son dossier est enregistré à l'état « brouillon » (étape 1, D-82).
2. L'écran « Agent » montre le formulaire « Corriger et valider », prérempli avec les valeurs du
   dossier.
3. L'artisan corrige un champ et clique une fois sur « Valider le dossier » : la console n'envoie
   que les champs modifiés, avec leur nouvelle valeur.
4. Le serveur applique les corrections, rejoue le contrôle de la commune et du code postal avec les
   référentiels, enregistre l'état « validé » et une ligne par champ corrigé, puis rend le dossier
   à jour dans sa réponse ; l'écran affiche « Dossier validé » et les nouveaux statuts.

## 2. Ce que le serveur garantit

| Règle                                                | Comment                                                                                                                                  |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Contrôle toujours rejoué                             | La correspondance de D-69 tourne à chaque validation, corrigée ou non                                                                    |
| Une paire fausse reste signalée                      | Bagnolet et 93100 restent « incohérent » : le serveur ne maquille rien                                                                   |
| Valeur corrigée jamais gardée                        | Ni dans le dossier (il garde ses valeurs synthétiques), ni dans `app.corrections` (le chemin et la date), ni dans le journal `revue.fin` |
| Valeur hors contrat refusée, jamais vidée en silence | 422 `validation_failed`, avec le chemin du champ, jamais sa valeur                                                                       |
| Une seule validation                                 | 409 `conflict` au second essai                                                                                                           |
| Texte libre non validable                            | Son contenu n'est pas enregistré (D-82) : pas de formulaire                                                                              |
| Provenance                                           | Un champ corrigé porte « corrigé » par « l'artisan »                                                                                     |

Champs corrigeables (liste fermée) : nom, prénom, téléphone, rue, code postal, commune, objet,
urgence.

## 3. Écart au contrat, propre à la démonstration

Le contrat (§ 6.7) ne transporte que la décision et les noms des champs : dans le produit, les
valeurs restent sur l'appareil de l'artisan. En démonstration, la console joue l'appareil (P-03) et
CA-5 exige que le serveur rejoue le contrôle du code postal corrigé : la requête porte donc aussi
les valeurs, et la réponse rend le dossier (200 au lieu de 204). La décision « rejected » n'est pas
proposée en V1 (D-86).

## 4. Défauts trouvés, corrigés

**Valeurs corrigées enregistrées.** La première version gardait le dossier validé, valeurs
corrigées comprises. Le formulaire est public : on peut y taper de vraies données personnelles, ce
que D-82 exclut, et le texte de l'écran (« jamais leurs valeurs ») devenait faux. Relevé par la
revue de sécurité automatique du commit : seuls l'état, la date et les noms des champs sont
désormais enregistrés ; le dossier corrigé n'existe que dans la réponse. Test :
`test_correction_rejoue_le_controle_sans_garder_la_valeur`.

**Téléphone vidé en silence.**

Un téléphone invalide (« pas un numéro ») était vidé sans le dire, au lieu d'être refusé : seuls
les séparateurs sont désormais retirés, et ce qui reste doit être un numéro valide, sinon 422.
