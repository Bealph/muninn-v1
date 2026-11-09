# V-2026-11-05-03 : règlement sur l'IA, le classement de Muninn vérifié au texte

| Champ                         | Valeur                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Date de lecture               | 2026-11-05                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Source                        | Suite de S10, texte lu au Journal officiel de l'UE, servi par l'Office des publications : règlement (UE) 2024/1689, version française, JO L du 12 juillet 2024, <https://publications.europa.eu/resource/cellar/dc8116a1-3fe6-11ef-865a-01aa75ed71a1.0009.03/DOC_1> ; règlement (UE) 2026/1744 du 8 juillet 2026, « omnibus numérique sur l'IA », JO L du 24 juillet 2026, <https://publications.europa.eu/resource/cellar/b459c07f-86fb-11f1-bf5e-01aa75ed71a1.0009.03/DOC_1> |
| Entrée de collecte            | aucune : lecture du texte, suite de la fiche V-2026-11-03-03                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Thème                         | Règlement européen sur l'IA                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Vérifiée à la source primaire | Oui, en partie : du règlement 2024/1689, articles 3, 6, 50 et 113, annexe III et considérant 58 ; du règlement 2026/1744, titre, considérants 40 et 41, article 1er (points 40 à 43) et article 4. Non lus : les points 1 à 39 de l'article 1er du règlement 2026/1744, la version consolidée et le rectificatif du 9 octobre 2025 ; EUR-Lex n'a pas répondu à l'outil de lecture (page vide)                                                                                  |

## En clair

Le règlement européen classe certains usages de l'IA « à haut risque », avec de lourdes
obligations. Selon ma lecture, Muninn n'en fait pas partie : l'obligation lue qui le vise est de
dire qu'il est une IA, ce qu'il fait dès sa première phrase. Ce classement tient tant que deux
conditions restent vraies : ne pas déduire d'émotion de la voix, et ne pas évaluer ni classer les
appels selon leur urgence. Les obligations du haut risque, d'abord prévues le 2 août 2026, sont
reportées au 2 décembre 2027. Ce n'est pas un avis juridique.

## Résumé

L'article 6, paragraphe 2, classe à haut risque les systèmes de l'annexe III, en huit domaines :
biométrie, infrastructures critiques, éducation, emploi, services essentiels, répression,
migration, justice. Le point 1 c) vise les « systèmes d'IA destinés à être utilisés pour la
reconnaissance des émotions », que l'article 3, point 39, définit à partir des données
biométriques, dont la voix. Le point 5 d) vise les systèmes destinés à « évaluer et hiérarchiser
les appels d'urgence émanant de personnes physiques » ou à répartir les services d'intervention
d'urgence (police, pompiers, assistance médicale) ; le considérant 58 les justifie parce qu'ils
« prennent des décisions dans des situations très critiques ».

L'article 50, paragraphe 1, impose d'informer les personnes qu'elles interagissent avec un système
d'IA, au plus tard à la première interaction (paragraphe 5), d'une manière conforme aux exigences
d'accessibilité. Le règlement s'applique depuis le 2 août 2026 (article 113), date d'origine aussi
des obligations de l'annexe III. Le règlement 2026/1744, entré en vigueur le troisième jour après
sa publication, les reporte au 2 décembre 2027 (article 1er, point 40). Les points qui modifient
des annexes (41 à 43) ne touchent pas l'annexe III ; selon le considérant 41, l'article 50 n'est
modifié qu'à son paragraphe 7.

## Impact sur Muninn

Le classement du projet (article 50, D-51) est confirmé par ma lecture du texte, sous réserve
d'avis juridique. Muninn ne déduit aucune émotion : il transcrit la parole, et la séparation des
locuteurs n'identifie personne, faute de comparer la voix à une base (article 3, point 35). Il ne
répartit aucun service d'urgence : il oriente vers les secours par un message fixe en cas d'odeur
de gaz et produit un brouillon que l'artisan valide. Le champ `urgence` du dossier reprend ce que
dit l'appelant (« ne jamais inventer ») ; la règle « gaz » est déterministe ; aucun écran ni
aucune règle ne classe les appels par urgence.

Le point 5 d) vise les appels adressés aux services de secours, non ceux qu'un artisan reçoit :
s'interdire de classer les appels selon une urgence évaluée par l'IA est une marge de prudence,
non une exigence lue. Le profilage n'est pas une condition d'entrée dans l'annexe III ; il reste
exclu pour d'autres raisons (minimisation des données).

Restent ouverts : l'accessibilité de l'annonce vocale pour une personne sourde ou malentendante
(article 50, paragraphe 5) ; le marquage des contenus audio de synthèse (article 50,
paragraphe 2), non lu ; et l'évaluation écrite du classement, que l'article 6, paragraphe 4,
n'exige que d'un système visé à l'annexe III, mais qu'il est prudent de consigner.

## Suite

Recommandation R3 de la synthèse S-2026-11-05 ; décision D-95 proposée.
