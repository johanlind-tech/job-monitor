-- Add countries filter column to user_preferences.
-- Empty array means "all countries" (same convention as sources_enabled).
ALTER TABLE user_preferences
  ADD COLUMN IF NOT EXISTS countries text[] DEFAULT '{}';

-- Add country column to jobs table (defaults to SE for backward compat).
-- Already exists in some environments; IF NOT EXISTS prevents errors.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'jobs' AND column_name = 'country'
  ) THEN
    ALTER TABLE jobs ADD COLUMN country text DEFAULT 'SE';
  END IF;
END $$;
