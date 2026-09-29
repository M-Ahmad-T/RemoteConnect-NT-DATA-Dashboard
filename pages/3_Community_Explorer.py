import re

import pandas as pd
import streamlit as st

from src.dashboard import chart, location_picker, money_or_distance, next_page, provider_distance_figure, setup_page, source_footer, stats
from src.prepare_data import haversine_distances_km, parse_flag
from src.priority import COMPONENT_COLUMNS

_, sites, view, _, weights = setup_page("Community explorer", "Read one location’s evidence, then decide what needs checking.")
row = location_picker(view)
st.subheader(row.community.title())
st.caption(f"{row.site_type} · NT source coordinates {row.latitude:.4f}, {row.longitude:.4f} · all figures below refer to this selected record")
stats([(money_or_distance(row.priority_score, "/100"), "Experimental indicator", str(row.priority_band) if pd.notna(row.priority_band) else "Unscored"),
       (money_or_distance(row.nearest_mobile_site_km), "Nearest NT site", "straight-line distance"),
       (str(int(row.sites_within_50km)) if pd.notna(row.sites_within_50km) else "—", "Mapped site keys", "within 50 km")])
st.markdown(f"**2022 source flags:** {row.coverage_type}. "
            f"**Score basis:** {row.coverage_score_basis} (least limiting listed type).")
st.caption(f"Population in the NT source: {int(row.population):,}. This is the workbook value, not a current estimate." if pd.notna(row.population) else "Population is not supplied for this location.")

st.subheader("How far is each operator’s infrastructure?")
chart(provider_distance_figure(row.to_frame().T), height=240)
st.caption("Distances use NT-listed sites only. TPG means its own listed network; shared access through Optus is excluded. Distance is not a service test.")

with st.expander("Listed bands and nearby site records", expanded=True):
    if pd.notna(row.latitude) and pd.notna(row.longitude) and not sites.empty:
        distances = haversine_distances_km(row.latitude, row.longitude, sites)
        nearby = sites.loc[distances <= 50].copy()
        nearby["Distance (km)"] = distances[distances <= 50].round(2)
        band_columns = [c for c in sites if re.fullmatch(r"(?:lte|nr)\d+", c)]
        nearby["Listed bands (MHz)"] = nearby.apply(lambda r: ", ".join(c.upper() for c in band_columns if parse_flag(r[c])) or "None listed", axis=1)
        if nearby.empty:
            st.info("No operator-site records fall within 50 km in the supplied NT files.")
        else:
            st.dataframe(nearby.sort_values("Distance (km)")[["provider", "rfnsa_id", "Distance (km)", "Listed bands (MHz)"]].rename(
                columns={"provider":"Operator", "rfnsa_id":"RFNSA ID"}), hide_index=True, width="stretch")
        st.caption("LTE = 4G; NR = 5G. These are bands listed at sites, not bands confirmed at this location. Multiple operators can share a mapped site key.")
    else:
        st.info("Site matching is not assessed without source coordinates and infrastructure records.")

st.subheader("What makes up the indicator?")
st.markdown("**Effective shares:** " + " · ".join(f"{name.split(' / ')[0]} {row[f'{column}_weight_pct']:.2f}%" for name, column in COMPONENT_COLUMNS.items()))
components = pd.DataFrame([{"Input": name.capitalize(), "Input /100": row[column],
                            "Effective weight %": row[f"{column}_weight_pct"],
                            "Points contributed": row[f"{column}_contribution"]}
                           for name, column in COMPONENT_COLUMNS.items()])
st.dataframe(components.round(2), hide_index=True, width="stretch")
st.caption("Missing inputs contribute no invented value. Remaining positive weights sum to 100%. Coverage proxy values and the 50 km radius are design assumptions.")
if pd.isna(row.context_component):
    st.info("No usable ADII/remoteness observation contributes to this location’s score.")
else:
    st.caption(f"Context source: {row.get('adii_source_note', 'source-supplied remoteness')} · year: {row.get('adii_year', 'not recorded')}")

st.subheader("What to verify next")
st.markdown("1. Check the current provider coverage map for this exact location and device.\n"
            "2. With permission, ask local users about indoor service, busy periods, outages and cost. No consultation has yet been undertaken for this prototype.\n"
            "3. Record the date and conditions of any service test before proposing infrastructure changes.")
next_page("6_Offline_Mode.py", "Save this location’s evidence for later →")
source_footer()
