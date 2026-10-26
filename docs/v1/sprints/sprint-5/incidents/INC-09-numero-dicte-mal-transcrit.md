# INC-09 : numéro dicté mal transcrit, CA-8 non atteint sur le téléphone

| Champ                  | Valeur                                                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Date                   | 26 octobre 2026, 13:07 UTC (première mesure de CA-8 sur la production, révision `ca-muninn-api-prod--0000101`)                     |
| Environnement          | Production, `POST /v1/demo/voice/call`, transcription rapide d'Azure AI Speech (West Europe, API 2025-10-15)                       |
| Gravité                | Moyenne pour la démonstration, nulle pour la sûreté : le numéro manque, aucun numéro n'est inventé                                 |
| Détection              | `eval/production/verifier_ca8.py`, preuve `preuves/etape-6-ca8-premiere-mesure.json`                                               |
| Statut                 | Limite constatée et documentée, sans contournement (décision du porteur du 26 octobre 2026) ; contrôle de fidélité assoupli à part |
| Compétences illustrées | C21 (résoudre et documenter un incident)                                                                                           |

## Symptôme

CA-8 exige que le dossier de SC-01 satisfasse les valeurs attendues de CA-1 en 45 s au plus. Sur
trois passages, SC-01 rend un dossier en 6,5 à 9,2 s, avec les locuteurs séparés et l'issue
attendue, mais un écart sur un champ : `telephone`. Bilan : CA-8 0 sur 3.

## Diagnostic

1. Le dialogue de SC-01 fait dicter « 06 99 00 00 01 » à l'appelant, un numéro de la tranche
   fictive (R9).
2. La transcription rend « 06 99 00 000 01 » : onze chiffres, donc un numéro invalide, que
   l'extraction ne retient pas. Le défaut se répète à chaque passage.
3. Trois façons de faire lire le numéro à la synthèse ont été essayées, deux fois chacune :
   texte brut, pauses de 150 ms entre les paires, balise SSML `say-as interpret-as="telephone"`.
   La transcription rend « 06 99 00 000 01 » cinq fois sur six, « 06 99 0000 01 » une fois.
4. La réponse de la transcription rapide n'a pas de forme lexicale (champs `text`, `words`,
   `confidence`) ; le découpage par mot porte la même erreur (« 00 », puis « 000 »).

## Cause racine

La transcription regroupe mal une suite de quatre « zéro » prononcés. Changer la façon de faire
lire le numéro ne corrige rien : les trois lectures donnent la même erreur (l'audio n'a pas été
écouté ; seul le texte transcrit est mesuré).

## Décision

Pas de correction ajustée au test : réécrire côté serveur « 000 » en « 00 » pour ce numéro, ou
donner le numéro à la transcription par une liste de phrases, reviendrait à faire réussir la mesure
sans rendre le système meilleur. Le numéro ne peut pas changer : il est dans la tranche fictive
(R9). CA-8 est donc noté « non atteint sur le téléphone ». Le comportement est sûr : le dossier
n'a pas de numéro dicté ; aucun numéro n'est inventé.

## Corrigé à cette occasion

La même mesure a montré que le contrôle de fidélité (`voix/fidelite.py`) refusait des
transcriptions réelles presque exactes (95 à 98 % des mots) : « 8h » pour « 8 heures », des
homophones (« au coupé » pour « eau coupée »), le « 000 » ci-dessus. Il est assoupli, avec l'accord
du porteur : heures lues comme dans le dialogue ; nombre bruité à sa place toléré une fois par
appel (un chiffre répété en plus ou en moins, comme « 000 » pour « 00 » ; un autre chiffre est
refusé, à la suite de la revue de sécurité) ; cinq mots en trop sans chiffre au lieu de trois. Un
nombre absent du dialogue reste refusé.

## Deuxième mesure

Après la fusion du correctif (PR 195), le 26 octobre 2026 vers 14 h 10 UTC
(`preuves/etape-6-ca8-deuxieme-mesure.json`) : SC-01 0 sur 3, avec le téléphone pour seul écart et
une fidélité acceptée ; démonstration 3 sur 4. SC-Q1 reste refusé : la transcription a rendu
« 8h00 » au lieu de « 8h » du premier passage, et les minutes nulles comptaient comme des chiffres
en trop. Les heures « 8h00 » sont désormais lues « 8 heures » (correctif suivant).

## Troisième mesure

Après la fusion de la PR 196, production `74b1e55`, le 26 octobre 2026 vers 15 h 20 UTC
(`preuves/etape-6-ca8.json`) : SC-01 0 sur 3, le téléphone seul en écart, fidélité acceptée ;
démonstration 4 sur 4 (SC-Q4, SC-04, SC-Q1, SC-10 conformes et jugés fidèles), de 4,5 à 15 s.

## Suite possible

Mesurer un autre service de transcription, ou un modèle personnalisé de Speech, sur les numéros
dictés (benchmark des services d'IA, carte #92). Hors de la V1.
