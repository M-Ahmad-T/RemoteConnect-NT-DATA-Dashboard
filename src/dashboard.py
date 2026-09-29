"""Shared Streamlit components for the RemoteConnect NT pages."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.priority import DEFAULT_WEIGHTS, apply_priority_weights  # noqa: E402

COMMUNITY_DATA = ROOT / "data" / "processed" / "communities.csv"
SITE_DATA = ROOT / "data" / "processed" / "infrastructure_nt.csv"
SUMMARY_DATA = ROOT / "data" / "processed" / "data_summary.json"

PALETTE = {
    "navy": "#102637",
    "teal": "#168C88",
    "gold": "#D99B39",
    "red": "#B94F43",
    "pale": "#F3F6F7",
    "muted": "#657782",
}
BAND_COLORS = {"Lower": "#3B9A87", "Moderate": "#D99B39", "Higher": "#B94F43"}


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    missing = [str(path.relative_to(ROOT)) for path in (COMMUNITY_DATA, SITE_DATA) if not path.exists()]
    if missing:
        raise FileNotFoundError(", ".join(missing))
    communities = pd.read_csv(COMMUNITY_DATA)
    sites = pd.read_csv(SITE_DATA)
    if "has_4g_nearby" in communities:
        communities["has_4g_nearby"] = communities["has_4g_nearby"].map(parse_boolean)
    if "has_5g_nearby" in communities:
        communities["has_5g_nearby"] = communities["has_5g_nearby"].map(parse_boolean)
    summary = json.loads(SUMMARY_DATA.read_text(encoding="utf-8")) if SUMMARY_DATA.exists() else {}
    return communities, sites, summary


def parse_boolean(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    text = str(value).strip().casefold()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return pd.NA


def setup_page(title: str, description: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict]:
    theme = (ROOT / "assets" / "theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{theme}</style>", unsafe_allow_html=True)
    st.sidebar.markdown("## RemoteConnect NT")
    st.sidebar.caption("A source-grounded view of remote connectivity")
    try:
        all_communities, sites, summary = load_data()
    except FileNotFoundError as error:
        st.title(title)
        st.warning("Prepared source data is not available yet.")
        st.code("python src/prepare_data.py\nstreamlit run app.py")
        st.caption(f"Missing: {error}")
        st.info("The NT community workbook, ACCC site CSVs, and NT boundary file are listed in data/raw/README.txt.")
        st.stop()
    weights = {}
    with st.sidebar.expander("Experimental score weights", expanded=False):
        st.caption("Weights are rescaled over available components for each record.")
        for name, default in DEFAULT_WEIGHTS.items():
            weights[name] = st.slider(
                name.title(),
                min_value=0,
                max_value=100,
                value=int(default),
                step=5,
                key=f"weight_{name}",
            )
    scored = apply_priority_weights(all_communities, weights)
    available_providers = set(summary.get("infrastructure_sources", {}))
    view = sidebar_filters(scored, available_providers)
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{description}</p></div>', unsafe_allow_html=True)
    return scored, sites, view, summary, weights


def sidebar_filters(frame: pd.DataFrame, available_providers: set[str]) -> pd.DataFrame:
    st.sidebar.divider()
    st.sidebar.markdown("### Explore filters")
    view = frame.copy()
    providers = [
        name
        for name in ("Telstra", "Optus", "TPG")
        if f"{name.lower()}_sites_nearby" in frame and name in available_providers
    ]
    selected_providers = st.sidebar.multiselect("Nearby provider within 50 km", providers, default=providers)
    if selected_providers and providers and set(selected_providers) != set(providers):
        masks = [pd.to_numeric(frame[f"{name.lower()}_sites_nearby"], errors="coerce").fillna(0).gt(0) for name in selected_providers]
        view = view.loc[np.logical_or.reduce(masks)]
    elif providers:
        if not selected_providers:
            view = view.iloc[0:0]

    coverage = sorted(frame["coverage_type"].dropna().astype(str).unique()) if "coverage_type" in frame else []
    selected_coverage = st.sidebar.multiselect("Source coverage type", coverage, default=coverage)
    if selected_coverage:
        view = view[view["coverage_type"].isin(selected_coverage)]
    else:
        view = view.iloc[0:0]

    priority_values = ["Lower", "Moderate", "Higher", "Unscored"]
    selected_priority = st.sidebar.multiselect("Priority band", priority_values, default=priority_values)
    priority = frame["priority_band"].fillna("Unscored")
    view = view.loc[priority.loc[view.index].isin(selected_priority)]

    for label, column in (
        ("4G band listed within 50 km", "has_4g_nearby"),
        ("5G band listed within 50 km", "has_5g_nearby"),
    ):
        if column not in frame:
            continue
        choice = st.sidebar.selectbox(label, ["All", "Available", "Not available", "Not assessed"], key=f"filter_{column}")
        values = frame[column].map(parse_boolean)
        if choice == "Available":
            view = view[values.loc[view.index].eq(True)]
        elif choice == "Not available":
            view = view[values.loc[view.index].eq(False)]
        elif choice == "Not assessed":
            view = view[values.loc[view.index].isna()]

    if "remoteness" in frame:
        remoteness_values = sorted(frame["remoteness"].dropna().astype(str).unique())
        options = ["All", "Not supplied", *remoteness_values]
        selection = st.sidebar.selectbox("Remoteness", options)
        if selection == "Not supplied":
            view = view[view["remoteness"].isna()]
        elif selection != "All":
            view = view[view["remoteness"].astype(str).eq(selection)]
    else:
        st.sidebar.caption("Remoteness: not supplied in the loaded source files.")
    return view


def money_or_distance(value: object, unit: str = "km") -> str:
    if pd.isna(value):
        return "Not available"
    return f"{float(value):,.1f} {unit}"


def render_map(frame: pd.DataFrame, sites: pd.DataFrame, key: str = "community-map") -> None:
    mapped = frame.dropna(subset=["latitude", "longitude"]).copy()
    if mapped.empty:
        st.info("No mapped community records remain after filtering.")
        return
    mapped["priority_band"] = mapped["priority_band"].fillna("Unscored")
    mapped["map_size"] = pd.to_numeric(mapped["priority_score"], errors="coerce").fillna(10).clip(lower=10)
    hover_columns = [
        column
        for column in (
            "coverage_type",
            "priority_score",
            "nearest_mobile_site_km",
            "nearest_telstra_site_km",
            "nearest_optus_site_km",
            "nearest_tpg_site_km",
            "sites_within_50km",
            "has_4g_nearby",
            "has_5g_nearby",
        )
        if column in mapped
    ]
    boundary_path = ROOT / "data" / "raw" / "nt_state_boundary.geojson"
    boundary_data = json.loads(boundary_path.read_text(encoding="utf-8"))
    geometry = boundary_data["features"][0]["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    figure = go.Figure()
    for polygon_index, polygon in enumerate(polygons):
        ring = polygon[0]
        figure.add_trace(
            go.Scattergeo(
                lon=[point[0] for point in ring],
                lat=[point[1] for point in ring],
                mode="lines",
                fill="toself",
                fillcolor="#E8F0EF",
                line={"color": "#83999B", "width": 1},
                name="Northern Territory boundary",
                hoverinfo="skip",
                showlegend=polygon_index == 0,
            )
        )
    priority_order = ["Lower", "Moderate", "Higher", "Unscored"]
    custom_columns = ["community", *hover_columns]
    custom_data = mapped[custom_columns].astype(object).where(mapped[custom_columns].notna(), "Not available").to_numpy()
    for band in priority_order:
        subset = mapped["priority_band"].eq(band)
        if not subset.any():
            continue
        selected = mapped.loc[subset]
        figure.add_trace(
            go.Scattergeo(
                lon=selected["longitude"],
                lat=selected["latitude"],
                mode="markers",
                name=f"{band} priority",
                marker={
                    "size": (7 + selected["map_size"] * 0.1).clip(8, 17),
                    "color": {**BAND_COLORS, "Unscored": PALETTE["muted"]}[band],
                    "line": {"width": 0.5, "color": "white"},
                    "opacity": 0.9,
                },
                customdata=custom_data[subset.to_numpy()],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    + "<br>".join(
                        f"{column.replace('_', ' ').title()}: %{{customdata[{index + 1}]}}"
                        for index, column in enumerate(hover_columns)
                    )
                    + "<extra></extra>"
                ),
            )
        )
    if sites is not None and not sites.empty and st.checkbox("Show ACCC mobile-site markers", value=False, key=f"show-sites-{key}"):
        provider_colors = {"Telstra": "#0072B2", "Optus": "#E87524", "TPG": "#7D5AA6"}
        for provider, subset in sites.groupby("provider"):
            figure.add_trace(
                go.Scattergeo(
                    lon=subset["longitude"],
                    lat=subset["latitude"],
                    mode="markers",
                    name=f"{provider} site",
                    marker={"size": 7, "color": provider_colors.get(provider, "#555555"), "opacity": 0.75},
                    customdata=np.stack(
                        [
                            subset["rfnsa_id"].fillna("Not supplied").astype(str),
                            subset["has_4g"].fillna(False).astype(str),
                            subset["has_5g"].fillna(False).astype(str),
                        ],
                        axis=-1,
                    ),
                    hovertemplate=(
                        f"{provider}<br>RFNSA ID: %{{customdata[0]}}"
                        "<br>4G bands present: %{customdata[1]}"
                        "<br>5G bands present: %{customdata[2]}<extra></extra>"
                    ),
                )
            )
    figure.update_layout(
        margin={"r": 0, "t": 5, "l": 0, "b": 0},
        legend_title_text="Community priority / infrastructure",
        height=590,
        geo={
            "projection": {"type": "mercator"},
            "center": {"lat": -19, "lon": 134},
            "showland": False,
            "showcoastlines": False,
            "showframe": False,
            "showlakes": False,
            "lonaxis": {"range": [128.5, 139], "showgrid": False},
            "lataxis": {"range": [-27.5, -9.5], "showgrid": False},
            "bgcolor": "#F7FAFA",
        },
    )
    st.plotly_chart(figure, width="stretch", key=key)
    st.caption("The NT boundary and data points are drawn from local source files; no external map tiles are used.")


def score_component_figure(row: pd.Series) -> go.Figure:
    labels = {
        "coverage_limitation_component": "Coverage type proxy",
        "distance_component": "Nearest site distance",
        "provider_diversity_component": "Provider diversity",
        "context_component": "ADII / remoteness context",
    }
    values = [
        {"Component": label, "Score (0-100)": float(row[column])}
        for column, label in labels.items()
        if column in row and pd.notna(row[column])
    ]
    return px.bar(
        pd.DataFrame(values),
        x="Score (0-100)",
        y="Component",
        orientation="h",
        range_x=[0, 100],
        color="Score (0-100)",
        color_continuous_scale=["#3B9A87", "#D99B39", "#B94F43"],
    ).update_layout(showlegend=False, coloraxis_showscale=False, margin={"l": 5, "r": 5, "t": 10, "b": 5})


def ethics_section() -> None:
    st.subheader("Ethics & limitations")
    st.markdown(
        """
        - Connectivity records can be outdated; NT coverage is from 2022 and ACCC site records are a 2026 release.
        - Tower proximity does not guarantee signal, capacity, reliability, indoor service or local service quality.
        - Coverage is not affordability. Digital inclusion also involves Access, Affordability and Digital Ability.
        - Aggregate statistics cannot describe every individual; never infer a person's digital ability.
        - Use respectful, strengths-based language; do not label First Nations communities “digitally illiterate”.
        - Community consultation should precede infrastructure decisions.
        - The experimental priority indicator is decision support, not an official ranking or investment decision.
        - Missing data is shown as unavailable rather than estimated without evidence.
        """
    )
