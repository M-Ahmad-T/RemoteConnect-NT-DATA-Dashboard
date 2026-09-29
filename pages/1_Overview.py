from html import escape

import streamlit as st
from src.dashboard import next_page, render_map, setup_page, source_footer, stats

all_rows, sites, view, summary, _ = setup_page(
    "Overview", "Which remote NT locations need a closer look at connectivity?")
st.caption("NT coverage list · 2022   /   ACCC operator sites · 31 January 2026")
if view.empty:
    st.info("No source locations match. Widen the sidebar filters to continue.")
    st.stop()

proximity = int(view.coverage_type.str.contains("Proximity to cell", regex=False).sum())
stats([(len(view), "Source locations", f"of {len(all_rows)} in the 2022 list"),
       (proximity, "List proximity coverage", "includes multiple source flags"),
       (int(view.priority_band.eq("Higher").sum()), "Flagged for follow-up", "higher experimental band")])
st.markdown(f"**{proximity} of {len(view)} selected locations list coverage by proximity to a cell.** "
            "Use the infrastructure comparison to choose what to check locally.")
st.caption("The NT list contains covered locations. It cannot identify every unserved community; a nearby site does not prove service.")

map_column, story = st.columns([1.35, 1], gap="large")
with map_column:
    render_map(view, key="overview-map", height=420)
    st.caption("Equal-size circles: 2022 source locations. Colour: experimental indicator band, not signal strength.")
with story:
    featured = view.sort_values(["priority_score", "community"], ascending=[False, True], na_position="last").iloc[0]
    distance = featured.nearest_mobile_site_km
    distance_text = f"{distance:.1f} km" if distance == distance else "not assessed"
    st.markdown(f'<div class="feature"><div class="eyebrow">Start with a location</div><h3>{escape(featured.community.title())}</h3>'
                f'<p>Nearest listed NT operator site: <b>{distance_text}</b>.</p>'
                f'<p>2022 source flags: {escape(featured.coverage_type)}.</p>'
                '<p>Selected by the highest current indicator in this view. This is a question to investigate, not a confirmed coverage gap.</p></div>', unsafe_allow_html=True)
    if st.button("Explore this location", type="primary", width="stretch"):
        st.session_state["selected_record"] = featured.name
        st.switch_page("pages/3_Community_Explorer.py")
    next_page("2_Connectivity_Map.py", "Browse the full connectivity map →")
    st.markdown("**Then check current service.** Confirm the provider, device and location with people who use the service, with their permission.")
source_footer()
