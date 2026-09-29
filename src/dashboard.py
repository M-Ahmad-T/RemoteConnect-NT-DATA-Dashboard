"""Shared presentation, controls and locally drawn maps."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.priority import COMPONENT_COLUMNS, DEFAULT_WEIGHTS, apply_priority_weights

ROOT = Path(__file__).resolve().parents[1]
PALETTE = {"navy": "#18352f", "teal": "#146458", "gold": "#a87520", "red": "#a64033", "muted": "#546660"}
BAND_COLORS = {"Lower": "#267567", "Moderate": "#ab771c", "Higher": "#ae4335", "Unscored": "#65716f"}
PROVIDER_COLORS = {"Telstra": "#196eaa", "Optus": "#a84e20", "TPG": "#795394"}
PAGES = [("1_Overview.py", "Overview"), ("2_Connectivity_Map.py", "Connectivity map"),
         ("3_Community_Explorer.py", "Community explorer"), ("4_Digital_Inclusion.py", "Digital inclusion"),
         ("5_Data_Insights.py", "Data insights"), ("6_Offline_Mode.py", "Save snapshots")]


def parse_boolean(value):
    if pd.isna(value):
        return pd.NA
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return {"true": True, "1": True, "yes": True, "y": True,
            "false": False, "0": False, "no": False, "n": False}.get(str(value).strip().casefold(), pd.NA)


@st.cache_data(show_spinner=False)
def load_data(revision=None):
    base = ROOT / "data/processed"
    communities = pd.read_csv(base / "communities.csv")
    sites = pd.read_csv(base / "infrastructure_nt.csv")
    for column in ("has_4g_nearby", "has_5g_nearby"):
        communities[column] = communities[column].map(parse_boolean)
    return communities, sites, json.loads((base / "data_summary.json").read_text(encoding="utf-8"))


def prepare_dashboard():
    st.markdown(f"<style>{(ROOT / 'assets/theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    paths = [ROOT / "data/processed" / name for name in ("communities.csv", "infrastructure_nt.csv", "data_summary.json")]
    if not all(path.exists() for path in paths):
        from src.prepare_data import main
        with st.spinner("Preparing the included source files for first use…"):
            if main() != 0:
                st.error("Source preparation failed. Check the required files listed in DATA_SOURCES.md, then run the data preparation command in README.md.")
                st.stop()
    data, sites, summary = load_data(tuple(path.stat().st_mtime_ns for path in paths))
    st.sidebar.markdown("### RemoteConnect NT")
    st.sidebar.caption("Field questions, grounded in public data.")
    weights = {}
    with st.sidebar.expander("Adjust the indicator"):
        st.caption("Design assumptions, not measured service quality. Set every available weight to zero to leave records unscored.")
        for name, default in DEFAULT_WEIGHTS.items():
            supported = data[COMPONENT_COLUMNS[name]].notna().any()
            weights[name] = st.slider(name.title(), 0, 100, default, 5,
                                      disabled=not supported, key=f"weight_{name}")
            if not supported:
                st.caption("Not used: no matched observations.")
    scored = apply_priority_weights(data, weights)
    with st.sidebar.expander("Filter source locations", expanded=False):
        view = sidebar_filters(scored, set(summary.get("infrastructure_sources", {})))
    st.sidebar.markdown(f"**{len(view)} of {len(scored)} source records**")
    st.sidebar.caption("Filters apply to profiles, insights and snapshots. Operator-site overlays retain the full NT extent.")
    if data.context_component.isna().all():
        denominator = sum(weights[name] for name in list(DEFAULT_WEIGHTS)[:3])
        if denominator:
            shares = [100 * weights[name] / denominator for name in list(DEFAULT_WEIGHTS)[:3]]
            st.sidebar.caption(f"Effective weights with all three inputs: coverage {shares[0]:g}% · distance {shares[1]:g}% · diversity {shares[2]:g}%. Context omitted.")
    return scored, sites, view, summary, weights


def setup_page(title, description):
    context = st.session_state.get("_dashboard_context")
    if context is None:
        context = prepare_dashboard()
    position = next((i + 1 for i, (_, label) in enumerate(PAGES) if title == label), 1)
    st.markdown(f'<header class="page-header"><div class="eyebrow">RemoteConnect NT / {position:02d}</div>'
                f'<h1>{escape(title)}</h1><p>{escape(description)}</p></header>', unsafe_allow_html=True)
    return context


def sidebar_filters(frame, available_providers):
    provider = st.selectbox("Operator within 50 km", ["All source locations", *sorted(available_providers)], key="filter_provider")
    coverage = st.selectbox("NT source coverage flag", ["All flags", "Macro cell", "Small cell", "Proximity to cell", "Multiple flags"], key="filter_coverage")
    band = st.selectbox("Experimental priority band", ["All bands", "Lower", "Moderate", "Higher", "Unscored"], key="filter_priority")
    technology = st.selectbox("Band at a site within 50 km", ["All records", "LTE listed", "No LTE listed", "NR listed", "No NR listed", "Not assessed"], key="filter_technology")
    return filter_records(frame, provider, coverage, band, technology)


def filter_records(frame, provider="All source locations", coverage="All flags", band="All bands", technology="All records"):
    """Apply source-location filters; combined flags match each constituent flag."""
    view = frame.copy()
    if provider != "All source locations":
        view = view.loc[pd.to_numeric(view[f"{provider.lower()}_sites_nearby"], errors="coerce").gt(0)]
    if coverage == "Multiple flags":
        view = view.loc[view.coverage_flag_count.gt(1)]
    elif coverage != "All flags":
        view = view.loc[view.coverage_type.str.contains(coverage, regex=False, na=False)]
    if band != "All bands":
        view = view.loc[view.priority_band.fillna("Unscored").eq(band)]
    if technology != "All records":
        column = "has_5g_nearby" if "NR" in technology else "has_4g_nearby"
        values = view[column].map(parse_boolean)
        mask = values.isna() if technology == "Not assessed" else values.eq(not technology.startswith("No ")).fillna(False)
        view = view.loc[mask]
    return view


def stats(items):
    st.markdown('<div class="stats">' + ''.join(
        f'<div class="stat"><strong>{escape(str(value))}</strong><span>{escape(label)}</span><small>{escape(detail)}</small></div>'
        for value, label, detail in items) + '</div>', unsafe_allow_html=True)


def chart(fig, height=330, key=None):
    fig.update_layout(template="plotly_white", height=height, font=dict(family="Arial, sans-serif", size=13, color=PALETTE["navy"]),
                      paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=16, r=20, t=25, b=30),
                      legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", title_text=""))
    fig.update_xaxes(gridcolor="#e8ece6", zeroline=False)
    fig.update_yaxes(gridcolor="#e8ece6", zeroline=False)
    st.plotly_chart(fig, width="stretch", theme=None, key=key, config={"displayModeBar": False, "scrollZoom": False})


def location_picker(view, label="Choose a source location"):
    if view.empty:
        st.info("No source locations match. Open ‘Filter source locations’ in the sidebar and widen the selection.")
        st.stop()
    options = view.sort_values(["community", "latitude"]).index.tolist()
    preferred = st.session_state.get("selected_record")
    index = options.index(preferred) if preferred in options else 0
    selected = st.selectbox(label, options, index=index,
                            format_func=lambda i: f"{view.loc[i, 'community'].title()} · {view.loc[i, 'coverage_type']}")
    st.session_state["selected_record"] = selected
    return view.loc[selected]


def source_footer():
    with st.expander("Sources, dates and limits"):
        st.markdown("[NT Government coverage list](https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt): **2022**, CC BY. "
                    "[ACCC operator-site release](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90): **31 January 2026 observations**, released September 2026, CC BY 2.5 AU. "
                    "[Natural Earth boundary](https://www.naturalearthdata.com/about/terms-of-use/): public domain.")
        st.caption("Files accessed 28 September 2026; publisher metadata checked 29 September 2026. These different observations are not a time series. "
                   "Distances use NT sites only; sites across the border and TPG access through the separate Optus–TPG MOCN file are excluded. "
                   "No local service measurements or community consultation are included. Full provenance: DATA_SOURCES.md; calculation rules: METHODOLOGY.md.")


def next_page(filename, label):
    st.page_link(f"pages/{filename}", label=label)


def money_or_distance(value, unit="km"):
    return "Not assessed" if pd.isna(value) else f"{float(value):,.1f} {unit}"


def map_figure(frame, sites=None, height=480):
    """Use a local Mercator projection on Cartesian axes; no remote topojson or tiles."""
    def northing(lat):
        return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))
    fig = go.Figure()
    boundary = json.loads((ROOT / "data/raw/nt_state_boundary.geojson").read_text(encoding="utf-8"))
    geometry = boundary["features"][0]["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    xs, ys = [], []
    for polygon in polygons:
        ring = polygon[0]
        xs.extend([p[0] for p in ring] + [None])
        ys.extend([float(northing(p[1])) for p in ring] + [None])
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor="#e9eee2",
                             line=dict(color="#92a394", width=1), hoverinfo="skip", showlegend=False))
    mapped = frame.dropna(subset=["latitude", "longitude"]).copy()
    for band, color in BAND_COLORS.items():
        rows = mapped.loc[mapped.priority_band.fillna("Unscored").eq(band)]
        if rows.empty:
            continue
        hover = [f"<b>{escape(row.community.title())}</b><br>NT 2022: {row.coverage_type}<br>Indicator: {money_or_distance(row.priority_score, '/100')}<br>Nearest NT site: {money_or_distance(row.nearest_mobile_site_km)}" for row in rows.itertuples()]
        fig.add_trace(go.Scatter(x=rows.longitude, y=northing(rows.latitude), mode="markers", name=band,
                                 marker=dict(size=10, color=color, line=dict(color="white", width=1)),
                                 text=hover, hovertemplate="%{text}<extra></extra>"))
    if sites is not None:
        for provider, rows in sites.groupby("provider"):
            fig.add_trace(go.Scatter(x=rows.longitude, y=northing(rows.latitude), mode="markers", name=f"{provider} sites",
                                     marker=dict(size=7, symbol="x", color=PROVIDER_COLORS[provider]),
                                     text=[f"{provider} · RFNSA {row.rfnsa_id}<br>ACCC 31 Jan 2026<br>LTE listed: {row.has_4g}<br>NR listed: {row.has_5g}" for row in rows.itertuples()],
                                     hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=15, b=10), showlegend=False,
                      plot_bgcolor="#f6f7f1", paper_bgcolor="#f6f7f1", dragmode="pan",
                      xaxis=dict(range=[128.5, 138.5], visible=False, constrain="domain"),
                      yaxis=dict(range=[float(northing(-26.5)), float(northing(-10.4))], visible=False, scaleanchor="x", scaleratio=1))
    return fig


def render_map(frame, sites=None, key="map", height=480):
    if frame.dropna(subset=["latitude", "longitude"]).empty:
        st.info("No mapped source locations match these filters.")
        return
    legend = ' '.join(f'<span style="color:{color};font-weight:700">●</span> {band} &nbsp;' for band, color in BAND_COLORS.items())
    st.markdown(f'<div style="font-size:.85rem">{legend}</div>', unsafe_allow_html=True)
    st.plotly_chart(map_figure(frame, sites, height), width="stretch", theme=None, key=key,
                    config={"displayModeBar": False, "scrollZoom": False})


def provider_distance_figure(frame):
    columns = {f"nearest_{p.lower()}_site_km": p for p in PROVIDER_COLORS}
    long = frame[["community", *columns]].rename(columns=columns).melt(id_vars="community", var_name="Provider", value_name="Distance (km)").dropna()
    long["Location"] = long.community.str.title()
    names = long.Location.drop_duplicates().tolist()
    # Small vertical offsets preserve co-located provider dots without changing distances.
    long["position"] = long.Location.map({name: i for i, name in enumerate(names)}) + long.Provider.map({"Telstra": -.18, "Optus": 0, "TPG": .18})
    fig = px.scatter(long, x="Distance (km)", y="position", color="Provider", symbol="Provider",
                     color_discrete_map=PROVIDER_COLORS,
                     hover_data={"community": False, "position": False, "Location": True, "Distance (km)": ":.1f"})
    fig.update_traces(marker_size=12)
    fig.update_yaxes(tickvals=list(range(len(names))), ticktext=names, title=None, range=[-.6, max(len(names)-.4, .6)])
    fig.update_xaxes(rangemode="tozero")
    return fig
