with source as (
    select * from {{ source('raw_data', 'external_green_tripdata')}}
),

renamed as (
    select
        -- identifiers
        cast(VendorID as int) as vendor_id,
        cast(RatecodeID as int) as rate_code_id,
        cast(PULocationID as int) as pickup_location_id,
        cast(DOLocationID as int) as dropoff_location_id,
        -- timestamps
        cast(lpep_pickup_datetime as timestamp) as pickup_datetime,
        cast(lpep_dropoff_datetime as timestamp) as dropoff_datetime,
        -- trip info
        store_and_fwd_flag,
        cast(passenger_count as int) as passenger_count,
        cast(trip_distance as numeric) as trip_distance,
        cast(trip_type as int) as trip_type,
        -- payment info
        cast(fare_amount as numeric) as fare_amount,
        cast(extra as numeric) as extra,
        cast(mta_tax as numeric) as mta_tax,
        cast(tip_amount as numeric) as tip_amount,
        cast(tolls_amount as numeric) as tolls_amount,
        cast(ehail_fee as numeric) as ehail_fee,
        cast(improvement_surcharge as numeric) as improvement_surcharge,
        cast(total_amount as numeric) as total_amount,
        cast(payment_type as int) as payment_type
    from source
),

filtered as (
    select * from renamed
    where
        trip_distance    >  0
        and fare_amount  >= 0
        and total_amount >= 0
        and passenger_count > 0
        and dropoff_datetime >= pickup_datetime
        and pickup_location_id  is not null
        and dropoff_location_id is not null
        and extract(year from pickup_datetime) between {{ var('start_year') }} and {{ var('end_year') }}
)

select * from filtered