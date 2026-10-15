# Calibration du seuil de similarité du lexique (sprint 3, étape 7)

**Statut :** protocole écrit et versionné le 15 octobre 2026, **avant toute mesure**. Les résultats
seront ajoutés à la section 4 sans modifier les sections 1 à 3.

## 1. Question

Quand l'API reçoit un mot entendu et un métier, elle rend le terme du lexique le plus proche, ou
refuse « hors corpus » si la similarité est sous un seuil (D-56). Quel seuil retenir ?

## 2. Protocole, fixé avant la mesure

- **Lexique évalué :** la version du lexique de plomberie construite le 15 octobre 2026 (142
  termes : 121 du Wiktionnaire, 21 marques de Wikidata) ; son empreinte est citée en section 4.
- **Jeu étiqueté :** `src/muninn/referentiels/calibration_lexique.csv`, 45 mots écrits avant la
  mesure :
  - 25 positifs, chacun avec le terme attendu : pluriels, fautes de frappe, accents ou séparateurs
    absents, marques en minuscules ;
  - 20 négatifs, qui doivent être refusés : hors sujet (8), métier voisin (6), plomberie mais
    absent du lexique (2), quasi-homographes d'un terme du lexique (4).
- **Mesure :** similarité trigramme de PostgreSQL (`pg_trgm`, fonction `similarity`) entre le mot
  normalisé (N1 à N3) et chaque terme normalisé du lexique ; le terme retenu est celui de plus forte
  similarité.
- **Seuils essayés :** de 0,30 à 0,95, par pas de 0,05.
- **Erreurs comptées à chaque seuil :**
  - fausse acceptation : un négatif accepté, ou un positif accepté avec un autre terme que
    l'attendu ;
  - faux refus : un positif refusé.
- **Règle de choix, fixée avant la mesure :** le seuil retenu est le plus bas qui ne donne
  **aucune fausse acceptation**. Refuser à tort coûte moins qu'inventer : un terme faux entrerait
  dans le dossier de l'artisan, alors qu'un refus laisse le mot entendu tel quel. Le rappel des
  positifs à ce seuil est rapporté, avec son intervalle de confiance.
- **Incertitude :** intervalles de Wilson à 95 %. Avec 20 négatifs, zéro fausse acceptation ne
  garantit pas un taux nul : la borne haute reste de l'ordre de 16 %.

## 3. Limites connues avant la mesure

- 45 mots ne suffisent pas à une estimation précise ; le jeu sert à choisir un seuil défendable,
  pas à garantir une performance.
- Les mots sont écrits par moi, pas tirés de vraies transcriptions : la V1 n'en a pas (R1, R2).
- La similarité trigramme ne connaît pas les synonymes : « mitigeur » ne peut pas trouver
  « mélangeur ». C'est un refus attendu, compté comme tel.

## 4. Résultats

**Mesuré le :** 15 octobre 2026, par `python -m muninn.referentiels.calibration`, sur un
PostgreSQL 16 local chargé par `muninn-ingestion tout`.
**Lexique évalué :** plomberie, 142 termes, empreinte
`9c661ed612a827aaf0c4227c6cb1ae052bc0ab8b6073727302019cda22621770`.

### 4.1 Erreurs par seuil

| Seuil | Fausses acceptations (sur 20 négatifs et 25 positifs) | Faux refus (sur 25 positifs) | Positifs justes |
| ----- | ----------------------------------------------------- | ---------------------------- | --------------- |
| 0,30  | 5                                                     | 0                            | 25 sur 25       |
| 0,35  | 4                                                     | 0                            | 25 sur 25       |
| 0,40  | 3                                                     | 0                            | 25 sur 25       |
| 0,45  | 3                                                     | 1                            | 24 sur 25       |
| 0,50  | 2                                                     | 1                            | 24 sur 25       |
| 0,55  | 0                                                     | 1                            | 24 sur 25       |
| 0,60  | 0                                                     | 2                            | 23 sur 25       |
| 0,65  | 0                                                     | 3                            | 22 sur 25       |
| 0,70  | 0                                                     | 4                            | 21 sur 25       |
| 0,75  | 0                                                     | 11                           | 14 sur 25       |
| 0,80  | 0                                                     | 14                           | 11 sur 25       |
| 0,85  | 0                                                     | 14                           | 11 sur 25       |
| 0,90  | 0                                                     | 15                           | 10 sur 25       |
| 0,95  | 0                                                     | 15                           | 10 sur 25       |

### 4.2 Seuil retenu : 0,55

Par la règle fixée en section 2, le plus bas seuil sans fausse acceptation.

- **Rappel :** 24 positifs sur 25, intervalle de Wilson à 95 % [0,80 ; 0,99]. Le seul faux refus
  est « syphon » (0,40 avec « siphon ») : le mot entendu reste tel quel dans le dossier.
- **Négatifs :** 0 accepté sur 20 ; borne haute à 95 % de 0,16.
- **Marge étroite :** les quasi-homographes « jointure » et « vannerie » sont à 0,50, le positif
  le plus faible accepté (« vane ») à 0,571. Le seuil passe dans un intervalle de 0,07 : un autre
  lexique peut le déplacer, d'où la règle de publication ci-dessous.
- **Seuil du contrat d'API :** l'hypothèse de 0,8 [H] aurait refusé 14 positifs sur 25 ; elle
  est remplacée par 0,55.

### 4.3 Mots les plus difficiles

| Mot       | Nature           | Terme le plus proche | Similarité | Au seuil de 0,55 |
| --------- | ---------------- | -------------------- | ---------- | ---------------- |
| syphon    | faute            | siphon               | 0,400      | refusé (à tort)  |
| jointure  | quasi-homographe | joint                | 0,500      | refusé           |
| vannerie  | quasi-homographe | vanne                | 0,500      | refusé           |
| chauffeur | quasi-homographe | chauffe-eau          | 0,467      | refusé           |
| vane      | faute            | vanne                | 0,571      | accepté          |
| joints    | pluriel          | joint                | 0,625      | accepté          |

Le détail des 45 mesures est rendu par la commande ; il n'est pas recopié ici.

### 4.4 Publication du lexique

Une version du lexique n'est publiée que si son empreinte figure dans
`src/muninn/ingestion/donnees/evaluations-lexique.json`, avec la référence de ce rapport
(US-48, critère 4). Un lexique au contenu différent reste `candidate` jusqu'à une nouvelle
calibration, et l'API continue de servir la version publiée.
