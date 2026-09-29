from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard import ROOT, setup_page

setup_page(
    "Digital inclusion",
    "Connectivity is one part of inclusion—not a proxy for affordability, access or ability.",
)

st.markdown(
    """
    The Australian Digital Inclusion Index (ADII) describes **Access, Affordability and Digital Ability**.
    Use each statistic only at the geography published by the source. An NT-wide, regional or other
    aggregate value must not be copied onto a community profile or interpreted as an individual's ability.
    """
)
source_path = ROOT / "data" / "raw" / "digital_inclusion_optional.csv"
source = pd.read_csv(source_path) if source_path.exists() else None
if source is None:
    st.warning("Optional ADII source file is missing. See data/raw/ADII_FILE_INSTRUCTION.txt.")
elif source.empty:
    st.info(
        "No ADII statistics have been supplied with this workspace. The dashboard does not estimate or "
        "fabricate values. Add sourced rows to data/raw/digital_inclusion_optional.csv and preserve the "
        "source geography and citation."
    )
else:
    required = {"geography_level", "geography_name"}
    if not required.issubset(source.columns):
        st.error("The ADII file must include geography_level and geography_name columns.")
    else:
        source["geography_level"] = source["geography_level"].astype(str)
        st.subheader("Supplied source records by published geography")
        levels = sorted(source["geography_level"].dropna().unique())
        for level in levels:
            rows = source.loc[source["geography_level"].eq(level)]
            st.markdown(f"**{level}** — {len(rows)} source record(s)")
            st.dataframe(rows, width="stretch", hide_index=True)

        metrics = [
            column
            for column in ("adii_score", "access", "affordability", "digital_ability")
            if column in source.columns
        ]
        if metrics:
            chart_data = source.melt(
                id_vars=["geography_level", "geography_name"],
                value_vars=metrics,
                var_name="Dimension",
                value_name="Source value",
            )
            chart_data["Source value"] = pd.to_numeric(chart_data["Source value"], errors="coerce")
            chart_data = chart_data.dropna(subset=["Source value"])
            if not chart_data.empty:
                chart_data["Geography"] = (
                    chart_data["geography_name"].astype(str)
                    + " · "
                    + chart_data["geography_level"].astype(str)
                )
                st.plotly_chart(
                    px.bar(
                        chart_data,
                        x="Geography",
                        y="Source value",
                        color="Dimension",
                        barmode="group",
                        hover_data=["geography_level", "geography_name"],
                    ),
                    width="stretch",
                )
        st.caption(
            "Values and geography labels are shown as supplied; no regional or national value is "
            "downscaled to individual communities."
        )
st.code("data/raw/ADII_FILE_INSTRUCTION.txt", language=None)
st.caption("ABS 2021 NT Indigenous Location (ILOC) population data are also not supplied; see data/raw/ABS_2021_ILOC_FILE_INSTRUCTION.txt.")

st.subheader("Geography and interpretation")
st.markdown(
    """
    - **Community-level:** only a source record explicitly published at that community geography may be linked to a community profile.
    - **Regional:** retain the named region and show it separately; do not distribute the value across communities within it.
    - **NT-level:** describe it as an NT-level statistic.
    - **National:** describe it as a national statistic.

    Source: [Australian Digital Inclusion Index — First Nations, remote communities](https://dashboard.digitalinclusionindex.org.au/FirstNations/Remote/).
    The dashboard states CC BY-NC-SA 4.0 terms for its report/data and requests the 2025 ADII citation; verify the current source terms and citation when exporting data.
    """
)
