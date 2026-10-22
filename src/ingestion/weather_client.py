import logging
from typing import Any, Optional

import requests

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

    def get_current_weather(self) -> dict[str, Any]:
        params = {
            "latitude": self.config.latitude,
            "longitude": self.config.longitude,
            "current": "temperature_2m,wind_speed_10m",
            "timezone": self.config.timezone,
        }

        logger.info(
            "მოთხოვნა Open-Meteo API-სთან: lat=%s, lon=%s",
            self.config.latitude,
            self.config.longitude,
        )

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

        except requests.exceptions.Timeout as exc:
            logger.error(
                "Timeout Open-Meteo API-სთან დაკავშირებისას"
            )
            raise WeatherAPIError(
                "API timeout-ით ჩავარდა"
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error(
                "Open-Meteo API-მ დააბრუნა შეცდომა: %s",
                exc,
            )
            raise WeatherAPIError(
                f"API request ჩავარდა: {exc}"
            ) from exc

        data = response.json()

        logger.info(
            "მიღებულია: temperature=%s°C, wind=%s km/h (დრო: %s)",
            data["current"]["temperature_2m"],
            data["current"]["wind_speed_10m"],
            data["current"]["time"],
        )

        return data