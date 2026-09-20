# Airport washroom monitoring prototype

This project simulates five-minute IoT telemetry for 10 airport washrooms over the last 90 days. It uses no terminal, gate, arrivals, or zone dimensions.

It implements three operational outputs:

- Continuous leak detection from excess flow that persists for 20 minutes.
- A logistic-regression prediction of a hygiene breach in the next 30 minutes.
- A Ridge-regression forecast of normal water demand for the next day and week.

## Setup

Python 3.11+ is recommended. Install the small dependency set if it is not already available:

```powershell
python -m pip install -r requirements.txt
```

## Run the project

Generate the synthetic three-month history:

```powershell
python generate_data.py
```

Train the cleaning model and prepare the operational outputs:

```powershell
python run_pipeline.py
```

Serve the dashboard from the project root:

```powershell
python -m http.server 8000
```

Then open [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/).

## Main outputs

- `outputs/airport_washroom_telemetry_3_months.csv` — 259,200 synthetic readings at five-minute resolution.
- `outputs/telemetry_with_predictions.csv` — input history plus leak, cleaning, and refill risk outputs.
- `outputs/water_demand_forecast_7_days.csv` — 7-day five-minute water-demand forecast.
- `outputs/training_data.csv` — first 80% of each washroom's timeline; the only data used to train models.
- `outputs/test_data.csv` — held-out final 20% of each washroom's timeline.
- `outputs/live_test_stream.json` — browser-ready copy of the held-out sensor records.
- `outputs/live_models.json` — exported model coefficients used for browser-side scoring.
- `outputs/dashboard_data.json` — compact initial dashboard state, based only on training data.
- `outputs/model_metrics.json` — held-out test metrics for the hygiene prediction model.

The generator uses a fixed seed so results are reproducible. It includes regular daily usage patterns, sustained low-flow leaks, missed-cleaning periods, low-consumable events, and active demonstration alerts at the end of the history.

## Train/test split and live playback

The pipeline splits each washroom's timeline chronologically: the first 80% trains the models and the final 20% is never used for training. The dashboard's **Play test-data feed** button selects a random held-out record every second. Each received record is scored live in the browser for leak risk, cleaning risk, refill risk, and predicted five-minute water demand. Press the button again to pause the feed.

## Detection logic in this first version

The leak score is deliberately rule-based: it compares observed flow with the flow expected from flushes, taps, and urinal use, then checks whether excess flow persisted over four five-minute readings. This is safer and easier to explain for a first prototype than an opaque anomaly-only model.

The cleaning classifier learns the synthetic `cleaning_needed_next_30min` label from current usage, consumables, odor, bin fill, humidity, CO₂, elapsed time since cleaning, and washroom criticality. The forecast model excludes known synthetic leak windows so it predicts normal water demand rather than incident-related consumption.
