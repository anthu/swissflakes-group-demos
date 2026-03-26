with source as (

    select * from {{ ref('product_tariff') }}

)

select
    tariff_id::varchar as tariff_id,
    product_id::varchar as product_id,
    hs_code::varchar as hs_code,
    description::varchar as description,
    duty_rate_pct::number(5,2) as duty_rate_pct,
    vat_rate_pct::number(5,2) as vat_rate_pct,
    preferential_rate_pct::number(5,2) as preferential_rate_pct
from source
