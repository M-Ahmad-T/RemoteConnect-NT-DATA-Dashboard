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
3. Parse source population and coordinates as numeric. Retain only non-empty named rows with valid latitude and longitude ranges; do not impute coordinates or population.
4. Remove duplicate coverage rows using normalized name, coordinates, coverage type and provider. Distinct coordinates or provider/coverage observations remain distinct source records.
5. Load each provider's newest available `mobile-sites-{provider}-{year}.csv` file. Parse all LTE and NR band columns from the ACCC field names; any populated band means that technology is listed at that site.
6. Drop operator records with invalid coordinates. Filter national site records to the NT by spatially intersecting WGS84 point geometries with the supplied NT boundary polygon. No rough bounding box is used.
7. Retain source RFNSA IDs, coordinates, provider and band/co-funding fields in the processed infrastructure output. Missing source values remain missing.
8. Optional ADII rows can join to a community profile only when `geography_level` is exactly `community` and the normalized source geography name matches uniquely. Regional, NT-wide and national rows remain context records. Optional ABS values are not used without a reliable source geography crosswalk.

## Geographic matching and distances

Community coordinates come directly from the NT Government source list. They represent listed source locations, not newly geocoded community centroids.

For each source location, the pipeline compares its coordinates with every NT-filtered ACCC operator record using the Haversine great-circle formula and mean Earth radius **6,371.0088 km**. The calculations produce:

- nearest overall, Telstra, Optus and TPG site distances;
- unique mapped RFNSA/location counts within 25, 50 and 100 km;
- provider operator-record counts within 50 km;
- number of distinct providers within 50 km; and
- whether an LTE or NR band is listed at any matched site within 50 km.

Unique physical-site counts use RFNSA ID plus rounded coordinates to avoid counting multi-provider records at the same site more than once. Provider-specific counts remain operator-site records. A 50 km radius is a descriptive matching threshold only—not a coverage radius. Straight-line proximity does not account for terrain, antenna direction, capacity, outages, network sharing or conditions at the user location.

## Experimental Connectivity Priority Indicator

Four user-adjustable components are available:

| Component | Default weight | Normalisation / interpretation |
|---|---:|---|
| Coverage-type limitation proxy | 40% | Prototype ordinal mapping from the NT source: proximity to cell = 100, small cell = 35, macro cell = 20; unspecified = missing. These values are design assumptions, not measured service performance. |
| Distance to infrastructure | 25% | Nearest ACCC site distance, clipped to 0–100 km and linearly scaled to 0–100. Larger distance increases the component. |
| Provider diversity | 15% | Inverse scale of distinct listed providers within 50 km: 0 providers = 100, 1 = 66.7, 2 = 33.3, 3 or more = 0. |
| Digital inclusion / remoteness context | 20% | When comparable exact-geography ADII values are supplied, reverse min-max scale within the matched records. Otherwise use source-supplied ordinal remoteness only when multiple categories are present. Missing or single-value context remains unavailable. |

For each record, components that lack evidence are excluded and the remaining configured weights are rescaled to 100%. A score is left missing if no component with a positive weight is supported. The interface discloses each component value, effective share, omitted components and the current adjustable weights.

Bands are **Lower: 0–33**, **Moderate: >33–66**, and **Higher: >66–100**. This indicator is experimental, relative only to its documented inputs and assumptions, and must not be used as a government ranking or investment decision.

## Digital inclusion and population

Connectivity availability does not itself show affordability, access to suitable devices, or digital ability. ADII dimensions are only shown at the geography that the source publishes. Aggregate ADII statistics are never copied to a community or an individual. No ADII file is currently supplied.

The NT Government coverage workbook's `POPULATION` field is displayed as its source value. ABS 2021 ILOC data are not included; any future join requires an authoritative geography identifier/crosswalk and clear Census reference year.

## Missing data, limitations and ethics

- NT coverage observations date from 2022; the ACCC infrastructure files are from 2026. Neither date guarantees present-day availability.
- This source scope is locations with listed mobile coverage. Absence from the list is not proof of no service.
- Proximity to a mapped site or a listed band does not guarantee signal, service quality or 4G/5G coverage at a community.
- Coverage does not establish affordability, devices, meaningful access or digital ability.
- Aggregate statistics cannot describe every person or community. Do not infer individual ability from geography.
- Use strengths-based and respectful language; do not describe First Nations communities as “digitally illiterate”.
- Consult affected communities before decisions about infrastructure, service or investment.
- Missing observations are explicitly unavailable; they are not silently estimated or backfilled.
- The priority indicator is decision support only. It is not an official government priority ranking or a substitute for community engagement and engineering assessment.
- The map draws its NT boundary and data points locally. CSV and text downloads are snapshots; local profile caching and synchronization are not implemented, so this is not a production offline-first client.
