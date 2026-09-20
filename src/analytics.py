"""Detection, prediction, forecasting, and ticket generation for the MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, mean_absolute_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


CLEANING_FEATURES = [
    "passenger_volume",
    "flow_rate_lpm",
    "flush_count",
    "tap_activations",
    "soap_level_pct",
    "sanitizer_level_pct",
    "paper_towel_level_pct",
    "bin_fill_pct",
    "odor_voc_ppb",
    "humidity_pct",
    "co2_ppm",
    "last_cleaned_minutes_ago",
    "criticality",
]


@dataclass
class Ticket:
    ticket_id: str
    restroom_id: str
    issue_type: str
    priority: str
    confidence: float
    recommended_action: str
    evidence: str


def add_detection_features(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Calculate transparent, fixture-aware leak and refill risk indicators."""
    frame = telemetry.copy().sort_values(["restroom_id", "timestamp"])
    frame["flow_excess_lpm"] = (frame["flow_rate_lpm"] - frame["expected_flow_lpm"]).clip(lower=0)
    frame["persistent_excess_lpm"] = frame.groupby("restroom_id")["flow_excess_lpm"].transform(
        lambda values: values.rolling(4, min_periods=4).min().fillna(0)
    )
    persistent_score = ((frame["persistent_excess_lpm"] - 0.18) / 0.65).clip(0, 1)
    excess_score = ((frame["flow_excess_lpm"] - 0.20) / 0.9).clip(0, 1)
    pressure_score = ((3.05 - frame["water_pressure_bar"]) / 0.5).clip(0, 1)
    frame["leak_probability"] = (
        0.68 * persistent_score + 0.22 * excess_score + 0.10 * pressure_score
    ).clip(0, 1)
    consumable_min = frame[["soap_level_pct", "sanitizer_level_pct", "paper_towel_level_pct"]].min(axis=1)
    frame["refill_risk"] = ((25 - consumable_min) / 25).clip(0, 1)
    return frame


def split_train_test(telemetry: pd.DataFrame, train_fraction: float = 0.80) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a chronological 80/20 split independently for every washroom."""
    frame = telemetry.copy().sort_values(["restroom_id", "timestamp"])
    frame["_row_number"] = frame.groupby("restroom_id").cumcount()
    frame["_split_at"] = frame.groupby("restroom_id")["_row_number"].transform(
        lambda values: int(len(values) * train_fraction)
    )
    training = frame.loc[frame["_row_number"] < frame["_split_at"]].drop(columns=["_row_number", "_split_at"])
    test = frame.loc[frame["_row_number"] >= frame["_split_at"]].drop(columns=["_row_number", "_split_at"])
    return training, test


def train_cleaning_model(
    training: pd.DataFrame, test: pd.DataFrame, model_path: Path
) -> tuple[Pipeline, dict[str, float | int | None]]:
    """Fit only on training data and assess once against the held-out test set."""
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=750, class_weight="balanced", random_state=42)),
        ]
    )
    model.fit(training[CLEANING_FEATURES], training["cleaning_needed_next_30min"])
    probabilities = model.predict_proba(test[CLEANING_FEATURES])[:, 1]
    labels = test["cleaning_needed_next_30min"]
    metrics: dict[str, float | int | None] = {
        "training_rows": len(training),
        "test_rows": len(test),
        "positive_rate": round(float(labels.mean()), 4),
        "average_precision": round(float(average_precision_score(labels, probabilities)), 4),
        "roc_auc": None,
    }
    if labels.nunique() > 1:
        metrics["roc_auc"] = round(float(roc_auc_score(labels, probabilities)), 4)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return model, metrics


def add_cleaning_predictions(telemetry: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    frame = telemetry.copy()
    frame["cleaning_probability"] = model.predict_proba(frame[CLEANING_FEATURES])[:, 1]
    return frame


def _forecast_features(index: pd.DatetimeIndex, restroom_numbers: np.ndarray, expected_passengers: np.ndarray) -> pd.DataFrame:
    hour_decimal = index.hour.to_numpy() + index.minute.to_numpy() / 60
    day_of_week = index.dayofweek.to_numpy()
    return pd.DataFrame(
        {
            "restroom_number": restroom_numbers,
            "expected_passenger_volume": expected_passengers,
            "hour_sin": np.sin(2 * np.pi * hour_decimal / 24),
            "hour_cos": np.cos(2 * np.pi * hour_decimal / 24),
            "weekday_sin": np.sin(2 * np.pi * day_of_week / 7),
            "weekday_cos": np.cos(2 * np.pi * day_of_week / 7),
        }
    )


FORECAST_FEATURES = [
    "restroom_number",
    "expected_passenger_volume",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
]


def create_water_forecast(
    training: pd.DataFrame, test: pd.DataFrame, periods: int = 7 * 24 * 12
) -> tuple[pd.DataFrame, dict[str, float], Pipeline]:
    """Forecast five-minute demand with calendar signals and expected traffic."""
    history = training.copy().sort_values("timestamp")
    history["restroom_number"] = history["restroom_id"].str.extract(r"(\d+)").astype(int)
    history["hour"] = history["timestamp"].dt.hour
    history["day_of_week"] = history["timestamp"].dt.dayofweek
    history["water_litres_5min"] = history["flow_rate_lpm"] * 5

    # Exclude known simulated leaks so the demand forecast represents normal operation.
    normal_history = history.loc[history["leak_present"].eq(0)].copy()
    normal_history["expected_passenger_volume"] = normal_history["passenger_volume"]
    train_features = _forecast_features(
        pd.DatetimeIndex(normal_history["timestamp"]),
        normal_history["restroom_number"].to_numpy(),
        normal_history["expected_passenger_volume"].to_numpy(),
    )
    model = Pipeline([("scale", StandardScaler()), ("regressor", Ridge(alpha=3.0))])
    model.fit(train_features[FORECAST_FEATURES], normal_history["water_litres_5min"])

    holdout = test.loc[test["leak_present"].eq(0)].copy()
    holdout["restroom_number"] = holdout["restroom_id"].str.extract(r"(\d+)").astype(int)
    holdout["water_litres_5min"] = holdout["flow_rate_lpm"] * 5
    holdout_features = _forecast_features(
        pd.DatetimeIndex(holdout["timestamp"]),
        holdout["restroom_number"].to_numpy(),
        holdout["passenger_volume"].to_numpy(),
    )
    holdout_predictions = model.predict(holdout_features[FORECAST_FEATURES])
    validation_mae = float(mean_absolute_error(holdout["water_litres_5min"], holdout_predictions))

    passenger_profile = (
        normal_history.groupby(["restroom_id", "day_of_week", "hour"], as_index=False)["passenger_volume"]
        .mean()
        .rename(columns={"passenger_volume": "expected_passenger_volume"})
    )
    future_timestamps = pd.date_range(
        start=history["timestamp"].max() + pd.Timedelta(minutes=5), periods=periods, freq="5min"
    )
    restroom_ids = history["restroom_id"].drop_duplicates().sort_values().to_list()
    future = pd.MultiIndex.from_product(
        [future_timestamps, restroom_ids], names=["timestamp", "restroom_id"]
    ).to_frame(index=False)
    future["hour"] = future["timestamp"].dt.hour
    future["day_of_week"] = future["timestamp"].dt.dayofweek
    future = future.merge(passenger_profile, on=["restroom_id", "day_of_week", "hour"], how="left")
    fallback_traffic = float(normal_history["passenger_volume"].mean())
    future["expected_passenger_volume"] = future["expected_passenger_volume"].fillna(fallback_traffic)
    future["restroom_number"] = future["restroom_id"].str.extract(r"(\d+)").astype(int)
    forecast_features = _forecast_features(
        pd.DatetimeIndex(future["timestamp"]),
        future["restroom_number"].to_numpy(),
        future["expected_passenger_volume"].to_numpy(),
    )
    future["predicted_water_litres_5min"] = np.maximum(
        model.predict(forecast_features[FORECAST_FEATURES]), 0
    ).round(2)
    future["predicted_water_litres_low"] = np.maximum(
        future["predicted_water_litres_5min"] - 1.28 * validation_mae, 0
    ).round(2)
    future["predicted_water_litres_high"] = (
        future["predicted_water_litres_5min"] + 1.28 * validation_mae
    ).round(2)
    forecast_start = future["timestamp"].min()
    summary = {
        "validation_mae_litres_per_5min": round(validation_mae, 2),
        "next_day_litres": round(
            float(
                future.loc[
                    future["timestamp"] < forecast_start + pd.Timedelta(days=1),
                    "predicted_water_litres_5min",
                ].sum()
            ),
            0,
        ),
        "next_week_litres": round(float(future["predicted_water_litres_5min"].sum()), 0),
    }
    return future, summary, model


def browser_model_payload(cleaning_model: Pipeline, water_model: Pipeline) -> dict:
    """Export simple scaler/regression parameters for browser-side live scoring."""
    def export_model(model: Pipeline, feature_names: list[str], estimator_name: str) -> dict:
        scaler = model.named_steps["scale"]
        estimator = model.named_steps[estimator_name]
        return {
            "features": feature_names,
            "mean": scaler.mean_.round(12).tolist(),
            "scale": scaler.scale_.round(12).tolist(),
            "coefficients": estimator.coef_[0].round(12).tolist() if estimator_name == "classifier" else estimator.coef_.round(12).tolist(),
            "intercept": float(estimator.intercept_[0] if estimator_name == "classifier" else estimator.intercept_),
        }

    return {
        "cleaning": export_model(cleaning_model, CLEANING_FEATURES, "classifier"),
        "water": export_model(water_model, FORECAST_FEATURES, "regressor"),
    }


def create_tickets(latest: pd.DataFrame) -> list[Ticket]:
    """Turn high-confidence model outputs into concise operator actions."""
    tickets: list[Ticket] = []
    counter = 1
    for row in latest.sort_values("restroom_id").itertuples(index=False):
        criticality_weight = {1: "Medium", 2: "High", 3: "High"}[row.criticality]
        if row.leak_probability >= 0.75:
            tickets.append(
                Ticket(
                    f"T-{counter:04d}",
                    row.restroom_id,
                    "Continuous leak risk",
                    "Immediate",
                    round(float(row.leak_probability), 2),
                    "Dispatch a technician immediately.",
                    f"Excess flow of {row.flow_excess_lpm:.2f} L/min persisted for at least 20 minutes.",
                )
            )
            counter += 1
        if row.cleaning_probability >= 0.70:
            passenger_band = "high" if row.passenger_volume >= 18 else "moderate"
            tickets.append(
                Ticket(
                    f"T-{counter:04d}",
                    row.restroom_id,
                    "Hygiene breach likely within 30 minutes",
                    criticality_weight,
                    round(float(row.cleaning_probability), 2),
                    "Add to the cleaner's next route.",
                    f"{passenger_band.title()} usage, bin {row.bin_fill_pct:.0f}%, odor {row.odor_voc_ppb:.0f} ppb, and {row.last_cleaned_minutes_ago} minutes since cleaning.",
                )
            )
            counter += 1
        if row.refill_risk >= 0.20 or row.refill_required_within_shift == 1:
            lowest = min(row.soap_level_pct, row.sanitizer_level_pct, row.paper_towel_level_pct)
            tickets.append(
                Ticket(
                    f"T-{counter:04d}",
                    row.restroom_id,
                    "Consumable refill required",
                    "High" if lowest < 15 else "Medium",
                    round(float(max(row.refill_risk, 0.35)), 2),
                    "Add consumables to the cleaner's route.",
                    f"Lowest consumable level is {lowest:.0f}%.",
                )
            )
            counter += 1
    return tickets


def build_dashboard_data(telemetry: pd.DataFrame, forecast_summary: dict[str, float]) -> dict:
    latest = telemetry.sort_values("timestamp").groupby("restroom_id", as_index=False).tail(1).copy()
    tickets = create_tickets(latest)
    latest["status"] = np.select(
        [
            latest["leak_probability"] >= 0.75,
            latest["cleaning_probability"] >= 0.70,
            latest["refill_risk"] >= 0.20,
        ],
        ["Immediate attention", "Cleaning needed", "Refill needed"],
        default="Normal",
    )
    washroom_columns = [
        "restroom_id",
        "criticality",
        "passenger_volume",
        "flow_rate_lpm",
        "water_pressure_bar",
        "water_tank_level_pct",
        "soap_level_pct",
        "sanitizer_level_pct",
        "paper_towel_level_pct",
        "bin_fill_pct",
        "odor_voc_ppb",
        "humidity_pct",
        "co2_ppm",
        "last_cleaned_minutes_ago",
        "leak_probability",
        "cleaning_probability",
        "refill_risk",
        "status",
    ]
    washrooms = latest[washroom_columns].copy()
    for column in ["leak_probability", "cleaning_probability", "refill_risk"]:
        washrooms[column] = washrooms[column].round(2)
    return {
        "data_as_of": latest["timestamp"].max().isoformat(),
        "summary": {
            "washrooms_monitored": int(len(latest)),
            "immediate_leak_tickets": sum(ticket.issue_type == "Continuous leak risk" for ticket in tickets),
            "cleaning_tickets": sum("Hygiene" in ticket.issue_type for ticket in tickets),
            "refill_tickets": sum("Consumable" in ticket.issue_type for ticket in tickets),
            **forecast_summary,
        },
        "washrooms": washrooms.sort_values("restroom_id").to_dict(orient="records"),
        "tickets": [asdict(ticket) for ticket in tickets],
    }
