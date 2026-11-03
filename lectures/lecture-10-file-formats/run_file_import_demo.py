"""Create and read three synthetic file examples from any working directory."""
import csv
import json
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.ingestion.file_import import FileImportError, read_csv, read_json, read_xml

SAMPLE_DIR = ROOT / "data/sample"


def build_samples():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = SAMPLE_DIR / "currency_demo_2026-01-01.csv"
    xml_path = SAMPLE_DIR / "weather_demo_2026-01-01.xml"
    json_path = SAMPLE_DIR / "earthquakes_demo_2026-01-01.geojson"
    # All values are synthetic. Preserve existing files.
    if not csv_path.exists():
        with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["currency_code", "rate", "rate_date"])
            writer.writeheader()
            writer.writerows([
                {"currency_code": "USD", "rate": "2.65", "rate_date": "2026-01-01"},
                {"currency_code": "EUR", "rate": "2.92", "rate_date": "2026-01-01"},
            ])
    if not xml_path.exists():
        root = ET.Element("forecasts")
        for city, temperature in [("Tbilisi", "28.3"), ("Batumi", "24.1")]:
            record = ET.SubElement(root, "forecast")
            ET.SubElement(record, "city").text = city
            ET.SubElement(record, "temperature_c").text = temperature
        ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    if not json_path.exists():
        sample = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": "demo-event",
                "properties": {"mag": 3.2, "place": "Demo location", "time": 1767225600000},
                "geometry": {"type": "Point", "coordinates": [44.75, 41.65, 8.2]},
            }],
        }
        json_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")
    return csv_path, xml_path, json_path


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    print("Synthetic examples; no API requests.")
    try:
        csv_path, xml_path, json_path = build_samples()
        rows = read_csv(csv_path, required_columns=["currency_code", "rate", "rate_date"])
        print(f"[OK] CSV: {len(rows)} rows; first: {rows[0]}")
        records = read_xml(xml_path)
        print(f"[OK] XML: {len(records)} records; first: {records[0]}")
        data = read_json(json_path)
        print(f"[OK] GeoJSON: {len(data['features'])} features")
    except FileImportError as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())