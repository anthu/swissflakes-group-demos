with customers as (

    select * from {{ ref('stg_business_customer') }}

),

primary_contacts as (

    select * from {{ ref('stg_customer_contact') }}
    where is_primary = true

)

select
    c.customer_id,
    c.company_name,
    c.legal_form,
    c.street,
    c.postal_code,
    c.city,
    c.canton,
    c.country,
    c.is_active,
    c.created_at,
    pc.contact_id as primary_contact_id,
    pc.first_name as primary_contact_first_name,
    pc.last_name as primary_contact_last_name,
    pc.role as primary_contact_role,
    pc.email as primary_contact_email,
    pc.phone as primary_contact_phone
from customers as c
left join primary_contacts as pc
    on c.customer_id = pc.customer_id
