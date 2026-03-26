with source as (

    select * from {{ ref('customer_contact') }}

)

select
    contact_id::varchar as contact_id,
    customer_id::varchar as customer_id,
    first_name::varchar as first_name,
    last_name::varchar as last_name,
    role::varchar as role,
    email::varchar as email,
    phone::varchar as phone,
    is_primary::boolean as is_primary
from source
