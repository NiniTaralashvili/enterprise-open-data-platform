import functools
import logging
import time

import requests

logger = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def is_retryable_request_error(exc: BaseException) -> bool:
    if isinstance(exc, requests.exceptions.SSLError):
        return False
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        return (
            exc.response is not None
            and exc.response.status_code in RETRYABLE_STATUS_CODES
        )
    return False


def retry_with_backoff(
    exceptions: tuple,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    should_retry=None,
):
    """max_attempts counts the initial call; three attempts sleep only 1s and 2s."""
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError('max_attempts must be a positive integer')
    if not 0 <= base_delay <= max_delay < float('inf'):
        raise ValueError('delays must be finite and 0 <= base_delay <= max_delay')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if should_retry is not None and not should_retry(exc):
                        logger.error('Non-retryable failure: %s', exc)
                        raise
                    if attempt == max_attempts:
                        logger.error('Attempt #%d failed finally: %s', attempt, exc)
                        raise
                    logger.warning('Attempt #%d failed (%s), retry in %.1fs', attempt, exc, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
        return wrapper
    return decorator
