"""Run from any working directory. Warmed medians, five repetitions."""
import copy
import csv
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
import fastavro
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from src.ingestion import format_writer as fw
from generate_synthetic_data import (generate_weather_records,
                                     generate_currency_records,
                                     generate_seismic_records)

OUT = ROOT / 'data/format_comparison'


def median_call(fn, repetitions=5):
    fn()  # Exclude first-import and initial setup costs.
    samples = []
    for _ in range(repetitions):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples), samples


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results, datasets = [], {}
    for name, gen in [('weather', generate_weather_records),
                      ('currency', generate_currency_records),
                      ('seismic', generate_seismic_records)]:
        records = gen()
        assert records == gen() and len(records) == 10_000
        datasets[name] = records
        schema = fw.avro_schema(name.title() + 'Record', records)
        (OUT / f'{name}.avsc').write_text(json.dumps(schema, indent=2))
        for fmt in ['json', 'csv', 'parquet', 'avro']:
            path = OUT / f'{name}.{fmt}'
            writer = getattr(fw, 'write_' + fmt)
            reader = getattr(fw, 'read_' + fmt)
            write = lambda: writer(records, path, schema) if fmt == 'avro' else writer(records, path)
            read = lambda: reader(path, schema)
            wt, ws = median_call(write)
            rt, rs = median_call(read)
            restored = read()
            assert restored == records, (name, fmt, 'round-trip mismatch')
            assert all(type(v) is type(restored[0][k]) for k, v in records[0].items())
            result = dict(dataset=name, format=fmt, rows=len(restored), bytes=path.stat().st_size,
                          write_ms=wt * 1000, read_ms=rt * 1000, validated=True,
                          write_samples_ms=[x*1000 for x in ws], read_samples_ms=[x*1000 for x in rs])
            results.append(result)
            print(f'{name:9} {fmt:7} {result["bytes"]:9} B write={wt*1000:8.3f} ms read={rt*1000:8.3f} ms PASS')

    weather = datasets['weather']
    v1 = fw.avro_schema('WeatherRecord', weather)
    v2 = copy.deepcopy(v1)
    v2['fields'].append({'name': 'wind_speed_kmh', 'type': 'double', 'default': 0.0})
    old_as_new = fw.read_avro(OUT / 'weather.avro', v2)
    assert all(r['wind_speed_kmh'] == 0.0 for r in old_as_new)
    new_records = [dict(r, wind_speed_kmh=12.5) for r in weather[:100]]
    fw.write_avro(new_records, OUT / 'weather_v2.avro', v2)
    assert fw.read_avro(OUT / 'weather_v2.avro', v1) == weather[:100]
    assert fw.read_avro(OUT / 'weather_v2.avro', v2) == new_records
    evolution = {'old_read_by_new_default_rows': len(old_as_new),
                 'new_read_by_old_rows': len(new_records), 'default': 0.0, 'validated': True}
    print('AVRO EVOLUTION: V1 -> V2 defaults=10000; V2 -> V1 ignores new field=100; PASS')

    # Old and new partitions differ in the optional wind column.
    partition_root = OUT / 'partitioned_weather'
    partition_root.mkdir(exist_ok=True)
    groups = {}
    for r in weather:
        year, month = r['forecast_time'][:7].split('-')
        groups.setdefault((year, month), []).append(r)
    for index, ((year, month), group) in enumerate(sorted(groups.items())):
        enriched = [dict(r, wind_speed_kmh=12.5) for r in group] if index % 2 else group
        target = partition_root / f'year={year}' / f'month={month}'
        target.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(enriched), target / 'part.parquet', compression='snappy')
    schemas = [pq.ParquetFile(p).schema_arrow for p in partition_root.rglob('*.parquet')]
    unified = pa.unify_schemas(schemas).append(pa.field('year', pa.int32())).append(pa.field('month', pa.int32()))
    dataset = ds.dataset(partition_root, format='parquet', partitioning='hive', schema=unified)
    all_rows = dataset.to_table().to_pylist()
    assert len(all_rows) == len(weather)
    by_time = {r['forecast_time']: r for r in weather}
    assert all({k: r[k] for k in weather[0]} == by_time[r['forecast_time']] for r in all_rows)
    missing = sum(r['wind_speed_kmh'] is None for r in all_rows)
    assert 0 < missing < len(weather)
    assert set(r['wind_speed_kmh'] for r in all_rows) == {None, 12.5}
    filt = (ds.field('year') == 2026) & (ds.field('month') == 8)
    all_fragments, selected = list(dataset.get_fragments()), list(dataset.get_fragments(filter=filt))
    selected_rows = dataset.to_table(filter=filt).to_pylist()
    expected = [r for r in weather if r['forecast_time'].startswith('2026-08')]
    assert len(selected_rows) == len(expected)
    assert all(r['forecast_time'].startswith('2026-08') for r in selected_rows)
    total_bytes = sum(Path(f.path).stat().st_size for f in all_fragments)
    selected_bytes = sum(Path(f.path).stat().st_size for f in selected)
    full_ms, _ = median_call(lambda: dataset.to_table(columns=['temperature_c']))
    filter_ms, _ = median_call(lambda: dataset.to_table(columns=['temperature_c'], filter=filt))
    partition = dict(total_rows=len(all_rows), selected_rows=len(selected_rows),
                     fragments=len(all_fragments), selected_fragments=len(selected),
                     candidate_bytes=total_bytes, selected_candidate_bytes=selected_bytes,
                     null_wind_rows=missing, full_scan_ms=full_ms*1000,
                     filtered_scan_ms=filter_ms*1000, validated=True)
    print('PARTITION:', json.dumps(partition))

    compression = []
    for codec in ['snappy', 'gzip', 'zstd']:
        path = OUT / f'weather_{codec}.parquet'
        wt, _ = median_call(lambda: pq.write_table(pa.Table.from_pylist(weather), path, compression=codec))
        rt, _ = median_call(lambda: pq.read_table(path).to_pylist())
        assert pq.read_table(path).to_pylist() == weather
        compression.append(dict(codec=codec, bytes=path.stat().st_size, write_ms=wt*1000, read_ms=rt*1000))

    summary = dict(environment=dict(python=sys.version, platform=platform.platform(),
                    pyarrow=pa.__version__, fastavro=fastavro.__version__, repetitions=5,
                    seed=42, input_kind='synthetic'), benchmark=results,
                    avro_evolution=evolution, partitioning=partition, compression=compression)
    (OUT / 'results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    with open(OUT / 'results.csv', 'w', newline='', encoding='utf-8') as f:
        fields = ['dataset', 'format', 'rows', 'bytes', 'write_ms', 'read_ms', 'validated']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    print('ALL VALIDATIONS PASSED')


if __name__ == '__main__':
    main()
