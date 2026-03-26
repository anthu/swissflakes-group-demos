with stations as (

    select * from {{ ref('stg_meteoswiss_stations') }}

)

select
    station_id,
    station_name,
    latitude,
    longitude,
    last_update,
    num_assets
from stations
