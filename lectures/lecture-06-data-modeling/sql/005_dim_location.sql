CREATE TABLE IF NOT EXISTS analytics.dim_location (
    location_key    SERIAL PRIMARY KEY,   -- surrogate key
    city            VARCHAR(50) NOT NULL UNIQUE,  -- natural key
    country         VARCHAR(50) NOT NULL DEFAULT 'Georgia',
    latitude        NUMERIC(8,4),
    longitude       NUMERIC(8,4)
);

INSERT INTO analytics.dim_location (city, latitude, longitude) VALUES
    ('Tbilisi', 41.7151, 44.8271),
    ('Batumi',  41.6168, 41.6367),
    ('Kutaisi', 42.2679, 42.7000),
    ('Telavi',  41.9189, 45.4739),
    ('Gori',    41.9847, 44.1164)
ON CONFLICT DO NOTHING;
