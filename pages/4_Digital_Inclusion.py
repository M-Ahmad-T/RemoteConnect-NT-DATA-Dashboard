import pandas as pd
import streamlit as st

from src.dashboard import ROOT, next_page, setup_page, source_footer

_, _, view, summary, _ = setup_page("Digital inclusion", "A nearby mobile site cannot tell us whether people can afford or use a service.")
path = ROOT / "data/raw/digital_inclusion_optional.csv"
source = pd.read_csv(path) if path.exists() else pd.DataFrame()
st.subheader("What this dataset cannot answer")
for title, question in [("Access", "Are suitable devices and reliable connections within reach?"),
                        ("Affordability", "Can people meet their needs without giving up other essentials?"),
                        ("Digital ability", "Do people have the skills and support to do what matters to them online?")]:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.write(question)

if source.empty:
    st.markdown('<div class="note"><b>No matched digital inclusion observations.</b><br>The ADII file contains no observations in this version. '
                'The indicator uses coverage, distance and provider records only; its context control is disabled.</div>', unsafe_allow_html=True)
    st.subheader("Why we leave a gap here")
    st.write("An average for a region describes the people surveyed in that region. It is not a result for every location inside it. "
             "We need an observation published for the same community, with its year and citation, before attaching it to a profile.")
else:
    st.subheader("Supplied observations at their published geography")
    st.caption("This table shows the full context source, independent of location filters. Regional and national values are never assigned to profiles.")
    st.dataframe(source, hide_index=True, width="stretch")
    st.caption(f"Matched community observations in the prepared data: {summary.get('digital_inclusion_records_matched', 0)}.")

st.link_button("Open the ADII remote communities dashboard", "https://dashboard.digitalinclusionindex.org.au/FirstNations/Remote/")
st.caption("The source offers 2022 and 2024 observations and requests the 2025 ADII report citation. No numerical ADII results are reproduced here.")
with st.expander("ADII attribution"):
    st.write("Thomas, J., McCosker, A., Parkinson, S., Hegarty, K., Featherstone, D., Kennedy, J., Ormond-Parker, L., Morrison, K., Rea, H., & Ganley, L. "
             "Measuring Australia’s Digital Divide: 2025 Australian Digital Inclusion Index. Melbourne: ARC Centre of Excellence for Automated Decision-Making and Society, "
             "RMIT University, Swinburne University of Technology, and Telstra.")
    st.caption("Dashboard text/data: CC BY-NC-SA 4.0; accessed 29 September 2026. Opinions in this prototype are its authors’ own. ABS Census context is also not joined.")
next_page("5_Data_Insights.py", "Explore what the available records do show →")
source_footer()
