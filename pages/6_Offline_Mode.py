from datetime import date

import pandas as pd
import streamlit as st

from src.dashboard import setup_page

all_rows, _, view, summary, _ = setup_page(
    "Offline mode",
    "Take a small, source-labelled community snapshot with you.",
)

st.markdown(
    """
    **This prototype provides downloadable snapshots; it is not a fully offline Streamlit application.**
    A production implementation could cache community profiles locally, operate without continuous
    internet access, and synchronise when connectivity becomes available. The plotted boundary and data
    points are local, although this prototype does not implement offline caching or synchronisation.
    """
)

if all_rows.empty:
    st.info("No community profiles are available to export.")
    st.stop()

profile = all_rows.sort_values("community").copy()
profile["selection"] = profile.apply(
    lambda row: f"{row['community']} — {row['latitude']:.4f}, {row['longitude']:.4f}"
    if pd.notna(row["latitude"]) and pd.notna(row["longitude"])
    else str(row["community"]),
    axis=1,
)
selected = st.selectbox("Community profile for export", profile["selection"].tolist())
record = profile.loc[profile["selection"].eq(selected)].iloc[0]
profile_csv = record.drop(labels="selection").to_frame().T.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download community profile CSV",
    data=profile_csv,
    file_name=f"remoteconnect-{record['community_key'].replace(' ', '-')}-profile.csv",
    mime="text/csv",
)

filtered_csv = view.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered dataset CSV",
    data=filtered_csv,
    file_name="remoteconnect-nt-filtered-snapshot.csv",
    mime="text/csv",
    disabled=view.empty,
)
if view.empty:
    st.caption("The filtered dataset is empty; adjust the sidebar filters to enable this download.")

def report_value(value: object) -> str:
    if pd.isna(value):
        return "Not available in supplied source data"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


report = f"""RemoteConnect NT — lightweight community profile
Generated: {date.today().isoformat()}

Location: {record['community']}
Coordinates (source): {report_value(record['latitude'])}, {report_value(record['longitude'])}
Coverage type (NT Government 2022): {report_value(record['coverage_type'])}
Population (NT Government source field): {report_value(record.get('population'))}
Nearest ACCC-listed mobile site: {report_value(record.get('nearest_mobile_site_km'))} km
Nearest Telstra site: {report_value(record.get('nearest_telstra_site_km'))} km
Nearest Optus site: {report_value(record.get('nearest_optus_site_km'))} km
Nearest TPG site: {report_value(record.get('nearest_tpg_site_km'))} km
Operator-site records within 50 km: {report_value(record.get('sites_within_50km'))}
4G band present within 50 km: {report_value(record.get('has_4g_nearby'))}
5G band present within 50 km: {report_value(record.get('has_5g_nearby'))}
Experimental priority indicator: {report_value(record.get('priority_score'))}/100
Priority explanation: {report_value(record.get('priority_explanation'))}

Source files: {summary.get('community_source', 'Not recorded')}; {', '.join(summary.get('infrastructure_sources', {}).values()) or 'No ACCC source files recorded'}.
This report is a prototype decision-support snapshot, not a service guarantee or investment decision.
Tower proximity does not guarantee coverage or service quality.
"""
st.download_button(
    "Download lightweight community report",
    data=report.encode("utf-8"),
    file_name=f"remoteconnect-{record['community_key'].replace(' ', '-')}-report.txt",
    mime="text/plain",
)

st.subheader("Selected profile preview")
preview = record.drop(labels="selection").map(report_value).to_frame("Value")
st.dataframe(preview, width="stretch")
st.caption("The files above are exports from locally prepared data. They do not implement offline app caching or synchronisation.")
