# Rôle de l'identité de l'application : limité à l'inférence ?

Étape 7 du sprint 5 (reprise du sprint 4, `../sprint-4/signaux-sprint-5.md`, § 4) : « rôle de
l'identité de l'application limité à l'inférence, si le service le permet ; sinon dette
documentée ». Vérifié le 26 octobre 2026 dans la documentation de Microsoft (Microsoft Learn).

## 1. Ce que l'identité fait

`id-muninn-execution`, identité managée de l'API, appelle une seule ressource Foundry
(`adialloext-muninn1-resource`, kind `AIServices`, West Europe), sans clé (Entra) :

1. l'inférence de gpt-5.4-mini (modèle A) ;
2. l'inférence de mistral-medium-3-5 (modèle B) ;
3. Azure AI Speech : synthèse et transcription rapide (étape 6).

Elle porte le rôle intégré `53ca6127-db72-4b80-b1b0-d745d6d5456d`, posé par `01-socle.sh`.

## 2. Ce que dit la documentation

| Point                        | Constat                                                                                                                                                                                         | Source                                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Nom du rôle actuel           | « Foundry User », anciennement « Azure AI User » ; identifiant et permissions inchangés par le renommage                                                                                        | <https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry>                             |
| Ce qu'il donne               | Tout le plan de données `Microsoft.CognitiveServices/*`, et `accounts/listkeys/action` (lecture des clés) : bien plus que l'inférence. Une clé donne un accès complet, sans restriction de rôle | <https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning> |
| Modèles OpenAI               | « Cognitive Services OpenAI User » : actions de données d'inférence OpenAI seulement, sans lecture des clés                                                                                     | <https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/role-based-access-control>          |
| Modèles non OpenAI (Mistral) | Le rôle OpenAI ne les couvre pas d'après ses actions ; la doc Foundry Models donne un rôle personnalisé équivalent avec la seule action `Microsoft.CognitiveServices/accounts/MaaS/*`           | <https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/configure-entra-id>          |
| Speech                       | « Cognitive Services Speech User » : reconnaissance, transcription par lots, synthèse                                                                                                           | <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-configure-azure-ad-auth>    |
| « Cognitive Services User »  | Aussi large que Foundry User sur le plan de données, lecture des clés comprise : ne restreint rien                                                                                              | <https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning> |

Pages consultées le 26 octobre 2026.

## 3. Verdict

Le service **permet** de limiter l'identité à l'inférence, mais aucun rôle intégré unique ne le
fait : il faut trois attributions sur la ressource Foundry, dont un rôle personnalisé :

1. Cognitive Services OpenAI User (gpt-5.4-mini) ;
2. un rôle personnalisé avec la seule action de données `Microsoft.CognitiveServices/accounts/MaaS/*`
   (mistral-medium-3-5) ;
3. Cognitive Services Speech User (synthèse et transcription).

Non vérifié dans la documentation, donc à prouver par un essai : que le point d'accès d'inférence
utilisé par l'API pour gpt-5.4-mini relève bien des actions OpenAI ; que les deux adresses Speech
utilisées (synthèse régionale, transcription rapide) relèvent des actions de Speech User ; que le
rôle personnalisé suffit pour mistral-medium-3-5.

## 4. Décision : dette, traitée après le premier oral

Changer les droits de l'identité de production à deux jours du gel du 28 octobre ferait courir un
risque (403 sur l'un des trois usages) sans gain pour la démonstration. La restriction est
**reportée** après le premier oral (V1.1), selon ce plan, par le porteur (R10) :

1. créer le rôle personnalisé `MaaS/*`, limité au groupe de ressources ;
2. attribuer les trois rôles à une identité d'essai, puis rejouer avec elle les cinq appels réels
   (gpt-5.4-mini, mistral-medium-3-5, synthèse, transcription, jeton `aad#`) ; aucun 403 attendu ;
3. attribuer les trois rôles à `id-muninn-execution`, livrer une révision contrôlée comme
   `deployer.sh` (appel réel au modèle A, synthèse réelle), puis retirer Foundry User ;
4. rejouer les critères (`verifier_criteres.py`, `verifier_ca8.py`) et consigner la preuve.

Coût : nul (les rôles ne sont pas facturés). Risque résiduel tant que la dette est ouverte :
l'identité de l'application peut lire les clés de la ressource ; elle n'est utilisable que depuis
l'application, sans secret à voler dans le dépôt ni dans la configuration.
