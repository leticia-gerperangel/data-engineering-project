-- Verifies that key trip measures do not contain negative values.
-- These filters mirror the quality rules applied in staging models.

select
    trip_id,
    trip_distance,
    fare_amount,
    total_amount,
    passenger_count
from {{ ref('fact_trips') }}
where trip_distance    <= 0
    or fare_amount      < 0
    or total_amount     < 0
    or passenger_count  < 0