# Infographies de la V1

Organisation : un dossier par document, puis un sous-dossier par format.

| Document                      | Statut                                                                          | Dossier                         |
| ----------------------------- | ------------------------------------------------------------------------------- | ------------------------------- |
| Fiche d'ingénierie de la V1   | En vigueur depuis le 14 octobre 2026                                            | `fiche-ingenieur/`              |
| Présentation produit de la V1 | Archive : remplacée le 14 octobre 2026, le formateur jugeant son ton commercial | `archive/presentation-produit/` |

Chaque dossier de document contient :

| Format          | Contenu                                                                         |
| --------------- | ------------------------------------------------------------------------------- |
| `html/`         | La source, à ouvrir dans un navigateur                                          |
| `pdf/`          | La page entière, pour l'impression ou l'envoi                                   |
| `png/`          | La page entière, en image                                                       |
| `png/sections/` | Une image par section, numérotée dans l'ordre de la page, pour les diapositives |

**À chaque fin de sprint**, les deux infographies reçoivent une section « Sprint N : travail
attendu et évaluation par le pair » (rituel décrit dans `../sprints/README.md`). Sprint 2 : section
9 de la fiche d'ingénierie, section 8 de la présentation produit ; sprint 3 : sections 10 et 9.

La fiche d'ingénierie affiche le schéma d'architecture du dossier V1
(`../../diagrammes/dossier-conception-v1/`) : après une modification de ce schéma, régénérer la
fiche.

## Régénérer la fiche

Avec l'outillage local de capture (Chrome et puppeteer), depuis le dossier de l'outil :

```bash
node capture.js <dépôt>/docs/v1/infographie/fiche-ingenieur/html/fiche-ingenieur.html <sortie>/fiche
```

Puis ranger les fichiers produits : `fiche.pdf` dans `pdf/fiche-ingenieur.pdf`, `fiche.png` dans
`png/fiche-ingenieur.png`, et `fiche-s-<section>.png` dans `png/sections/`, sous le numéro de la
section (01-probleme à 10-sprint-3).
