"""Load Lab 4 sample data into PostgreSQL."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
SAMPLE_DIR = ROOT / "data" / "sample"


def read_sample(name):
    return json.loads(
        (SAMPLE_DIR / name).read_text(encoding="utf-8")
    )


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "enterprise_open_data"),
        user=os.getenv("POSTGRES_USER", "eodp_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        connect_timeout=10,
    )


def load_weather(cur):
    data = read_sample("weather_sample.json")
    hourly = data["hourly"]

    fields = (
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
    )

    if len({len(hourly[field]) for field in fields}) != 1:
        raise ValueError("Weather arrays have different lengths")

    rows = []
    for time, temp, humidity, rain, wind in zip(
        *(hourly[field] for field in fields)
    ):
        # This Tbilisi sample has no timezone in its timestamps.
        forecast_time = datetime.fromisoformat(time).replace(
            tzinfo=ZoneInfo("Asia/Tbilisi")
        )
        rows.append((
            data["city"],
            data["latitude"],
            data["longitude"],
            forecast_time,
            temp,
            humidity,
            rain,
            wind,
        ))

    cur.executemany(
        """
        INSERT INTO weather.forecasts
            (city, latitude, longitude, forecast_time,
             temperature_c, humidity_pct,
             precipitation_mm, wind_speed_kmh)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, forecast_time) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def load_currency(cur):
    data = read_sample("nbg_sample.json")
    attempted = 0

    for entry in data:
        rate_date = entry["date"][:10]

        for currency in entry["currencies"]:
            cur.execute(
                """
                INSERT INTO currency.currencies (code, name)
                VALUES (%s, %s)
                ON CONFLICT (code) DO NOTHING
                """,
                (currency["code"], currency["name"]),
            )
            cur.execute(
                """
                INSERT INTO currency.rates
                    (currency_code, quantity, rate, rate_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (currency_code, rate_date) DO NOTHING
                """,
                (
                    currency["code"],
                    currency["quantity"],
                    currency["rate"],
                    rate_date,
                ),
            )
            attempted += 1

    return attempted


def load_seismic(cur):
    data = read_sample("earthquakes_sample.geojson")
    rows = []

    for feature in data["features"]:
        props = feature["properties"]
        lon, lat, depth = feature["geometry"]["coordinates"]

        event_time = datetime.fromtimestamp(
            props["time"] / 1000,
            tz=timezone.utc,
        )

        rows.append((
            feature["id"],
            props["mag"],
            props["place"],
            event_time,
            lat,
            lon,
            depth,
        ))

    cur.executemany(
        """
        INSERT INTO seismic.events
            (event_id, magnitude, place, event_time,
             latitude, longitude, depth_km)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def main():
    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                weather = load_weather(cur)
                currency = load_currency(cur)
                seismic = load_seismic(cur)

        print(f"[OK] weather.forecasts: {weather} row(s) attempted")
        print(f"[OK] currency.rates: {currency} row(s) attempted")
        print(f"[OK] seismic.events: {seismic} row(s) attempted")
        print("Transaction committed.")

    except Exception as exc:
        print(f"[FAIL] შეცდომა, rollback: {exc}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
