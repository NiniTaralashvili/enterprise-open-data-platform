"""Create a CSV example and demonstrate required-column validation."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.file_import import FileImportError, read_csv


def main():
    path = Path(__file__).resolve().parents[2] / "data/sample/currency_rates_demo.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["currency_code", "rate", "rate_date"])
            writer.writeheader()
            writer.writerows([
                {"currency_code": "USD", "rate": "2.65", "rate_date": "2026-01-01"},
                {"currency_code": "EUR", "rate": "2.92", "rate_date": "2026-01-01"},
            ])
    rows = read_csv(path, required_columns=["currency_code", "rate", "rate_date"])
    print("[OK] CSV rows:", len(rows))
    print("First row:", rows[0])
    print("Rate type:", type(rows[0]["rate"]).__name__)
    try:
        read_csv(path, required_columns=["currency_code", "nonexistent_column"])
    except FileImportError as exc:
        print("[OK] Expected validation error:", exc)
    else:
        raise AssertionError("Missing-column validation did not run")


if __name__ == "__main__":
    main()