import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class AirQualityConfig:
    city: str
    latitude: float
    longitude: float
    timeout_seconds: int = 10


def load_air_quality_config() -> AirQualityConfig:
    return AirQualityConfig(
        city=os.getenv("AIR_CITY", "Tbilisi"),
        latitude=float(os.getenv("AIR_LAT", "41.7151")),
        longitude=float(os.getenv("AIR_LON", "44.8271")),
        timeout_seconds=int(os.getenv("AIR_TIMEOUT", "10")),
    )