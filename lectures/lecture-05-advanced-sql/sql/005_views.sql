-- Live currency trend.
CREATE OR REPLACE VIEW currency.v_usd_eur_trend AS
SELECT
    currency_code,
    rate_date,
    rate,
    ROUND(rate - LAG(rate) OVER (
        PARTITION BY currency_code ORDER BY rate_date
    ), 4) AS daily_change
FROM currency.rates
WHERE currency_code IN ('USD', 'EUR');

SELECT *
FROM currency.v_usd_eur_trend
ORDER BY currency_code, rate_date;

-- Stored daily summary using Tbilisi calendar dates.
CREATE MATERIALIZED VIEW IF NOT EXISTS weather.mv_daily_summary AS
SELECT
    city,
    (forecast_time AT TIME ZONE 'Asia/Tbilisi')::date AS forecast_date,
    COUNT(*) AS records_count,
    ROUND(AVG(temperature_c), 2) AS avg_temp,
    ROUND(MAX(temperature_c), 2) AS max_temp,
    ROUND(MIN(temperature_c), 2) AS min_temp
FROM weather.forecasts
GROUP BY city, (forecast_time AT TIME ZONE 'Asia/Tbilisi')::date;

REFRESH MATERIALIZED VIEW weather.mv_daily_summary;

SELECT *
FROM weather.mv_daily_summary
ORDER BY city, forecast_date;
