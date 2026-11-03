# Lab 11 Modern Data Formats

Standalone lab extension for Enterprise Open Data Platform. All input data is
synthetic (seed 42); no API calls or database changes are performed.

## Run

```powershell
python -m pip install -r requirements.txt
python lectures/lecture-11-data-formats/compare_formats.py
```

The script resolves output paths relative to the repository root. It runs 12 format
round trips (three sources, 10,000 rows each), five warmed timing repetitions,
Avro evolution in both directions, mixed-schema Hive partitioning with explicit
schema union, pruning validation and three compression benchmarks.

Results: `data/format_comparison/results.json` and `results.csv`.
CSV read times include explicit type restoration. All formats materialize Python
records, so this is a full-record benchmark rather than a column-projection query.
Partition candidate bytes are file sizes, not measured physical disk IO.
Repeated reads benefit from OS cache. Run-to-run timings can vary.

Old Parquet partitions return null for the added optional field; Parquet does
not automatically supply the Avro-style default. Schema union is explicit.

## Report

`docs/lab11/Lab11_Nini_Taralashvili.docx` records the local execution before GitHub publication.
Run commands above from the repository root.
