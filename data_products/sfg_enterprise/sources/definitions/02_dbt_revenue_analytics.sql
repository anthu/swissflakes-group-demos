DEFINE DBT PROJECT SFG_ENTERPRISE{{env_suffix}}.DCM.DBT_REVENUE_ANALYTICS
  FROM 'sources/dbt_revenue_analytics'
  DEFAULT_TARGET = 'prod';
