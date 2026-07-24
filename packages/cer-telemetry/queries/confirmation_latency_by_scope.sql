WITH action_confirmation AS (
  SELECT
    ea.type,
    c.scope,
    (julianday(c.created_at) - julianday(ea.created_at)) * 86400.0 AS latency_s
  FROM external_actions ea
  JOIN confirmations c ON c.step_id = ea.step_id
  WHERE c.confirmed = 1
),
ranked AS (
  SELECT
    scope,
    latency_s,
    ROW_NUMBER() OVER (PARTITION BY scope ORDER BY latency_s) AS rn,
    COUNT(*) OVER (PARTITION BY scope) AS cnt
  FROM action_confirmation
)
SELECT
  scope,
  ROUND(MAX(CASE WHEN rn = CAST(0.5 * (cnt + 1) AS INT) THEN latency_s END), 3) AS p50_s,
  ROUND(MAX(CASE WHEN rn = CAST(0.9 * (cnt + 1) AS INT) THEN latency_s END), 3) AS p90_s,
  ROUND(MAX(CASE WHEN rn = CAST(0.99 * (cnt + 1) AS INT) THEN latency_s END), 3) AS p99_s,
  COUNT(*) AS n
FROM ranked
GROUP BY scope
ORDER BY scope;
