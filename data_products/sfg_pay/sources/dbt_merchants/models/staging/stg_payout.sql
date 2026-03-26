with source as (

    select * from {{ ref('payout') }}

)

select
    payout_id::varchar as payout_id,
    merchant_id::varchar as merchant_id,
    period_start::date as period_start,
    period_end::date as period_end,
    gross_amount_chf::number(12,2) as gross_amount_chf,
    fee_amount_chf::number(12,2) as fee_amount_chf,
    net_amount_chf::number(12,2) as net_amount_chf,
    status::varchar as status,
    paid_at::date as paid_at
from source
