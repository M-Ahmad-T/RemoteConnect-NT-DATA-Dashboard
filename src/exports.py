"""Small, source-labelled snapshots; no Streamlit dependency."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

NT_URL = "https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt"
ACCC_URL = "https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90"


def report_value(value):
    if pd.isna(value):
        return "Not assessed"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def snapshot_csv(frame):
    out = frame.copy()
    out["snapshot_generated_darwin"] = datetime.now(ZoneInfo("Australia/Darwin")).isoformat(timespec="seconds")
    out["nt_source_url"] = NT_URL
    out["accc_source_url"] = ACCC_URL
    out["nt_source_year"] = 2022
    out["accc_observation_date"] = "2026-01-31"
    out["source_files_accessed"] = "2026-09-28"
    out["nt_source_licence"] = "Creative Commons Attribution (catalogue)"
    out["accc_source_licence"] = "Creative Commons Attribution 2.5 Australia"
    out["site_count_definition"] = "Distinct RFNSA ID + coordinates rounded to 5 decimal places; not a verified tower count"
    out["limitation"] = "Site proximity and listed bands do not establish local service. TPG shared-network access is not counted."
    return out.to_csv(index=False).encode("utf-8-sig")


def profile_report(record, summary):
    lines = ["RemoteConnect NT | location snapshot",
             f"Generated (Darwin): {datetime.now(ZoneInfo('Australia/Darwin')).isoformat(timespec='seconds')}", ""]
    fields = {
        "Location": "community", "Latitude": "latitude", "Longitude": "longitude",
        "All NT source coverage flags (2022)": "coverage_type",
        "Derived score basis": "coverage_score_basis",
        "Population (NT source field; reference year unspecified)": "population",
        "Nearest NT-listed site (km)": "nearest_mobile_site_km",
        "Nearest Telstra site (km)": "nearest_telstra_site_km",
        "Nearest Optus site (km)": "nearest_optus_site_km",
        "Nearest TPG own-network site (km)": "nearest_tpg_site_km",
        "Distinct mapped site keys within 50 km (RFNSA + rounded coordinates)": "sites_within_50km",
        "Telstra operator-site records within 50 km": "telstra_sites_nearby",
        "Optus operator-site records within 50 km": "optus_sites_nearby",
        "TPG operator-site records within 50 km": "tpg_sites_nearby",
        "LTE band listed at a site within 50 km": "has_4g_nearby",
        "NR band listed at a site within 50 km": "has_5g_nearby",
        "Experimental indicator (0-100)": "priority_score",
        "Effective weights and inputs": "priority_explanation",
    }
    for label, column in fields.items():
        value = record.get(column)
        formatted = f"{float(value):.5f}" if column in {"latitude", "longitude"} and pd.notna(value) else report_value(value)
        lines.append(f"{label}: {formatted}")
    lines += ["", "Verify next: check current provider maps, device/band compatibility and local service with permission.",
              "The 2022 source lists covered locations, not confirmed black spots. No community consultation is claimed.",
              "Distances use NT-filtered sites only; cross-border sites and TPG MOCN access are not included.",
              "Nearby sites and listed bands do not prove current service, reliability or affordability.", "",
              f"NT Government (2022; CC BY): {NT_URL}",
              f"ACCC (31 January 2026 observations; CC BY 2.5 AU): {ACCC_URL}",
              "Natural Earth boundary: public domain; https://www.naturalearthdata.com/about/terms-of-use/",
              "Source files accessed 2026-09-28; publisher metadata checked 2026-09-29.",
              f"Source files: {summary.get('community_source')}; {', '.join(summary.get('infrastructure_sources', {}).values())}"]
    return "\n".join(lines)
