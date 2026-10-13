-- Verify sample count and source.
SELECT source, data_kind, COUNT(*) AS row_count
FROM air_quality.measurements
GROUP BY source, data_kind;

-- Join synthetic air-quality samples with weather.
SELECT
    a.city,
    a.measured_at AT TIME ZONE 'Asia/Tbilisi' AS tbilisi_time,
    a.pm2_5_ug_m3,
    a.pm10_ug_m3,
    w.temperature_c,
    w.wind_speed_kmh,
    w.precipitation_mm
FROM air_quality.measurements AS a
JOIN weather.forecasts AS w
    ON a.city = w.city
    AND a.latitude = w.latitude
    AND a.longitude = w.longitude
    AND a.measured_at = w.forecast_time
WHERE a.source = 'synthetic-lab-sample'
  AND a.data_kind = 'synthetic'
ORDER BY a.measured_at;
