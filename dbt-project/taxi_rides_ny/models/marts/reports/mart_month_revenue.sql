-- Queries that aggregate the revenue by month and service type, to be used in the reports.

{{
    config(
        materialized='table',
        cluster_by=['service_type']
    )
}}
 
with trips as (
    select * from {{ ref('fact_trips') }}
)
 
select
    extract(year  from pickup_datetime) as year,
    extract(month from pickup_datetime) as month,
    service_type,
 
    -- volume
    count(*)                                    as total_trips,
    sum(passenger_count)                        as total_passengers,
 
    -- distance
    round(avg(trip_distance), 2)                as avg_distance_miles,
    round(sum(trip_distance), 2)                as total_distance_miles,
 
    -- duration
    round(avg(trip_duration), 2)                as avg_duration_minutes,
 
    -- revenue
    round(sum(fare_amount),  2)                 as total_fare,
    round(sum(tip_amount),   2)                 as total_tips,
    round(sum(total_amount), 2)                 as total_revenue,
    round(avg(fare_amount),  2)                 as avg_fare,
    round(avg(total_amount), 2)                 as avg_total
 
from trips
where pickup_datetime is not null
group by 1, 2, 3