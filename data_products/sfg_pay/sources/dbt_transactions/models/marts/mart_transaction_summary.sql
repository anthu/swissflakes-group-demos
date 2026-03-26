with payments as (

    select * from {{ ref('stg_payment') }}

),

refunds as (

    select * from {{ ref('stg_refund') }}

),

refund_agg as (

    select
        payment_id,
        count(*) as refund_count,
        sum(amount_chf) as total_refund_amount_chf,
        max(case when status = 'PROCESSED' then 1 else 0 end) as has_processed_refund
    from refunds
    group by payment_id

)

select
    p.payment_id,
    p.order_id,
    p.merchant_id,
    p.amount_chf,
    p.currency,
    p.payment_method,
    p.card_brand,
    p.status,
    p.created_at,
    p.processed_at,
    p.is_international,
    p.requires_aml_check,
    coalesce(ra.refund_count, 0) as refund_count,
    coalesce(ra.total_refund_amount_chf, 0) as total_refund_amount_chf,
    coalesce(ra.has_processed_refund, 0) = 1 as has_processed_refund,
    p.amount_chf - coalesce(ra.total_refund_amount_chf, 0) as net_amount_chf
from payments as p
left join refund_agg as ra
    on p.payment_id = ra.payment_id
