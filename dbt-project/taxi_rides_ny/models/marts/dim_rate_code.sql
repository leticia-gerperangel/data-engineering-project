-- Dimension table for rate codes used in taxi rides.
-- Source: official NYC TLC data dictionary.
-- The 6 rate codes are static — they do not change between years.
 
with rate_codes as (
    select 1 as rate_code_id, 'Standard rate'        as rate_code_description, 'Standard'  as rate_code_group
    union all
    select 2,                  'JFK',                                           'Airport'
    union all
    select 3,                  'Newark',                                        'Airport'
    union all
    select 4,                  'Nassau or Westchester',                         'Outer zone'
    union all
    select 5,                  'Negotiated fare',                               'Special'
    union all
    select 6,                  'Group ride',                                    'Special'
    union all
    select 99,                 'Unknown',                                       'Unknown'
)
 
select * from rate_codes
