import streamlit as st
from snowflake.snowpark.context import get_active_session


@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=300)
def run_query(sql: str):
    session = get_session()
    return session.sql(sql).to_pandas()
