"""Pipeline d'ingestion des référentiels (sprint 3, V-04 à V-06).

Chaque source est téléchargée, contrôlée, nettoyée, puis chargée comme une nouvelle version de
`ref.dataset_versions`. La version précédente reste servie tant que la nouvelle n'est pas publiée.
"""
