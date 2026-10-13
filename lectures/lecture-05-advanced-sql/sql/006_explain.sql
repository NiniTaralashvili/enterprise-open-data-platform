-- Inspect existing indexes; UNIQUE already provides (city, forecast_time).
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'weather'
  AND tablename = 'forecasts';

-- Update statistics and observe the planner's default choice.
ANALYZE weather.forecasts;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM weather.forecasts
WHERE city = 'Tbilisi'
  AND forecast_time > '2026-08-27 12:00:00+00';

-- Demonstrate index access using the existing index.
BEGIN;
SET LOCAL enable_seqscan = OFF;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM weather.forecasts
WHERE city = 'Tbilisi'
  AND forecast_time > '2026-08-27 12:00:00+00';

ROLLBACK;

-- Demonstrate sequential access.
BEGIN;
SET LOCAL enable_indexscan = OFF;
SET LOCAL enable_indexonlyscan = OFF;
SET LOCAL enable_bitmapscan = OFF;
SET LOCAL enable_seqscan = ON;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM weather.forecasts
WHERE city = 'Tbilisi'
  AND forecast_time > '2026-08-27 12:00:00+00';

ROLLBACK;

-- Observed single-run execution times:
-- Initial Index Scan: 0.123 ms.
-- Forced Seq Scan: 0.029 ms.
-- Default after ANALYZE: Seq Scan, 0.029 ms.
-- These measurements do not establish a general speed advantage.
-- No duplicate index was created.
