SELECT
  gate,
  decision,
  COUNT(*) AS n,
  ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY gate), 4) AS rate
FROM gate_checks
GROUP BY gate, decision
ORDER BY gate, decision;
