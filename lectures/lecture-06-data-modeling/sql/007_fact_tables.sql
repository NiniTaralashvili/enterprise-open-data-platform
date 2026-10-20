CREATE TABLE IF NOT EXISTS analytics.fact_weather (
    fact_id           SERIAL PRIMARY KEY,
    date_key          INT NOT NULL REFERENCES analytics.dim_date(date_key),
    location_key      INT NOT NULL REFERENCES analytics.dim_location(location_key),
    forecast_time     TIMESTAMPTZ NOT NULL,   -- degenerate dimension: საათობრივი დეტალი
    temperature_c     NUMERIC(5,2),
    humidity_pct      NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    wind_speed_kmh    NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS analytics.fact_currency (
    fact_id         SERIAL PRIMARY KEY,
    date_key        INT NOT NULL REFERENCES analytics.dim_date(date_key),
    currency_key    INT NOT NULL REFERENCES analytics.dim_currency(currency_key),
    quantity        INT NOT NULL,
    rate            NUMERIC(10,4) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.fact_seismic (
    fact_id        SERIAL PRIMARY KEY,
    date_key       INT NOT NULL REFERENCES analytics.dim_date(date_key),
    location_key   INT REFERENCES analytics.dim_location(location_key),  -- nullable: fuzzy match
    magnitude      NUMERIC(3,1),
    depth_km       NUMERIC(6,2)
);
