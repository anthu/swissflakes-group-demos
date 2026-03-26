with source as (

    select * from {{ ref('merchant_account') }}

)

select
    merchant_id::varchar as merchant_id,
    merchant_name::varchar as merchant_name,
    business_type::varchar as business_type,
    registration_number::varchar as registration_number,
    bank_account_iban::varchar as bank_account_iban,
    settlement_currency::varchar as settlement_currency,
    fee_rate_pct::number(4,2) as fee_rate_pct,
    customer_id::varchar as customer_id,
    is_active::boolean as is_active,
    onboarded_at::date as onboarded_at
from source
