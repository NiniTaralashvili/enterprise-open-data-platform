"""Equivalent retry policy; reraise=True preserves the original request exception."""
import logging
import sys
from pathlib import Path

import requests
from tenacity import before_sleep_log, retry, retry_if_exception, stop_after_attempt, wait_exponential

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.retry import is_retryable_request_error


@retry(
    retry=retry_if_exception(is_retryable_request_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)
def get_with_tenacity(url, params=None, timeout=10):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response
