"""Prepare source-backed community and mobile-site data for RemoteConnect NT."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

if __package__:
    from .priority import DEFAULT_WEIGHTS, apply_priority_weights
else:
    from priority import DEFAULT_WEIGHTS, apply_priority_weights

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROVIDERS = ("Telstra", "Optus", "TPG")
COVERAGE_FLAGS = {"macro_cell": "Macro cell", "small_cell": "Small cell", "proximity_to_cell": "Proximity to cell"}


def coverage_flags(row: pd.Series) -> list[str]:
    """Keep every positive source flag; flags are not mutually exclusive."""
    return [label for field, label in COVERAGE_FLAGS.items()
            if str(row.get(field, "")).strip().casefold() in {"yes", "y", "true", "1"}]
def clean_column_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return re.sub(r"[^a-z0-9]+", "_", text.encode("ascii", "ignore").decode().lower()).strip("_")


def clean_community_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    return re.sub(r"\s+", " ", text)


def community_key(value: object) -> str:
    text = clean_community_name(value).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [clean_column_name(column) for column in result.columns]
    return result


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def find_core_workbook() -> Path:
    candidates = sorted(RAW.glob("*coverage*.xlsx"))
    if not candidates:
        raise FileNotFoundError(
            "Required NT community coverage workbook is missing. Download "
            "'Remote Areas Mobile Coverage' (XLSX) from "
            "https://data.nt.gov.au/dataset/mobile-phone-coverage-in-remote-areas-of-the-nt "
            "and save it as data/raw/nt-mobile-coverage-2022.xlsx."
        )
    return candidates[0]


def read_core_coverage(path: Path) -> pd.DataFrame:
    with pd.ExcelFile(path) as workbook:
        sheets = workbook.sheet_names
    for sheet in sheets:
        for header_row in range(11):
            candidate = normalise_columns(
                pd.read_excel(path, sheet_name=sheet, header=header_row)
            )
            if "site_name" in candidate.columns and "latitude" in candidate.columns:
                candidate["source_sheet"] = sheet
                candidate["source_file"] = path.name
                return candidate
    raise ValueError(
        f"Could not find a community/site name and coordinates in {path.name}. "
        "Check that this is the NT Government 'Remote Areas Mobile Coverage' workbook."
    )


def valid_coordinates(frame: pd.DataFrame) -> pd.Series:
    latitude = pd.to_numeric(frame["latitude"], errors="coerce")
    longitude = pd.to_numeric(frame["longitude"], errors="coerce")
    return (
        latitude.between(-90, 90)
        & longitude.between(-180, 180)
        & latitude.notna()
        & longitude.notna()
    )


def coverage_category(row: pd.Series) -> str:
    return " + ".join(coverage_flags(row)) or "Not specified"


def load_communities(path: Path) -> pd.DataFrame:
    raw = read_core_coverage(path)
    required = {"site_name", "latitude", "longitude"}
    if not required.issubset(raw.columns):
        raise ValueError(f"{path.name} is missing required columns: {sorted(required - set(raw.columns))}")

    out = pd.DataFrame(index=raw.index)
    out["community"] = raw["site_name"].map(clean_community_name)
    out["community_key"] = out["community"].map(community_key)
    out["site_type"] = raw.get("site_type", pd.Series("", index=raw.index)).fillna("").astype(str).str.strip()
    out["population"] = pd.to_numeric(raw.get("population", np.nan), errors="coerce")
    out["latitude"] = pd.to_numeric(raw["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(raw["longitude"], errors="coerce")
    out["coverage_type"] = raw.apply(coverage_category, axis=1)
    for field in COVERAGE_FLAGS:
        out[field] = raw.get(field, pd.Series(pd.NA, index=raw.index))
    out["coverage_flag_count"] = raw.apply(lambda row: len(coverage_flags(row)), axis=1)
    # Explicit scoring rule: use the least limiting listed type, preserving all flags.
    out["coverage_score_basis"] = raw.apply(lambda row: next(iter(coverage_flags(row)), "Not specified"), axis=1)
    out["coverage_provider"] = raw.get(
        "provider", pd.Series("Not specified", index=raw.index)
    ).fillna("Not specified").astype(str).str.strip()
    out["source_sheet"] = raw["source_sheet"]
    out["source_file"] = raw["source_file"]
    out = out.loc[out["community_key"].ne("")].copy()
    invalid_location = ~valid_coordinates(out)
    out.loc[invalid_location, ["latitude", "longitude"]] = np.nan
    out = out.drop_duplicates(
        subset=["community_key", "latitude", "longitude", "coverage_type", "coverage_provider"]
    )
    if out.empty:
        raise ValueError("The NT coverage workbook contained no records with a valid location name.")
    return out.reset_index(drop=True)


def find_boundary_file() -> Path:
    path = RAW / "nt_state_boundary.geojson"
    if not path.exists():
        raise FileNotFoundError(
            "Required NT boundary for accurately filtering national ACCC mobile sites is missing. "
            "See data/raw/README.txt for the Natural Earth admin-1 boundary download and extraction steps."
        )
    return path


def load_nt_boundary() -> gpd.GeoDataFrame:
    boundary = gpd.read_file(find_boundary_file())
    if boundary.empty:
        raise ValueError("The NT boundary file has no geometries.")
    if boundary.crs is None:
        raise ValueError("The NT boundary file must declare its coordinate reference system.")
    boundary = boundary.to_crs("EPSG:4326")
    return boundary


def latest_provider_file(provider: str) -> Path | None:
    matches = list(RAW.glob(f"mobile-sites-{provider.lower()}-*.csv"))
    if not matches:
        return None
    return max(matches, key=lambda path: (int(re.search(r"(20\d{2})", path.stem).group(1)), path.stat().st_mtime))


def parse_flag(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().casefold() not in {"", "n", "no", "false", "0", "nan", "none"}


def load_mobile_sites(boundary: gpd.GeoDataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    parts: list[pd.DataFrame] = []
    selected_sources: dict[str, str] = {}
    for provider in PROVIDERS:
        source = latest_provider_file(provider)
        if source is None:
            print(f"Optional infrastructure source missing for {provider}; provider distances will be unavailable.")
            continue
        frame = normalise_columns(read_csv(source))
        required = {"latitude", "longitude"}
        if not required.issubset(frame.columns):
            raise ValueError(f"{source.name} needs latitude and longitude columns.")
        frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
        frame["longitude"] = pd.to_numeric(frame["longitude"], errors="coerce")
        frame = frame.loc[valid_coordinates(frame)].copy()
        frame["provider"] = frame.get("mno", pd.Series(provider, index=frame.index)).fillna(provider).astype(str)
        frame["provider"] = provider
        frame["rfnsa_id"] = frame.get("rfnsa_id", pd.Series(pd.NA, index=frame.index)).astype("string")
        lte_columns = [column for column in frame if re.fullmatch(r"lte\d+", column)]
        nr_columns = [column for column in frame if re.fullmatch(r"nr\d+", column)]
        frame["has_4g"] = frame[lte_columns].apply(lambda row: any(parse_flag(v) for v in row), axis=1) if lte_columns else False
        frame["has_5g"] = frame[nr_columns].apply(lambda row: any(parse_flag(v) for v in row), axis=1) if nr_columns else False
        frame["source_file"] = source.name
        frame = frame.drop_duplicates()
        parts.append(frame)
        selected_sources[provider] = source.name

    if not parts:
        empty_sites = pd.DataFrame(
            columns=[
                "provider",
                "rfnsa_id",
                "latitude",
                "longitude",
                "has_4g",
                "has_5g",
                "source_file",
            ]
        )
        return empty_sites, selected_sources
    sites = pd.concat(parts, ignore_index=True)
    points = gpd.GeoDataFrame(
        sites,
        geometry=gpd.points_from_xy(sites["longitude"], sites["latitude"]),
        crs="EPSG:4326",
    )
    nt_sites = gpd.sjoin(points, boundary[["geometry"]], how="inner", predicate="intersects")
    nt_sites = pd.DataFrame(nt_sites.drop(columns=["geometry", "index_right"], errors="ignore"))
    return nt_sites.reset_index(drop=True), selected_sources


def haversine_distances_km(lat: float, lon: float, sites: pd.DataFrame) -> np.ndarray:
    """Return great-circle distances in kilometres using the Haversine formula."""
    earth_radius_km = 6371.0088
    lat1 = np.radians(float(lat))
    lat2 = np.radians(sites["latitude"].to_numpy(dtype=float))
    dlat = lat2 - lat1
    dlon = np.radians(sites["longitude"].to_numpy(dtype=float) - float(lon))
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return earth_radius_km * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def mapped_site_keys(sites: pd.DataFrame) -> pd.Series:
    """A reproducible deduplication key, not a verified count of physical towers."""
    return (sites["rfnsa_id"].fillna("").astype(str) + "|"
            + sites["latitude"].round(5).astype(str) + "|"
            + sites["longitude"].round(5).astype(str))


def match_infrastructure(
    communities: pd.DataFrame,
    sites: pd.DataFrame,
    available_providers: set[str] | None = None,
) -> pd.DataFrame:
    if available_providers is None:
        available_providers = set(sites["provider"].dropna().unique()) if "provider" in sites else set()
    metrics: list[dict[str, object]] = []
    for community in communities.itertuples(index=False):
        record: dict[str, object] = {
            "nearest_mobile_site_km": np.nan,
            "nearest_telstra_site_km": np.nan,
            "nearest_optus_site_km": np.nan,
            "nearest_tpg_site_km": np.nan,
            "sites_within_25km": np.nan,
            "sites_within_50km": np.nan,
            "sites_within_100km": np.nan,
            "telstra_sites_nearby": np.nan,
            "optus_sites_nearby": np.nan,
            "tpg_sites_nearby": np.nan,
            "has_4g_nearby": pd.NA,
            "has_5g_nearby": pd.NA,
            "infrastructure_diversity": np.nan,
        }
        has_coordinates = pd.notna(community.latitude) and pd.notna(community.longitude)
        distances = np.array([], dtype=float)
        if has_coordinates and not sites.empty:
            distances = haversine_distances_km(community.latitude, community.longitude, sites)
        if has_coordinates:
            for provider in PROVIDERS:
                if provider not in available_providers:
                    continue
                subset = (
                    sites["provider"].eq(provider).to_numpy()
                    if "provider" in sites
                    else np.zeros(0, dtype=bool)
                )
                if subset.any():
                    record[f"nearest_{provider.lower()}_site_km"] = float(np.min(distances[subset]))
                    record[f"{provider.lower()}_sites_nearby"] = int(np.sum(distances[subset] <= 50))
                else:
                    record[f"{provider.lower()}_sites_nearby"] = 0
            if set(PROVIDERS).issubset(available_providers):
                if distances.size:
                    record["nearest_mobile_site_km"] = float(np.min(distances))
                    within_25 = distances <= 25
                    within_50 = distances <= 50
                    within_100 = distances <= 100
                    # A physical site can have more than one MNO record; count unique mapped site locations.
                    site_keys = mapped_site_keys(sites)
                    record["sites_within_25km"] = int(site_keys[within_25].nunique())
                    record["sites_within_50km"] = int(site_keys[within_50].nunique())
                    record["sites_within_100km"] = int(site_keys[within_100].nunique())
                    nearby = sites.loc[within_50]
                    record["infrastructure_diversity"] = int(nearby["provider"].nunique())
                    record["has_4g_nearby"] = bool(nearby["has_4g"].any())
                    record["has_5g_nearby"] = bool(nearby["has_5g"].any())
                else:
                    record["sites_within_25km"] = 0
                    record["sites_within_50km"] = 0
                    record["sites_within_100km"] = 0
                    record["infrastructure_diversity"] = 0
                    record["has_4g_nearby"] = False
                    record["has_5g_nearby"] = False
        metrics.append(record)
    return pd.concat([communities.reset_index(drop=True), pd.DataFrame(metrics)], axis=1)


def load_optional_context(communities: pd.DataFrame) -> pd.DataFrame:
    result = communities.copy()
    inclusion_path = RAW / "digital_inclusion_optional.csv"
    if inclusion_path.exists():
        inclusion = normalise_columns(read_csv(inclusion_path))
        if not inclusion.empty:
            if "geography_level" not in inclusion.columns or "geography_name" not in inclusion.columns:
                print(
                    "ADII context not joined: provide geography_level and geography_name. "
                    "Only exact community-level rows may join to community profiles."
                )
            else:
                community_rows = inclusion.loc[
                    inclusion["geography_level"].astype(str).str.casefold().eq("community")
                ].copy()
                community_rows["community_key"] = community_rows["geography_name"].map(community_key)
                community_rows = community_rows.drop_duplicates("community_key", keep=False)
                # A repeated target name at different coordinates is not a defensible match.
                ambiguous = result.loc[result.duplicated("community_key", keep=False), "community_key"]
                community_rows = community_rows.loc[~community_rows["community_key"].isin(ambiguous)]
                numeric_names = {
                    "adii_score": "digital_inclusion_score",
                    "access": "access_score",
                    "affordability": "affordability_score",
                    "digital_ability": "digital_ability_score",
                    "year": "adii_year",
                    "source_note": "adii_source_note",
                }
                rename = {old: new for old, new in numeric_names.items() if old in community_rows.columns}
                community_rows = community_rows.rename(columns=rename)
                allowed = [
                    "community_key",
                    "digital_inclusion_score",
                    "access_score",
                    "affordability_score",
                    "digital_ability_score",
                    "remoteness",
                    "adii_year",
                    "adii_source_note",
                ]
                available = [column for column in allowed if column in community_rows.columns]
                result = result.merge(
                    community_rows[available],
                    on="community_key",
                    how="left",
                    validate="many_to_one",
                )
                for column in (
                    "digital_inclusion_score",
                    "access_score",
                    "affordability_score",
                    "digital_ability_score",
                ):
                    if column in result:
                        result[column] = pd.to_numeric(result[column], errors="coerce")
    abs_path = RAW / "abs_2021_iloc_optional.csv"
    if abs_path.exists():
        census = normalise_columns(read_csv(abs_path))
        required_census_fields = {
            "community",
            "geography_code",
            "geography_name",
            "population",
            "match_method",
        }
        if not census.empty and required_census_fields.issubset(census.columns):
            census = census.loc[
                census["match_method"].notna()
                & census["match_method"].astype(str).str.strip().ne("")
            ].copy()
            census["community_key"] = census["community"].map(community_key)
            census["abs_population_2021"] = pd.to_numeric(census["population"], errors="coerce")
            census = census.drop_duplicates("community_key", keep=False)
            if not census.empty:
                census = census.rename(
                    columns={
                        "geography_code": "abs_geography_code",
                        "geography_name": "abs_geography_name",
                        "match_method": "abs_match_method",
                    }
                )
                result = result.merge(
                    census[
                        [
                            "community_key",
                            "abs_population_2021",
                            "abs_geography_code",
                            "abs_geography_name",
                            "abs_match_method",
                        ]
                    ].dropna(subset=["community_key"]),
                    on="community_key",
                    how="left",
                    validate="many_to_one",
                )
        elif not census.empty:
            print(
                "ABS context not joined: provide community, geography_code, geography_name, "
                "population and a documented match_method."
            )
    return result


def add_priority_components(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    coverage_map = {
        "Proximity to cell": 100.0,
        "Small cell": 35.0,
        "Macro cell": 20.0,
        "Not specified": np.nan,
    }
    out["coverage_limitation_component"] = out.get("coverage_score_basis", out["coverage_type"]).map(coverage_map)
    out["distance_component"] = (out["nearest_mobile_site_km"].clip(lower=0, upper=100) / 100) * 100
    out["provider_diversity_component"] = (
        (1 - out["infrastructure_diversity"].clip(lower=0, upper=3) / 3) * 100
    )
    inclusion = pd.to_numeric(out.get("digital_inclusion_score", pd.Series(np.nan, index=out.index)), errors="coerce")
    if inclusion.notna().sum() >= 2 and inclusion.max() > inclusion.min():
        out["context_component"] = 100 * (1 - (inclusion - inclusion.min()) / (inclusion.max() - inclusion.min()))
    else:
        remoteness = out.get("remoteness", pd.Series(index=out.index, dtype="object")).astype("string")
        out["context_component"] = np.nan
        # Remoteness is an ordinal source classification; order only if it is explicitly present.
        remoteness_order = ["Major Cities", "Inner Regional", "Outer Regional", "Remote", "Very Remote"]
        normalised = remoteness.str.strip().str.casefold()
        rank = {name.casefold(): index for index, name in enumerate(remoteness_order)}
        normalised = normalised.str.replace(r"\s+(of\s+)?australia$", "", regex=True)
        ranks = normalised.map(rank)
        if ranks.notna().sum() >= 2 and ranks.max() > ranks.min():
            out["context_component"] = 100 * (ranks - ranks.min()) / (ranks.max() - ranks.min())

    return apply_priority_weights(out, DEFAULT_WEIGHTS)


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    try:
        core_file = find_core_workbook()
        communities = load_communities(core_file)
        boundary = load_nt_boundary()
        sites, provider_sources = load_mobile_sites(boundary)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    prepared = match_infrastructure(communities, sites, set(provider_sources))
    prepared = load_optional_context(prepared)
    prepared = add_priority_components(prepared)
    prepared.to_csv(PROCESSED / "communities.csv", index=False)
    sites.to_csv(PROCESSED / "infrastructure_nt.csv", index=False)
    summary = {
        "generated_on": date.today().isoformat(),
        "community_source": core_file.name,
        "infrastructure_sources": provider_sources,
        "community_records": int(len(prepared)),
        "communities_with_coordinates": int(prepared[["latitude", "longitude"]].notna().all(axis=1).sum()),
        "infrastructure_operator_records_in_nt": int(len(sites)),
        "distinct_mapped_site_keys_in_nt": int(mapped_site_keys(sites).nunique()) if not sites.empty else 0,
        "accc_observation_date": "2026-01-31",
        "source_access_date": "2026-09-28",
        "multiple_coverage_flag_records": int(prepared["coverage_flag_count"].gt(1).sum()),
        "priority_scored_communities": int(prepared["priority_score"].notna().sum()),
        "communities_with_5g_within_50km": int(prepared["has_5g_nearby"].eq(True).sum()),
        "digital_inclusion_records_matched": int(
            prepared["digital_inclusion_score"].notna().sum()
        ) if "digital_inclusion_score" in prepared else 0,
    }
    (PROCESSED / "data_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Prepared {len(prepared)} community records and {len(sites)} NT MNO-site records.")
    print(f"Output: {PROCESSED / 'communities.csv'}")
    if summary["digital_inclusion_records_matched"] == 0:
        print("ADII context: not joined; no matching community-level source records were supplied.")
    if summary["infrastructure_operator_records_in_nt"] == 0:
        print("Infrastructure: no ACCC sites fell within the supplied NT boundary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
