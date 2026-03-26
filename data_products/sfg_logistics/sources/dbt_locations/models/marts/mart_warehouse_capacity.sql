with warehouses as (

    select * from {{ ref('stg_warehouse') }}

),

zone_aggregates as (

    select
        warehouse_id,
        count(*) as total_zones,
        sum(capacity_pallets) as total_zone_capacity_pallets,
        sum(case when temperature_controlled then 1 else 0 end) as temp_controlled_zones,
        sum(case when zone_type = 'STORAGE' then capacity_pallets else 0 end) as storage_capacity_pallets,
        sum(case when zone_type = 'COLD' then capacity_pallets else 0 end) as cold_capacity_pallets,
        sum(case when zone_type = 'HAZMAT' then capacity_pallets else 0 end) as hazmat_capacity_pallets,
        sum(case when zone_type = 'RECEIVING' then capacity_pallets else 0 end) as receiving_capacity_pallets,
        sum(case when zone_type = 'LOADING' then capacity_pallets else 0 end) as loading_capacity_pallets,
        sum(case when zone_type = 'RETURNS' then capacity_pallets else 0 end) as returns_capacity_pallets
    from {{ ref('stg_warehouse_zone') }}
    group by warehouse_id

)

select
    w.warehouse_id,
    w.warehouse_name,
    w.street,
    w.postal_code,
    w.city,
    w.canton,
    w.latitude,
    w.longitude,
    w.capacity_pallets as warehouse_capacity_pallets,
    w.is_active,
    za.total_zones,
    za.total_zone_capacity_pallets,
    za.temp_controlled_zones,
    za.storage_capacity_pallets,
    za.cold_capacity_pallets,
    za.hazmat_capacity_pallets,
    za.receiving_capacity_pallets,
    za.loading_capacity_pallets,
    za.returns_capacity_pallets
from warehouses as w
left join zone_aggregates as za
    on w.warehouse_id = za.warehouse_id
