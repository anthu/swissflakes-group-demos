DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_FLEET
  FROM 'sources/dbt_fleet'
  DEFAULT_TARGET = 'prod';
