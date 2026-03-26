DEFINE DBT PROJECT SFG_LOGISTICS{{env_suffix}}.DCM.DBT_LOCATIONS
  FROM 'sources/dbt_locations'
  DEFAULT_TARGET = 'prod';
