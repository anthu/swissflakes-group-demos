DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_CUSTOMERS
  FROM 'sources/dbt_customers'
  DEFAULT_TARGET = 'prod';
