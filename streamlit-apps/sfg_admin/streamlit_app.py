import streamlit as st

st.set_page_config(
    page_title="SwissFlakes Platform Admin",
    page_icon="⚙️",
    layout="wide",
)

home = st.Page("views/home.py", title="Overview", icon="🏠", default=True)
warehouses = st.Page("views/warehouses.py", title="Warehouses", icon="🏭")
roles = st.Page("views/roles.py", title="Roles & Grants", icon="🔐")

pg = st.navigation([home, warehouses, roles])

with st.sidebar:
    st.caption("SwissFlakes Platform Admin")
    st.divider()

pg.run()
