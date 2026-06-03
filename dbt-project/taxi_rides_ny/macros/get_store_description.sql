-- Macro to convert store and forward flags into human-readable descriptions.

{% macro get_store_and_fwd_description(column) %}
    case upper(cast({{ column }} as string))
        when 'Y' then 'Store and forward trip'
        when 'N' then 'Direct trip'
        else 'Unknown'
    end
{% endmacro %}
