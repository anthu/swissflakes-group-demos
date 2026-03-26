with customers as (
    select * from {{ source('CUSTOMERS', 'MART_CUSTOMER_OVERVIEW') }}
),

orders as (
    select
        customer_id,
        count(*) as total_orders,
        sum(header_total_chf) as total_order_value_chf,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from {{ source('ORDERS', 'MART_ORDER_SUMMARY') }}
    group by customer_id
),

merchants as (
    select * from {{ source('MERCHANTS', 'MART_MERCHANT_OVERVIEW') }}
)

select
    c.customer_id,
    c.company_name,
    c.legal_form,
    c.city,
    c.canton,
    c.is_active,
    c.created_at,
    c.primary_contact_email,
    coalesce(o.total_orders, 0) as total_orders,
    coalesce(o.total_order_value_chf, 0) as total_order_value_chf,
    o.first_order_date,
    o.last_order_date,
    m.merchant_id,
    m.merchant_name,
    m.business_type,
    case when m.merchant_id is not null then true else false end as is_merchant
from customers c
left join orders o on c.customer_id = o.customer_id
left join merchants m on c.customer_id = m.customer_id
