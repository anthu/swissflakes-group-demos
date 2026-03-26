with source as (

    select * from {{ ref('business_customer') }}

)

select
    customer_id::varchar as customer_id,
    company_name::varchar as company_name,
    legal_form::varchar as legal_form,
    street::varchar as street,
    postal_code::varchar as postal_code,
    city::varchar as city,
    canton::varchar as canton,
    country::varchar as country,
    contact_name::varchar as contact_name,
    contact_email::varchar as contact_email,
    phone::varchar as phone,
    is_active::boolean as is_active,
    created_at::date as created_at
from source
