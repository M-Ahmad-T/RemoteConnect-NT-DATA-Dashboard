import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import PALETTE, chart, next_page, provider_distance_figure, setup_page, source_footer
from src.priority import DEFAULT_WEIGHTS, apply_priority_weights

all_rows, sites, view, _, _ = setup_page("Data insights", "Three ways to read the evidence: source flags, infrastructure distance and scoring assumptions.")
if view.empty:
    st.info("No source locations match the sidebar filters.")
    st.stop()
st.caption(f"All three comparisons use the same {len(view)} filtered source records, out of {len(all_rows)}. Weights change the indicator, not the source observations.")

st.subheader("01 / Coverage descriptions overlap")
mix = view.coverage_type.where(view.coverage_flag_count.le(1), "Multiple flags").value_counts()
colors = {"Macro cell":"#267567", "Small cell":"#a87520", "Proximity to cell":"#a64b2a", "Multiple flags":"#795394", "Not specified":"#65716f"}
fig = go.Figure()
for label, color in colors.items():
    count = int(mix.get(label, 0))
    if count:
        fig.add_bar(name=label, x=[100 * count / len(view)], y=["Source mix"], orientation="h", marker_color=color,
                    customdata=[[count, len(view)]], hovertemplate=f"{label}<br>%{{customdata[0]}} of %{{customdata[1]}} records (%{{x:.1f}}%)<extra></extra>")
fig.update_layout(barmode="stack", showlegend=False)
fig.update_xaxes(range=[0,100], title="Share of filtered source records (%)", ticksuffix="%")
fig.update_yaxes(visible=False)
chart(fig, 160)
st.markdown(" · ".join(f"**{label}: {int(mix.get(label, 0))}**" for label in colors if mix.get(label, 0)))
multiple = int(view.coverage_flag_count.gt(1).sum())
st.caption(f"{multiple} records have multiple YES flags. They are grouped once in this composition; every original flag remains in profiles and exports. These categories describe the 2022 source, not current quality.")

st.subheader("02 / Nearby infrastructure differs by operator")
default = view.nlargest(5, "nearest_mobile_site_km").index.tolist()
selected = st.multiselect("Compare up to six locations", view.sort_values("community").index.tolist(), default=default,
                         max_selections=6, format_func=lambda i: view.loc[i, "community"].title())
if selected:
    subset = view.loc[selected]
    chart(provider_distance_figure(subset), height=max(260, 50 * len(subset) + 100))
    median = subset.nearest_mobile_site_km.median()
    st.caption(f"Across these {len(subset)} locations, median distance to the nearest listed NT site is {median:.1f} km. Initial selection: the five greatest nearest-site distances in this view.")
else:
    st.info("Choose a location to compare its provider distances.")
st.caption("TPG distances exclude access through the separate Optus–TPG shared network. Provider proximity is not a count of retail services available locally.")

st.subheader("03 / Does changing the weights change the result?")
baseline = apply_priority_weights(all_rows, DEFAULT_WEIGHTS).loc[view.index]
comparison = pd.DataFrame({"Location":view.community.str.title(), "Default indicator":baseline.priority_score,
                           "Current indicator":view.priority_score})
valid = comparison.dropna()
if valid.empty:
    st.info("No scores are supported by the current weights. Give at least one available input a positive weight.")
else:
    figure = px.scatter(valid, x="Default indicator", y="Current indicator", hover_name="Location",
                        range_x=[0,100], range_y=[0,100], color_discrete_sequence=[PALETTE["teal"]])
    figure.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="#7b827c", dash="dot"))
    figure.update_traces(marker=dict(size=9, opacity=.75), hovertemplate="%{hovertext}<br>Default: %{x:.1f}/100<br>Current: %{y:.1f}/100<extra></extra>")
    figure.update_xaxes(title="Default weights · indicator /100")
    figure.update_yaxes(title="Current weights · indicator /100")
    chart(figure, 340)
    changed = int((valid["Default indicator"] - valid["Current indicator"]).abs().gt(.05).sum())
    delta = (valid["Default indicator"] - valid["Current indicator"]).abs().max()
    st.caption(f"{changed} of {len(valid)} scored records change; largest absolute change: {delta:.1f} points. Dots on the dashed line are unchanged. Use ‘Adjust the indicator’ in the sidebar.")
    st.caption("Both scores use these same records. Priority-band filters use the current score. This compares assumptions, not change over time.")

with st.expander("Full NT infrastructure context — unaffected by location filters"):
    counts = sites.groupby("provider").agg(**{"Operator-site records": ("provider", "size"), "LTE band listed": ("has_4g", "sum"), "NR band listed": ("has_5g", "sum")}).reset_index()
    st.dataframe(counts.rename(columns={"provider":"Operator"}), hide_index=True, width="stretch")
    st.caption(f"{len(sites)} records across the entire NT boundary. A site can host several operator records; LTE and NR counts overlap.")
next_page("6_Offline_Mode.py", "Save the filtered evidence →")
source_footer()
