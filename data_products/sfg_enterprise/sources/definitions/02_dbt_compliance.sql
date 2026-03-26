DEFINE DBT PROJECT SFG_ENTERPRISE{{env_suffix}}.DCM.DBT_COMPLIANCE
  FROM 'sources/dbt_compliance'
  DEFAULT_TARGET = 'prod';
