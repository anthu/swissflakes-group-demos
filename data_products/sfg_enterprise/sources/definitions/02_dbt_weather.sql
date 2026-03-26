DEFINE DBT PROJECT SFG_ENTERPRISE{{env_suffix}}.DCM.DBT_WEATHER
  FROM 'sources/dbt_weather'
  DEFAULT_TARGET = 'prod';
