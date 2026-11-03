"""Use the existing AirQualityClient with the Lab 10 readers. Default: offline."""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.ingestion.air_quality_client import AirQualityClient
from src.ingestion.air_quality_files import export_measurements, import_measurements, normalize_measurements, compute_air_quality_stats
from src.ingestion.file_import import FileImportError


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Fetch one current model measurement from Open-Meteo")
    args=parser.parse_args()
    if args.live:
        rows=[AirQualityClient().get_current_measurement()]
        print("LIVE Open-Meteo model data; one observation, not historical statistics.")
    else:
        # Exercise the real client parser with a synthetic HTTP response.
        rows=[]
        with patch("src.ingestion.air_quality_client.requests.get") as get:
            for hour, pm25, pm10 in [(0,10,20),(1,14,28)]:
                get.return_value.json.return_value={"current": {
                    "time": int(datetime(2026,1,1,hour,tzinfo=timezone.utc).timestamp()),
                    "pm2_5":pm25, "pm10":pm10,
                }}
                rows.append(AirQualityClient().fetch(41.7151,44.8271,"Tbilisi"))
            assert get.call_count==2
        print("OFFLINE synthetic observations through the existing AirQualityClient.")
    expected=normalize_measurements(rows)
    with TemporaryDirectory() as directory:
        paths=export_measurements(rows,Path(directory))
        for extension,path in paths.items():
            actual=import_measurements(path)
            assert actual==expected, extension
            print(f"[OK] {extension}: {len(actual)} records, values and timestamps preserved")
    stats=compute_air_quality_stats(rows)
    if not args.live:
        assert stats.loc["Tbilisi",("pm2_5_ug_m3","mean")]==12
        assert stats.loc["Tbilisi",("pm10_ug_m3","mean")]==24
    print(stats.to_string())
    for field,value in [("pm2_5_ug_m3",-1),("pm10_ug_m3",float("nan")),("measured_at","2026-01-01")]:
        invalid=dict(rows[0],**{field:value})
        try:
            normalize_measurements([invalid])
        except FileImportError:
            print(f"[OK] Rejected invalid {field}")
        else:
            raise AssertionError(f"Accepted invalid {field}")


if __name__=="__main__":
    main()
