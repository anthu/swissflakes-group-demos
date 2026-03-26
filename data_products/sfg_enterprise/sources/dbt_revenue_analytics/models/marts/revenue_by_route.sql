with shipments as (
    select * from {{ source('SHIPMENTS', 'MART_SHIPMENT_TRACKING') }}
),

orders as (
    select * from {{ source('ORDERS', 'MART_ORDER_SUMMARY') }}
),

transactions as (
    select * from {{ source('TRANSACTIONS', 'MART_TRANSACTION_SUMMARY') }}
)

select
    s.origin_warehouse,
    s.destination_city,
    count(distinct s.shipment_id) as total_shipments,
    count(distinct o.order_id) as total_orders,
    sum(o.header_total_chf) as total_revenue_chf,
    sum(t.amount_chf) as total_payments_chf,
    sum(t.total_refund_amount_chf) as total_refunds_chf,
    sum(t.net_amount_chf) as net_revenue_chf,
    avg(datediff('day', s.shipped_at, s.delivered_at)) as avg_delivery_days,
    avg(o.header_total_chf) as avg_order_value_chf
from shipments s
join orders o on s.order_id = o.order_id
join transactions t on o.order_id = t.order_id
group by s.origin_warehouse, s.destination_city
