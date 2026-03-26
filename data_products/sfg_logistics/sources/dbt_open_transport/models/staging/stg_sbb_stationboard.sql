with source as (

    select * from {{ source('RAW_SHIPMENTS', 'SBB_STATIONBOARD') }}

),

flattened as (

    select
        r.value:fahrt_bezeichner::string as fahrt_bezeichner,
        r.value:haltestellen_name::string as station_name,
        r.value:linien_text::string as line_text,
        r.value:produkt_id::string as product,
        r.value:abfahrtszeit::timestamp_ntz as scheduled_departure,
        r.value:ankunftszeit::timestamp_ntz as scheduled_arrival,
        r.value:ab_prognose::timestamp_ntz as forecast_departure,
        r.value:an_prognose::timestamp_ntz as forecast_arrival,
        r.value:abfahrtsverspatung::boolean as has_departure_delay,
        r.value:ankunftsverspatung::boolean as has_arrival_delay,
        r.value:faellt_aus_tf::boolean as is_cancelled,
        r.value:betreiber_name::string as operator_name,
        r.value:betriebstag::string as operating_day,
        r.value:bezeichnung_offiziell::string as official_name,
        r.value:bpuic::string as bpuic,
        r.value:verkehrsmittel_text::string as transport_type
    from source,
         lateral flatten(input => raw:results) r

)

select * from flattened
