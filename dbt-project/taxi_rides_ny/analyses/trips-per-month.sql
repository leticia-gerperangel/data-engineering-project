-- Trips loaded per execution (detect incomplete loads)
SELECT
    EXTRACT(YEAR  FROM pickup_datetime) AS year,
    EXTRACT(MONTH FROM pickup_datetime) AS month,
    service_type,
    COUNT(*) AS trips
FROM {{ ref('fact_trips') }}
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;