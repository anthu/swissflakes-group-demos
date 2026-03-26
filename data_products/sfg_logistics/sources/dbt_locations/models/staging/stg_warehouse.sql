with source as (

    select * from {{ ref('warehouse') }}

)

select
    warehouse_id::varchar as warehouse_id,
    warehouse_name::varchar as warehouse_name,
    street::varchar as street,
    postal_code::varchar as postal_code,
    city::varchar as city,
    canton::varchar as canton,
    latitude::float as latitude,
    longitude::float as longitude,
    capacity_pallets::int as capacity_pallets,
    is_active::boolean as is_active
from source
