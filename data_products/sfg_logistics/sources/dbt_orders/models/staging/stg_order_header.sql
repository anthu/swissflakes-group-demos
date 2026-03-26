with source as (

    select * from {{ ref('order_header') }}

)

select
    order_id::varchar as order_id,
    customer_id::varchar as customer_id,
    order_date::date as order_date,
    status::varchar as status,
    delivery_street::varchar as delivery_street,
    delivery_postal_code::varchar as delivery_postal_code,
    delivery_city::varchar as delivery_city,
    total_amount_chf::number(12,2) as total_amount_chf,
    currency::varchar as currency,
    warehouse_origin::varchar as warehouse_origin
from source
