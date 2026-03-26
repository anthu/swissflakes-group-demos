with source as (

    select * from {{ source('RAW_LOCATIONS', 'TRANSPORT_CONNECTIONS') }}

),

flattened as (

    select
        to_timestamp_ntz(c.value:from:departure::string, 'YYYY-MM-DD"T"HH24:MI:SSTZHTZM') as departure,
        c.value:from:station:name::string as from_station,
        c.value:from:station:coordinate:x::float as from_latitude,
        c.value:from:station:coordinate:y::float as from_longitude,
        c.value:to:station:name::string as to_station,
        c.value:duration::string as duration,
        c.value:products[0]::string as product,
        c.value:sections[0]:journey:operator::string as operator,
        c.value:sections[0]:journey:category::string as category,
        c.value:from:delay::int as delay_minutes,
        c.value:from:platform::string as platform
    from source,
         lateral flatten(input => raw:connections) c

)

select * from flattened
