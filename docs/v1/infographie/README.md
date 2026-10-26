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
9 de la fiche d'ingénierie, section 8 de la présentation produit ; sprint 3 : sections 10 et 9 ; sprint 4 : sections 11 et 10 ; sprint 5 : sections 12 et 11.

Capture : Edge 155 ne démarre plus sans interface sur le poste ; `OUTILS_NODE` peut désigner un
dossier Node dont `puppeteer-edge.json` vise Chrome (constaté le 26 octobre 2026).

La fiche d'ingénierie affiche le schéma d'architecture du dossier V1
(`../../diagrammes/dossier-conception-v1/`) : après une modification de ce schéma, régénérer la
fiche.

## Régénérer la fiche

Avec `capture.cjs` (puppeteer et un navigateur Chromium ou Edge ; `OUTILS_NODE` désigne le
dossier Node où puppeteer est installé), depuis la racine du dépôt :

```bash
node docs/v1/infographie/capture.cjs docs/v1/infographie/fiche-ingenieur/html/fiche-ingenieur.html <sortie> fiche-ingenieur
```

Le script produit `fiche-ingenieur.pdf`, `fiche-ingenieur.png` et `sections/<numéro>-<section>.png`,
numérotés dans l'ordre de la page (01-probleme à 11-sprint-4). Les ranger dans `pdf/`, `png/` et
`png/sections/`. Même commande pour la présentation produit, avec son fichier et son nom.
