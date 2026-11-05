# Audit RGAA de la console (C10) : protocole

**Statut :** protocole écrit le 3 novembre 2026, avant l'audit. La grille, les résultats, les
corrections et la déclaration iront dans ce dossier, sans modifier ce protocole ; un écart y sera
signalé comme tel.
**Références :** `docs/conception/sources_de_donnees/04-accessibilite-utilisabilite.md` (EXA-01 à
EXA-16, niveau visé), tests `tests/test_accessibilite.py` (axe-core en CI).

## 1. Ce qui est audité, et pourquoi

Muninn est conçu pour être une **application mobile** destinée à l'artisan (Android et iOS,
conception, document 04, section 1). Faute de temps, la V1 présentée à la soutenance n'en contient
pas : elle tient le détail du produit côté serveur (API, agent, données, exploitation) et se montre
par une **console web de démonstration et de test**. Cette console n'est pas une interface de
l'artisan et ne lui sera jamais présentée.

L'audit porte donc sur la console, parce qu'elle est la seule interface de la V1 qui intègre l'API
du modèle : c'est elle que vise la compétence C10 (« intégrer l'API d'un modèle […] dans une
application, en respectant […] les normes d'accessibilité en vigueur »). L'accessibilité de
l'application mobile reste traitée par la conception (WCAG 2.2 AA appliqué au mobile, critères AAA
1.4.6 et 2.5.5, recommandations des plateformes), que le RGAA 4.1 ne couvre pas : sa méthode ne
s'applique pas aux applications mobiles natives (document 04, section 2.1).

## 2. Référentiel

- **RGAA 4.1.2** : 106 critères en 13 thématiques, liste officielle tirée du dépôt de la DINUM
  (`DISIC/accessibilite.numerique.gouv.fr`, `RGAA/criteres.json`, commit `95d5ef3` du 7 janvier
  2026). Le RGAA 5 est annoncé pour fin 2026, sans suspendre les travaux.
- **Niveau visé par la conception :** WCAG 2.2 niveau AA pour la console. Les critères WCAG 2.2
  absents du RGAA 4.1.2 sont rapportés à part, sans entrer dans le taux.

## 3. Échantillon

Les cinq écrans de la console, chacun dans ses états. Les pages obligatoires du RGAA (contact,
mentions légales, accessibilité, plan du site, aide, authentification) n'existent pas dans une
console de démonstration : leur absence est notée, pas comptée.

| Écran         | Route            | États audités                                                                                |
| ------------- | ---------------- | -------------------------------------------------------------------------------------------- |
| Accueil       | `/`              | Formulaire vide ; réponse du modèle ; erreur de l'API                                        |
| Référentiels  | `/referentiels`  | Formulaires vides ; communes candidates ; terme métier ; marché (cellules masquées) ; erreur |
| Agent         | `/agent`         | Liste des scénarios ; dossier à vérifier ; dossier validé ; lot interrompu ; erreur          |
| Démonstration | `/demonstration` | Avant l'appel ; appel en cours ; dossier rendu ; erreur de l'API                             |
| Qualité       | `/qualite`       | Tableau de bord avec données ; erreur                                                        |

## 4. Méthode

Chaque critère est évalué sur chaque écran : conforme, non conforme ou non applicable, avec la
preuve (élément, état, observation).

| Moyen                             | Qui            | Ce qu'il couvre                                                                 |
| --------------------------------- | -------------- | ------------------------------------------------------------------------------- |
| axe-core, WCAG 2.2 AA             | CI et auditeur | Contrastes, noms accessibles, structure, attributs ARIA : détection automatique |
| Lecture du code et du DOM rendu   | Auditeur       | Alternatives, titres, listes, formulaires, tableaux, langue, ordre du contenu   |
| Clavier seul                      | Auditeur       | Tab, Maj+Tab, Entrée, Espace, Échap : ordre, focus visible, aucun piège         |
| Zoom à 200 % et largeur de 320 px | Auditeur       | Agrandissement du texte et reflux, sans perte de contenu ni défilement double   |
| NVDA et Firefox                   | Porteur        | Parcours au lecteur d'écran, selon un scénario écrit pas à pas                  |

L'environnement de référence du RGAA pour ordinateur comprend NVDA, dernière version, avec Firefox ;
un dispositif doit fonctionner pleinement avec au moins une combinaison de la base de référence.

## 5. Calcul

Selon la méthode du RGAA : un critère invalidé sur un seul écran est invalidé pour l'échantillon ;
il est non applicable seulement s'il l'est sur tous les écrans. **Taux global** = critères validés
/ critères applicables ; **taux moyen** = moyenne des taux de chaque écran. Mention : « totalement
conforme » si tous les critères sont respectés, « partiellement conforme » à partir de 50 %, « non
conforme » en dessous.

## 6. Corrections et livrables

- Chaque non-conformité est classée : **bloquante** (un parcours de la démonstration ne peut pas
  être fait au clavier ou au lecteur d'écran) ou **à planifier**. Les bloquantes sont corrigées, chacune
  avec un test de non-régression ; l'audit est alors rejoué sur les critères touchés.
- Livrables : `grille.md` (106 critères × 5 écrans, avec preuves), `scenario-nvda.md` (le parcours
  joué par le porteur et ses observations), `rapport.md` (taux avant et après corrections), et
  `declaration.md` (modèle de la DINUM).

## 7. Limites assumées

- L'auditeur n'est pas certifié ; l'audit suit la méthode publiée, il n'en a pas la valeur légale.
- Le lecteur d'écran est joué par le porteur, une fois, avec une seule combinaison de la base de
  référence.
- La console est une interface de démonstration : l'accessibilité de l'application mobile, la vraie
  interface de l'artisan, n'est pas mesurée ici.
