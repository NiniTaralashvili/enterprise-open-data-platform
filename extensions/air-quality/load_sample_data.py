"""Load synthetic air-quality samples into PostgreSQL."""

import json
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main():
    path = ROOT / "data/sample/air_quality_sample.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if data["data_kind"] != "synthetic":
        raise ValueError("Expected synthetic sample data")

    if data["units"] != "ug/m3":
        raise ValueError("Expected concentrations in ug/m3")

    rows = []
    for record in data["records"]:
        measured_at = datetime.fromisoformat(record["measured_at"])

        if measured_at.tzinfo is None:
            raise ValueError("Timestamp must include a timezone")

        rows.append((
            data["city"],
            data["latitude"],
            data["longitude"],
            measured_at,
            record["pm2_5"],
            record["pm10"],
            data["source"],
            data["data_kind"],
        ))

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    )

    try:
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO air_quality.measurements (
                        city, latitude, longitude, measured_at,
                        pm2_5_ug_m3, pm10_ug_m3, source, data_kind
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (
                        latitude, longitude, measured_at,
                        source, data_kind
                    ) DO NOTHING
                    """,
                    rows,
                )
                inserted = cur.rowcount

        print(f"[OK] Attempted: {len(rows)}, inserted: {inserted}")
        print("Transaction committed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
