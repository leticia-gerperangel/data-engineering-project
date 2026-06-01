-- Dimension table for payment types used in taxi rides.
-- Source data is enriched with descriptive payment type information from the payment_type_lookup table.

{{
    config(
        materialized='table'
    )
}}

select
    payment_type as payment_type_id,
    description as payment_type_description
from {{ ref('payment_type_lookup') }}