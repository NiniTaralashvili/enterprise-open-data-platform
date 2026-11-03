"""Round-trip existing AirQualityClient measurements through four file formats."""
import csv
import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import pandas as pd
from .file_import import FileImportError, read_file
from .excel_handler import write_excel

FIELDS = ["city", "latitude", "longitude", "measured_at", "pm2_5_ug_m3", "pm10_ug_m3", "source", "data_kind"]
NUMBERS = ["latitude", "longitude", "pm2_5_ug_m3", "pm10_ug_m3"]


def normalize_measurements(rows):
    normalized = []
    for row in rows:
        try:
            record = {field: row[field] for field in FIELDS}
            for field in ["city", "source", "data_kind"]:
                if not isinstance(record[field], str) or not record[field].strip():
                    raise ValueError(f"Invalid {field}")
            for field in NUMBERS:
                if isinstance(record[field], bool):
                    raise ValueError(f"Invalid {field}")
                record[field] = float(record[field])
                if not math.isfinite(record[field]):
                    raise ValueError(f"Non-finite {field}")
            if not -90 <= record["latitude"] <= 90 or not -180 <= record["longitude"] <= 180:
                raise ValueError("Invalid coordinates")
            if record["pm2_5_ug_m3"] < 0 or record["pm10_ug_m3"] < 0:
                raise ValueError("Negative PM value")
            timestamp = record["measured_at"]
            if not isinstance(timestamp, datetime):
                timestamp = datetime.fromisoformat(str(timestamp))
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Timestamp must include a timezone")
            record["measured_at"] = timestamp.isoformat()
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise FileImportError(f"Invalid air quality record: {exc}") from exc
        normalized.append(record)
    if not normalized:
        raise FileImportError("No air quality records")
    return normalized


def export_measurements(rows, directory: Path):
    rows = normalize_measurements(rows)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {ext: directory / f"air_quality.{ext}" for ext in ["csv", "json", "xml", "xlsx"]}
    if any(path.exists() for path in paths.values()):
        raise FileImportError("Output files already exist; choose a new directory")
    with paths["csv"].open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    paths["json"].write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    xml_root = ET.Element("measurements")
    for row in rows:
        record = ET.SubElement(xml_root, "measurement")
        for field in FIELDS:
            ET.SubElement(record, field).text = str(row[field])
    ET.ElementTree(xml_root).write(paths["xml"], encoding="utf-8", xml_declaration=True)
    write_excel(pd.DataFrame(rows), paths["xlsx"])
    return paths


def import_measurements(path):
    data = read_file(path, required_columns=FIELDS)
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    if not isinstance(data, list):
        raise FileImportError("Expected a list of air quality records")
    return normalize_measurements(data)


def compute_air_quality_stats(rows):
    df = pd.DataFrame(normalize_measurements(rows))
    return df.groupby("city")[["pm2_5_ug_m3", "pm10_ug_m3"]].agg(["mean", "min", "max"])
