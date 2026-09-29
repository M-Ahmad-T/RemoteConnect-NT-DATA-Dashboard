import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard import money_or_distance, parse_boolean, score_component_figure, setup_page

all_rows, _, view, _, _ = setup_page(
    "Community explorer",
    "Review source coverage, nearby mobile sites, and the inputs behind one location's score.",
)

if all_rows.empty:
    st.info("No community records are available.")
    st.stop()

options = all_rows[["community", "latitude", "longitude"]].drop_duplicates()
options = options.sort_values(["community", "latitude", "longitude"], na_position="last")
options["selection"] = options.apply(
    lambda row: f"{row['community']} — {row['latitude']:.4f}, {row['longitude']:.4f}"
    if pd.notna(row["latitude"]) and pd.notna(row["longitude"])
    else str(row["community"]),
    axis=1,
)
selected = st.selectbox("Select a community or source location", options["selection"].tolist())
selected_location = options.loc[options["selection"].eq(selected)].iloc[0]
matches = all_rows.loc[
    all_rows["community"].eq(selected_location["community"])
    & all_rows["latitude"].eq(selected_location["latitude"])
    & all_rows["longitude"].eq(selected_location["longitude"])
]
row = matches.iloc[0]

st.subheader(str(row["community"]))
st.caption(f"Source location: {row['latitude']:.5f}, {row['longitude']:.5f} · {row['site_type'] or 'Site type not specified'}")

source_population = row.get("population")
abs_population = row.get("abs_population_2021")
metrics = st.columns(5)
metrics[0].metric(
    "Population in NT coverage source",
    f"{int(source_population):,}" if pd.notna(source_population) else "Not supplied",
)
metrics[1].metric(
    "ABS ILOC population (2021)",
    f"{int(abs_population):,}" if pd.notna(abs_population) else "Not supplied",
)
metrics[2].metric("Coverage type", str(row["coverage_type"]))
metrics[3].metric(
    "Priority indicator",
    f"{row['priority_score']:.1f}/100" if pd.notna(row["priority_score"]) else "Not scored",
    str(row["priority_band"]) if pd.notna(row["priority_band"]) else None,
)
metrics[4].metric(
    "Unique sites within 50 km",
    f"{int(row['sites_within_50km']):,}" if pd.notna(row["sites_within_50km"]) else "Not assessed",
)

st.markdown("#### Nearest operator infrastructure")
distances = {
    "All operators": row.get("nearest_mobile_site_km"),
    "Telstra": row.get("nearest_telstra_site_km"),
    "Optus": row.get("nearest_optus_site_km"),
    "TPG": row.get("nearest_tpg_site_km"),
}
distance_columns = st.columns(4)
for column, (provider, distance) in zip(distance_columns, distances.items()):
    column.metric(f"Nearest {provider}", money_or_distance(distance))

technology = st.columns(2)
has_4g = parse_boolean(row.get("has_4g_nearby"))
has_5g = parse_boolean(row.get("has_5g_nearby"))
technology[0].metric(
    "4G band at a site within 50 km",
    "Available" if has_4g is True else (
        "Not available in matched sites" if has_4g is False else "Not assessed"
    ),
)
technology[1].metric(
    "5G band at a site within 50 km",
    "Available" if has_5g is True else (
        "Not available in matched sites" if has_5g is False else "Not assessed"
    ),
)
st.caption("Band presence at nearby ACCC-listed sites is not a coverage or service-quality guarantee.")

left, right = st.columns(2)
provider_distance = pd.DataFrame(
    [
        {"Provider": provider, "Nearest site distance (km)": value}
        for provider, value in distances.items()
        if provider != "All operators" and pd.notna(value)
    ]
)
with left:
    st.markdown("#### Distance to provider infrastructure")
    if provider_distance.empty:
        st.info("Provider-specific distances are unavailable.")
    else:
        fig = px.bar(
            provider_distance,
            x="Provider",
            y="Nearest site distance (km)",
            color="Provider",
            color_discrete_map={"Telstra": "#0072B2", "Optus": "#E87524", "TPG": "#7D5AA6"},
        )
        st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("#### Nearby sites by provider")
    site_counts = pd.DataFrame(
        [
            {"Provider": provider, "Operator-site records within 50 km": row.get(f"{provider.lower()}_sites_nearby")}
            for provider in ("Telstra", "Optus", "TPG")
        ]
    ).dropna(subset=["Operator-site records within 50 km"])
    if site_counts.empty:
        st.info("Nearby infrastructure counts are unavailable.")
    else:
        st.plotly_chart(px.bar(site_counts, x="Provider", y="Operator-site records within 50 km"), width="stretch")

st.markdown("#### Priority indicator components")
if pd.notna(row["priority_score"]):
    st.plotly_chart(score_component_figure(row), width="stretch")
    st.markdown("**Why this community received this score**")
    st.write(str(row["priority_explanation"]))
    st.caption(
        "This is an experimental, adjustable decision-support indicator. Available components are "
        "rescaled to 100%; missing components do not receive an invented value."
    )
else:
    st.info("No supported score components are available for this location.")

matched_context = [
    ("ADII score", "digital_inclusion_score"),
    ("Access", "access_score"),
    ("Affordability", "affordability_score"),
    ("Digital Ability", "digital_ability_score"),
]
available_context = [(label, row.get(column)) for label, column in matched_context if column in row and pd.notna(row.get(column))]
st.markdown("#### Digital inclusion context")
if available_context:
    st.dataframe(
        pd.DataFrame(available_context, columns=["Source dimension", "Source value"]),
        hide_index=True,
        width="stretch",
    )
    st.caption("Only exact community-level matches are shown; aggregate results are not assigned to this location.")
else:
    st.info("No exact community-level ADII record is currently supplied. See the Digital inclusion page for source-geography guidance.")
