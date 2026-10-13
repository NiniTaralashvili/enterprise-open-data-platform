-- Daily currency changes: 20 rows.
SELECT
    currency_code,
    rate_date,
    rate,
    LAG(rate) OVER (
        PARTITION BY currency_code ORDER BY rate_date
    ) AS previous_rate,
    ROUND(rate - LAG(rate) OVER (
        PARTITION BY currency_code ORDER BY rate_date
    ), 4) AS daily_change
FROM currency.rates
WHERE currency_code IN ('USD', 'EUR')
ORDER BY currency_code, rate_date;

-- Moving average of the last three records.
-- ROWS counts records, including across timestamp gaps.
SELECT
    forecast_time,
    temperature_c,
    ROUND(AVG(temperature_c) OVER (
        ORDER BY forecast_time
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3_rows
FROM weather.forecasts
WHERE city = 'Tbilisi'
ORDER BY forecast_time;

-- Significant USD changes: 8 rows.
WITH usd_changes AS (
    SELECT
        rate_date,
        rate,
        ROUND(rate - LAG(rate) OVER (
            ORDER BY rate_date
        ), 4) AS daily_change
    FROM currency.rates
    WHERE currency_code = 'USD'
)
SELECT rate_date, rate, daily_change
FROM usd_changes
WHERE ABS(daily_change) > 0.002
ORDER BY rate_date;

-- Currencies with at least five recorded days.
SELECT
    c.code,
    c.name,
    COUNT(*) AS days_recorded,
    ROUND(AVG(r.rate), 4) AS avg_rate
FROM currency.rates AS r
JOIN currency.currencies AS c ON c.code = r.currency_code
GROUP BY c.code, c.name
HAVING COUNT(*) >= 5
ORDER BY avg_rate DESC;
