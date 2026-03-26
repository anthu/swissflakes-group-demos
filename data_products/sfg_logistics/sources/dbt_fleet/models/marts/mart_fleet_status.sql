with vehicles as (

    select * from {{ ref('stg_vehicle') }}

),

latest_positions as (

    select
        vehicle_id,
        recorded_at as latest_recorded_at,
        latitude as latest_latitude,
        longitude as latest_longitude,
        speed_kmh as latest_speed_kmh,
        heading_degrees as latest_heading_degrees,
        is_moving as latest_is_moving
    from {{ ref('stg_gps_position') }}
    qualify row_number() over (partition by vehicle_id order by recorded_at desc) = 1

),

position_counts as (

    select
        vehicle_id,
        count(*) as total_positions
    from {{ ref('stg_gps_position') }}
    group by vehicle_id

)

select
    v.vehicle_id,
    v.plate_number,
    v.vehicle_type,
    v.make,
    v.model,
    v.year,
    v.capacity_kg,
    v.capacity_m3,
    v.fuel_type,
    v.home_base,
    v.is_active,
    v.last_service_date,
    lp.latest_recorded_at,
    lp.latest_latitude,
    lp.latest_longitude,
    lp.latest_speed_kmh,
    lp.latest_heading_degrees,
    lp.latest_is_moving,
    pc.total_positions
from vehicles as v
left join latest_positions as lp
    on v.vehicle_id = lp.vehicle_id
left join position_counts as pc
    on v.vehicle_id = pc.vehicle_id
