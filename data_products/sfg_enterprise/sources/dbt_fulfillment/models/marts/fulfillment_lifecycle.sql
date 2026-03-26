with orders as (
    select * from {{ source('ORDERS', 'MART_ORDER_SUMMARY') }}
),

shipments as (
    select * from {{ source('SHIPMENTS', 'MART_SHIPMENT_TRACKING') }}
),

transactions as (
    select * from {{ source('TRANSACTIONS', 'MART_TRANSACTION_SUMMARY') }}
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status as order_status,
    o.header_total_chf as order_total_chf,
    s.shipment_id,
    s.status as shipment_status,
    s.vehicle_id,
    s.origin_warehouse,
    s.destination_city,
    s.shipped_at,
    s.delivered_at,
    datediff('day', s.shipped_at, s.delivered_at) as delivery_days,
    t.payment_id,
    t.payment_method,
    t.status as payment_status,
    t.amount_chf as payment_amount_chf,
    t.net_amount_chf as net_payment_chf
from orders o
left join shipments s on o.order_id = s.order_id
left join transactions t on o.order_id = t.order_id
