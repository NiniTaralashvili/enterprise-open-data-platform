CREATE TABLE IF NOT EXISTS analytics.fact_air_quality (
 fact_id BIGSERIAL PRIMARY KEY,
 measurement_id BIGINT NOT NULL UNIQUE REFERENCES air_quality.measurements(id),
 date_key INT NOT NULL REFERENCES analytics.dim_date(date_key),
 location_key INT NOT NULL REFERENCES analytics.dim_location(location_key),
 measured_at TIMESTAMPTZ NOT NULL,
 pm2_5_ug_m3 NUMERIC, pm10_ug_m3 NUMERIC,
 source VARCHAR, data_kind VARCHAR
);
INSERT INTO analytics.fact_air_quality
 (measurement_id,date_key,location_key,measured_at,pm2_5_ug_m3,pm10_ug_m3,source,data_kind)
SELECT m.id, TO_CHAR(m.measured_at AT TIME ZONE 'Asia/Tbilisi','YYYYMMDD')::INT,
 l.location_key,m.measured_at,m.pm2_5_ug_m3,m.pm10_ug_m3,m.source,m.data_kind
FROM air_quality.measurements m
JOIN analytics.dim_location l ON l.city=m.city
 AND (m.measured_at AT TIME ZONE 'Asia/Tbilisi')::date >= l.valid_from
 AND (l.valid_to IS NULL OR (m.measured_at AT TIME ZONE 'Asia/Tbilisi')::date < l.valid_to)
ON CONFLICT (measurement_id) DO NOTHING;
