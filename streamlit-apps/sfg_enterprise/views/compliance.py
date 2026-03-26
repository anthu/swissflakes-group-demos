import streamlit as st
import plotly.express as px
from shared.data import run_query, get_table_preview
from shared.config import ENTERPRISE_DB

SCHEMA = f"{ENTERPRISE_DB}.MART_COMPLIANCE"
TABLE = f"{SCHEMA}.TRANSACTION_REPORT"

st.title("Compliance Monitor")
st.caption("FINMA reporting, BAZG customs, and GwG anti-money laundering")

try:
    df = get_table_preview(TABLE, limit=1000)
except Exception:
    st.warning(
        "Compliance data not yet available. Run the dbt models:\n\n"
        "```sql\nEXECUTE DBT PROJECT SFG_ENTERPRISE.DCM.DBT_COMPLIANCE ARGS = 'run';\n```"
    )
    st.stop()

if df.empty:
    st.info("No data in transaction_report.")
    st.stop()

tab_overview, tab_aml, tab_customs, tab_data = st.tabs(["Overview", "AML Flags", "Customs", "Data"])

with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    total = len(df)
    aml_count = df["REQUIRES_AML_CHECK"].sum() if "REQUIRES_AML_CHECK" in df.columns else 0
    customs_count = df["REQUIRES_CUSTOMS"].sum() if "REQUIRES_CUSTOMS" in df.columns else 0
    intl_count = df["IS_INTERNATIONAL"].sum() if "IS_INTERNATIONAL" in df.columns else 0

    c1.metric("Total Transactions", f"{total:,}")
    c2.metric("AML Flagged", f"{int(aml_count):,}", delta=f"{aml_count/total*100:.1f}%" if total > 0 else "0%")
    c3.metric("Customs Required", f"{int(customs_count):,}")
    c4.metric("International", f"{int(intl_count):,}")

    if "PAYMENT_METHOD" in df.columns and "AMOUNT_CHF" in df.columns:
        method_df = df.groupby("PAYMENT_METHOD")["AMOUNT_CHF"].agg(["sum", "count"]).reset_index()
        method_df.columns = ["PAYMENT_METHOD", "TOTAL_CHF", "COUNT"]
        fig = px.bar(method_df, x="PAYMENT_METHOD", y="TOTAL_CHF", title="Transaction Volume by Payment Method (CHF)")
        st.plotly_chart(fig, use_container_width=True)

with tab_aml:
    st.subheader("GwG Anti-Money Laundering Flags")
    if "REQUIRES_AML_CHECK" in df.columns:
        aml_df = df[df["REQUIRES_AML_CHECK"] == True]
        if aml_df.empty:
            st.success("No AML-flagged transactions.")
        else:
            st.warning(f"{len(aml_df)} transaction(s) flagged for AML review.")
            st.dataframe(aml_df, use_container_width=True)
    else:
        st.info("AML data not available in this table.")

with tab_customs:
    st.subheader("BAZG Customs Declarations")
    if "REQUIRES_CUSTOMS" in df.columns:
        customs_df = df[df["REQUIRES_CUSTOMS"] == True]
        if customs_df.empty:
            st.success("No shipments requiring customs declarations.")
        else:
            st.info(f"{len(customs_df)} shipment(s) with customs requirements.")
            st.dataframe(customs_df, use_container_width=True)
    else:
        st.info("Customs data not available in this table.")

with tab_data:
    st.dataframe(df, use_container_width=True)
