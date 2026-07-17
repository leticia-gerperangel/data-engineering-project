-- Stats on taxi pickups by zone and service type

{{
    config(
        materialized='table',
        cluster_by=['service_type', 'pickup_borough']
    )
}}
 
with trips as (
    select * from {{ ref('fact_trips') }}
),
 
zones as (
    select * from {{ ref('dim_zones') }}
),
 
zone_metrics as (
    select
        t.service_type,
        t.pickup_location_id,
        pz.borough                          as pickup_borough,
        pz.zone                             as pickup_zone,
        pz.service_zone                     as pickup_service_zone,
 
        count(*)                            as total_pickups,
        round(avg(t.trip_distance),  2)     as avg_distance_miles,
        round(avg(t.trip_duration), 2)      as avg_duration_minutes,
        round(avg(t.fare_amount),    2)     as avg_fare,
        round(sum(t.total_amount),   2)     as total_revenue
 
    from trips t
    left join zones pz on t.pickup_location_id = pz.location_id
    group by 1, 2, 3, 4, 5
)
 
select * from zone_metrics
