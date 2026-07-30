SELECT *
FROM information_schema.TABLES
ORDER BY TABLE_NAME;

SELECT *
FROM public."core_callreport"

UPDATE core_callreport
SET ss_data_raw = jsonb_build_object(
    'Location', location,
    'Company Domain', company_domain,
    'LinkedIn Profile', linkedin_url
)
WHERE ss_data_raw IS NULL OR ss_data_raw = '{}'::jsonb;