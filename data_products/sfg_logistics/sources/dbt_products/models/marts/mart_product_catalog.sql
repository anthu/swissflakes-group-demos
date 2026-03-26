with products as (

    select * from {{ ref('stg_product') }}

),

tariffs as (

    select * from {{ ref('stg_product_tariff') }}

)

select
    p.product_id,
    p.product_name,
    p.category,
    p.weight_kg,
    p.unit_price_chf,
    p.currency,
    p.origin_country,
    p.is_hazardous,
    p.requires_customs_declaration,
    p.created_at,
    t.tariff_id,
    t.hs_code,
    t.description as tariff_description,
    t.duty_rate_pct,
    t.vat_rate_pct,
    t.preferential_rate_pct,
    round(p.unit_price_chf * t.duty_rate_pct / 100, 2) as duty_amount_chf,
    round(p.unit_price_chf * t.vat_rate_pct / 100, 2) as vat_amount_chf,
    round(p.unit_price_chf * (1 + t.vat_rate_pct / 100 + t.duty_rate_pct / 100), 2) as total_landed_cost_chf
from products as p
left join tariffs as t
    on p.product_id = t.product_id
