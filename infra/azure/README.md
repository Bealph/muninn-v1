# Ressources Azure de Muninn (V1)

Scripts versionnés qui créent les environnements de préproduction et de production (sprint 2,
étape 5). Le porteur les lance lui-même (R10) ; ils servent aussi à reconstruire l'ensemble
depuis le dépôt (étape 9). Aucun secret n'est écrit dans ces fichiers.

## Ce qui est créé

Groupe de ressources `adialloRG`, région France Central. Toutes les ressources portent
l'étiquette `projet=muninn`.

| Ressource                                     | Nom                                                      | Réglage                                                           |
| --------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------- |
| Espace Log Analytics                          | `log-muninn`                                             | 30 jours de rétention, plafond de 0,5 Go par jour                 |
| Registre d'images                             | `crmuninn`                                               | Basic, compte administrateur désactivé                            |
| Environnement Container Apps                  | `cae-muninn`                                             | Plan consommation                                                 |
| Identité d'exécution                          | `id-muninn-execution`                                    | AcrPull sur le registre ; Foundry User sur la ressource Foundry   |
| Identité de déploiement                       | `id-muninn-deploiement`                                  | AcrPush ; Container Apps Contributor ; OIDC avec GitHub Actions   |
| Serveur PostgreSQL                            | `psql-muninn`                                            | Version 16, Burstable B1ms, 32 Go, sauvegardes 7 jours            |
| Bases de données                              | `muninn_preprod`, `muninn_prod`                          | Une par environnement, sur le même serveur                        |
| Applications de préproduction                 | `ca-muninn-api-preprod`, `ca-muninn-console-preprod`     | 0 à 1 réplique, 0,5 vCPU, 1 Gio, révisions multiples              |
| Applications de production                    | `ca-muninn-api-prod`, `ca-muninn-console-prod`           | Mêmes réglages                                                    |
| Budget                                        | `budget-muninn`                                          | 60 par mois, filtré sur l'étiquette ; alertes à 50, 80 et 100 %   |

## Procédure

Dans Git Bash, depuis la racine du dépôt, sur un commit de `main` sans modification locale :

```bash
az login
python infra/azure/verifier-options.py infra/azure/*.sh   # doit finir par « options absentes : 0 »
export POSTGRES_MOT_DE_PASSE="$(openssl rand -hex 24)"   # à conserver hors du dépôt
export COURRIEL_ALERTE="adresse@exemple.fr"               # destinataire des alertes de budget
bash infra/azure/00-foundry.sh          # ressource Foundry et modèles (reconstruction seulement)
bash infra/azure/01-socle.sh            # environ 10 min (PostgreSQL est le plus long)
bash infra/azure/02-image-initiale.sh   # Docker doit tourner
bash infra/azure/03-applications.sh     # affiche les adresses et les identifiants pour GitHub
bash infra/azure/04-budget.sh
```

Le mot de passe PostgreSQL n'est stocké que dans les secrets des applications de l'API. Le
conserver dans un gestionnaire de mots de passe : il sera demandé si l'on relance le script 03.

Les scripts sont relançables : une ressource déjà présente est laissée telle quelle. Seul le
secret `database-url` des applications d'API est réécrit à chaque passage du script 03. Pour
changer le mot de passe : `az postgres flexible-server update -g adialloRG -n psql-muninn
--admin-password ...`, puis relancer le script 03 avec la nouvelle valeur.

Si un script s'arrête sur une erreur, ne pas lancer le suivant : le script 03 refuse de
s'exécuter si le serveur PostgreSQL manque.

## Coût estimé

Prix publics de détail en France Central, lus le 13 octobre 2026 (API `prices.azure.com`).

| Poste                                 | Calcul                                             | Coût mensuel estimé            |
| ------------------------------------- | -------------------------------------------------- | ------------------------------ |
| PostgreSQL B1ms                       | 0,0167 € par heure × 730 h                         | 12,2 €                         |
| Stockage PostgreSQL 32 Go             | Prix non relu                                      | environ 4 € [H]                |
| Registre Basic                        | 0,1466 € par jour × 30,4 j                         | 4,5 €                          |
| Container Apps                        | Zéro réplique au repos ; offre gratuite mensuelle  | proche de 0 €                  |
| Log Analytics                         | 2,43 € par Go ingéré ; plafond de 0,5 Go par jour  | moins de 1 € attendu           |
| Appels aux modèles                    | Essais de démonstration                            | quelques centimes              |
| **Total**                             |                                                    | **environ 21 € sur 60 €**      |

L'offre gratuite de Container Apps (180 000 vCPU-secondes, 360 000 Gio-secondes, 2 millions de
requêtes par mois) est partagée par tout l'abonnement. Le serveur PostgreSQL peut être arrêté
quand il ne sert pas : son calcul n'est alors plus facturé.

## Choix et justifications

| Choix                                                    | Raison                                                                                                     |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Budget filtré sur l'étiquette `projet=muninn`            | Le groupe de ressources héberge d'autres projets ; le porteur ne peut pas créer de groupe dédié            |
| Identités managées plutôt qu'une application Entra       | Le porteur n'a de droits que sur le groupe de ressources ; OIDC sans secret                                 |
| Une identité d'exécution affectée par l'utilisateur      | Elle existe avant les applications : les droits de tirage d'image sont posés avant leur création           |
| Préproduction et production dans le même environnement   | Une seule infrastructure à payer ; séparation par application, base et variables                           |
| Un serveur PostgreSQL, deux bases                        | Un serveur par environnement doublerait le poste le plus cher                                              |
| Accès PostgreSQL depuis les services Azure (0.0.0.0)     | Pas de réseau privé en V1 (coût et complexité) ; TLS exigé et mot de passe aléatoire de 48 caractères      |
| Une réplique au plus, zéro au repos                      | Coût et abus bornés sur une démonstration publique                                                         |
| Révisions multiples                                      | Retour arrière par le trafic, en une opération (étape 8)                                                   |

## Risques connus

- **Pare-feu PostgreSQL.** La documentation indique qu'il faut être propriétaire ou contributeur
  de l'abonnement pour créer une règle de pare-feu ; le porteur ne l'est que du groupe de
  ressources. Si le script 01 échoue à cette étape, s'arrêter et le signaler.
- **Accès depuis tout Azure.** La règle 0.0.0.0 ouvre le serveur aux services Azure de tous les
  clients, pas seulement aux nôtres. La protection repose sur TLS et sur le mot de passe.
- **Foundry User** permet aussi de lire les clés de la ressource Foundry. Rôle retenu parce que
  la documentation Foundry le recommande pour l'inférence par Entra ID, modèles non OpenAI
  compris.
- **Démarrage à froid.** Avec zéro réplique au repos, le premier appel prend plusieurs secondes.
  Avant une démonstration, passer le minimum à une réplique.
- **Monnaie du budget.** Le montant s'exprime dans la monnaie de facturation de l'abonnement.

## Sources

- OIDC avec une identité managée :
  <https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect>
- Sujet du jeton GitHub pour un environnement :
  <https://docs.github.com/en/actions/reference/security/oidc>
- Tirage d'image par identité managée :
  <https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull>
- Rôles Foundry : <https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry>
- Budget par API : <https://learn.microsoft.com/en-us/rest/api/consumption/budgets/create-or-update>
- Pare-feu PostgreSQL :
  <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-firewall-rules>
- Facturation de Container Apps : <https://learn.microsoft.com/en-us/azure/container-apps/billing>

## Livraison continue

Sur chaque fusion dans `main`, après un `verdict` vert, le workflow `ci` livre sans action
manuelle (`.github/workflows/ci.yml`, jobs `preproduction` puis `production`) :

1. connexion à Azure par OIDC avec l'identité `id-muninn-deploiement` (aucun secret) ;
2. image construite et étiquetée par le SHA du commit, poussée dans `crmuninn` ;
3. `deployer.sh preproduction <sha>` : pour l'API puis la console, nouvelle révision créée sans
   trafic, contrôlée à sa propre adresse (santé, SHA livré, appel réel au modèle A pour l'API),
   puis bascule de 100 % du trafic ; la révision précédente reste active ;
4. `deployer.sh production <sha>` : même image, mêmes contrôles.

Si un contrôle échoue, le trafic reste sur la révision précédente et la livraison s'arrête ;
la production n'est jamais touchée si la préproduction échoue. Les environnements GitHub
`preproduction` et `production` n'acceptent que les branches protégées.

## Retour arrière

Chaque livraison garde la révision précédente active, à 0 % du trafic. Le retour arrière ramène
100 % du trafic de l'API et de la console sur une révision antérieure, en une opération, sans
reconstruire d'image :

```bash
gh workflow run retour-arriere -f environnement=production          # version précédente
gh workflow run retour-arriere -f environnement=production -f sha=<sha>   # commit précis
```

Le workflow (`.github/workflows/retour-arriere.yml`) lance `retour-arriere.sh`, vérifie que
l'adresse publique sert bien le commit visé et affiche la durée mesurée. Il partage un verrou avec
la livraison du même environnement : les deux ne tournent jamais en même temps. La livraison
suivante repart de la révision servie après le retour arrière.
