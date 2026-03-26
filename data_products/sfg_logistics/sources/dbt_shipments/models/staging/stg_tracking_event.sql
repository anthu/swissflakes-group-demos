with source as (

    select * from {{ ref('tracking_event') }}

)

select
    event_id::varchar as event_id,
    shipment_id::varchar as shipment_id,
    event_type::varchar as event_type,
    event_timestamp::timestamp as event_timestamp,
    location_name::varchar as location_name,
    latitude::float as latitude,
    longitude::float as longitude,
    notes::varchar as notes
from source
