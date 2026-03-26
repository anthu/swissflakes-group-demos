import streamlit as st

st.set_page_config(
    page_title="SwissFlakes Enterprise Analytics",
    page_icon="🏔️",
    layout="wide",
)

home = st.Page("views/home.py", title="Home", icon="🏠", default=True)
fulfillment = st.Page("views/fulfillment.py", title="Fulfillment", icon="📦")
revenue = st.Page("views/revenue.py", title="Revenue", icon="💰")
compliance = st.Page("views/compliance.py", title="Compliance", icon="🛡️")

pg = st.navigation([home, fulfillment, revenue, compliance])

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Flag_of_Switzerland.svg/120px-Flag_of_Switzerland.svg.png",
        width=40,
    )
    st.caption("SwissFlakes Group AG")
    st.divider()
    st.caption("Enterprise Analytics Dashboard")

pg.run()
