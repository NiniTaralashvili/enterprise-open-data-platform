"""Demonstrate JSON reading and a malformed JSON error offline."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ingestion.file_import import FileImportError, read_json


def main():
    # Synthetic data, not an API response.
    sample = {
        "source": "demo",
        "events": [{"magnitude": 3.2, "coordinates": [44.75, 41.65, 8.2]}],
        "reviewed": True,
        "note": None,
    }
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.json"
        path.write_text(json.dumps(sample), encoding="utf-8-sig")
        data = read_json(path)
        assert data == sample
        print("[OK] JSON round-trip, including UTF-8 BOM")
        print("Root type:", type(data).__name__)
        print("Magnitude:", data["events"][0]["magnitude"])
        print("Magnitude type:", type(data["events"][0]["magnitude"]).__name__)
        print("Reviewed:", data["reviewed"], "Note:", data["note"])

        path.write_text('{"magnitude": 3.2,}', encoding="utf-8")
        try:
            read_json(path)
        except FileImportError as exc:
            print("[OK] Expected parse error:", exc)
        else:
            raise AssertionError("Malformed JSON was accepted")


if __name__ == "__main__":
    main()