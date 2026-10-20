CREATE SCHEMA IF NOT EXISTS analytics;
COMMENT ON SCHEMA analytics IS 'Star Schema — Kimball dimensional model 3 domain-ისთვის';

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key            INT PRIMARY KEY,      -- surrogate key, YYYYMMDD ფორმატში
    full_date           DATE NOT NULL UNIQUE,  -- natural key
    year                INT NOT NULL,
    month               INT NOT NULL,
    day                 INT NOT NULL,
    month_name          VARCHAR(20) NOT NULL,
    day_of_week_name    VARCHAR(20) NOT NULL,
    is_weekend          BOOLEAN NOT NULL
);

INSERT INTO analytics.dim_date
    (date_key, full_date, year, month, day, month_name, day_of_week_name, is_weekend)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    EXTRACT(DAY FROM d)::INT,
    TO_CHAR(d, 'FMMonth'),
    TO_CHAR(d, 'FMDay'),
    EXTRACT(ISODOW FROM d) IN (6, 7)
FROM generate_series('2026-08-01'::date, '2026-09-30'::date, '1 day'::interval) AS d
ON CONFLICT (date_key) DO NOTHING;
