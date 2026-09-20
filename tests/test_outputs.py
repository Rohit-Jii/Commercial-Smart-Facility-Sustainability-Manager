import json
import unittest
from pathlib import Path

import pandas as pd


class ProjectOutputTests(unittest.TestCase):
    def test_three_month_telemetry_has_complete_five_minute_coverage(self):
        data = pd.read_csv("outputs/airport_washroom_telemetry_3_months.csv", parse_dates=["timestamp"])
        self.assertEqual(len(data), 259_200)
        self.assertEqual(data["restroom_id"].nunique(), 10)
        self.assertTrue((data.groupby("restroom_id").size() == 25_920).all())
        self.assertTrue(data[["flow_rate_lpm", "water_pressure_bar", "co2_ppm"]].notna().all().all())

    def test_dashboard_has_one_of_each_required_action(self):
        test_data = pd.read_csv("outputs/test_data.csv")
        self.assertTrue(test_data["leak_present"].eq(1).any())
        self.assertTrue(test_data["cleaning_needed_next_30min"].eq(1).any())
        self.assertTrue(test_data["refill_required_within_shift"].eq(1).any())

    def test_explicit_80_20_split_and_live_feed_are_complete(self):
        training = pd.read_csv("outputs/training_data.csv", parse_dates=["timestamp"])
        test = pd.read_csv("outputs/test_data.csv", parse_dates=["timestamp"])
        split = json.loads(Path("outputs/data_split_summary.json").read_text(encoding="utf-8"))
        stream = json.loads(Path("outputs/live_test_stream.json").read_text(encoding="utf-8"))
        models = json.loads(Path("outputs/live_models.json").read_text(encoding="utf-8"))
        self.assertEqual(len(training), 207_360)
        self.assertEqual(len(test), 51_840)
        self.assertEqual(split["training_fraction"], 0.8)
        self.assertEqual(split["test_fraction"], 0.2)
        self.assertEqual(len(stream), len(test))
        self.assertIn("cleaning", models)
        self.assertIn("water", models)
        for restroom_id in training["restroom_id"].unique():
            self.assertLess(
                training.loc[training["restroom_id"] == restroom_id, "timestamp"].max(),
                test.loc[test["restroom_id"] == restroom_id, "timestamp"].min(),
            )

    def test_weekly_forecast_has_every_restroom_and_interval(self):
        forecast = pd.read_csv("outputs/water_demand_forecast_7_days.csv")
        self.assertEqual(len(forecast), 7 * 24 * 12 * 10)
        self.assertEqual(forecast["restroom_id"].nunique(), 10)
        self.assertTrue((forecast["predicted_water_litres_5min"] >= 0).all())


if __name__ == "__main__":
    unittest.main()
