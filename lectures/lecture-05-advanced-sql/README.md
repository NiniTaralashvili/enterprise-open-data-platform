# Lab 5: Advanced SQL

## Execution order

Run the SQL files against enterprise_open_data:

1. sql/003_seed_historical_data.sql
2. sql/004_analytical_queries.sql
3. sql/005_views.sql
4. sql/006_explain.sql

The historical data is synthetic educational sample data.
The seed skips duplicates using ON CONFLICT DO NOTHING.

## Verified results

- Historical seed inserted 18 currency rates and 20 weather records.
- Total records: 23 currency rates and 24 weather forecasts.
- USD and EUR each have 10 dates: 2026-08-18 through 2026-08-27.
- LAG query and currency trend view return 20 rows.
- The first daily change for each currency is NULL.
- Moving average returns 24 rows and uses the last three records.
- There is a timestamp gap, so three records do not always mean three hours.
- USD CTE returns 8 changes with ABS(daily_change) > 0.002.
- HAVING returns EUR and USD, each with 10 records.
- Average rates: EUR 2.9235; USD 2.6487.
- Materialized summary uses Asia/Tbilisi calendar dates:
  2026-08-27 has 20 records; 2026-08-28 has 4.
- REFRESH MATERIALIZED VIEW completed successfully.

## Query plans

The existing UNIQUE constraint on (city, forecast_time) already
provides an index suitable for the tested weather filter.
A duplicate index was not created.

Observed single-run execution times:
- Initial Index Scan: 0.123 ms.
- Forced Seq Scan: 0.029 ms.
- Default after ANALYZE: Seq Scan, 0.029 ms.

The query returns 11 rows and excludes 13.
After ANALYZE, the estimated row count changed from 1 to 11,
matching the actual count.

Planner settings used for demonstrations are transaction-local
and reset by ROLLBACK.

## AI Corner

Optimization request:
"This weather query is slow. Suggest an index or a rewrite."

Evaluation:
An index on (city, forecast_time) fits the filter, but it already
exists through the UNIQUE constraint. Creating another would
duplicate storage and add write overhead.

The 24-row table fits in one data page, and sequential access was
faster in the observed runs. A general performance claim requires
repeated measurements with representative data volumes, filter
selectivity and cache conditions.

Even a 2x improvement on one dataset does not prove that the advice
is correct for other workloads.
