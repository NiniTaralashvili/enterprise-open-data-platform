"""Offline Excel round-trip and two expected failures."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.excel_handler import ExcelImportError, read_excel, write_excel


def main():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "currency_demo.xlsx"
        original = pd.DataFrame({"currency_code": ["USD", "EUR"], "rate": [2.65, 2.92]})
        write_excel(original, path, sheet_name="Rates")
        result = read_excel(path, sheet_name="Rates", required_columns={"currency_code", "rate"})
        pd.testing.assert_frame_equal(original, result)
        print("[OK] Excel round-trip: data and column types match")
        print(result.to_string(index=False))
        print("Rate dtype:", result["rate"].dtype)
        for label, file, columns in [
            ("missing column", path, {"nonexistent_column"}),
            ("missing file", Path(directory) / "missing.xlsx", None),
        ]:
            try:
                read_excel(file, required_columns=columns)
            except ExcelImportError as exc:
                print(f"[OK] Expected {label}: {exc}")
            else:
                raise AssertionError(f"Expected failure: {label}")


if __name__ == "__main__":
    main()