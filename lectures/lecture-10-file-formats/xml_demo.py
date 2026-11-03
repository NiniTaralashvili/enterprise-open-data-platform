"""Demonstrate flat XML records and malformed XML handling offline."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.file_import import FileImportError, read_xml


def main():
    # Synthetic weather values, not an API response.
    sample = """<?xml version="1.0" encoding="utf-8"?>
<forecasts>
    <forecast>
        <city>Tbilisi</city>
        <temperature_c>28.3</temperature_c>
    </forecast>
    <forecast>
        <city>Batumi</city>
        <temperature_c>24.1</temperature_c>
    </forecast>
</forecasts>
"""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "weather.xml"
        path.write_text(sample, encoding="utf-8")
        rows = read_xml(path)
        assert rows == [
            {"city": "Tbilisi", "temperature_c": "28.3"},
            {"city": "Batumi", "temperature_c": "24.1"},
        ]
        print("[OK] XML records:", len(rows))
        print("First record:", rows[0])
        print("Temperature type:", type(rows[0]["temperature_c"]).__name__)

        path.write_text("<forecasts><forecast></forecasts>", encoding="utf-8")
        try:
            read_xml(path)
        except FileImportError as exc:
            print("[OK] Expected parse error:", exc)
        else:
            raise AssertionError("Malformed XML was accepted")


if __name__ == "__main__":
    main()