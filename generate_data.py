"""Create the synthetic three-month airport washroom telemetry dataset."""

from pathlib import Path

from src.simulator import generate_telemetry


def main() -> None:
    output = Path("outputs/airport_washroom_telemetry_3_months.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    telemetry = generate_telemetry()
    telemetry.to_csv(output, index=False)
    print(f"Wrote {len(telemetry):,} rows to {output}")
    print(f"Time range: {telemetry['timestamp'].min()} to {telemetry['timestamp'].max()}")


if __name__ == "__main__":
    main()
