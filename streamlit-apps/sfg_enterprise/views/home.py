import streamlit as st
from shared.data import run_query
from shared.config import ENTERPRISE_DB, SEMANTIC_VIEWS, AGENT_FQN


def _get_intelligence_url():
    try:
        row = run_query("SELECT CURRENT_ORGANIZATION_NAME() AS ORG, CURRENT_ACCOUNT_NAME() AS ACCT")
        org = row["ORG"].iloc[0].lower()
        acct = row["ACCT"].iloc[0].lower()
        return f"https://app.snowflake.com/{org}/{acct}/#/intelligence"
    except Exception:
        return None


st.title("SwissFlakes Enterprise Analytics")
st.markdown("Overview of enterprise data products across Fulfillment, Revenue, and Compliance.")

st.divider()

st.subheader("Snowflake Intelligence")
st.markdown(
    f"Ask questions in natural language using the **Fulfillment Analyst** agent "
    f"(`{AGENT_FQN}`). The agent has access to 3 semantic views covering "
    f"fulfillment lifecycle, revenue by route, and compliance transactions."
)
intel_url = _get_intelligence_url()
if intel_url:
    st.link_button("Open Snowflake Intelligence", url=intel_url, type="primary")
else:
    st.info("Could not determine Snowflake Intelligence URL.")

st.divider()

st.subheader("Data Product Overview")

schemas = ["MART_FULFILLMENT", "MART_CUSTOMER_360", "MART_REVENUE_ANALYTICS", "MART_COMPLIANCE"]
cols = st.columns(len(schemas))

for col, schema in zip(cols, schemas):
    with col:
        label = schema.replace("MART_", "").replace("_", " ").title()
        try:
            df = run_query(f"SHOW TABLES IN SCHEMA {ENTERPRISE_DB}.{schema}")
            table_count = len(df)
        except Exception:
            table_count = 0

        try:
            df_sv = run_query(f"SHOW SEMANTIC VIEWS IN SCHEMA {ENTERPRISE_DB}.{schema}")
            sv_count = len(df_sv)
        except Exception:
            sv_count = 0

        st.metric(label, f"{table_count} tables")
        if sv_count > 0:
            st.caption(f"{sv_count} semantic view(s)")

st.divider()

st.subheader("Semantic Views")
for name, fqn in SEMANTIC_VIEWS.items():
    with st.expander(f"{name.replace('_', ' ').title()} — `{fqn}`"):
        try:
            desc = run_query(f"DESCRIBE SEMANTIC VIEW {fqn}")
            st.dataframe(desc, use_container_width=True)
        except Exception as e:
            st.info(f"Semantic view not yet materialized. Deploy dbt models first.\n\n`{e}`")
