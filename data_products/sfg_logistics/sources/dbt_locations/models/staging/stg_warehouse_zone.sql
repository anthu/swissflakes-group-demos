with source as (

    select * from {{ ref('warehouse_zone') }}

)

select
    zone_id::varchar as zone_id,
    warehouse_id::varchar as warehouse_id,
    zone_name::varchar as zone_name,
    zone_type::varchar as zone_type,
    capacity_pallets::int as capacity_pallets,
    temperature_controlled::boolean as temperature_controlled
from source
