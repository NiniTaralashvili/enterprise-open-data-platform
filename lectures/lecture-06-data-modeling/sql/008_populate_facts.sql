-- Initial snapshot load only. Refuse a repeat to prevent duplicate facts.
BEGIN;
LOCK TABLE analytics.fact_weather, analytics.fact_currency, analytics.fact_seismic IN EXCLUSIVE MODE;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM analytics.fact_weather)
 OR EXISTS (SELECT 1 FROM analytics.fact_currency)
 OR EXISTS (SELECT 1 FROM analytics.fact_seismic) THEN
   RAISE EXCEPTION 'Facts already populated. Initial loader must run only once.';
 END IF;
END $$;
-- fact_weather: city → location_key
INSERT INTO analytics.fact_weather
    (date_key, location_key, forecast_time, temperature_c, humidity_pct, precipitation_mm, wind_speed_kmh)
SELECT
    TO_CHAR(w.forecast_time AT TIME ZONE 'Asia/Tbilisi', 'YYYYMMDD')::INT,
    l.location_key,
    w.forecast_time,
    w.temperature_c,
    w.humidity_pct,
    w.precipitation_mm,
    w.wind_speed_kmh
FROM weather.forecasts w
JOIN analytics.dim_location l ON l.city = w.city
 AND (w.forecast_time AT TIME ZONE 'Asia/Tbilisi')::date >= l.valid_from
 AND (l.valid_to IS NULL OR (w.forecast_time AT TIME ZONE 'Asia/Tbilisi')::date < l.valid_to);

-- fact_currency: currency_code → currency_key
INSERT INTO analytics.fact_currency (date_key, currency_key, quantity, rate)
SELECT
    TO_CHAR(r.rate_date, 'YYYYMMDD')::INT,
    dc.currency_key,
    r.quantity,
    r.rate
FROM currency.rates r
JOIN analytics.dim_currency dc ON dc.code = r.currency_code;

-- fact_seismic: place-ის ტექსტიდან უახლოესი city-ის მოძებნა (fuzzy match)
INSERT INTO analytics.fact_seismic (date_key, location_key, magnitude, depth_km)
SELECT
    TO_CHAR(s.event_time AT TIME ZONE 'Asia/Tbilisi', 'YYYYMMDD')::INT,
    l.location_key,
    s.magnitude,
    s.depth_km
FROM seismic.events s
LEFT JOIN analytics.dim_location l ON s.place ILIKE '%' || l.city || '%'
 AND (s.event_time AT TIME ZONE 'Asia/Tbilisi')::date >= l.valid_from
 AND (l.valid_to IS NULL OR (s.event_time AT TIME ZONE 'Asia/Tbilisi')::date < l.valid_to);
COMMIT;
