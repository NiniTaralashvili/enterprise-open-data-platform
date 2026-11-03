"""Excel input and output for the ingestion pipeline."""
from pathlib import Path
import pandas as pd


class ExcelImportError(Exception):
    """Excel reading or required-column validation failed."""


def read_excel(
    path: Path | str,
    sheet_name: str | int = 0,
    required_columns: set[str] | None = None,
) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except (OSError, ValueError) as exc:
        raise ExcelImportError(f"Cannot read Excel {path}: {exc}") from exc
    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ExcelImportError(f"Missing Excel columns: {sorted(missing)}")
    return df


def write_excel(
    df: pd.DataFrame, path: Path | str, sheet_name: str = "Sheet1"
) -> None:
    df.to_excel(path, sheet_name=sheet_name, index=False, engine="openpyxl")