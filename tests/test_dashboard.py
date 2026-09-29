"""Focused navigation and state regressions; browser review remains separate."""
import io
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.dashboard import filter_records, PAGES, map_figure
from src.exports import profile_report, snapshot_csv
from src.prepare_data import mapped_site_keys

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(ROOT / "data/processed/communities.csv")

    def test_flag_filter_includes_combined_flags(self):
        filtered = filter_records(self.data, coverage="Proximity to cell")
        self.assertEqual(len(filtered), 98)
        self.assertIn("MUTITJULU", filtered.community.tolist())
        self.assertIn("MOUNT EBENEZER", filtered.community.tolist())
        self.assertEqual(len(filter_records(self.data, coverage="Multiple flags")), 7)

    def test_export_preserves_weights_dates_sources_and_distinct_key_label(self):
        row = self.data.iloc[0]
        exported = pd.read_csv(io.BytesIO(snapshot_csv(row.to_frame().T)))
        self.assertEqual(exported.loc[0, "accc_observation_date"], "2026-01-31")
        self.assertEqual(exported.loc[0, "coverage_limitation_component_weight_pct"], 50)
        self.assertEqual(exported.loc[0, "macro_cell"], row.macro_cell)
        text = profile_report(row, {})
        self.assertIn("Distinct mapped site keys within 50 km", text)
        self.assertNotIn("Operator-site records within 50 km:", text)
        self.assertIn("CC BY 2.5 AU", text)
        self.assertIn(f"Latitude: {row.latitude:.5f}", text)
        self.assertEqual(exported.loc[0, "accc_source_licence"], "Creative Commons Attribution 2.5 Australia")

    def test_mapped_site_keys_deduplicate_only_same_id_and_rounded_coordinates(self):
        sites = pd.DataFrame({"rfnsa_id":["1","1","2"], "latitude":[-12.0,-12.0000001,-12.0], "longitude":[130.0]*3})
        self.assertEqual(mapped_site_keys(sites).nunique(), 2)

    def test_map_uses_local_cartesian_geometry_and_fixed_marker_sizes(self):
        figure = map_figure(self.data)
        self.assertTrue(all(trace.type == "scatter" for trace in figure.data))
        self.assertEqual({trace.marker.size for trace in figure.data if trace.mode == "markers"}, {10})

    def test_all_pages_render_with_filtered_context(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(app.sidebar.slider[3].disabled)
        app.sidebar.selectbox(key="filter_coverage").set_value("Multiple flags").run()
        for filename, title in PAGES:
            app.switch_page(f"pages/{filename}").run(timeout=30)
            self.assertFalse(app.exception, title)
            # AppTest executes switched pages directly; real navigation persistence
            # is checked separately in scripts/browser_interactions.py.
            self.assertEqual(len(app.session_state["_dashboard_context"][2]), 7)
        self.assertEqual(len(app.selectbox[-1].options), 7)

    def test_explorer_selection_and_empty_filter_state(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        app.sidebar.selectbox(key="filter_coverage").set_value("Multiple flags").run()
        app.switch_page("pages/3_Community_Explorer.py").run()
        picker = app.selectbox[-1]
        picker.select_index(5).run()
        self.assertFalse(app.exception)
        selected = app.session_state["selected_record"]
        self.assertEqual(self.data.loc[selected, "community"], "MOUNT EBENEZER")
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        app.sidebar.selectbox(key="filter_technology").set_value("Not assessed").run()
        app.switch_page("pages/3_Community_Explorer.py").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No source locations match" in item.value for item in app.info))

    def test_score_controls_and_all_zero_state(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        baseline = app.session_state["_dashboard_context"][0].priority_score.copy()
        app.sidebar.slider[0].set_value(0).run()
        current = app.session_state["_dashboard_context"][0].priority_score
        self.assertTrue(baseline.ne(current).any())
        app.sidebar.slider[1].set_value(0).run()
        app.sidebar.slider[2].set_value(0).run()
        self.assertTrue(app.session_state["_dashboard_context"][0].priority_score.isna().all())
        app.switch_page("pages/5_Data_Insights.py").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No scores are supported" in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
