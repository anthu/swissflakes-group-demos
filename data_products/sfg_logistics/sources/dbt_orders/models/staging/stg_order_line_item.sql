with source as (

    select * from {{ ref('order_line_item') }}

)

select
    line_item_id::varchar as line_item_id,
    order_id::varchar as order_id,
    product_id::varchar as product_id,
    quantity::number(10,0) as quantity,
    unit_price_chf::number(10,2) as unit_price_chf,
    line_total_chf::number(12,2) as line_total_chf
from source
