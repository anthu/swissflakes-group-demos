DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_PRODUCTS
  FROM 'sources/dbt_products'
  DEFAULT_TARGET = 'prod';
