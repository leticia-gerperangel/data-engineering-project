-- This fact table contains trip measures and dimensions for taxi rides in New York City. 
-- It is built by unioning the green and yellow taxi trip data, generating a surrogate key for each trip, eliminating duplicates, and enriching the data with descriptive payment type information.

{{
    config(
        materialized='table',
        partition_by={
            'field': 'pickup_datetime',
            'data_type': 'timestamp',
            'granularity': 'month'
        },
        cluster_by=['service_type', 'payment_type_id']
    )
}}

with trips_union as (
    -- bring in the union of green and yellow taxi trips
    select *
    from {{ ref('int_trips_union') }}
),

trips_with_id as (
    -- generate a surrogate key for each trip using dbt_utils
    select
        {{ dbt_utils.generate_surrogate_key([
            'vendor_id',
            'pickup_datetime',
            'dropoff_datetime',
            'pickup_location_id',
            'dropoff_location_id'
        ]) }} as trip_id,
        *
    from trips_union
),

deduped as (
    -- eliminate duplicates by keeping only the first record for each trip_id based on pickup_datetime
    select *
    from (
        select
            *,
            row_number() over (
                partition by trip_id
                order by pickup_datetime
            ) as rn
        from trips_with_id
    )
    where rn = 1
),

final as (
    select
        -- surrogate key
        trip_id,
 
        -- foreign keys
        vendor_id,                  -- dim_vendor
        rate_code_id,               -- dim_rate_code
        pickup_location_id,         -- dim_zones
        dropoff_location_id,        -- dim_zones
        payment_type as payment_type_id,            -- dim_payment_type
 
        -- timestamps
        pickup_datetime,
        dropoff_datetime,
 
        -- trip measures
        trip_distance,
        passenger_count,
        timestamp_diff(dropoff_datetime, pickup_datetime, minute) as trip_duration,
 
        -- payment details
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        ehail_fee,
        improvement_surcharge,
        total_amount,
 
        -- categorical attributes
        service_type,
        trip_type,
        {{ get_trip_type_description('trip_type') }}         as trip_type_description,
        store_and_fwd_flag,
        {{ get_store_and_fwd_description('store_and_fwd_flag') }} as store_and_fwd_description
 
    from deduped
)
 
select * from final
