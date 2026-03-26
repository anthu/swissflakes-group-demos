with orders as (

    select * from {{ ref('stg_order_header') }}

),

line_items as (

    select * from {{ ref('stg_order_line_item') }}

),

order_lines_agg as (

    select
        order_id,
        count(*) as line_item_count,
        sum(quantity) as total_quantity,
        sum(line_total_chf) as calculated_total_chf,
        count(distinct product_id) as distinct_product_count
    from line_items
    group by order_id

)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    o.delivery_street,
    o.delivery_postal_code,
    o.delivery_city,
    o.currency,
    o.warehouse_origin,
    o.total_amount_chf as header_total_chf,
    coalesce(a.line_item_count, 0) as line_item_count,
    coalesce(a.total_quantity, 0) as total_quantity,
    coalesce(a.calculated_total_chf, 0) as calculated_total_chf,
    coalesce(a.distinct_product_count, 0) as distinct_product_count
from orders as o
left join order_lines_agg as a
    on o.order_id = a.order_id
