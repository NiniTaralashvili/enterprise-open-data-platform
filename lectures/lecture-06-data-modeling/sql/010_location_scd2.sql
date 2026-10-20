BEGIN;
ALTER TABLE analytics.dim_location
 ADD COLUMN IF NOT EXISTS valid_from DATE NOT NULL DEFAULT DATE '2026-08-01',
 ADD COLUMN IF NOT EXISTS valid_to DATE,
 ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE analytics.dim_location DROP CONSTRAINT IF EXISTS dim_location_city_key;
CREATE UNIQUE INDEX IF NOT EXISTS dim_location_current_city_idx
 ON analytics.dim_location(city) WHERE is_current = TRUE;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint
 WHERE conrelid = 'analytics.dim_location'::regclass
 AND conname = 'dim_location_valid_period_check') THEN
 ALTER TABLE analytics.dim_location ADD CONSTRAINT dim_location_valid_period_check
 CHECK (valid_to IS NULL OR valid_to > valid_from);
 END IF;
END $$;
COMMIT;
