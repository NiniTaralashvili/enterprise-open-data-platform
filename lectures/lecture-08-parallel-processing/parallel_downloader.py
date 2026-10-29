import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.logging_config import setup_logging
from src.ingestion.weather_client import WeatherAPIError, WeatherClient


CITIES = [
    ("Tbilisi", 41.7151, 44.8271),
    ("Batumi", 41.6168, 41.6367),
    ("Kutaisi", 42.2679, 42.7000),
    ("Telavi", 41.9189, 45.4739),
]


def fetch_one(
    client: WeatherClient,
    city: str,
    lat: float,
    lon: float,
) -> tuple[str, Optional[dict]]:
    try:
        data = client.fetch(lat, lon, city)
        return city, data
    except WeatherAPIError as exc:
        print(f"[FAIL] {city}: {exc}")
        return city, None


def run_sequential(client: WeatherClient) -> float:
    start = time.perf_counter()

    for city, lat, lon in CITIES:
        fetch_one(client, city, lat, lon)

    return time.perf_counter() - start


def run_parallel(client: WeatherClient) -> float:
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(fetch_one, client, city, lat, lon)
            for city, lat, lon in CITIES
        ]

        for future in as_completed(futures):
            future.result()

    return time.perf_counter() - start


def main() -> int:
    setup_logging()
    client = WeatherClient()

    print("--- Sequential ---")
    seq_time = run_sequential(client)
    print(f"სულ დრო (sequential): {seq_time:.2f}s")

    print("\n--- Parallel: 4 threads ---")
    par_time = run_parallel(client)
    print(f"სულ დრო (parallel): {par_time:.2f}s")

    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x")

    return 0


if __name__ == "__main__":
    sys.exit(main())