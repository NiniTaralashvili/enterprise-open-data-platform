import sys
from pathlib import Path
from pprint import pprint


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.logging_config import setup_logging
from src.ingestion.air_quality_client import (
    AirQualityAPIError,
    AirQualityClient,
)


def main() -> int:
    setup_logging()

    try:
        client = AirQualityClient()
        measurement = client.get_current_measurement()
    except AirQualityAPIError as exc:
        print(f"[FAIL] {exc}")
        return 1

    pprint(measurement)
    print("[OK] ჰაერის ხარისხის მონაცემები მიღებულია")
    return 0


if __name__ == "__main__":
    sys.exit(main())