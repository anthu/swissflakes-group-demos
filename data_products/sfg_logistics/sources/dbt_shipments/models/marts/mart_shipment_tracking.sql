with shipments as (

    select * from {{ ref('stg_shipment') }}

),

latest_events as (

    select
        shipment_id,
        event_type as latest_event_type,
        event_timestamp as latest_event_timestamp,
        location_name as latest_location,
        latitude as latest_latitude,
        longitude as latest_longitude,
        notes as latest_notes
    from {{ ref('stg_tracking_event') }}
    qualify row_number() over (partition by shipment_id order by event_timestamp desc) = 1

),

event_counts as (

    select
        shipment_id,
        count(*) as total_events
    from {{ ref('stg_tracking_event') }}
    group by shipment_id

)

select
    s.shipment_id,
    s.order_id,
    s.vehicle_id,
    s.origin_warehouse,
    s.destination_city,
    s.destination_postal_code,
    s.status,
    s.created_at,
    s.shipped_at,
    s.delivered_at,
    s.weight_kg,
    s.volume_m3,
    s.requires_customs,
    s.customs_declaration_id,
    le.latest_event_type,
    le.latest_event_timestamp,
    le.latest_location,
    le.latest_latitude,
    le.latest_longitude,
    le.latest_notes,
    ec.total_events
from shipments as s
left join latest_events as le
    on s.shipment_id = le.shipment_id
left join event_counts as ec
    on s.shipment_id = ec.shipment_id
