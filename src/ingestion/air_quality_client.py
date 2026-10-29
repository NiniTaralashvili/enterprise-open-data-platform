import logging
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Optional

import requests

from .retry import is_retryable_request_error, retry_with_backoff

from .air_quality_config import (
    AirQualityConfig,
    load_air_quality_config,
)


logger = logging.getLogger(__name__)

BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class AirQualityAPIError(Exception):
    """ჰაერის ხარისხის მონაცემების მიღების შეცდომა."""


class AirQualityClient:
    def __init__(
        self,
        config: Optional[AirQualityConfig] = None,
    ) -> None:
        self.config = config or load_air_quality_config()

    @retry_with_backoff(
        (requests.exceptions.RequestException,),
        should_retry=is_retryable_request_error,
    )
    def _get(self, params: dict) -> requests.Response:
        response = requests.get(
            BASE_URL, params=params, timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response

    def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
    ) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "pm2_5,pm10",
            "timezone": "UTC",
            "timeformat": "unixtime",
        }

        logger.info(
            "ჰაერის ხარისხის მოთხოვნა: city=%s, lat=%s, lon=%s",
            city,
            latitude,
            longitude,
        )

        try:
            response = self._get(params)

        except requests.exceptions.Timeout as exc:
            logger.error("ჰაერის ხარისხის API: timeout")
            raise AirQualityAPIError(
                "API-ის პასუხის ლოდინის დრო ამოიწურა"
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error("API მოთხოვნის შეცდომა: %s", exc)
            raise AirQualityAPIError(
                f"API მოთხოვნა ვერ შესრულდა: {exc}"
            ) from exc

        try:
            data = response.json()
            current = data["current"]

            pm2_5 = current["pm2_5"]
            pm10 = current["pm10"]

            for name, value in (("pm2_5", pm2_5), ("pm10", pm10)):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    or value < 0
                ):
                    raise ValueError(
                        f"{name}-ის არასწორი მნიშვნელობა: {value}"
                    )

            measured_at = datetime.fromtimestamp(
                current["time"],
                tz=timezone.utc,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
            OSError,
        ) as exc:
            logger.error("API პასუხის დამუშავების შეცდომა: %s", exc)
            raise AirQualityAPIError(
                f"API-მ მოულოდნელი მონაცემები დააბრუნა: {exc}"
            ) from exc

        measurement = {
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "measured_at": measured_at,
            "pm2_5_ug_m3": pm2_5,
            "pm10_ug_m3": pm10,
            "source": "open-meteo",
            "data_kind": "model",
        }

        logger.info(
            "მიღებულია: city=%s, PM2.5=%s, PM10=%s, time=%s",
            measurement["city"],
            pm2_5,
            pm10,
            measured_at.isoformat(),
        )

        return measurement

    def get_current_measurement(self) -> dict[str, Any]:
        return self.fetch(
            latitude=self.config.latitude,
            longitude=self.config.longitude,
            city=self.config.city,
        )
