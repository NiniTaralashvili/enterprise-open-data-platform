CREATE TABLE IF NOT EXISTS analytics.dim_currency (
    currency_key    SERIAL PRIMARY KEY,
    code            CHAR(3) NOT NULL UNIQUE,
    name            VARCHAR(50) NOT NULL
);

INSERT INTO analytics.dim_currency (code, name)
SELECT code, name FROM currency.currencies
ON CONFLICT (code) DO NOTHING;
