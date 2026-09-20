"""Train the simple cleaning model and produce dashboard-ready project outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analytics import (
    add_cleaning_predictions,
    add_detection_features,
    browser_model_payload,
    build_dashboard_data,
    create_water_forecast,
    split_train_test,
    train_cleaning_model,
)


def main() -> None:
    data_path = Path("outputs/airport_washroom_telemetry_3_months.csv")
    if not data_path.exists():
        raise FileNotFoundError("Generate the telemetry first: python generate_data.py")

    telemetry = pd.read_csv(data_path, parse_dates=["timestamp", "last_cleaned_at"])
    telemetry = add_detection_features(telemetry)
    training, test = split_train_test(telemetry)
    model, metrics = train_cleaning_model(training, test, Path("models/cleaning_model.joblib"))
    telemetry = add_cleaning_predictions(telemetry, model)
    training = telemetry.loc[training.index]
    test = telemetry.loc[test.index]
    forecast, forecast_summary, water_model = create_water_forecast(training, test)
    dashboard_data = build_dashboard_data(training, forecast_summary)

    live_columns = [
        "timestamp", "restroom_id", "criticality", "passenger_volume", "flow_rate_lpm",
        "expected_flow_lpm", "water_pressure_bar", "flush_count", "tap_activations",
        "urinal_use", "water_tank_level_pct", "soap_level_pct", "sanitizer_level_pct",
        "paper_towel_level_pct", "bin_fill_pct", "odor_voc_ppb", "humidity_pct",
        "indoor_temperature_c", "co2_ppm", "last_cleaned_minutes_ago",
        "persistent_excess_lpm", "refill_required_within_shift",
    ]

    Path("outputs").mkdir(exist_ok=True)
    telemetry.to_csv("outputs/telemetry_with_predictions.csv", index=False)
    training.to_csv("outputs/training_data.csv", index=False)
    test.to_csv("outputs/test_data.csv", index=False)
    forecast.to_csv("outputs/water_demand_forecast_7_days.csv", index=False)
    Path("outputs/model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    Path("outputs/dashboard_data.json").write_text(json.dumps(dashboard_data, indent=2), encoding="utf-8")
    Path("outputs/live_test_stream.json").write_text(
        test[live_columns].to_json(orient="records", date_format="iso"), encoding="utf-8"
    )
    Path("outputs/live_models.json").write_text(
        json.dumps(browser_model_payload(model, water_model), indent=2), encoding="utf-8"
    )
    Path("outputs/data_split_summary.json").write_text(
        json.dumps(
            {
                "split_method": "chronological per washroom",
                "training_rows": len(training),
                "test_rows": len(test),
                "training_fraction": round(len(training) / len(telemetry), 2),
                "test_fraction": round(len(test) / len(telemetry), 2),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Created split CSVs, live stream data, browser models, and dashboard outputs")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
