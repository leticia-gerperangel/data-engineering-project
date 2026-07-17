SELECT
    service_type,
    COUNT(*) as trips_with_invalid_duration,
FROM {{ ref('fact_trips') }}
where trip_duration <= 0 or trip_duration > 1440
GROUP BY 1