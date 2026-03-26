with source as (

    select * from {{ ref('shipment') }}

)

select
    shipment_id::varchar as shipment_id,
    order_id::varchar as order_id,
    vehicle_id::varchar as vehicle_id,
    origin_warehouse::varchar as origin_warehouse,
    destination_city::varchar as destination_city,
    destination_postal_code::varchar as destination_postal_code,
    status::varchar as status,
    created_at::timestamp as created_at,
    shipped_at::timestamp as shipped_at,
    delivered_at::timestamp as delivered_at,
    weight_kg::float as weight_kg,
    volume_m3::float as volume_m3,
    requires_customs::boolean as requires_customs,
    customs_declaration_id::varchar as customs_declaration_id
from source
