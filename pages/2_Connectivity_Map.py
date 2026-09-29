import streamlit as st
from src.dashboard import PROVIDER_COLORS, location_picker, next_page, render_map, setup_page, source_footer

_, sites, view, _, _ = setup_page("Connectivity map", "Compare the 2022 source locations with the 2026 operator-site records.")
st.caption(f"{len(view)} filtered source locations · equal-size circles · colour shows the experimental priority band.")
show = st.toggle("Overlay ACCC operator sites", value=False)
if show:
    st.markdown("**Crosses = 2026 operator sites.**")
    st.markdown(' &nbsp; '.join(f'<span style="color:{color};font-weight:700">×</span> {name}' for name, color in PROVIDER_COLORS.items()), unsafe_allow_html=True)
    st.caption(f"All {len(sites)} NT operator-site records are shown, independent of location filters. TPG shared-network access is excluded.")
render_map(view, sites if show else None, key="connectivity-map", height=510)
st.caption("Marker size is fixed. Neither layer is a coverage footprint. Drag to pan; double-click to reset. Boundary: Natural Earth.")
row = location_picker(view, "Open a location from this view")
next_page("3_Community_Explorer.py", f"Inspect {row.community.title()} →")
with st.expander("Read the map as a table"):
    st.dataframe(view[["community", "coverage_type", "priority_score", "priority_band", "nearest_mobile_site_km"]].rename(
        columns={"community":"Location", "coverage_type":"2022 source flags", "priority_score":"Indicator /100", "priority_band":"Band", "nearest_mobile_site_km":"Nearest NT site (km)"}), hide_index=True, width="stretch")
source_footer()
