import streamlit as st
import plotly.express as px
from shared.data import run_query, get_table_preview
from shared.config import ENTERPRISE_DB

SCHEMA = f"{ENTERPRISE_DB}.MART_REVENUE_ANALYTICS"
TABLE = f"{SCHEMA}.REVENUE_BY_ROUTE"

st.title("Revenue Analytics")
st.caption("Revenue aggregated by shipping route (origin warehouse to destination city)")

try:
    df = get_table_preview(TABLE, limit=1000)
except Exception:
    st.warning(
        "Revenue data not yet available. Run the dbt models:\n\n"
        "```sql\nEXECUTE DBT PROJECT SFG_ENTERPRISE.DCM.DBT_REVENUE_ANALYTICS ARGS = 'run';\n```"
    )
    st.stop()

if df.empty:
    st.info("No data in revenue_by_route.")
    st.stop()

tab_kpis, tab_data = st.tabs(["KPIs", "Data"])

with tab_kpis:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue (CHF)", f"{df['TOTAL_REVENUE_CHF'].sum():,.0f}" if "TOTAL_REVENUE_CHF" in df.columns else "N/A")
    c2.metric("Total Shipments", f"{df['TOTAL_SHIPMENTS'].sum():,}" if "TOTAL_SHIPMENTS" in df.columns else "N/A")
    c3.metric("Avg Order Value (CHF)", f"{df['AVG_ORDER_VALUE_CHF'].mean():,.0f}" if "AVG_ORDER_VALUE_CHF" in df.columns else "N/A")

    if "ORIGIN_WAREHOUSE" in df.columns and "TOTAL_REVENUE_CHF" in df.columns:
        fig = px.bar(
            df.sort_values("TOTAL_REVENUE_CHF", ascending=False),
            x="ORIGIN_WAREHOUSE",
            y="TOTAL_REVENUE_CHF",
            color="DESTINATION_CITY" if "DESTINATION_CITY" in df.columns else None,
            title="Revenue by Route (CHF)",
        )
        st.plotly_chart(fig, use_container_width=True)

    if "DESTINATION_CITY" in df.columns and "AVG_DELIVERY_DAYS" in df.columns:
        fig2 = px.scatter(
            df,
            x="AVG_DELIVERY_DAYS",
            y="TOTAL_REVENUE_CHF",
            size="TOTAL_SHIPMENTS",
            color="DESTINATION_CITY",
            title="Revenue vs Delivery Time by City",
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab_data:
    st.dataframe(df, use_container_width=True)
