# Air quality extension

Stores PM2.5 and PM10 concentrations in ug/m3.

The four Tbilisi records are invented educational samples,
not real measurements or API output.
Source: synthetic-lab-sample. Data kind: synthetic.

The loader uses a transaction and skips duplicate records.
First run inserted 4 rows; the second inserted 0.

The SQL JOIN matches air-quality and weather records by city,
coordinates and timestamp. It returns four matching hours.

A live API connection will be added later.
