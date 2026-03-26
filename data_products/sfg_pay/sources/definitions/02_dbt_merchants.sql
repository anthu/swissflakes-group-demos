DEFINE DBT PROJECT SFG_PAY{{env_suffix}}.DCM.DBT_MERCHANTS
  FROM 'sources/dbt_merchants'
  DEFAULT_TARGET = 'prod';
