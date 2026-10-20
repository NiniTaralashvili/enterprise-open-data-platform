WITH w AS (
 SELECT f.date_key, ROUND(AVG(f.temperature_c),2) AS avg_temp_tbilisi
 FROM analytics.fact_weather f JOIN analytics.dim_location l USING(location_key)
 WHERE l.city='Tbilisi' GROUP BY f.date_key
), c AS (
 SELECT f.date_key, ROUND(AVG(f.rate/NULLIF(f.quantity,0)),4) AS usd_rate_per_unit
 FROM analytics.fact_currency f JOIN analytics.dim_currency d USING(currency_key)
 WHERE d.code='USD' GROUP BY f.date_key
), s AS (
 SELECT date_key,COUNT(*) AS earthquake_count FROM analytics.fact_seismic GROUP BY date_key
), a AS (
 SELECT f.date_key,ROUND(AVG(f.pm2_5_ug_m3),2) AS avg_pm2_5,
 ROUND(AVG(f.pm10_ug_m3),2) AS avg_pm10
 FROM analytics.fact_air_quality f JOIN analytics.dim_location l USING(location_key)
 WHERE l.city='Tbilisi' AND f.data_kind='synthetic' GROUP BY f.date_key
)
SELECT d.full_date,w.avg_temp_tbilisi,c.usd_rate_per_unit,
 COALESCE(s.earthquake_count,0) AS earthquake_count,a.avg_pm2_5,a.avg_pm10
FROM analytics.dim_date d
LEFT JOIN w USING(date_key) LEFT JOIN c USING(date_key)
LEFT JOIN s USING(date_key) LEFT JOIN a USING(date_key)
WHERE d.full_date=DATE '2026-08-27';
