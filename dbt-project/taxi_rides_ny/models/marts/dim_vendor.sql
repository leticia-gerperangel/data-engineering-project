-- Dimension table for taxi technology vendors
-- Small static dimension defining vendor codes and their company names

with trips_union as (
    select * from {{ ref('int_trips_union') }}
),

vendors as (
    select
        distinct vendor_id,
        {{ get_vendor_data('vendor_id') }} as vendor_name
    from trips_union
)

select * from vendors