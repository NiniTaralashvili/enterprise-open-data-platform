import logging
from typing import Any, Optional

import requests

from .retry import is_retryable_request_error, retry_with_backoff

from .config import WeatherConfig, load_weather_config


logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAPIError(Exception):
    """ამინდის API-სთან დაკავშირებული შეცდომა."""


class WeatherClient:
    def __init__(
        self,
        config: Optional[WeatherConfig] = None,
    ) -> None:
        self.config = config or load_weather_config()

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
        label: str = "",
    ) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
            "timezone": self.config.timezone,
        }

        logger.info(
            "მოთხოვნა Open-Meteo API-სთან [%s]: lat=%s, lon=%s",
            label or "?",
            latitude,
            longitude,
        )

        try:
            response = self._get(params)

        except requests.exceptions.Timeout as exc:
            logger.error(
                "[%s] Timeout Open-Meteo API-სთან დაკავშირებისას",
                label,
            )
            raise WeatherAPIError(
                f"[{label}] API timeout-ით ჩავარდა"
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error(
                "[%s] Open-Meteo API-მ დააბრუნა შეცდომა: %s",
                label,
                exc,
            )
            raise WeatherAPIError(
                f"[{label}] API request ჩავარდა: {exc}"
            ) from exc

        try:
            data = response.json()
            current = data["current"]
            for field in ("temperature_2m", "wind_speed_10m", "time"):
                if current[field] is None:
                    raise ValueError(f"Missing current value: {field}")
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherAPIError(f"Unexpected weather response: {exc}") from exc

        logger.info(
            "[%s] მიღებულია: temperature=%s°C, wind=%s km/h (დრო: %s)",
            label,
            data["current"]["temperature_2m"],
            data["current"]["wind_speed_10m"],
            data["current"]["time"],
        )

        return data

    def get_current_weather(self) -> dict[str, Any]:
        return self.fetch(
            self.config.latitude,
            self.config.longitude,
            label="default",
        )
