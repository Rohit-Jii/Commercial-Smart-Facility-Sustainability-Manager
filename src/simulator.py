"""Synthetic five-minute airport washroom telemetry generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Restroom:
    restroom_id: str
    usage_multiplier: float
    criticality: int


RESTROOMS: tuple[Restroom, ...] = (
    Restroom("R001", 1.30, 3),
    Restroom("R002", 1.15, 2),
    Restroom("R003", 1.25, 3),
    Restroom("R004", 0.95, 1),
    Restroom("R005", 1.20, 3),
    Restroom("R006", 0.85, 2),
    Restroom("R007", 1.10, 3),
    Restroom("R008", 0.90, 1),
    Restroom("R009", 1.05, 2),
    Restroom("R010", 0.80, 1),
)


def _hourly_demand(hour_decimal: np.ndarray) -> np.ndarray:
    """Return a smooth airport-wide usage profile for a five-minute interval."""
    morning = 1.15 * np.exp(-0.5 * ((hour_decimal - 8.0) / 1.8) ** 2)
    midday = 0.70 * np.exp(-0.5 * ((hour_decimal - 13.0) / 2.4) ** 2)
    evening = 1.00 * np.exp(-0.5 * ((hour_decimal - 18.5) / 2.2) ** 2)
    return 0.14 + morning + midday + evening


def _interval_signal(
    length: int,
    rng: np.random.Generator,
    event_count: int,
    min_duration: int,
    max_duration: int,
    low: float,
    high: float,
) -> np.ndarray:
    """Create sustained incident values rather than isolated random spikes."""
    signal = np.zeros(length, dtype=float)
    safe_end = max(length - max_duration - 1, 1)
    for _ in range(event_count):
        start = int(rng.integers(0, safe_end))
        duration = int(rng.integers(min_duration, max_duration + 1))
        severity = float(rng.uniform(low, high))
        signal[start : min(start + duration, length)] = np.maximum(
            signal[start : min(start + duration, length)], severity
        )
    return signal


def _boolean_incidents(
    length: int,
    rng: np.random.Generator,
    event_count: int,
    min_duration: int,
    max_duration: int,
) -> np.ndarray:
    return _interval_signal(
        length, rng, event_count, min_duration, max_duration, 1.0, 1.0
    ).astype(bool)


def _future_window_max(values: pd.Series, periods: int) -> pd.Series:
    """Maximum value strictly after each sample through the given horizon."""
    shifted = values.shift(-1)
    return shifted.iloc[::-1].rolling(periods, min_periods=1).max().iloc[::-1]


def _future_window_min(values: pd.Series, periods: int) -> pd.Series:
    """Minimum value strictly after each sample through the given horizon."""
    shifted = values.shift(-1)
    return shifted.iloc[::-1].rolling(periods, min_periods=1).min().iloc[::-1]


def generate_telemetry(
    periods: int = 90 * 24 * 12,
    end: str | pd.Timestamp = "2026-09-14 21:55:00",
    seed: int = 42,
    restrooms: Iterable[Restroom] = RESTROOMS,
) -> pd.DataFrame:
    """Generate a reproducible three-month synthetic telemetry history.

    Rows represent a five-minute interval.  The last samples include active
    incidents so the dashboard always has meaningful alerts to demonstrate.
    """
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(end=pd.Timestamp(end), periods=periods, freq="5min")
    hour = timestamps.hour.to_numpy() + timestamps.minute.to_numpy() / 60
    weekday = timestamps.dayofweek.to_numpy()
    demand_curve = _hourly_demand(hour)
    weekend_factor = np.where(weekday >= 5, 0.82, 1.0)
    restroom_list = tuple(restrooms)
    frames: list[pd.DataFrame] = []

    for restroom in restroom_list:
        leak_lpm = _interval_signal(periods, rng, 3, 12, 120, 0.32, 1.10)
        missed_cleaning = _boolean_incidents(periods, rng, 4, 24, 72)
        forced_refill = _boolean_incidents(periods, rng, 2, 18, 48)

        # Persistent current incidents make the initial dashboard demonstrable.
        if restroom.restroom_id == "R003":
            leak_lpm[-48:] = 0.82  # continuous leak for the final four hours
        if restroom.restroom_id == "R007":
            missed_cleaning[-72:] = True  # missed cleaning for final six hours
        if restroom.restroom_id == "R006":
            forced_refill[-48:] = True

        expected_passengers = 13 * restroom.usage_multiplier * demand_curve * weekend_factor
        passengers = rng.poisson(np.maximum(expected_passengers, 0.05))
        flushes = rng.poisson(passengers * 0.43)
        taps = rng.poisson(passengers * 0.66)
        urinals = rng.poisson(passengers * 0.18)

        expected_flow_lpm = (flushes * 6.0 + taps * 1.25 + urinals * 2.2) / 5.0
        flow_lpm = np.maximum(
            expected_flow_lpm + leak_lpm + rng.normal(0, 0.035, periods), 0
        )
        pressure_bar = np.clip(
            3.25 - expected_flow_lpm * 0.010 - leak_lpm * 0.18 + rng.normal(0, 0.05, periods),
            1.5,
            4.0,
        )

        soap = float(rng.uniform(76, 96))
        sanitizer = float(rng.uniform(74, 95))
        paper = float(rng.uniform(72, 96))
        tank = float(rng.uniform(88, 100))
        bin_fill = float(rng.uniform(3, 16))
        cleanliness_debt = float(rng.uniform(0, 10))
        last_cleaned = timestamps[0] - pd.Timedelta(minutes=int(rng.integers(10, 130)))

        soap_values: list[float] = []
        sanitizer_values: list[float] = []
        paper_values: list[float] = []
        tank_values: list[float] = []
        bin_values: list[float] = []
        odor_values: list[float] = []
        humidity_values: list[float] = []
        temperature_values: list[float] = []
        co2_values: list[float] = []
        last_cleaned_values: list[pd.Timestamp] = []
        hygiene_breach: list[int] = []

        for index, timestamp in enumerate(timestamps):
            scheduled_cleaning = timestamp.minute == 0 and timestamp.hour in {0, 4, 8, 12, 16, 20}
            daily_restock = timestamp.minute == 0 and timestamp.hour == 2
            tank_replenish = timestamp.minute == 0 and timestamp.hour == 3

            if daily_restock:
                soap = float(rng.uniform(90, 100))
                sanitizer = float(rng.uniform(90, 100))
                paper = float(rng.uniform(90, 100))
            if tank_replenish:
                tank = float(rng.uniform(96, 100))
            if scheduled_cleaning and not missed_cleaning[index]:
                bin_fill = float(rng.uniform(2, 7))
                cleanliness_debt = float(rng.uniform(0, 4))
                last_cleaned = timestamp

            # Daily consumption is material, but a normally stocked washroom
            # should not exhaust every consumable before the next restock.
            soap -= taps[index] * 0.018
            sanitizer -= passengers[index] * 0.002
            paper -= (flushes[index] + taps[index]) * 0.012
            bin_fill += passengers[index] * 0.026 + rng.uniform(0.0, 0.09)
            cleanliness_debt += passengers[index] * 0.16 + bin_fill * 0.010
            tank -= flow_lpm[index] * 5 / 500.0

            if forced_refill[index]:
                soap = float(np.clip(soap, 8.0, 13.0))
                paper = float(np.clip(paper, 6.0, 11.0))

            soap = float(np.clip(soap, 0, 100))
            sanitizer = float(np.clip(sanitizer, 0, 100))
            paper = float(np.clip(paper, 0, 100))
            bin_fill = float(np.clip(bin_fill, 0, 100))
            tank = float(np.clip(tank, 0, 100))

            temperature = 22.7 + 1.6 * np.sin((hour[index] - 12) * np.pi / 12) + rng.normal(0, 0.35)
            humidity = np.clip(
                48 + passengers[index] * 0.58 + cleanliness_debt * 0.09 + rng.normal(0, 2.2),
                30,
                95,
            )
            odor = np.clip(
                45 + cleanliness_debt * 4.7 + bin_fill * 1.8 + passengers[index] * 1.2 + rng.normal(0, 8),
                10,
                1000,
            )
            co2 = np.clip(425 + passengers[index] * 15 + rng.normal(0, 28), 380, 1800)
            breach = int(
                bin_fill >= 82
                or odor >= 460
                or cleanliness_debt >= 74
                or (humidity >= 78 and passengers[index] >= 14)
            )

            soap_values.append(round(soap, 2))
            sanitizer_values.append(round(sanitizer, 2))
            paper_values.append(round(paper, 2))
            tank_values.append(round(tank, 2))
            bin_values.append(round(bin_fill, 2))
            odor_values.append(round(float(odor), 2))
            humidity_values.append(round(float(humidity), 2))
            temperature_values.append(round(float(temperature), 2))
            co2_values.append(round(float(co2), 2))
            last_cleaned_values.append(last_cleaned)
            hygiene_breach.append(breach)

        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "restroom_id": restroom.restroom_id,
                "criticality": restroom.criticality,
                "passenger_volume": passengers,
                "flow_rate_lpm": np.round(flow_lpm, 3),
                "expected_flow_lpm": np.round(expected_flow_lpm, 3),
                "water_pressure_bar": np.round(pressure_bar, 3),
                "flush_count": flushes,
                "tap_activations": taps,
                "urinal_use": urinals,
                "water_tank_level_pct": tank_values,
                "soap_level_pct": soap_values,
                "sanitizer_level_pct": sanitizer_values,
                "paper_towel_level_pct": paper_values,
                "bin_fill_pct": bin_values,
                "odor_voc_ppb": odor_values,
                "humidity_pct": humidity_values,
                "indoor_temperature_c": temperature_values,
                "co2_ppm": co2_values,
                "last_cleaned_at": last_cleaned_values,
                "leak_present": (leak_lpm > 0).astype(int),
                "missed_cleaning_event": missed_cleaning.astype(int),
                "hygiene_breach": hygiene_breach,
            }
        )
        frame["last_cleaned_minutes_ago"] = (
            (frame["timestamp"] - frame["last_cleaned_at"]).dt.total_seconds() / 60
        ).round().astype(int)
        frame["refill_required_now"] = (
            (frame[["soap_level_pct", "sanitizer_level_pct", "paper_towel_level_pct"]].min(axis=1) < 20)
        ).astype(int)
        frames.append(frame)

    telemetry = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "restroom_id"])
    telemetry["cleaning_needed_next_30min"] = telemetry.groupby("restroom_id")[
        "hygiene_breach"
    ].transform(lambda values: _future_window_max(values, 6).fillna(0).astype(int))

    future_soap = telemetry.groupby("restroom_id")["soap_level_pct"].transform(
        lambda values: _future_window_min(values, 96)
    )
    future_sanitizer = telemetry.groupby("restroom_id")["sanitizer_level_pct"].transform(
        lambda values: _future_window_min(values, 96)
    )
    future_paper = telemetry.groupby("restroom_id")["paper_towel_level_pct"].transform(
        lambda values: _future_window_min(values, 96)
    )
    telemetry["refill_required_within_shift"] = (
        pd.concat([future_soap, future_sanitizer, future_paper], axis=1).min(axis=1).fillna(100) < 20
    ).astype(int)

    telemetry["anomaly_type"] = np.select(
        [
            telemetry["leak_present"].eq(1),
            telemetry["missed_cleaning_event"].eq(1),
            telemetry["refill_required_now"].eq(1),
        ],
        ["leak", "missed_cleaning", "consumable_low"],
        default="normal",
    )
    return telemetry.reset_index(drop=True)
