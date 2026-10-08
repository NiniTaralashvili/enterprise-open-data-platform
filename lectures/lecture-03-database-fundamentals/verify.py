"""Verify the PostgreSQL connection and Lab 3 schemas."""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

EXPECTED_SCHEMAS = ["weather", "currency", "seismic"]


def main():
    passed = 0
    total = 1 + len(EXPECTED_SCHEMAS)

    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "enterprise_open_data"),
            user=os.getenv("POSTGRES_USER", "eodp_user"),
            password=os.getenv("POSTGRES_PASSWORD"),
            connect_timeout=10,
        )
    except psycopg2.Error as exc:
        print(f"[FAIL] დაკავშირება ვერ მოხერხდა: {exc}")
        return 1

    try:
        print("[OK] დაკავშირება Postgres-თან წარმატებულია")
        passed += 1

        with conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata;"
            )
            existing = {row[0] for row in cur.fetchall()}

        for schema in EXPECTED_SCHEMAS:
            if schema in existing:
                print(f"[OK] schema '{schema}' არსებობს")
                passed += 1
            else:
                print(f"[FAIL] schema '{schema}' არ მოიძებნა")
    except psycopg2.Error as exc:
        print(f"[FAIL] შემოწმება ვერ შესრულდა: {exc}")
        return 1
    finally:
        conn.close()

    if passed == total:
        print(f"\nყველა შემოწმება გავლილია ({passed}/{total})")
        return 0

    print(f"\nშემოწმებები გავლილია: {passed}/{total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
