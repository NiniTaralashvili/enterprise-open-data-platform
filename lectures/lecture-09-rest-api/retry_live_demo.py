"""Simulated network errors with real backoff sleeps (about 6 seconds total)."""
import sys
import time
from pathlib import Path
from unittest import mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.air_quality_client import AirQualityAPIError, AirQualityClient
from src.ingestion.logging_config import setup_logging


def main():
    setup_logging()
    reply = mock.Mock()
    reply.json.return_value = {'current': {'pm2_5': 9.0, 'pm10': 11.4, 'time': 1793268000}}
    start = time.perf_counter()
    with mock.patch('requests.get', side_effect=[
        requests.exceptions.ConnectionError('simulated glitch'),
        requests.exceptions.ConnectionError('simulated glitch'), reply,
    ]) as get:
        result = AirQualityClient().get_current_measurement()
        print(f"[OK] Flaky: {get.call_count} attempts, {time.perf_counter() - start:.2f}s; "
              f"PM2.5={result['pm2_5_ug_m3']} (mock data)")
    start = time.perf_counter()
    with mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError('permanent glitch')) as get:
        try:
            AirQualityClient().get_current_measurement()
        except AirQualityAPIError:
            print(f'[OK] AirQualityAPIError caught: {get.call_count} attempts, '
                  f'{time.perf_counter() - start:.2f}s')
        else:
            raise AssertionError('Expected AirQualityAPIError')


if __name__ == '__main__':
    main()
