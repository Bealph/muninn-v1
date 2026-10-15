-- Établissements actifs de la tête de pont dans le stock Sirene (SRC-01 ; sprint 3, étape 6).
-- Lecture par DuckDB des fichiers Parquet de data.gouv.fr, par requêtes HTTP partielles : seules
-- les colonnes nommées ici sont lues (VD-20). Minimisation : ni nom, ni adresse, ni
-- géolocalisation, ni SIRET ; le SIREN ne sert qu'en mémoire à compter les entreprises
-- distinctes et à joindre la catégorie juridique, puis il est abandonné.
-- {etablissements} et {unites_legales} sont remplacés par les adresses des fichiers.
SELECT
    e.siren,
    e.activitePrincipaleEtablissement AS naf_code,
    CASE
        WHEN e.trancheEffectifsEtablissement = 'NN' THEN 'NN'
        WHEN e.trancheEffectifsEtablissement = '00' THEN '00'
        WHEN e.trancheEffectifsEtablissement IS NULL OR e.trancheEffectifsEtablissement = ''
            THEN 'empty'
        ELSE 'employer'
    END AS headcount_band,
    CASE
        WHEN u.categorieJuridiqueUniteLegale = '1000' THEN 'ei'
        WHEN u.categorieJuridiqueUniteLegale LIKE '54%' THEN 'sarl'
        WHEN u.categorieJuridiqueUniteLegale LIKE '57%' THEN 'sas'
        ELSE 'other'
    END AS legal_category_group,
    CASE
        WHEN e.codeCommuneEtablissement IS NULL OR e.codeCommuneEtablissement = '' THEN NULL
        WHEN e.codeCommuneEtablissement LIKE '97%' OR e.codeCommuneEtablissement LIKE '98%'
            THEN left(e.codeCommuneEtablissement, 3)
        ELSE left(e.codeCommuneEtablissement, 2)
    END AS department_code
FROM read_parquet({etablissements}) AS e
LEFT JOIN (
    -- La catégorie juridique est un entier dans le Parquet : convertie en texte.
    SELECT siren, CAST(categorieJuridiqueUniteLegale AS VARCHAR) AS categorieJuridiqueUniteLegale
    FROM read_parquet({unites_legales})
) AS u USING (siren)
WHERE e.etatAdministratifEtablissement = 'A'
  AND e.activitePrincipaleEtablissement IN ({codes_naf})
