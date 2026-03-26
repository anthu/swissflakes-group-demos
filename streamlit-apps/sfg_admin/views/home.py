import streamlit as st
from shared.data import run_query

st.title("SwissFlakes Platform Overview")

st.divider()

st.subheader("Domain Databases")
try:
    dbs = run_query("SHOW DATABASES LIKE 'SFG%'")
    if not dbs.empty:
        st.dataframe(
            dbs[["name", "owner", "comment", "created_on"]],
            use_container_width=True,
        )
    else:
        st.info("No SFG databases found.")
except Exception as e:
    st.error(str(e))

st.subheader("DCM Projects")
try:
    dcm = run_query("SHOW DCM PROJECTS")
    if not dcm.empty:
        st.dataframe(dcm, use_container_width=True)
    else:
        st.info("No DCM projects found.")
except Exception as e:
    st.info(f"DCM projects query not available: {e}")

st.subheader("Governance Tags")
try:
    tags = run_query("SHOW TAGS IN SCHEMA SFG_ADMIN.GOVERNANCE")
    if not tags.empty:
        st.dataframe(
            tags[["name", "comment", "allowed_values"]] if "allowed_values" in tags.columns else tags,
            use_container_width=True,
        )
except Exception as e:
    st.info(f"Tags not available: {e}")
