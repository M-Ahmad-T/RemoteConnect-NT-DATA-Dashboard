# Methodology

## Purpose and scope

RemoteConnect NT combines the Northern Territory Government's 2022 remote mobile coverage list with ACCC operator-site data released in 2026. It presents a transparent prototype decision-support indicator, not an official government priority ranking, service-quality prediction or investment decision.

The core NT source lists locations **with** mobile coverage outside named main centres. It does not enumerate every remote community, nor does it provide a comparable measurement of coverage quality. Counts are therefore described as source locations/records where appropriate, not as a complete census of NT communities.

## Input files

Required inputs:

- `data/raw/nt-mobile-coverage-2022.xlsx`
- `data/raw/mobile-sites-telstra-2026.csv`
- `data/raw/mobile-sites-optus-2026.csv`
- `data/raw/mobile-sites-tpg-2026.csv`
- `data/raw/nt_state_boundary.geojson`

The NT boundary polygon is an auxiliary Natural Earth admin-1 geography used to spatially select ACCC records in the Northern Territory. Its provenance is recorded in [DATA_SOURCES.md](DATA_SOURCES.md). The optional ADII and ABS templates are not evidence and contain no fabricated observations.

## Cleaning and validation

1. Read the workbook sheet containing `SITE NAME`, scanning the first rows because the official worksheet includes a description above the table header.
2. Standardise field names to lowercase snake case and trim community/location names and provider labels.
3. Parse source population and coordinates as numeric. Retain non-empty named rows. Invalid coordinates are set to missing; retain those records for inspection but omit them from maps and distance matching. Do not impute coordinates or population.
4. Preserve the original `macro_cell`, `small_cell` and `proximity_to_cell` fields, including blanks. `coverage_type` lists every positive flag; `coverage_flag_count` counts them. Remove duplicate coverage rows using normalized name, coordinates, combined coverage flags and provider. Distinct coordinates or provider/coverage observations remain distinct source records.
5. Load each provider's newest available `mobile-sites-{provider}-{year}.csv` file. Parse all LTE and NR band columns from the ACCC field names; any populated band means that technology is listed at that site.
6. Drop operator records with invalid coordinates. Filter national site records to the NT by spatially intersecting WGS84 point geometries with the supplied NT boundary polygon. No rough bounding box is used.
7. Retain source RFNSA IDs, coordinates, provider and band/co-funding fields in the processed infrastructure output. Missing source values remain missing.
8. Optional ADII rows can join to a community profile only when `geography_level` is `community` (case-insensitive) and the normalized source geography name matches uniquely on both sides. Repeated target names and repeated context names are excluded. This is a minimum technical safeguard, not proof of geographic equivalence: source geography/year/citation must be reviewed before adding data. Regional, NT-wide and national rows remain context records. Optional ABS values require a documented geography crosswalk. Neither optional template currently contains observations.

## Geographic matching and distances

Community coordinates come directly from the NT Government source list. They represent listed source locations, not newly geocoded community centroids.

For each source location, the pipeline compares its coordinates with every NT-filtered ACCC operator record using the Haversine great-circle formula and mean Earth radius **6,371.0088 km**. The calculations produce:

- nearest overall, Telstra, Optus and TPG site distances;
- unique mapped RFNSA/location counts within 25, 50 and 100 km;
- provider operator-record counts within 50 km;
- number of distinct providers within 50 km; and
- whether an LTE or NR band is listed at any matched site within 50 km.

Distinct mapped-site counts use RFNSA ID plus latitude and longitude rounded to five decimal places. The same function is used for the NT summary and the 25/50/100 km counts. This is a deduplication key, not a verified count of physical towers: coordinate or identifier differences can leave co-located equipment separate. The supplied files yield **419 operator-site records and 405 distinct mapped-site keys**. The previous summary used unrounded coordinates (408 keys), inconsistent with the proximity counts. Provider-specific counts remain operator-site records.

A 50 km radius is a descriptive matching threshold only—not a coverage radius. All distances are to **NT-filtered sites**, so a nearer site across the border may be excluded. Straight-line proximity does not account for terrain, antenna direction, capacity, outages or conditions at the user location. The separately published **Optus–TPG MOCN** file is not included: TPG distances describe its own listed infrastructure, and provider diversity is not a measure of retail customer choice.

The map projects the local boundary and points to Mercator coordinates on Plotly Cartesian axes; it fetches no external tiles or topographic files. Circles identify NT 2022 records and have a fixed size. Colour shows the indicator band. Optional crosses identify ACCC 2026 operator records, coloured consistently by operator. Filters select source locations; the optional site overlay always contains the full NT infrastructure file.

## Experimental Connectivity Priority Indicator

Four user-adjustable components are available:

| Component | Default weight | Normalisation / interpretation |
|---|---:|---|
| Coverage-type limitation proxy | 40% | Prototype ordinal mapping: proximity to cell = 100, small cell = 35, macro cell = 20; unspecified = missing. For multiple YES flags, `coverage_score_basis` explicitly chooses the least limiting listed type: macro before small before proximity. All original flags remain visible. This preserves the previous score ordering while making its assumption explicit; it does not establish measured performance. |
| Distance to infrastructure | 25% | Nearest ACCC site distance, clipped to 0–100 km and linearly scaled to 0–100. Larger distance increases the component. |
| Provider diversity | 15% | Inverse scale of distinct listed providers within 50 km: 0 providers = 100, 1 = 66.7, 2 = 33.3, 3 or more = 0. |
| Digital inclusion / remoteness context | 20% | When comparable exact-geography ADII values are supplied, reverse min-max scale within the matched records. Otherwise use source-supplied ordinal remoteness only when multiple categories are present. Missing or single-value context remains unavailable. |

For each record, components that lack evidence are excluded and the remaining configured weights are rescaled to 100%. A score is left missing if no component with a positive weight is supported. The interface discloses each component value, effective share, omitted components and the current adjustable weights.

With the supplied data there is **no usable context component**. The default effective weights are therefore **50% coverage, 31.25% distance, 18.75% diversity, 0% context** (40/80, 25/80, 15/80). The unsupported context slider is disabled. Each profile and CSV contains exact effective percentages and point contributions; the displayed total is rounded to one decimal place. These default percentages assume the other three inputs are present. If another input is missing, renormalisation is specific to that record.

Seven records have multiple positive flags: Barrow Creek, Daly Waters, Elliott, Erldunda and Mataranka (macro + small); Mount Ebenezer (small + proximity); Mutitjulu (macro + proximity). There are **98** records with any proximity flag, of which **96** are proximity-only. The composition chart groups the seven multi-flag records once so its percentages sum to 100%. Source-flag filters match every constituent flag. The indicator remains 16 records in the higher band at default weights; this is not 16 confirmed service gaps.

Sidebar filters and weights persist through in-app navigation and apply to Overview, Explorer, Insights and snapshots. Full NT infrastructure counts are labelled separately. The sensitivity plot applies baseline and current weights to the same records; current priority-band filters define that subset. It is a comparison of assumptions, not years.

Bands are **Lower: 0–33**, **Moderate: >33–66**, and **Higher: >66–100**. This indicator is experimental, relative only to its documented inputs and assumptions, and must not be used as a government ranking or investment decision.

## Digital inclusion and population

Connectivity availability does not itself show affordability, access to suitable devices, or digital ability. ADII dimensions are only shown at the geography that the source publishes. Aggregate ADII statistics are never copied to a community or an individual. The ADII input is a header-only template; no observations are supplied.

The NT Government coverage workbook's `POPULATION` field is displayed as its source value. ABS 2021 ILOC data are not included; any future join requires an authoritative geography identifier/crosswalk and clear Census reference year.

## Missing data, limitations and ethics

- NT coverage is the 2022 catalogue/workbook version; a measurement date for each record is not supplied. ACCC site observations are as at 31 January 2026, published in September 2026. Source files were accessed 28 September 2026; publisher metadata was verified 29 September 2026. Neither dataset guarantees present-day availability. Do not treat them as a time series.
- This source scope is locations with listed mobile coverage. Absence from the list is not proof of no service.
- Proximity to a mapped site or a listed band does not guarantee signal, service quality or 4G/5G coverage at a community.
- Coverage does not establish affordability, devices, meaningful access or digital ability.
- Aggregate statistics cannot describe every person or community. Do not infer individual ability from geography.
- Use strengths-based and respectful language; do not describe First Nations communities as “digitally illiterate”.
- Consult affected communities before decisions about infrastructure, service or investment.
- Missing observations are explicitly unavailable; they are not silently estimated or backfilled.
- The priority indicator is decision support only. It is not an official government priority ranking or a substitute for community engagement and engineering assessment.
- The map draws its NT boundary and data points locally. CSV and text downloads are snapshots; local profile caching and synchronization are not implemented, so this is not a production offline-first client.
