WITH step_counts AS (
  SELECT run_id, COUNT(*) AS n_steps
  FROM steps
  GROUP BY run_id
),
exception_counts AS (
  SELECT s.run_id, COUNT(*) AS n_exceptions
  FROM gate_checks gc
  JOIN steps s ON s.step_id = gc.step_id
  WHERE gc.decision IN ('warn','escalate','block')
  GROUP BY s.run_id
)
SELECT
  sc.run_id,
  sc.n_steps,
  COALESCE(ec.n_exceptions, 0) AS n_exceptions,
  ROUND(100.0 * COALESCE(ec.n_exceptions, 0) / NULLIF(sc.n_steps, 0), 4) AS exceptions_per_100_steps
FROM step_counts sc
LEFT JOIN exception_counts ec ON ec.run_id = sc.run_id
ORDER BY exceptions_per_100_steps DESC;
