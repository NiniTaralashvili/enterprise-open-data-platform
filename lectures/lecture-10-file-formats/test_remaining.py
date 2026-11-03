"""Offline verification of aggregation, XSD, and extension dispatch."""
import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.ingestion.file_import import FileImportError, read_file
from src.ingestion.excel_handler import write_excel
from src.ingestion.pandas_transform import compute_daily_currency_stats
from src.ingestion.xml_validator import validate_xml


class RemainingTests(unittest.TestCase):
    def test_stats_against_stdlib(self):
        path = ROOT / "data/sample/currency_history_demo.csv"
        with path.open() as file:
            groups = {}
            for row in csv.DictReader(file):
                groups.setdefault(row["currency_code"], []).append(float(row["rate"]))
        actual = compute_daily_currency_stats(path).set_index("currency_code")
        self.assertEqual(set(actual.index), set(groups))
        for code, values in groups.items():
            self.assertAlmostEqual(actual.loc[code, "avg_rate"], round(sum(values)/len(values), 4))
            self.assertEqual(actual.loc[code, "min_rate"], min(values))
            self.assertEqual(actual.loc[code, "max_rate"], max(values))
        print(actual.to_string())

    def test_xsd_valid(self):
        validate_xml(ROOT / "data/sample/weather_demo_2026-01-01.xml", ROOT / "data/sample/weather_demo.xsd")

    def test_xsd_missing_field_and_wrong_type(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "weather.xml"
            for content in [
                "<forecasts><forecast><city>Tbilisi</city></forecast></forecasts>",
                "<forecasts><forecast><city>Tbilisi</city><temperature_c>warm</temperature_c></forecast></forecasts>",
            ]:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(FileImportError):
                        validate_xml(path, ROOT / "data/sample/weather_demo.xsd")

    def test_dispatch_all_formats_and_bom(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            csv_path = directory / "sample.CSV"
            csv_path.write_text("city,rate\nTbilisi,2.65\n", encoding="utf-8-sig")
            self.assertEqual(read_file(csv_path, ["city"])[0]["city"], "Tbilisi")
            json_path = directory / "sample.json"
            json_path.write_text('{"ok": true}', encoding="utf-8-sig")
            self.assertEqual(read_file(json_path), {"ok": True})
            self.assertEqual(len(read_file(ROOT / "data/sample/weather_demo_2026-01-01.xml")), 2)
            self.assertEqual(read_file(ROOT / "data/sample/earthquakes_demo_2026-01-01.geojson")["type"], "FeatureCollection")
            excel = directory / "sample.xlsx"
            df = pd.DataFrame({"rate": [2.65]})
            write_excel(df, excel)
            pd.testing.assert_frame_equal(read_file(excel, {"rate"}), df)
            with self.assertRaises(FileImportError):
                read_file(excel, {"missing"})

    def test_unknown_extensions(self):
        for path in ["sample.txt", "sample", "sample.zip"]:
            with self.subTest(path=path), self.assertRaisesRegex(FileImportError, "Unsupported"):
                read_file(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
