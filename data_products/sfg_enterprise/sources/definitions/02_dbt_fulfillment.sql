DEFINE DBT PROJECT SFG_ENTERPRISE{{env_suffix}}.DCM.DBT_FULFILLMENT
  FROM 'sources/dbt_fulfillment'
  DEFAULT_TARGET = 'prod';
