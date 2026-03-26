import streamlit as st
from snowflake.snowpark.context import get_active_session


@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=300)
def run_query(sql: str):
    session = get_session()
    return session.sql(sql).to_pandas()


@st.cache_data(ttl=300)
def get_table_preview(fqn: str, limit: int = 100):
    return run_query(f"SELECT * FROM {fqn} LIMIT {limit}")


@st.cache_data(ttl=600)
def get_row_count(fqn: str) -> int:
    df = run_query(f"SELECT COUNT(*) AS CNT FROM {fqn}")
    return int(df["CNT"].iloc[0]) if len(df) > 0 else 0


@st.cache_data(ttl=600)
def list_tables_in_schema(db: str, schema: str):
    return run_query(
        f"SHOW TABLES IN SCHEMA {db}.{schema}"
    )
