with source as (

    select * from {{ source('RAW_WEATHER', 'METEOSWISS_MEASUREMENTS') }}

),

flattened as (

    select
        f.value:id::string as station_id,
        f.value:properties:title::string as station_name,
        f.value:properties:datetime::timestamp_ntz as last_update,
        f.value:geometry:coordinates[0]::float as longitude,
        f.value:geometry:coordinates[1]::float as latitude,
        array_size(object_keys(f.value:assets)) as num_assets
    from source,
         lateral flatten(input => raw:features) f

)

select * from flattened
