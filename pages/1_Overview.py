import streamlit as st

from src.dashboard import ethics_section, render_map, setup_page

all_rows, sites, view, summary, _ = setup_page(
    "RemoteConnect NT",
    "Understanding connectivity gaps across remote Northern Territory communities.",
)

known_5g = all_rows["has_5g_nearby"].notna()
no_5g = int(all_rows.loc[known_5g, "has_5g_nearby"].eq(False).sum())
assessed_5g = int(known_5g.sum())
unique_sites = (
    sites[["rfnsa_id", "latitude", "longitude"]].drop_duplicates().shape[0]
    if not sites.empty
    else 0
)
proximity = int(all_rows["coverage_type"].eq("Proximity to cell").sum())
higher = int(all_rows["priority_band"].eq("Higher").sum())

kpis = st.columns(5)
kpis[0].metric("Community / location records", f"{len(all_rows):,}")
kpis[1].metric("Distinct mapped site locations", f"{unique_sites:,}")
kpis[2].metric("Proximity coverage records", f"{proximity:,}")
kpis[3].metric("Higher priority indicator", f"{higher:,}")
kpis[4].metric(
    "No nearby 5G band listed",
    f"{no_5g:,}" if assessed_5g else "Not assessed",
    f"{assessed_5g:,} assessed",
    delta_color="off",
)
st.caption("KPIs summarize the complete prepared dataset; sidebar filters change the map and filtered views.")

st.markdown(
    '<div class="note"><b>How to read these figures.</b> The NT Government list records remote locations '
    'with mobile coverage and distinguishes macro-cell, small-cell and proximity coverage; it is not a '
    'complete list of uncovered communities. “Proximity coverage” is shown as a source category, not as a '
    'measured quality-of-service rating. “No nearby 5G band listed” refers only to ACCC operator-site '
    'band records within 50 km and is not a service-availability claim. ACCC 2026 operator sites are '
    'matched using straight-line distance.</div>',
    unsafe_allow_html=True,
)

st.subheader("Community connectivity overview")
st.caption("Map pins show NT source locations, coloured by the experimental, adjustable priority indicator.")
render_map(view, sites, key="overview-map")

with st.expander("Data coverage and source files"):
    st.json(summary)
    st.write(
        "Community coverage source: NT Government, 2022. Infrastructure source: ACCC Mobile "
        "Infrastructure Report data release, 2026 Telstra, Optus and TPG mobile-site CSVs."
    )

ethics_section()
