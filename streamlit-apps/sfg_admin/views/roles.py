import streamlit as st
from shared.data import run_query

st.title("Roles & Grants")

st.subheader("SwissFlakes Roles")
try:
    roles = run_query("SHOW ROLES LIKE 'SWISSFLAKES%'")
    dp_roles = run_query("SHOW ROLES LIKE 'DP_%'")
    
    tab_platform, tab_dp = st.tabs(["Platform Roles", "Data Product Roles"])
    
    with tab_platform:
        if not roles.empty:
            display_cols = [c for c in ["name", "comment", "owner", "created_on"] if c in roles.columns]
            st.dataframe(roles[display_cols] if display_cols else roles, use_container_width=True)
        else:
            st.info("No SWISSFLAKES_* roles found.")
    
    with tab_dp:
        if not dp_roles.empty:
            display_cols = [c for c in ["name", "comment", "owner", "created_on"] if c in dp_roles.columns]
            st.dataframe(dp_roles[display_cols] if display_cols else dp_roles, use_container_width=True)
        else:
            st.info("No DP_* roles found.")
except Exception as e:
    st.error(str(e))

st.divider()

st.subheader("Role Hierarchy Explorer")
role_name = st.text_input("Enter a role name to inspect grants:", value="SWISSFLAKES_PLATFORM_ADMIN")
if role_name and st.button("Show Grants"):
    try:
        grants = run_query(f"SHOW GRANTS TO ROLE {role_name}")
        if not grants.empty:
            st.dataframe(grants, use_container_width=True)
        else:
            st.info(f"No grants found for role {role_name}.")
    except Exception as e:
        st.error(str(e))
