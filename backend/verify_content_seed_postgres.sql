SELECT current_database() AS database_name, current_schema() AS schema_name;

SELECT version_num AS alembic_revision FROM alembic_version;

SELECT
  CASE WHEN to_regclass('public.practice_problems') IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS practice_problems_table,
  CASE WHEN to_regclass('public.featured_courses') IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS featured_courses_table,
  CASE WHEN to_regclass('public.learning_path_concepts') IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS learning_path_concepts_table,
  CASE WHEN to_regclass('public.learning_path_subtopics') IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS learning_path_subtopics_table,
  CASE WHEN to_regclass('public.theory_course_pages') IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS theory_course_pages_table;

SELECT
  CASE WHEN COUNT(*) FILTER (WHERE column_name = 'level') > 0 THEN 'OK' ELSE 'MISSING' END AS has_level,
  CASE WHEN COUNT(*) FILTER (WHERE column_name = 'section') > 0 THEN 'OK' ELSE 'MISSING' END AS has_section,
  CASE WHEN COUNT(*) FILTER (WHERE column_name = 'order_index') > 0 THEN 'OK' ELSE 'MISSING' END AS has_order_index,
  CASE WHEN COUNT(*) FILTER (WHERE column_name = 'description') > 0 THEN 'OK' ELSE 'MISSING' END AS has_description,
  CASE WHEN COUNT(*) FILTER (WHERE column_name = 'test_cases') > 0 THEN 'OK' ELSE 'MISSING' END AS has_test_cases
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'practice_problems';

WITH counts AS (
  SELECT
    COUNT(*) AS total_problems,
    COUNT(*) FILTER (WHERE lower(level) = 'beginner') AS beginner_count,
    COUNT(*) FILTER (WHERE lower(level) = 'intermediate') AS intermediate_count,
    COUNT(*) FILTER (WHERE lower(level) = 'advanced') AS advanced_count,
    COUNT(*) FILTER (WHERE description IS NULL OR btrim(description) = '') AS missing_description_count,
    COUNT(*) FILTER (WHERE length(coalesce(description, '')) < 120) AS short_description_count,
    COUNT(*) FILTER (
      WHERE test_cases IS NULL
         OR jsonb_typeof(test_cases::jsonb) <> 'array'
         OR jsonb_array_length(test_cases::jsonb) = 0
    ) AS missing_test_cases_count
  FROM practice_problems
)
SELECT
  total_problems,
  beginner_count,
  intermediate_count,
  advanced_count,
  missing_description_count,
  short_description_count,
  missing_test_cases_count,
  CASE WHEN total_problems >= 75 THEN 'OK' ELSE 'CHECK' END AS total_check,
  CASE WHEN beginner_count >= 25 THEN 'OK' ELSE 'CHECK' END AS beginner_check,
  CASE WHEN intermediate_count >= 25 THEN 'OK' ELSE 'CHECK' END AS intermediate_check,
  CASE WHEN advanced_count >= 25 THEN 'OK' ELSE 'CHECK' END AS advanced_check,
  CASE WHEN missing_description_count = 0 THEN 'OK' ELSE 'CHECK' END AS description_check,
  CASE WHEN short_description_count = 0 THEN 'OK' ELSE 'CHECK' END AS long_description_check,
  CASE WHEN missing_test_cases_count = 0 THEN 'OK' ELSE 'CHECK' END AS test_cases_check
FROM counts;

SELECT
  id,
  title,
  level,
  difficulty,
  length(coalesce(description, '')) AS description_length,
  CASE
    WHEN test_cases IS NULL THEN 0
    WHEN jsonb_typeof(test_cases::jsonb) <> 'array' THEN 0
    ELSE jsonb_array_length(test_cases::jsonb)
  END AS test_case_count
FROM practice_problems
ORDER BY level, section NULLS FIRST, order_index, id
LIMIT 40;

SELECT
  COUNT(*) AS featured_courses_count,
  COUNT(*) FILTER (WHERE title IS NULL OR btrim(title) = '') AS featured_courses_missing_title,
  COUNT(*) FILTER (WHERE description IS NULL OR btrim(description) = '') AS featured_courses_missing_description
FROM featured_courses;

SELECT
  COUNT(*) AS learning_path_concepts_count,
  COUNT(*) FILTER (WHERE title IS NULL OR btrim(title) = '') AS learning_path_missing_title,
  COUNT(*) FILTER (WHERE description IS NULL OR btrim(description) = '') AS learning_path_missing_description,
  COUNT(*) FILTER (WHERE tutorial_url IS NULL OR btrim(tutorial_url) = '') AS learning_path_missing_tutorial_url
FROM learning_path_concepts;

SELECT
  COUNT(*) AS learning_path_subtopics_count,
  COUNT(*) FILTER (WHERE title IS NULL OR btrim(title) = '') AS learning_path_subtopics_missing_title
FROM learning_path_subtopics;

SELECT
  COUNT(*) AS theory_course_pages_count,
  COUNT(*) FILTER (WHERE title IS NULL OR btrim(title) = '') AS theory_pages_missing_title,
  COUNT(*) FILTER (WHERE html_path IS NULL OR btrim(html_path) = '') AS theory_pages_missing_html_path
FROM theory_course_pages;

SELECT id, level, section, title, difficulty, order_index, left(description, 80) AS description_preview
FROM practice_problems
ORDER BY level, section NULLS FIRST, order_index, id
LIMIT 30;

SELECT id, title, level, tutorial_url, order_index
FROM learning_path_concepts
ORDER BY level, order_index, id;

SELECT id, title, level, html_path, order_index
FROM theory_course_pages
ORDER BY level, order_index, id
LIMIT 40;

SELECT id, title, language, kind, route_path, external_url, order_index
FROM featured_courses
ORDER BY order_index, id;
