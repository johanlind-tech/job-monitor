-- 006_batch3_sources.sql
--
-- Add batch 3 sources to existing users who have a customised
-- sources_enabled list (non-empty array).  Users with '{}' (empty = all)
-- already get every source automatically.

UPDATE user_preferences
SET    sources_enabled = (
           SELECT array_agg(DISTINCT s ORDER BY s)
           FROM   unnest(
                      sources_enabled || ARRAY[
                          'hays','people360','hudsonnordic','humancapital',
                          'kornferry_interim','kornferry','mercuriurval',
                          'needo','andpartners'
                      ]
                  ) AS s
       )
WHERE  sources_enabled <> '{}'
  AND  array_length(sources_enabled, 1) > 0;
