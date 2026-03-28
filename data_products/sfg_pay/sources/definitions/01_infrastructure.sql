-- ============================================================
-- SFG_PAY Domain Infrastructure
-- 2 source data products: transactions, merchants
-- ============================================================

{% for dp in ['TRANSACTIONS', 'MERCHANTS'] %}
DEFINE SCHEMA SFG_PAY{{env_suffix}}.RAW_{{dp}};
DEFINE SCHEMA SFG_PAY{{env_suffix}}.STG_{{dp}};
DEFINE SCHEMA SFG_PAY{{env_suffix}}.MART_{{dp}};
{% endfor %}

DEFINE ROLE DP_SFG_PAY{{env_suffix}}_OWNER
    COMMENT = 'Full control for {{dp_name}} domain';

{% for dp in ['TRANSACTIONS', 'MERCHANTS'] %}
DEFINE ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER
    COMMENT = 'RAW + STG read/write for {{dp}} in {{dp_name}}';

DEFINE ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER
    COMMENT = 'MART read-only for {{dp}} in {{dp_name}}';

GRANT ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER TO ROLE DP_SFG_PAY{{env_suffix}}_OWNER;

GRANT USAGE ON DATABASE SFG_PAY{{env_suffix}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER;
GRANT USAGE ON SCHEMA SFG_PAY{{env_suffix}}.MART_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA SFG_PAY{{env_suffix}}.MART_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER;
GRANT SELECT ON ALL VIEWS IN SCHEMA SFG_PAY{{env_suffix}}.MART_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_READER;

GRANT USAGE ON SCHEMA SFG_PAY{{env_suffix}}.RAW_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT USAGE ON SCHEMA SFG_PAY{{env_suffix}}.STG_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA SFG_PAY{{env_suffix}}.RAW_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA SFG_PAY{{env_suffix}}.STG_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT SELECT ON ALL TABLES IN SCHEMA SFG_PAY{{env_suffix}}.RAW_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;
GRANT SELECT ON ALL TABLES IN SCHEMA SFG_PAY{{env_suffix}}.STG_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_{{dp}}_WRITER;

GRANT CREATE TABLE, CREATE VIEW ON SCHEMA SFG_PAY{{env_suffix}}.RAW_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_OWNER;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA SFG_PAY{{env_suffix}}.STG_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_OWNER;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA SFG_PAY{{env_suffix}}.MART_{{dp}} TO ROLE DP_SFG_PAY{{env_suffix}}_OWNER;
{% endfor %}

GRANT ROLE DP_SFG_PAY{{env_suffix}}_OWNER TO ROLE SWISSFLAKES_PLATFORM_ADMIN;
GRANT ROLE SFG_PAY_DATA_PUBLISHER TO ROLE DP_SFG_PAY{{env_suffix}}_OWNER;

-- Openflow SPCS streaming: SNOWFLAKE_MANAGED auth runs as PUBLIC primary role.
-- Narrow grants so PutSnowpipeStreaming2 can write to pre-created target tables.
GRANT USAGE ON DATABASE SFG_PAY{{env_suffix}} TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA SFG_PAY{{env_suffix}}.RAW_TRANSACTIONS TO ROLE PUBLIC;
GRANT CREATE PIPE ON SCHEMA SFG_PAY{{env_suffix}}.RAW_TRANSACTIONS TO ROLE PUBLIC;
GRANT INSERT, EVOLVE SCHEMA ON TABLE SFG_PAY{{env_suffix}}.RAW_TRANSACTIONS.ECB_EXCHANGE_RATES TO ROLE PUBLIC;
