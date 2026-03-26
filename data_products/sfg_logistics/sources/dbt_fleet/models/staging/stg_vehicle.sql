with source as (

    select * from {{ ref('vehicle') }}

)

select
    vehicle_id::varchar as vehicle_id,
    plate_number::varchar as plate_number,
    vehicle_type::varchar as vehicle_type,
    make::varchar as make,
    model::varchar as model,
    year::int as year,
    capacity_kg::int as capacity_kg,
    capacity_m3::float as capacity_m3,
    fuel_type::varchar as fuel_type,
    home_base::varchar as home_base,
    is_active::boolean as is_active,
    last_service_date::date as last_service_date
from source
