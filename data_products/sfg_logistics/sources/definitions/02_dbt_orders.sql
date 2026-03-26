DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_ORDERS
  FROM 'sources/dbt_orders'
  DEFAULT_TARGET = 'prod';
