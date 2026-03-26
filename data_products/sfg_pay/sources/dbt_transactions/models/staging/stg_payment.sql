with source as (

    select * from {{ ref('payment') }}

)

select
    payment_id::varchar as payment_id,
    order_id::varchar as order_id,
    merchant_id::varchar as merchant_id,
    amount_chf::number(12,2) as amount_chf,
    currency::varchar as currency,
    payment_method::varchar as payment_method,
    card_brand::varchar as card_brand,
    status::varchar as status,
    created_at::date as created_at,
    processed_at::date as processed_at,
    is_international::boolean as is_international,
    requires_aml_check::boolean as requires_aml_check
from source
