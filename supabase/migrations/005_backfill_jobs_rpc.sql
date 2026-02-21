-- 005_backfill_jobs_rpc.sql
--
-- Postgres function that backfills the user_job_queue for a given user
-- by matching recent jobs against their preferences.
--
-- Called from the frontend when a user first opens the dashboard and
-- has no queued jobs yet.  This gives them instant results instead of
-- waiting for the next scraper run.

CREATE OR REPLACE FUNCTION public.backfill_jobs_for_user()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER          -- bypasses RLS so it can read jobs + write queue
SET search_path = public
AS $$
DECLARE
    _user_id          uuid := auth.uid();
    _prefs            record;
    _inserted         integer := 0;
BEGIN
    -- ── 1. Abort if user already has queued jobs ──────────────────────────
    IF EXISTS (
        SELECT 1 FROM user_job_queue WHERE user_id = _user_id LIMIT 1
    ) THEN
        RETURN 0;
    END IF;

    -- ── 2. Load preferences ──────────────────────────────────────────────
    SELECT
        COALESCE(keywords_include, '{}')  AS kw_inc,
        COALESCE(keywords_exclude, '{}')  AS kw_exc,
        COALESCE(sources_enabled, '{}')   AS sources,
        COALESCE(countries, '{SE}')       AS countries,
        COALESCE(regions, '{}')           AS regions,
        COALESCE(municipalities, '{}')    AS munis,
        COALESCE(employment_types, '{}')  AS emp_types
    INTO _prefs
    FROM user_preferences
    WHERE user_id = _user_id;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    -- ── 3. Insert matching jobs from the last 14 days ────────────────────
    WITH matching_jobs AS (
        SELECT j.id AS job_id
        FROM jobs j
        WHERE j.first_seen_at >= now() - interval '14 days'

          -- 1a. Country filter
          AND (
              array_length(_prefs.countries, 1) IS NULL
              OR COALESCE(j.country, 'SE') = ANY(_prefs.countries)
          )

          -- 1b. Source filter (empty array = all sources)
          AND (
              array_length(_prefs.sources, 1) IS NULL
              OR j.source = ANY(_prefs.sources)
          )

          -- 2. Keyword include (at least one must appear in title, case-insensitive)
          AND (
              array_length(_prefs.kw_inc, 1) IS NULL
              OR EXISTS (
                  SELECT 1 FROM unnest(_prefs.kw_inc) AS kw
                  WHERE lower(j.title) LIKE '%' || lower(kw) || '%'
              )
          )

          -- 3. Keyword exclude (none may appear in title)
          AND NOT EXISTS (
              SELECT 1 FROM unnest(_prefs.kw_exc) AS kw
              WHERE array_length(_prefs.kw_exc, 1) IS NOT NULL
                AND lower(j.title) LIKE '%' || lower(kw) || '%'
          )

          -- 4. Region filter (empty = all; NULL lan_code passes through)
          AND (
              array_length(_prefs.regions, 1) IS NULL
              OR j.lan_code IS NULL
              OR j.lan_code = ANY(_prefs.regions)
          )

          -- 5. Municipality filter (empty = all; NULL municipality_code passes)
          AND (
              array_length(_prefs.munis, 1) IS NULL
              OR j.municipality_code IS NULL
              OR j.municipality_code = ANY(_prefs.munis)
          )

          -- 6. Employment type filter (empty = all; NULL employment_type passes)
          AND (
              array_length(_prefs.emp_types, 1) IS NULL
              OR j.employment_type IS NULL
              OR j.employment_type = ANY(_prefs.emp_types)
          )
    )
    INSERT INTO user_job_queue (user_id, job_id)
    SELECT _user_id, mj.job_id
    FROM matching_jobs mj
    ON CONFLICT (user_id, job_id) DO NOTHING;

    GET DIAGNOSTICS _inserted = ROW_COUNT;
    RETURN _inserted;
END;
$$;

-- Allow authenticated users to call this function
GRANT EXECUTE ON FUNCTION public.backfill_jobs_for_user() TO authenticated;

-- ── RLS: allow users to INSERT into their own queue rows ─────────────────
-- (The backfill function uses SECURITY DEFINER so it bypasses RLS,
--  but we add this policy for completeness / future direct inserts.)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'user_job_queue'
          AND policyname = 'user_job_queue_insert'
    ) THEN
        CREATE POLICY user_job_queue_insert ON user_job_queue
            FOR INSERT
            WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;
