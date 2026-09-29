RemoteConnect NT raw-data instructions
======================================

Already supplied in this folder:
- nt-mobile-coverage-2022.xlsx
  NT Government, Mobile Phone Coverage in Remote Areas of the NT 2022.
- mobile-sites-telstra-2026.csv
- mobile-sites-optus-2026.csv
- mobile-sites-tpg-2026.csv
  Latest ACCC Mobile Infrastructure Report site CSVs available when accessed
  (2026 release, 28 September 2026).
- nt_state_boundary.geojson
  The AU-NT admin-1 polygon extracted from the Natural Earth 1:10m admin-1
  states/provinces source; used only to filter national ACCC site points.

If replacing a source:
1. Download the NT Government XLSX from:
   https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt
   Save it with "coverage" in its .xlsx filename.
2. Download the newest appropriate "Mobile Sites - Telstra", "Mobile Sites -
   Optus" and "Mobile Sites - TPG" CSVs from:
   https://data.gov.au/data/dataset/4b472a18-d0fa-409c-994a-ab17162bcb90
   Name them mobile-sites-telstra-YYYY.csv, mobile-sites-optus-YYYY.csv and
   mobile-sites-tpg-YYYY.csv. The pipeline automatically selects the newest
   year available for each operator and spatially filters to NT.
3. Keep the NT boundary at nt_state_boundary.geojson. If you replace it, use
   a WGS84/EPSG:4326 polygon containing only the NT and record its provenance.

Optional digital inclusion file:
- digital_inclusion_optional.csv is a HEADER-ONLY TEMPLATE, not data.
- ADII_FILE_INSTRUCTION.txt gives the exact source/export fields required.
- Obtain real ADII values from the First Nations remote communities dashboard:
  https://dashboard.digitalinclusionindex.org.au/FirstNations/Remote/
- Include the source-published geography_level and geography_name, ADII score,
  Access, Affordability, Digital Ability, year and source citation.
- Only exact, unique rows with geography_level="community" can join a
  community profile. Regional, NT-wide and national records remain separate.
- Verify the source licence and citation before redistribution.

Optional ABS file:
- abs_2021_iloc_optional.csv is a HEADER-ONLY TEMPLATE, not data.
- ABS_2021_ILOC_FILE_INSTRUCTION.txt identifies the ABS geography/table to select.
- Download the appropriate 2021 Census DataPack at NT Indigenous Location
  (ILOC) geography from:
  https://www.abs.gov.au/census/find-census-data/datapacks
- Populate only real source values and a community field reviewed through an
  explicit, documented geography crosswalk. Include ILOC code/name and
  match_method. Do not join records on an approximate name match.

If a required input is absent, python src/prepare_data.py reports the exact
missing source file. No synthetic/demo records are used.
