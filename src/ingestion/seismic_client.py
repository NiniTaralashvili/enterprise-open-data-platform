import logging
from datetime import datetime, timezone

import requests

from .retry import is_retryable_request_error, retry_with_backoff

logger = logging.getLogger(__name__)
BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
GEORGIA_BBOX = {
    "minlatitude": 41.0,
    "maxlatitude": 43.6,
    "minlongitude": 40.0,
    "maxlongitude": 46.7,
}


class SeismicAPIError(Exception):
    """USGS request or response error."""


class SeismicClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    @retry_with_backoff(
        (requests.exceptions.RequestException,),
        max_attempts=3,
        should_retry=is_retryable_request_error,
    )
    def _get(self, params: dict) -> requests.Response:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response

    def get_recent_events(
        self,
        start_date: str,
        end_date: str,
        min_magnitude: float = 1.5,
    ) -> list[dict]:
        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": min_magnitude,
            "orderby": "time",
            **GEORGIA_BBOX,
        }

        logger.info(
            "USGS მოთხოვნა: %s — %s",
            start_date,
            end_date,
        )

        try:
            response = self._get(params)
        except requests.exceptions.RequestException as exc:
            raise SeismicAPIError(
                f"USGS მოთხოვნა ჩავარდა: {exc}"
            ) from exc

        try:
            data = response.json()
            events = []

            for feature in data["features"]:
                props = feature["properties"]
                lon, lat, depth = feature["geometry"]["coordinates"]

                events.append({
                    "event_id": feature["id"],
                    "magnitude": props["mag"],
                    "place": props["place"],
                    "event_time": datetime.fromtimestamp(
                        props["time"] / 1000,
                        tz=timezone.utc,
                    ),
                    "latitude": lat,
                    "longitude": lon,
                    "depth_km": depth,
                })
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise SeismicAPIError(
                f"USGS პასუხის დამუშავება ვერ მოხერხდა: {exc}"
            ) from exc

        logger.info("მიღებულია %d მიწისძვრა", len(events))
        return events