# Lab 6 Data modeling

Prerequisite: Labs 3–5 and air_quality.measurements with the sample data.

SQL files are in sql/. On a fresh analytics schema, run in this order:

1. 004_dim_date.sql
2. 005_dim_location.sql
3. 006_dim_currency.sql
4. 007_fact_tables.sql
5. 010_location_scd2.sql
6. 008_populate_facts.sql
7. 011_air_quality.sql
8. 009_cross_domain_analysis.sql

SCD2 setup runs before the loaders because the loaders select the location version valid on the event date.

Example from the repository root (replace FILE.sql with a filename):

```bash
docker exec -i eodp-postgres psql -v ON_ERROR_STOP=1 -U eodp_user -d enterprise_open_data < lectures/lecture-06-data-modeling/sql/FILE.sql
python3 src/modeling/scd2.py
```

008 is an initial snapshot loader: it refuses to run if any of its three destination tables already contains data. This prevents accidental duplicate loads; it is not an incremental ETL pipeline. Do not rerun 008 on the already populated lab database.

011 deduplicates air quality records by measurement_id. Existing records are not updated.
005 seeds current cities. It does not create SCD2 history or detect changed attributes.
The Python SCD2 example works in memory and does not persist history to PostgreSQL.
Location intervals must not overlap for a city; the lab SQL enforces one current version and valid individual date ranges, but does not enforce all historical non-overlap cases.

Documentation and AI comparison: docs/star_schema.md.

Validation: the scripts were executed against a temporary schema in one transaction, then rolled back. Counts: weather 24, currency 23, seismic 3, air quality 4. The combined report returned 2026-08-27, 24.45, 2.6512, 1, 12.63, 21.75.
