# Registre des sources

Flux vérifiés le 2 novembre 2026, et S04 le 3 novembre : chaque adresse a répondu (code 200,
flux RSS ou Atom non vide).
Les sources sans flux se lisent à la main, à la fréquence indiquée. Fiabilité : élevée pour un
texte officiel ou la documentation d'un éditeur sur son propre produit ; moyenne pour la
recherche non relue, une communauté ou un expert reconnu ; à confirmer pour la presse.

| N°  | Source                                              | Thème                       | Type       | Fiabilité | Fréquence    | Accès                                                                                                                                                              |
| --- | --------------------------------------------------- | --------------------------- | ---------- | --------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| S01 | Azure Updates                                       | Modèles et services d'IA    | Éditeur    | Élevée    | Hebdomadaire | <https://www.microsoft.com/releasecommunications/api/v2/azure/rss>                                                                                                 |
| S02 | Microsoft Learn, nouveautés de Foundry et de Speech | Modèles et services d'IA    | Éditeur    | Élevée    | Mensuelle    | À la main : <https://learn.microsoft.com/en-us/azure/foundry/whats-new-foundry>, <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/releasenotes> |
| S03 | Mistral AI, notes de version                        | Modèles et services d'IA    | Éditeur    | Élevée    | Mensuelle    | À la main : <https://docs.mistral.ai/getting-started/changelog/>                                                                                                   |
| S04 | Langfuse, versions du SDK Python                    | Évaluation et observabilité | Éditeur    | Élevée    | Hebdomadaire | <https://github.com/langfuse/langfuse-python/releases.atom> (Muninn épingle `langfuse==4.15.6`)                                                                    |
| S05 | OpenTelemetry, conventions sémantiques              | Évaluation et observabilité | Normatif   | Élevée    | Mensuelle    | <https://github.com/open-telemetry/semantic-conventions/releases.atom>                                                                                             |
| S06 | arXiv, catégorie cs.CL                              | Agents et extraction        | Recherche  | Moyenne   | Hebdomadaire | <https://rss.arxiv.org/rss/cs.CL> (filtrer : évaluation, extraction, agents)                                                                                       |
| S07 | Hugging Face, blog                                  | Agents et extraction        | Communauté | Moyenne   | Hebdomadaire | <https://huggingface.co/blog/feed.xml>                                                                                                                             |
| S08 | Simon Willison                                      | Agents et extraction        | Expert     | Moyenne   | Hebdomadaire | <https://simonwillison.net/atom/everything/>                                                                                                                       |
| S09 | GitHub Changelog                                    | Chaîne de livraison         | Éditeur    | Élevée    | Hebdomadaire | <https://github.blog/changelog/feed/>                                                                                                                              |
| S10 | Commission européenne, stratégie numérique          | Règlement européen sur l'IA | Officielle | Élevée    | Hebdomadaire | <https://digital-strategy.ec.europa.eu/en/rss.xml>                                                                                                                 |
| S11 | CNIL, actualités                                    | Données personnelles        | Officielle | Élevée    | Hebdomadaire | <https://www.cnil.fr/fr/rss.xml>                                                                                                                                   |
| S12 | Service-public.fr, actualités professionnelles      | Démarchage et téléphonie    | Officielle | Élevée    | Hebdomadaire | <https://www.service-public.fr/abonnements/rss/actu-actu-pro.rss>                                                                                                  |
| S13 | Légifrance et Arcep                                 | Démarchage et téléphonie    | Officielle | Élevée    | Mensuelle    | À la main : Code de la consommation sur Légifrance (démarchage téléphonique), <https://www.arcep.fr/actualites.html>                                               |
| S14 | W3C, initiative pour l'accessibilité (WAI)          | Accessibilité               | Normatif   | Élevée    | Mensuelle    | <https://www.w3.org/WAI/feed.xml>                                                                                                                                  |

Sources écartées le 2 novembre : le flux du blog Azure AI Foundry de Tech Community (vide) ; les
adresses de flux supposées de Mistral, de l'Arcep et de l'ANSSI (erreur ou page HTML, pas de
flux) ; les versions du SDK Azure pour Python (trop de volume pour l'usage de Muninn). Le 3 novembre,
S04 est passé des versions du serveur Langfuse (mises à jour par l'offre cloud) à celles du SDK
Python, que Muninn épingle ; le filtre d'arXiv a été resserré (130 titres sur 30 jours, 9 après).
