-- Last loaded month per service type
SELECT
    service_type,
    MAX(pickup_datetime) AS last_trip_date,
    COUNT(*)             AS total_trips
FROM {{ ref('fact_trips') }}
GROUP BY 1;
