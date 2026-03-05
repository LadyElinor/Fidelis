SELECT
  status,
  COUNT(*) AS n,
  ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS rate
FROM external_actions
GROUP BY status
ORDER BY status;
