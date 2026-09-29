"""RemoteConnect NT Streamlit application."""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="RemoteConnect NT",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="auto",
)

ROOT = Path(__file__).resolve().parent
from src.dashboard import PAGES, prepare_dashboard

navigation = st.navigation(
    [st.Page(str(ROOT / "pages" / filename), title=title) for filename, title in PAGES],
    position="sidebar",
)
# Entry-point widgets keep their state when navigating between pages.
st.session_state["_dashboard_context"] = prepare_dashboard()
navigation.run()
