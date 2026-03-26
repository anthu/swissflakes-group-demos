with source as (

    select * from {{ ref('refund') }}

)

select
    refund_id::varchar as refund_id,
    payment_id::varchar as payment_id,
    reason::varchar as reason,
    amount_chf::number(12,2) as amount_chf,
    status::varchar as status,
    created_at::date as created_at,
    processed_at::date as processed_at
from source
