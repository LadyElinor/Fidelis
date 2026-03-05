SELECT
  kind,
  severity,
  COUNT(*) AS n
FROM data_issues
GROUP BY kind, severity
ORDER BY n DESC, kind, severity;
