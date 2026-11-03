"""Deterministic synthetic fixtures, never live observations."""
import random
from datetime import datetime, timedelta, timezone


def generate_weather_records(n=10_000):
    rng = random.Random(42)
    base = datetime(2026, 8, 1, tzinfo=timezone.utc)
    return [{'city': rng.choice(['Tbilisi', 'Batumi', 'Kutaisi', 'Telavi']),
             'latitude': round(rng.uniform(41, 43), 4),
             'longitude': round(rng.uniform(41, 46), 4),
             'forecast_time': (base + timedelta(hours=i)).isoformat(),
             'temperature_c': round(rng.uniform(-5, 35), 2),
             'humidity_pct': round(rng.uniform(20, 90), 2)} for i in range(n)]


def generate_currency_records(n=10_000):
    rng = random.Random(42)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [{'currency_code': rng.choice(['USD', 'EUR', 'GBP', 'JPY']),
             'rate': round(rng.uniform(1, 4), 4), 'quantity': 1,
             'rate_date': (base + timedelta(days=i // 4)).date().isoformat()}
            for i in range(n)]


def generate_seismic_records(n=10_000):
    rng = random.Random(42)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [{'event_id': f'synthetic-{i:06d}',
             'magnitude': round(rng.uniform(0, 5), 2),
             'place': rng.choice(['Georgia sample A', 'Georgia sample B']),
             'event_time': (base + timedelta(hours=i)).isoformat(),
             'latitude': round(rng.uniform(41, 43), 4),
             'longitude': round(rng.uniform(40, 46), 4),
             'depth_km': round(rng.uniform(1, 50), 2)} for i in range(n)]
