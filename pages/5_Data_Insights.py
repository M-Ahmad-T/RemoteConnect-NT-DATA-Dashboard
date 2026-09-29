import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard import PALETTE, setup_page

all_rows, sites, view, _, _ = setup_page(
    "Data insights",
    "Explore patterns in the loaded NT coverage records and ACCC mobile-site data.",
)

if view.empty:
    st.info("No community records match the active filters.")
    st.stop()

left, right = st.columns(2)
with left:
    st.subheader("Coverage type")
    coverage = view["coverage_type"].fillna("Not specified").value_counts().rename_axis("Coverage type").reset_index(name="Locations")
    st.plotly_chart(px.bar(coverage, x="Coverage type", y="Locations", color="Coverage type"), width="stretch")
    proximity_count = int(view["coverage_type"].eq("Proximity to cell").sum())
    st.caption(
        f"{proximity_count:,} of {len(view):,} filtered source locations are listed as receiving coverage "
        "by proximity to a cell; this is a source category, not a service-quality measurement."
    )

with right:
    st.subheader("Priority indicator distribution")
    priority = view["priority_band"].fillna("Unscored").value_counts().reindex(
        ["Lower", "Moderate", "Higher", "Unscored"], fill_value=0
    ).rename_axis("Priority band").reset_index(name="Locations")
    st.plotly_chart(px.bar(priority, x="Priority band", y="Locations", color="Priority band"), width="stretch")
    st.caption(
        f"{int(view['priority_band'].eq('Higher').sum()):,} filtered locations fall in the higher experimental band; "
        "this is not an official government priority ranking."
    )

left, right = st.columns(2)
with left:
    st.subheader("Infrastructure operator-site records")
    if sites.empty:
        st.info("No ACCC infrastructure records are available.")
    else:
        by_provider = sites["provider"].value_counts().rename_axis("Provider").reset_index(name="Operator-site records")
        st.plotly_chart(px.bar(by_provider, x="Provider", y="Operator-site records", color="Provider"), width="stretch")
        st.caption(
            f"The NT-filtered infrastructure file contains {len(sites):,} operator-site records across "
            f"{sites['provider'].nunique()} provider(s). A shared physical site can have separate provider records."
        )

with right:
    st.subheader("4G / 5G bands in ACCC site records")
    if sites.empty:
        st.info("No ACCC infrastructure records are available.")
    else:
        tech = pd.DataFrame(
            {
                "Technology": ["4G / LTE", "5G / NR"],
                "Site records with at least one band": [
                    int(sites["has_4g"].fillna(False).sum()),
                    int(sites["has_5g"].fillna(False).sum()),
                ],
            }
        )
        st.plotly_chart(px.bar(tech, x="Technology", y="Site records with at least one band"), width="stretch")
        st.caption("A band listed at an infrastructure site does not establish a coverage footprint or service at a community.")

left, right = st.columns(2)
with left:
    st.subheader("Distance to nearest listed mobile site")
    distances = pd.to_numeric(view["nearest_mobile_site_km"], errors="coerce").dropna()
    if distances.empty:
        st.info("Nearest-site distance is not available for the filtered locations.")
    else:
        chart = px.histogram(
            distances.to_frame("Distance (km)"),
            x="Distance (km)",
            nbins=20,
            color_discrete_sequence=[PALETTE["teal"]],
        )
        st.plotly_chart(chart, width="stretch")
        st.caption(f"Median nearest-site distance among matched filtered locations: {distances.median():.1f} km.")

with right:
    st.subheader("Provider diversity within 50 km")
    diversity = pd.to_numeric(view["infrastructure_diversity"], errors="coerce").dropna()
    if diversity.empty:
        st.info("Provider diversity is unavailable for the filtered locations.")
    else:
        counts = diversity.value_counts().sort_index().rename_axis("Providers within 50 km").reset_index(name="Locations")
        st.plotly_chart(px.bar(counts, x="Providers within 50 km", y="Locations"), width="stretch")
        st.caption(f"Median distinct-provider count within 50 km: {diversity.median():.1f}.")

st.subheader("Filtered source-backed records")
st.dataframe(
    view[
        [
            column
            for column in (
                "community",
                "coverage_type",
                "nearest_mobile_site_km",
                "sites_within_50km",
                "infrastructure_diversity",
                "has_4g_nearby",
                "has_5g_nearby",
                "priority_score",
                "priority_band",
            )
            if column in view
        ]
    ],
    width="stretch",
    hide_index=True,
)
