CREATE SCHEMA IF NOT EXISTS weather;
COMMENT ON SCHEMA weather IS 'Open-Meteo API-დან საქართველოს ამინდის მონაცემები';

CREATE SCHEMA IF NOT EXISTS currency;
COMMENT ON SCHEMA currency IS 'ეროვნული ბანკის ვალუტის კურსების მონაცემები';

CREATE SCHEMA IF NOT EXISTS seismic;
COMMENT ON SCHEMA seismic IS 'USGS-დან საქართველოს რეგიონის სეისმური მონაცემები';
