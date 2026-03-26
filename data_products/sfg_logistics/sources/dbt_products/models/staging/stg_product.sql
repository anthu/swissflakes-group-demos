with source as (

    select * from {{ ref('product') }}

)

select
    product_id::varchar as product_id,
    product_name::varchar as product_name,
    category::varchar as category,
    hs_tariff_code::varchar as hs_tariff_code,
    weight_kg::number(10,2) as weight_kg,
    unit_price_chf::number(10,2) as unit_price_chf,
    currency::varchar as currency,
    origin_country::varchar as origin_country,
    is_hazardous::boolean as is_hazardous,
    requires_customs_declaration::boolean as requires_customs_declaration,
    created_at::date as created_at
from source
