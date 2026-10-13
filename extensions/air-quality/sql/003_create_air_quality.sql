CREATE SCHEMA IF NOT EXISTS air_quality;

CREATE TABLE IF NOT EXISTS air_quality.measurements (
    id BIGSERIAL PRIMARY KEY,
    city VARCHAR(50) NOT NULL,

    latitude NUMERIC(8,4) NOT NULL
        CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(8,4) NOT NULL
        CHECK (longitude BETWEEN -180 AND 180),

    measured_at TIMESTAMPTZ NOT NULL,

    pm2_5_ug_m3 NUMERIC(8,2) NOT NULL
        CHECK (pm2_5_ug_m3 >= 0),
    pm10_ug_m3 NUMERIC(8,2) NOT NULL
        CHECK (pm10_ug_m3 >= 0),

    source VARCHAR(100) NOT NULL,
    data_kind VARCHAR(20) NOT NULL
        CHECK (data_kind IN ('synthetic', 'observation', 'model')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (
        latitude, longitude, measured_at, source, data_kind
    )
);
