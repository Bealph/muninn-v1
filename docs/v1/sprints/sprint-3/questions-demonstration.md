# Jeu de questions de démonstration du sprint 3

**Livrable du sprint 3 :** un jeu de 5 à 10 questions de démonstration, couvertes et hors corpus,
versionné. Ce jeu en compte 10 : 7 couvertes, 2 hors corpus, 1 hors périmètre.

**Référence rejouée par la machine :** `src/muninn/referentiels/questions_demonstration.json`. Ce
document en est la version lisible ; un test (`tests/test_demonstration.py`) vérifie que les deux
disent la même chose.

**Résultat en production, le 16 octobre 2026 :** 10 sur 10, en préproduction et en production.

## 1. Les questions

Écran de production : <https://ca-muninn-console-prod.graybeach-70019748.francecentral.azurecontainerapps.io/referentiels>.

| N°  | Nature                    | Ce qu'on tape dans l'écran                    | Statut attendu   | Réponse attendue                                                                                                | Source citée                       |
| --- | ------------------------- | --------------------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Q01 | Couverte                  | Commune : « Vincennes »                       | `trouve`         | Vincennes, code INSEE 94080, code postal 94300                                                                  | COG 2026 (SRC-07)                  |
| Q02 | Couverte, ambiguë         | Commune : « Montreuil »                       | `trouve`         | Trois communes : 28267 (28500), 85148 (85200), 93048 (93100) ; aucune n'est choisie à la place de l'utilisateur | COG 2026 (SRC-07)                  |
| Q03 | Couverte, incohérente     | Commune : « Bagnolet », code postal « 93100 » | `incoherent`     | Aucune commune de ce nom n'a ce code ; Bagnolet est listée avec son vrai code, 93170, sans correction           | Codes postaux de La Poste (SRC-06) |
| Q04 | Couverte, par code postal | Code postal : « 75001 »                       | `trouve`         | Paris, code INSEE 75056, par son arrondissement                                                                 | Codes postaux de La Poste (SRC-06) |
| Q05 | Couverte                  | Terme : « cumulus », métier plomberie         | `trouve`         | Terme « cumulus », similarité 1,0, lien vers sa page du Wiktionnaire, licence CC BY-SA 4.0                      | Wiktionnaire (SRC-12)              |
| Q06 | Couverte, mot approché    | Terme : « chauffe eau », métier plomberie     | `trouve`         | Terme « chauffe-eau » : le tiret manquant ne gêne pas                                                           | Wiktionnaire (SRC-12)              |
| Q07 | Couverte                  | Marché : métier plomberie                     | `trouve`         | Établissements actifs du code NAF 43.22A, totaux nationaux ; cellules trop petites masquées                     | Stock Sirene (SRC-01)              |
| Q08 | Hors corpus               | Commune : « Gotham City »                     | `hors_corpus`    | Refus, avec le motif ; aucune commune proposée                                                                  | COG 2026 (SRC-07)                  |
| Q09 | Hors corpus               | Terme : « ordinateur », métier plomberie      | `hors_corpus`    | Refus : aucun terme n'atteint le seuil de similarité de 0,55 ; aucun terme proposé                              | Wiktionnaire (SRC-12)              |
| Q10 | Hors périmètre            | Terme : « disjoncteur », métier électricité   | `hors_perimetre` | Refus : aucun lexique publié pour l'électricité en V1                                                           | Aucune                             |

## 2. Ce que chaque question montre

- **Q01, Q04 :** une réponse simple, tirée des données, avec la ligne en base et la source.
- **Q02 :** une ambiguïté n'est pas tranchée à la place de l'utilisateur ; les trois candidates
  sont rendues.
- **Q03 :** une incohérence est signalée, jamais corrigée en silence.
- **Q05, Q06 :** l'ancrage du lexique, y compris sur un mot approché ; le seuil de 0,55 a été
  calibré par un protocole écrit avant la mesure (`calibration-seuil.md`).
- **Q07 :** les agrégats Sirene, sous secret statistique.
- **Q08, Q09 :** le refus hors corpus, sans valeur inventée.
- **Q10 :** le refus hors périmètre.

L'évaluateur peut aussi poser ses propres questions : le jeu n'est qu'un socle reproductible.

## 3. Le rejouer

```bash
make questions URL=https://ca-muninn-api-prod.graybeach-70019748.francecentral.azurecontainerapps.io
# ou, après un rechargement complet des données en production :
gh workflow run donnees -f environnement=production
```

Chaque question est vérifiée sur trois points : le statut, les valeurs attendues dans la réponse,
et la source citée. La commande s'arrête en erreur au premier écart.
