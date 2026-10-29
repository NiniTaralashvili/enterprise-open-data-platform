"""Lab 9 offline verification and visible retry demonstration."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.air_quality_client import AirQualityAPIError, AirQualityClient
from src.ingestion.currency_client import CurrencyAPIError, CurrencyClient
from src.ingestion.logging_config import setup_logging
from src.ingestion.retry import is_retryable_request_error, retry_with_backoff
from src.ingestion.weather_client import WeatherAPIError, WeatherClient


def response(payload):
    result = mock.Mock()
    result.json.return_value = payload
    return result


def http_error(status):
    result = requests.Response()
    result.status_code = status
    return requests.exceptions.HTTPError(f'HTTP {status}', response=result)


WEATHER = {'current': {'temperature_2m': 24.3, 'wind_speed_10m': 8.1, 'time': '2026-10-29T14:00'}}
AIR = {'current': {'pm2_5': 9.0, 'pm10': 11.4, 'time': 1793268000}}
RATES = [{'date': '2026-10-29T00:00:00.000Z', 'currencies': [
    {'code': 'USD', 'quantity': 1, 'rate': 2.5},
]}]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RetryTests(unittest.TestCase):
    def test_flaky_success_for_all_clients(self):
        cases = [
            (WeatherClient().get_current_weather, WEATHER),
            (AirQualityClient().get_current_measurement, AIR),
            (CurrencyClient().get_rates, RATES),
        ]
        for fetch, payload in cases:
            with self.subTest(client=fetch.__qualname__):
                with mock.patch('requests.get', side_effect=[
                    requests.exceptions.ConnectionError('simulated glitch'),
                    requests.exceptions.Timeout('simulated timeout'), response(payload),
                ]) as get, mock.patch('src.ingestion.retry.time.sleep') as sleep:
                    fetch()
                    self.assertEqual(get.call_count, 3)
                    self.assertEqual(sleep.call_args_list, [mock.call(1.0), mock.call(2.0)])

    def test_exhaustion_for_all_clients(self):
        for client, method, error in [
            (WeatherClient(), 'get_current_weather', WeatherAPIError),
            (AirQualityClient(), 'get_current_measurement', AirQualityAPIError),
            (CurrencyClient(), 'get_rates', CurrencyAPIError),
        ]:
            with self.subTest(client=type(client).__name__):
                with mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError('permanent glitch')) as get:
                    with mock.patch('src.ingestion.retry.time.sleep') as sleep:
                        with self.assertRaises(error):
                            getattr(client, method)()
                        self.assertEqual(get.call_count, 3)
                        self.assertEqual(sleep.call_count, 2)

    def test_http_policy(self):
        for status in (400, 401, 403, 404, 408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                with mock.patch('requests.get', side_effect=http_error(status)) as get:
                    with mock.patch('src.ingestion.retry.time.sleep'):
                        with self.assertRaises(CurrencyAPIError):
                            CurrencyClient().get_rates()
                        self.assertEqual(get.call_count, 1 if status < 408 or status == 404 else 3)

    def test_invalid_payloads_are_not_retried(self):
        for fetch, error, payload in [
            (CurrencyClient().get_rates, CurrencyAPIError, []),
            (CurrencyClient().get_rates, CurrencyAPIError, [{'date': 'bad', 'currencies': []}]),
            (WeatherClient().get_current_weather, WeatherAPIError, {}),
            (AirQualityClient().get_current_measurement, AirQualityAPIError,
             {'current': {'pm2_5': -1, 'pm10': 5, 'time': 0}}),
        ]:
            with mock.patch('requests.get', return_value=response(payload)) as get:
                with self.assertRaises(error):
                    fetch()
                self.assertEqual(get.call_count, 1)

    def test_invalid_json_is_wrapped(self):
        bad = response(None)
        bad.json.side_effect = requests.exceptions.JSONDecodeError('invalid', 'x', 0)
        for fetch, error in [
            (CurrencyClient().get_rates, CurrencyAPIError),
            (WeatherClient().get_current_weather, WeatherAPIError),
            (AirQualityClient().get_current_measurement, AirQualityAPIError),
        ]:
            with mock.patch('requests.get', return_value=bad):
                with self.assertRaises(error):
                    fetch()

    def test_delay_cap_and_metadata(self):
        work = mock.Mock(side_effect=ValueError('temporary'))

        @retry_with_backoff((ValueError,), max_attempts=5, max_delay=2)
        def sample():
            """Retained documentation."""
            return work()

        with mock.patch('src.ingestion.retry.time.sleep') as sleep:
            with self.assertRaises(ValueError):
                sample()
            self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2), mock.call(2), mock.call(2)])
        self.assertEqual(sample.__name__, 'sample')
        self.assertEqual(sample.__doc__, 'Retained documentation.')

    def test_multi_source_failure_isolation(self):
        runner = load_script('multi_source_fetch')
        for failed in ('weather', 'air', 'currency'):
            with self.subTest(failed=failed):
                with mock.patch.object(runner.WeatherClient, 'get_current_weather', return_value=WEATHER) as weather:
                    with mock.patch.object(runner.AirQualityClient, 'get_current_measurement', return_value={
                        'city': 'Tbilisi', 'pm2_5_ug_m3': 9, 'pm10_ug_m3': 11,
                        'measured_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
                    }) as air, mock.patch.object(runner.CurrencyClient, 'get_rates', return_value=RATES[0]) as currency:
                        {'weather': weather, 'air': air, 'currency': currency}[failed].side_effect = {
                            'weather': WeatherAPIError, 'air': AirQualityAPIError, 'currency': CurrencyAPIError,
                        }[failed]('simulated failure')
                        self.assertEqual(runner.main(), 1)
                        for fetch in (weather, air, currency):
                            fetch.assert_called_once()

    def test_tenacity_equivalence(self):
        alternative = load_script('tenacity_example')
        for status, attempts in ((404, 1), (503, 3)):
            with mock.patch('requests.get', side_effect=http_error(status)) as get:
                with mock.patch.object(alternative.get_with_tenacity.retry, 'sleep') as sleep:
                    with self.assertRaises(requests.exceptions.HTTPError):
                        alternative.get_with_tenacity('https://example.test')
                    self.assertEqual(get.call_count, attempts)
                    if attempts == 3:
                        self.assertEqual([float(c.args[0]) for c in sleep.call_args_list], [1, 2])


if __name__ == '__main__':
    setup_logging()
    unittest.main(verbosity=2)
