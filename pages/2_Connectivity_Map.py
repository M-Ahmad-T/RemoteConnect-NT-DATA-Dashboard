import streamlit as st

from src.dashboard import render_map, setup_page

_, sites, view, _, _ = setup_page(
    "Connectivity map",
    "Explore source locations and nearby ACCC mobile infrastructure.",
)
st.caption(
    "Use the sidebar filters for provider, NT coverage type, priority band, nearby 4G/5G and remoteness. "
    "A missing tower match is shown as unavailable, not estimated."
)
render_map(view, sites, key="connectivity-map")

columns = [
    "community",
    "coverage_type",
    "priority_score",
    "priority_band",
    "nearest_mobile_site_km",
    "nearest_telstra_site_km",
    "nearest_optus_site_km",
    "nearest_tpg_site_km",
    "sites_within_50km",
    "has_4g_nearby",
    "has_5g_nearby",
]
columns = [column for column in columns if column in view]
st.subheader("Filtered community records")
if view.empty:
    st.info("No records match the selected filters.")
else:
    st.dataframe(view[columns], width="stretch", hide_index=True)
