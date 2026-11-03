"""Read and validate files used by the ingestion pipeline."""
import csv
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)


class FileImportError(Exception):
    """File reading or validation failed."""


def read_csv(path: Path | str, required_columns: list[str] | None = None) -> list[dict]:
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            if required_columns:
                missing = set(required_columns) - set(columns)
                if missing:
                    raise FileImportError(
                        f"CSV missing required columns in {path}: {sorted(missing)}"
                    )
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise FileImportError(f"Cannot read CSV {path}: {exc}") from exc

    if not rows:
        raise FileImportError(f"CSV is empty: {path}")

    logger.info("Read %d CSV rows: %s", len(rows), path.name)
    return rows

def read_json(path: Path | str):
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise FileImportError(
            f"Invalid JSON {path}, line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise FileImportError(f"Cannot read JSON {path}: {exc}") from exc

    logger.info("Read JSON: %s", path.name)
    return data

def read_xml(path: Path | str) -> list[dict[str, str | None]]:
    """Read a flat XML collection: root -> records -> text fields."""
    path = Path(path)
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise FileImportError(f"Invalid XML {path}: {exc}") from exc
    except OSError as exc:
        raise FileImportError(f"Cannot read XML {path}: {exc}") from exc

    records = []
    for record_element in tree.getroot():
        record = {child.tag: child.text for child in record_element}
        records.append(record)

    logger.info("Read %d XML records: %s", len(records), path.name)
    return records


def read_file(path: Path | str, required_columns=None):
    """Dispatch by extension, not by content detection. Excel returns a DataFrame."""
    path = Path(path)
    extension = path.suffix.lower()
    if extension == ".csv":
        return read_csv(path, required_columns=required_columns)
    if extension in {".json", ".geojson"}:
        return read_json(path)
    if extension == ".xml":
        return read_xml(path)
    if extension == ".xlsx":
        from .excel_handler import ExcelImportError, read_excel
        try:
            return read_excel(path, required_columns=required_columns)
        except ExcelImportError as exc:
            raise FileImportError(str(exc)) from exc
    raise FileImportError(f"Unsupported file extension: {extension or '(none)'}")
