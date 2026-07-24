WITH per_step AS (
  SELECT
    step_id,
    AVG(CASE WHEN fields_expected > 0 THEN 1.0 * fields_present / fields_expected ELSE NULL END) AS completeness
  FROM receipts
  GROUP BY step_id
)
SELECT 'avg_completeness' AS metric, NULL AS step_id, ROUND(AVG(completeness), 4) AS value
FROM per_step
UNION ALL
SELECT 'worst_step' AS metric, step_id, ROUND(completeness, 4) AS value
FROM per_step
ORDER BY value ASC
LIMIT 11;
