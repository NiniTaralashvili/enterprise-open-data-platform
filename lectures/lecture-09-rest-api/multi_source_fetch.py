"""Fetch three independent sources; one source failure does not stop the others."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ingestion.logging_config import setup_logging
from src.ingestion.weather_client import WeatherAPIError, WeatherClient
from src.ingestion.air_quality_client import AirQualityAPIError, AirQualityClient
from src.ingestion.currency_client import CurrencyAPIError, CurrencyClient


def main() -> int:
    setup_logging()
    exit_code = 0
    try:
        weather = WeatherClient().get_current_weather()
        print(f"[OK] Weather: {weather['current']['temperature_2m']} C")
    except (WeatherAPIError, ValueError) as exc:
        print(f'[FAIL] Weather: {exc}')
        exit_code = 1

    try:
        air = AirQualityClient().get_current_measurement()
        print(f"[OK] Air {air['city']}: PM2.5={air['pm2_5_ug_m3']}, "
              f"PM10={air['pm10_ug_m3']} ug/m3; {air['measured_at'].isoformat()}")
    except (AirQualityAPIError, ValueError) as exc:
        print(f'[FAIL] Air quality: {exc}')
        exit_code = 1

    try:
        rates = CurrencyClient().get_rates()
        usd = next((c for c in rates['currencies'] if c['code'] == 'USD'), None)
        if usd is None:
            raise CurrencyAPIError('USD is missing')
        print(f"[OK] 1 USD = {usd['rate'] / usd['quantity']:.4f} GEL; "
              f"source date={rates['date']}")
    except CurrencyAPIError as exc:
        print(f'[FAIL] Currency: {exc}')
        exit_code = 1
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
