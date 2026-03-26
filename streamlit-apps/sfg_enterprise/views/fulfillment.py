import streamlit as st
import plotly.express as px
from shared.data import run_query, get_table_preview
from shared.config import ENTERPRISE_DB

SCHEMA = f"{ENTERPRISE_DB}.MART_FULFILLMENT"
TABLE = f"{SCHEMA}.FULFILLMENT_LIFECYCLE"

st.title("Fulfillment Analytics")
st.caption("Order-to-delivery lifecycle: orders, shipments, and payments")

try:
    df = get_table_preview(TABLE, limit=1000)
except Exception:
    st.warning(
        "Fulfillment data not yet available. Run the dbt models:\n\n"
        "```sql\nEXECUTE DBT PROJECT SFG_ENTERPRISE.DCM.DBT_FULFILLMENT ARGS = 'run';\n```"
    )
    st.stop()

if df.empty:
    st.info("No data in fulfillment_lifecycle. Seed the source data products first.")
    st.stop()

tab_kpis, tab_data, tab_explore = st.tabs(["KPIs", "Data", "Explore"])

with tab_kpis:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Orders", f"{df['ORDER_ID'].nunique():,}")
    c2.metric("Total Shipments", f"{df['SHIPMENT_ID'].nunique():,}")
    c3.metric("Avg Delivery Days", f"{df['DELIVERY_DAYS'].mean():.1f}" if "DELIVERY_DAYS" in df.columns else "N/A")
    c4.metric("Total Revenue (CHF)", f"{df['ORDER_TOTAL_CHF'].sum():,.0f}" if "ORDER_TOTAL_CHF" in df.columns else "N/A")

    if "ORDER_STATUS" in df.columns:
        fig = px.pie(df, names="ORDER_STATUS", title="Order Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

    if "ORIGIN_WAREHOUSE" in df.columns and "ORDER_TOTAL_CHF" in df.columns:
        wh_df = df.groupby("ORIGIN_WAREHOUSE")["ORDER_TOTAL_CHF"].sum().reset_index()
        fig2 = px.bar(wh_df, x="ORIGIN_WAREHOUSE", y="ORDER_TOTAL_CHF", title="Revenue by Warehouse (CHF)")
        st.plotly_chart(fig2, use_container_width=True)

with tab_data:
    st.dataframe(df, use_container_width=True)

with tab_explore:
    st.markdown("Write custom SQL against the fulfillment mart:")
    sql = st.text_area("SQL", value=f"SELECT * FROM {TABLE} LIMIT 50", height=100)
    if st.button("Run", key="run_fulfillment"):
        try:
            result = run_query(sql)
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(str(e))
