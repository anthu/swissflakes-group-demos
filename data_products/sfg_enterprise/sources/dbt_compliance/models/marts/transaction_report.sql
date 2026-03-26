with transactions as (
    select * from {{ source('TRANSACTIONS', 'MART_TRANSACTION_SUMMARY') }}
),

orders as (
    select * from {{ source('ORDERS', 'MART_ORDER_SUMMARY') }}
),

shipments as (
    select * from {{ source('SHIPMENTS', 'MART_SHIPMENT_TRACKING') }}
),

customers as (
    select * from {{ source('CUSTOMERS', 'MART_CUSTOMER_OVERVIEW') }}
)

select
    t.payment_id,
    t.order_id,
    o.customer_id,
    c.company_name,
    t.amount_chf,
    t.payment_method,
    t.status as payment_status,
    t.is_international,
    t.requires_aml_check,
    s.shipment_id,
    s.requires_customs,
    s.customs_declaration_id,
    t.created_at,
    t.processed_at
from transactions t
join orders o on t.order_id = o.order_id
left join shipments s on o.order_id = s.order_id
left join customers c on o.customer_id = c.customer_id
