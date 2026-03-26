DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_OPEN_TRANSPORT
  FROM 'sources/dbt_open_transport'
  DEFAULT_TARGET = 'prod';
