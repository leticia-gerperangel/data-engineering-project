-- Union green and yellow taxi data into a single dataset
with external_green_tripdata as (
    select
        vendor_id,
        rate_code_id,
        pickup_location_id,
        dropoff_location_id,
        pickup_datetime,
        dropoff_datetime,
        store_and_fwd_flag,
        passenger_count,
        trip_distance,
        trip_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        ehail_fee,
        improvement_surcharge,
        total_amount,
        payment_type,
        'green' as service_type
    from {{ ref('stg_green_tripdata') }}
),

external_yellow_tripdata as (
    select
        vendor_id,
        rate_code_id,
        pickup_location_id,
        dropoff_location_id,
        pickup_datetime,
        dropoff_datetime,
        store_and_fwd_flag,
        passenger_count,
        trip_distance,
        cast(1 as integer) as trip_type,  -- Yellow taxis only do street-hail (code 1)
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        cast(0 as numeric) as ehail_fee,  -- Yellow taxis don't have ehail_fee
        improvement_surcharge,
        total_amount,
        payment_type,
        'yellow' as service_type
    from {{ ref('stg_yellow_tripdata') }}
),

trips_union as (
    select * from external_green_tripdata
    union all
    select * from external_yellow_tripdata
)

select *
from trips_union