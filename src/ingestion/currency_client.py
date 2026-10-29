import logging
from datetime import date as date_type
from math import isfinite
from typing import Any, Optional

import requests

from .retry import is_retryable_request_error, retry_with_backoff

logger = logging.getLogger(__name__)
BASE_URL = 'https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/'


class CurrencyAPIError(Exception):
    """NBG request or response error."""


class CurrencyClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    @retry_with_backoff(
        (requests.exceptions.RequestException,),
        should_retry=is_retryable_request_error,
    )
    def _get(self, params: dict) -> requests.Response:
        response = requests.get(BASE_URL, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response

    def get_rates(self, on_date: Optional[date_type] = None) -> dict[str, Any]:
        params = {'date': on_date.isoformat()} if on_date else {}
        logger.info('NBG request date=%s', on_date or 'latest')
        try:
            response = self._get(params)
        except requests.exceptions.RequestException as exc:
            logger.error('NBG request failed finally: %s', exc)
            raise CurrencyAPIError(f'NBG request failed: {exc}') from exc
        try:
            data = response.json()
            if not isinstance(data, list) or not data:
                raise ValueError('Expected a nonempty list')
            entry = data[0]
            date_type.fromisoformat(entry['date'][:10])
            currencies = entry['currencies']
            if not isinstance(currencies, list) or not currencies:
                raise ValueError('Expected currencies')
            codes = set()
            for currency in currencies:
                code = currency['code']
                if not isinstance(code, str) or len(code) != 3 or code in codes:
                    raise ValueError('Invalid or duplicate currency code')
                codes.add(code)
                for field in ('rate', 'quantity'):
                    value = currency[field]
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise ValueError(f'Invalid {field}')
                    if not isfinite(value) or value <= 0:
                        raise ValueError(f'Invalid {field}')
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise CurrencyAPIError(f'Unexpected NBG response: {exc}') from exc
        logger.info('Received %d currencies, source date=%s', len(currencies), entry['date'])
        return entry
