-- 004_sources_enabled_empty_means_all.sql
--
-- The system convention is: sources_enabled = '{}' (empty array) means
-- "all sources enabled".  The original trigger hardcoded 9 sources,
-- so every user created before this fix is stuck on only those 9.
--
-- This migration:
--   1. Sets existing users who still have the original 9-source array
--      (i.e. never manually changed) to the empty array so they
--      automatically receive jobs from all current and future sources.
--   2. For users who have customised their list (added or removed),
--      appends the new sources that didn't exist when they signed up.
--
-- The trigger in 001 has already been updated to insert '{}' for new users.

-- Step 1: Users who never touched their sources → switch to "all"
UPDATE user_preferences
SET    sources_enabled = '{}'
WHERE  sources_enabled = ARRAY[
           'capa','interimsearch','wise','headagent','michaelberglund',
           'mason','hammerhanborg','novare','platsbanken'
       ];

-- Step 2: Users who customised their list → add the new batch-1 and batch-2
--         sources so they aren't silently missing them.
--         (array_cat + ARRAY removes duplicates via DISTINCT later, but
--          Postgres doesn't have array_distinct, so we use a subquery.)
UPDATE user_preferences
SET    sources_enabled = (
           SELECT array_agg(DISTINCT s ORDER BY s)
           FROM   unnest(
                      sources_enabled || ARRAY[
                          'wes','stardust','academicsearch','signpost',
                          'inhouse','peopleprovide','futurevalue_rekrytering',
                          'futurevalue_interim','avanti','pooliaexecutive',
                          'nigel_wright','gazella','alumni','properpeople',
                          'jobway','beyondretail','bonesvirik','visindi','vindex',
                          'executive','cip','trib','mesh','brightpeople',
                          'bondi','basedonpeople','bohmans','addpeople',
                          'compasshrg','levelrecruitment','performiq','safemind'
                      ]
                  ) AS s
       )
WHERE  sources_enabled <> '{}'   -- skip users already on "all"
  AND  array_length(sources_enabled, 1) > 0;

-- Step 3: Update the trigger function so new sign-ups get empty array.
--         (This is a safety net — the 001 file was edited directly, but
--          running this migration on an existing DB applies the change.)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, subscription_status, trial_ends_at, created_at)
    VALUES (
        NEW.id,
        NEW.email,
        'trialing',
        now() + interval '14 days',
        now()
    );

    INSERT INTO public.user_preferences (
        user_id,
        delivery_days,
        keywords_include,
        keywords_exclude,
        sources_enabled,
        regions,
        municipalities,
        employment_types
    ) VALUES (
        NEW.id,
        '{1,2,3,4,5}',
        ARRAY[
            'CEO','Country Manager','General Manager','Managing Director',
            'Business Unit Director','BU Director','Vice President','VP',
            'Senior Vice President','SVP','CMO','CCO','CSO','CBDO',
            'Commercial Director','Marketing Director','Commercial Lead',
            'Head of Commercial','Head of Marketing',
            'VD','Landschef','Affärsområdesdirektör','Affärsområdeschef',
            'Marknadsdirektör','Kommersiell direktör',
            'Affärsutvecklingsdirektör','Försäljningsdirektör'
        ],
        ARRAY['junior','assistant','coordinator','assisterande','assistent'],
        '{}',   -- sources_enabled: empty = all sources
        '{}',   -- regions: empty = all
        '{}',   -- municipalities: empty = all
        '{"permanent","interim"}'
    );

    RETURN NEW;
END;
$$;
