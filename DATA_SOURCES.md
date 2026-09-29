# Data sources and provenance

Access date for downloaded source files: **2026-09-28**. The file register records the current source version known when this prototype was prepared; check publisher metadata again before reuse.

**Publisher verification: 2026-09-29.** The three ACCC download URLs, resource modification timestamps and dataset licence below were checked using the publisher's [catalogue API](https://data.gov.au/data/api/3/action/package_show?id=4b472a18-d0fa-409c-994a-ab17162bcb90). The normal catalogue pages returned HTTP 403 to the web reader; the API was accessible. This verifies the registered resources, not a byte-for-byte comparison of local downloads. Keep the original access date distinct from this metadata check.

The [ACCC 2026 report](https://www.accc.gov.au/system/files/mobile-infrastructure-report-2026.pdf), background section, dates the site observations to **31 January 2026**. The [publication page](https://www.accc.gov.au/by-industry/telecommunications-and-internet/mobile-services-regulation/mobile-infrastructure-report/mobile-infrastructure-report-2026/download-report) is dated **22 September 2026**. Neither the report publication date nor CSV modification date is a current service observation. The NT catalogue's 2022 workbook has no per-record measurement dates. The two datasets do not constitute a comparable time series.

| Dataset | Publisher | URL | Year/version | Licence | Fields used | Status |
|---|---|---|---|---|---|---|
| Mobile Phone Coverage in Remote Areas of the NT | Northern Territory Government, Department of Corporate and Digital Development | [Dataset and XLSX](https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt) | 2022 workbook; source resource last modified 2022-07-04 | Creative Commons Attribution (CC BY), per catalogue | Site name, site type, population, macro cell, small cell, proximity to cell, provider, latitude, longitude | Downloaded as `data/raw/nt-mobile-coverage-2022.xlsx`; processed |
| Mobile Sites - Telstra | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/b508e517-a2d1-41aa-a8f4-3ec7e57e0cb3/download/mobile-sites-telstra-2026.csv) | 2026; resource modified 2026-09-21 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Mobile Sites - Optus | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/4eb2ff1e-0065-430f-9154-1f05daf993be/download/mobile-sites-optus-2026.csv) | 2026; resource modified 2026-09-20 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Mobile Sites - TPG | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/8597d7d7-31da-401f-bfbe-dc09b47a2474/download/mobile-sites-tpg-2026.csv) | 2026; resource modified 2026-09-21 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Admin-1 state/province boundaries (NT polygon only) | Natural Earth | [Natural Earth vector source](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_1_states_provinces.geojson) | 1:10m admin-1; retrieved 2026-09-28 | Public domain, per Natural Earth | `iso_3166_2=AU-NT`, geometry | NT geometry extracted to `data/raw/nt_state_boundary.geojson`; auxiliary spatial filter, not community evidence |
| Australian Digital Inclusion Index - First Nations remote communities | ADII partnership: RMIT University, Swinburne University of Technology and Telstra; 2025 report citation shown on dashboard | [Remote communities dashboard](https://dashboard.digitalinclusionindex.org.au/FirstNations/Remote/) | 2022 and 2024 observation options; 2025 report citation | CC BY-NC-SA 4.0 for text/data, excluding logos (terms dated 2023-07-18), verified 2026-09-29 | Access, Affordability, Digital Ability, ADII score, published geography and source citation | **No observations downloaded**; only supplied if a defensible geography-specific extract is obtained |
| 2021 Census DataPacks - NT Indigenous Location (ILOC) | Australian Bureau of Statistics | [Census DataPacks](https://www.abs.gov.au/census/find-census-data/datapacks) | 2021 Census | ABS conditions/licence apply; verify product terms on download | Selected ILOC code/name and supported population/context fields | **Not downloaded**; optional template only |

## Supplied raw files

- `data/raw/nt-mobile-coverage-2022.xlsx`
- `data/raw/mobile-sites-telstra-2026.csv`
- `data/raw/mobile-sites-optus-2026.csv`
- `data/raw/mobile-sites-tpg-2026.csv`
- `data/raw/nt_state_boundary.geojson`

## Outstanding sources

- An ADII extract containing its published geography level/name, Access, Affordability, Digital Ability, overall score, year and citation. Do not attach region, NT or national statistics to individual communities.
- ABS 2021 ILOC extract with official ILOC geography identifiers and only the required population/context fields. Name-based matching alone is not accepted as a reliable community crosswalk.

No community-level ADII values or ABS values are included in the processed dataset until those source files are supplied and defensibly matched.

## ACCC verification details and scope

Resource timestamps as returned by the catalogue (retained without inferring a local timezone):

- Telstra: `2026-09-21T00:00:11.056479`.
- Optus: `2026-09-20T23:52:25.035905`.
- TPG: `2026-09-21T00:00:56.026041`.

Local CSV headers contain `Year`, `MNO`, `RFNSA ID`, latitude/longitude, LTE/NR band fields and co-funding fields. The Optus file also retains active-sharing fields. Band suffixes are spectrum frequencies in MHz; a positive value means a band is listed at the operator site, not at the matched source location. Original fields are retained in the processed infrastructure CSV.

The publisher also registers [Optus–TPG MOCN mobile sites 2026](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/59283aa5-76d9-4e82-8d13-6892034a8def/download/mobile-sites-optus-tpg-mocn-2026.csv), modified `2026-09-21T00:01:51.312022`. **It is not included in this prototype.** TPG's own site list does not describe all infrastructure it may access through sharing. Provider-distance charts and diversity indicators must not be read as retail coverage/choice comparisons. The API identifies [interpretation guide v6](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/769c78a5-14c4-4742-9844-78a38aad7825/download/accc-mobile-infrastructure-report-data-release-data-interpretation-guide-v6.pdf); its PDF contents were not fetched during this review.

Natural Earth's [terms of use](https://www.naturalearthdata.com/about/terms-of-use/) confirm public-domain boundaries. The low-resolution admin boundary is an auxiliary spatial filter, not a legal boundary survey; border-site inclusion depends on its geometry. Sites outside that polygon are not distance candidates.

## ADII attribution

Thomas, J., McCosker, A., Parkinson, S., Hegarty, K., Featherstone, D., Kennedy, J., Ormond-Parker, L., Morrison, K., Rea, H., & Ganley, L. *Measuring Australia's Digital Divide: 2025 Australian Digital Inclusion Index*. Melbourne: ARC Centre of Excellence for Automated Decision-Making and Society, RMIT University, Swinburne University of Technology, and Telstra.

This is the citation requested by the publisher dashboard when checked on 29 September 2026. No ADII numerical observations are reproduced. Regional, NT-wide or national values cannot be assigned to individual community profiles. The source's research partnerships are not community consultation conducted by this project.

## Where attribution appears

- Every app page: “Sources, dates and limits” links to NT Government, ACCC and Natural Earth.
- Digital Inclusion: ADII link, years, licence and full attribution.
- Saved location text: source URLs, years, licences, effective weights and scope limitations.
- CSV snapshots: source URLs, observation dates, original source-file fields, original coverage flags, effective weights and limitations.
- This register and `data_sources.csv`: publisher and resource details; `METHODOLOGY.md`: derivations and limitations.
