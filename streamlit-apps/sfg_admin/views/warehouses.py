import streamlit as st
import plotly.express as px
from shared.data import run_query

st.title("Warehouse Monitoring")

try:
    wh_df = run_query("SHOW WAREHOUSES LIKE 'SWISSFLAKES%'")
except Exception as e:
    st.error(str(e))
    st.stop()

if wh_df.empty:
    st.info("No SwissFlakes warehouses found.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Total Warehouses", len(wh_df))
running = wh_df[wh_df["state"] == "STARTED"] if "state" in wh_df.columns else wh_df[wh_df["STATE"] == "STARTED"] if "STATE" in wh_df.columns else []
c2.metric("Currently Running", len(running))
suspended = len(wh_df) - len(running)
c3.metric("Suspended", suspended)

st.divider()

display_cols = []
for c in ["name", "state", "size", "auto_suspend", "auto_resume", "comment"]:
    if c in wh_df.columns:
        display_cols.append(c)
    elif c.upper() in wh_df.columns:
        display_cols.append(c.upper())

if display_cols:
    st.dataframe(wh_df[display_cols], use_container_width=True)
else:
    st.dataframe(wh_df, use_container_width=True)

st.subheader("Credit Usage (Last 7 Days)")
try:
    credits = run_query("""
        SELECT
            WAREHOUSE_NAME,
            SUM(CREDITS_USED) AS CREDITS_USED
        FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
        WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
          AND WAREHOUSE_NAME LIKE 'SWISSFLAKES%'
        GROUP BY WAREHOUSE_NAME
        ORDER BY CREDITS_USED DESC
    """)
    if not credits.empty:
        fig = px.bar(credits, x="WAREHOUSE_NAME", y="CREDITS_USED", title="Credits Used (Last 7 Days)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No credit usage data in the last 7 days.")
except Exception as e:
    st.info(f"Credit usage requires SNOWFLAKE.ACCOUNT_USAGE access: {e}")
