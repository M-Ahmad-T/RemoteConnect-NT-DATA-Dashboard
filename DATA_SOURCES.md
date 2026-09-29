# Data sources and provenance

Access date for downloaded source files: **2026-09-28**. The file register records the current source version known when this prototype was prepared; check publisher metadata again before reuse.

| Dataset | Publisher | URL | Year/version | Licence | Fields used | Status |
|---|---|---|---|---|---|---|
| Mobile Phone Coverage in Remote Areas of the NT | Northern Territory Government, Department of Corporate and Digital Development | [Dataset and XLSX](https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt) | 2022 workbook; source resource last modified 2022-07-04 | Creative Commons Attribution (CC BY), per catalogue | Site name, site type, population, macro cell, small cell, proximity to cell, provider, latitude, longitude | Downloaded as `data/raw/nt-mobile-coverage-2022.xlsx`; processed |
| Mobile Sites - Telstra | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/b508e517-a2d1-41aa-a8f4-3ec7e57e0cb3/download/mobile-sites-telstra-2026.csv) | 2026; resource modified 2026-09-21 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Mobile Sites - Optus | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/4eb2ff1e-0065-430f-9154-1f05daf993be/download/mobile-sites-optus-2026.csv) | 2026; resource modified 2026-09-20 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Mobile Sites - TPG | ACCC | [2026 CSV resource](https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90/resource/8597d7d7-31da-401f-bfbe-dc09b47a2474/download/mobile-sites-tpg-2026.csv) | 2026; resource modified 2026-09-21 | Creative Commons Attribution 2.5 Australia, per catalogue | MNO, RFNSA ID, latitude, longitude, LTE bands, NR bands, Co_funded, Co_contribution_program, Round | Downloaded; filtered to NT |
| Admin-1 state/province boundaries (NT polygon only) | Natural Earth | [Natural Earth vector source](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_1_states_provinces.geojson) | 1:10m admin-1; retrieved 2026-09-28 | Public domain, per Natural Earth | `iso_3166_2=AU-NT`, geometry | NT geometry extracted to `data/raw/nt_state_boundary.geojson`; auxiliary spatial filter, not community evidence |
| Australian Digital Inclusion Index - First Nations remote communities | ADII partnership: RMIT University, Swinburne University of Technology and Telstra; 2025 report citation shown on dashboard | [Remote communities dashboard](https://dashboard.digitalinclusionindex.org.au/FirstNations/Remote/) | 2025 citation on source dashboard | Dashboard states CC BY-NC-SA 4.0 for report/data (terms dated 2023-07-18); confirm current terms and citation at use | Access, Affordability, Digital Ability, ADII score, published geography and source citation | **Not downloaded**; only supplied if a defensible geography-specific extract is obtained |
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
