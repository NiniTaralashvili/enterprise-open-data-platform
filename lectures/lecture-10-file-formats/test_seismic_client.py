"""Offline checks for GeoJSON coordinates and millisecond timestamps."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ingestion.seismic_client import SeismicClient


class SeismicClientTests(unittest.TestCase):
    def fetch_sample(self):
        response = Mock()
        response.json.return_value = {
            "features": [{
                "id": "sample-event",
                "properties": {
                    "mag": 3.2,
                    "place": "Sample location",
                    "time": 1704067200123,
                },
                "geometry": {"coordinates": [44.75, 41.65, 8.2]},
            }]
        }
        with patch(
            "src.ingestion.seismic_client.requests.get",
            return_value=response,
        ) as get:
            events = SeismicClient().get_recent_events("2024-01-01", "2024-01-02")
        get.assert_called_once()
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(len(events), 1)
        return events[0]

    def test_coordinates_keep_longitude_latitude_order(self):
        event = self.fetch_sample()
        self.assertEqual(event["latitude"], 41.65)
        self.assertEqual(event["longitude"], 44.75)
        self.assertEqual(event["depth_km"], 8.2)

    def test_milliseconds_become_utc_datetime(self):
        event = self.fetch_sample()
        self.assertEqual(
            event["event_time"],
            datetime(2024, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc),
        )
        self.assertIs(event["event_time"].tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main(verbosity=2)