with source as (

    select * from {{ ref('gps_position') }}

)

select
    position_id::varchar as position_id,
    vehicle_id::varchar as vehicle_id,
    recorded_at::timestamp as recorded_at,
    latitude::float as latitude,
    longitude::float as longitude,
    speed_kmh::float as speed_kmh,
    heading_degrees::float as heading_degrees,
    is_moving::boolean as is_moving
from source
