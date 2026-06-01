-- Macro to convert trip type codes into human-readable descriptions.
-- Only green taxi trips have a trip type column. Yellow is always 1 (street hail) and green is either 1 (street hail) or 2 (dispatch).

{% macro get_trip_type_description(trip_type_column) %}
    case cast({{ trip_type_column }} as integer)
        when 1 then 'Street-hail'
        when 2 then 'Dispatch'
        else 'Unknown'
    end
{% endmacro %}
