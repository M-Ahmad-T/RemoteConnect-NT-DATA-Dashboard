import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.prepare_data import haversine_distances_km, load_communities, match_infrastructure
from src.priority import DEFAULT_WEIGHTS, apply_priority_weights


class HaversineTests(unittest.TestCase):
    def test_one_degree_latitude_is_about_111_km(self):
        sites = pd.DataFrame({"latitude": [-11.0], "longitude": [130.0]})
        distance = haversine_distances_km(-12.0, 130.0, sites)[0]
        self.assertAlmostEqual(distance, 111.195, delta=0.02)

    def test_empty_sites_return_empty_distances(self):
        sites = pd.DataFrame({"latitude": [], "longitude": []})
        self.assertEqual(len(haversine_distances_km(-12.0, 130.0, sites)), 0)

    def test_missing_community_coordinates_remain_unmatched(self):
        communities = pd.DataFrame(
            {
                "community": ["Unlocated source record"],
                "community_key": ["unlocated source record"],
                "latitude": [np.nan],
                "longitude": [np.nan],
            }
        )
        matched = match_infrastructure(communities, pd.DataFrame())
        self.assertEqual(len(matched), 1)
        self.assertTrue(pd.isna(matched.loc[0, "nearest_mobile_site_km"]))
        self.assertTrue(pd.isna(matched.loc[0, "sites_within_50km"]))

    def test_unavailable_provider_data_does_not_become_zero_coverage(self):
        communities = pd.DataFrame(
            {
                "community": ["Location A"],
                "community_key": ["location a"],
                "latitude": [-12.0],
                "longitude": [130.0],
            }
        )
        telstra_only = pd.DataFrame(
            {
                "provider": ["Telstra"],
                "rfnsa_id": ["100"],
                "latitude": [-12.1],
                "longitude": [130.0],
                "has_4g": [True],
                "has_5g": [False],
            }
        )
        matched = match_infrastructure(communities, telstra_only, {"Telstra"})
        self.assertGreater(matched.loc[0, "nearest_telstra_site_km"], 0)
        self.assertTrue(pd.isna(matched.loc[0, "nearest_optus_site_km"]))
        self.assertTrue(pd.isna(matched.loc[0, "optus_sites_nearby"]))
        self.assertTrue(pd.isna(matched.loc[0, "nearest_mobile_site_km"]))
        self.assertTrue(pd.isna(matched.loc[0, "sites_within_50km"]))


class CommunityCleaningTests(unittest.TestCase):
    def test_duplicate_rows_are_removed_and_missing_coordinates_are_not_invented(self):
        raw = pd.DataFrame(
            {
                "site_name": ["Source location A", "Source location A", "Source location B"],
                "site_type": ["COMMUNITY", "COMMUNITY", "VILLAGE"],
                "population": [12, 12, np.nan],
                "latitude": [-13.2, -13.2, np.nan],
                "longitude": [131.1, 131.1, np.nan],
                "macro_cell": ["YES", "YES", np.nan],
                "small_cell": [np.nan, np.nan, np.nan],
                "proximity_to_cell": [np.nan, np.nan, "YES"],
                "provider": ["TELSTRA", "TELSTRA", "OPTUS"],
                "source_sheet": ["Coverage", "Coverage", "Coverage"],
                "source_file": ["official.xlsx", "official.xlsx", "official.xlsx"],
            }
        )
        with patch("src.prepare_data.read_core_coverage", return_value=raw):
            cleaned = load_communities(Path("official.xlsx"))
        self.assertEqual(len(cleaned), 2)
        missing = cleaned.loc[cleaned["community"].eq("Source location B")].iloc[0]
        self.assertTrue(pd.isna(missing["latitude"]))
        self.assertTrue(pd.isna(missing["longitude"]))


class PriorityTests(unittest.TestCase):
    def test_missing_components_are_excluded_and_remaining_weights_rescaled(self):
        frame = pd.DataFrame(
            {
                "coverage_limitation_component": [100.0],
                "distance_component": [np.nan],
                "provider_diversity_component": [50.0],
                "context_component": [np.nan],
            }
        )
        scored = apply_priority_weights(frame, DEFAULT_WEIGHTS)
        expected = (100 * 40 + 50 * 15) / (40 + 15)
        self.assertAlmostEqual(scored.loc[0, "priority_score"], expected, places=1)
        self.assertIn("digital inclusion / remoteness context", scored.loc[0, "priority_explanation"])
        self.assertEqual(scored.loc[0, "priority_band"], "Higher")

    def test_no_supported_component_remains_unscored(self):
        frame = pd.DataFrame(
            {
                "coverage_limitation_component": [np.nan],
                "distance_component": [np.nan],
                "provider_diversity_component": [np.nan],
                "context_component": [np.nan],
            }
        )
        scored = apply_priority_weights(frame, DEFAULT_WEIGHTS)
        self.assertTrue(pd.isna(scored.loc[0, "priority_score"]))
        self.assertTrue(pd.isna(scored.loc[0, "priority_band"]))
        self.assertIn("no score assigned", scored.loc[0, "priority_explanation"])

    def test_zero_weights_do_not_produce_a_score(self):
        frame = pd.DataFrame(
            {
                "coverage_limitation_component": [80.0],
                "distance_component": [40.0],
                "provider_diversity_component": [25.0],
                "context_component": [np.nan],
            }
        )
        scored = apply_priority_weights(frame, {name: 0 for name in DEFAULT_WEIGHTS})
        self.assertTrue(pd.isna(scored.loc[0, "priority_score"]))


if __name__ == "__main__":
    unittest.main()
