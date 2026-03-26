with merchants as (

    select * from {{ ref('stg_merchant_account') }}

),

payouts as (

    select * from {{ ref('stg_payout') }}

),

payout_agg as (

    select
        merchant_id,
        count(*) as payout_count,
        sum(gross_amount_chf) as total_gross_amount_chf,
        sum(fee_amount_chf) as total_fee_amount_chf,
        sum(net_amount_chf) as total_net_amount_chf,
        sum(case when status = 'PAID' then net_amount_chf else 0 end) as total_paid_amount_chf,
        min(period_start) as first_payout_period,
        max(period_end) as last_payout_period
    from payouts
    group by merchant_id

)

select
    m.merchant_id,
    m.merchant_name,
    m.business_type,
    m.registration_number,
    m.bank_account_iban,
    m.settlement_currency,
    m.fee_rate_pct,
    m.customer_id,
    m.is_active,
    m.onboarded_at,
    coalesce(pa.payout_count, 0) as payout_count,
    coalesce(pa.total_gross_amount_chf, 0) as total_gross_amount_chf,
    coalesce(pa.total_fee_amount_chf, 0) as total_fee_amount_chf,
    coalesce(pa.total_net_amount_chf, 0) as total_net_amount_chf,
    coalesce(pa.total_paid_amount_chf, 0) as total_paid_amount_chf,
    pa.first_payout_period,
    pa.last_payout_period
from merchants as m
left join payout_agg as pa
    on m.merchant_id = pa.merchant_id
