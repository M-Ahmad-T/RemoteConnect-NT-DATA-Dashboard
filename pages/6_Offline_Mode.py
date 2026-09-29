import streamlit as st
from src.dashboard import location_picker, setup_page, source_footer
from src.exports import profile_report, snapshot_csv

_, _, view, summary, _ = setup_page("Save snapshots", "Keep a small evidence file for a low-connectivity visit or a later conversation.")
st.caption("Saved CSV and text files open without the dashboard. The interactive app still needs a running Streamlit server; it does not cache or synchronise on your device.")
row = location_picker(view, "Location to save")
report = profile_report(row, summary)
slug = row.community_key.replace(" ", "-")
with st.container(border=True):
    st.subheader("One location, with its evidence")
    st.write(f"{row.community.title()} · source flags, provider distances, listed bands, score weights and the next checks.")
    st.download_button("Save readable location snapshot", report.encode("utf-8"), f"remoteconnect-{slug}.txt", "text/plain", type="primary")
    st.download_button("Save location CSV", snapshot_csv(row.to_frame().T), f"remoteconnect-{slug}.csv", "text/csv")
with st.container(border=True):
    st.subheader(f"Your filtered set · {len(view)} records")
    st.write("Includes the current indicator and effective weights for each record. Source URLs, dates and limitations travel with the data.")
    st.download_button("Save filtered CSV", snapshot_csv(view), "remoteconnect-nt-filtered-snapshot.csv", "text/csv")
with st.expander("Preview the readable snapshot"):
    st.text(report)
source_footer()
