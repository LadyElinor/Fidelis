CREATE TABLE IF NOT EXISTS run_metrics (
  run_id TEXT PRIMARY KEY,
  step_count INTEGER NOT NULL,
  gate_check_count INTEGER NOT NULL,
  safety_exception_rate REAL,
  exposure_attempt_rate REAL,
  receipt_completeness REAL,
  confirmation_violation_count INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS drift_signals (
  signal_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  ewma_value REAL,
  cusum_value REAL,
  alert INTEGER NOT NULL CHECK (alert IN (0,1)),
  details TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);
