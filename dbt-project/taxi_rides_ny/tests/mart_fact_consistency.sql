
-- Mart vs fact consistency check
-- Expected: difference = 0 for all rows
SELECT
    m.year,
    m.month,
    m.service_type,
    m.total_trips                    AS mart_trips,
    COUNT(f.trip_id)                 AS fact_trips,
    m.total_trips - COUNT(f.trip_id) AS difference
FROM {{ ref('mart_month_revenue') }} m
LEFT JOIN {{ ref('fact_trips') }} f
    ON  EXTRACT(YEAR  FROM f.pickup_datetime) = m.year
    AND EXTRACT(MONTH FROM f.pickup_datetime) = m.month
    AND f.service_type = m.service_type
GROUP BY 1, 2, 3, m.total_trips
HAVING m.total_trips != COUNT(f.trip_id)