DEFINE DBT PROJECT SFG_PAY{{env_suffix}}.DCM.DBT_TRANSACTIONS
  FROM 'sources/dbt_transactions'
  DEFAULT_TARGET = 'prod';
