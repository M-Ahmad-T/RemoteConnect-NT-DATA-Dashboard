"""RemoteConnect NT Streamlit application."""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="RemoteConnect NT",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
navigation = st.navigation(
    [
        st.Page(str(ROOT / "pages" / "1_Overview.py"), title="Overview", icon=":material/dashboard:"),
        st.Page(str(ROOT / "pages" / "2_Connectivity_Map.py"), title="Connectivity map", icon=":material/map:"),
        st.Page(str(ROOT / "pages" / "3_Community_Explorer.py"), title="Community explorer", icon=":material/location_city:"),
        st.Page(str(ROOT / "pages" / "4_Digital_Inclusion.py"), title="Digital inclusion", icon=":material/diversity_3:"),
        st.Page(str(ROOT / "pages" / "5_Data_Insights.py"), title="Data insights", icon=":material/analytics:"),
        st.Page(str(ROOT / "pages" / "6_Offline_Mode.py"), title="Offline mode", icon=":material/download:"),
    ],
    position="sidebar",
)
navigation.run()
