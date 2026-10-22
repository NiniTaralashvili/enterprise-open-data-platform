import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class WeatherConfig:
    latitude: float
    longitude: float
    timezone: str = "Asia/Tbilisi"
    timeout_seconds: int = 10


def load_weather_config() -> WeatherConfig:
    return WeatherConfig(
        latitude=float(os.getenv("WEATHER_LAT", "41.7151")),
        longitude=float(os.getenv("WEATHER_LON", "44.8271")),
    )