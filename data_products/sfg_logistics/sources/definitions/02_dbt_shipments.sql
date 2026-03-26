DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_SHIPMENTS
  FROM 'sources/dbt_shipments'
  DEFAULT_TARGET = 'prod';
