with connections as (

    select
        departure,
        from_station as station_name,
        product as line_text,
        category as product,
        operator,
        from_latitude as latitude,
        from_longitude as longitude,
        delay_minutes,
        platform,
        'transport_opendata' as data_source
    from {{ ref('stg_transport_connections') }}

),

stationboard as (

    select
        scheduled_departure as departure,
        station_name,
        line_text,
        product,
        operator_name as operator,
        null::float as latitude,
        null::float as longitude,
        case
            when has_departure_delay and forecast_departure is not null and scheduled_departure is not null
            then datediff('minute', scheduled_departure, forecast_departure)
            else 0
        end as delay_minutes,
        null::string as platform,
        'sbb_stationboard' as data_source
    from {{ ref('stg_sbb_stationboard') }}

)

select
    departure,
    station_name,
    line_text,
    product,
    operator,
    latitude,
    longitude,
    delay_minutes,
    platform,
    data_source
from connections

union all

select
    departure,
    station_name,
    line_text,
    product,
    operator,
    latitude,
    longitude,
    delay_minutes,
    platform,
    data_source
from stationboard
