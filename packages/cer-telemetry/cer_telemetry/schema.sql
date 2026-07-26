PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  agent_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  model TEXT NOT NULL,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
  step_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  t INTEGER NOT NULL,
  event_time TEXT NOT NULL,
  user_text_hash TEXT,
  assistant_text_hash TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gate_checks (
  gate_check_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL,
  gate TEXT NOT NULL CHECK (gate IN ('intent','authority','irreversibility','exposure','traceability')),
  decision TEXT NOT NULL CHECK (decision IN ('pass','warn','escalate','block')),
  justification TEXT NOT NULL,
  confidence REAL,
  evidence_ref TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS confirmations (
  confirmation_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL,
  scope TEXT NOT NULL CHECK (scope IN ('external_action','message_send','deletion','purchase','credential_change','other')),
  confirmed INTEGER NOT NULL CHECK (confirmed IN (0,1)),
  created_at TEXT NOT NULL,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gate_check_confirmations (
  gate_check_id TEXT NOT NULL,
  confirmation_id TEXT NOT NULL,
  PRIMARY KEY(gate_check_id, confirmation_id),
  FOREIGN KEY(gate_check_id) REFERENCES gate_checks(gate_check_id) ON DELETE CASCADE,
  FOREIGN KEY(confirmation_id) REFERENCES confirmations(confirmation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tool_calls (
  tool_call_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL,
  tool TEXT NOT NULL,
  operation TEXT NOT NULL,
  args_hash TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('success','fail')),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  error_code TEXT,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS external_actions (
  external_action_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('post','reply','dm','email','purchase','delete','upload','other')),
  target TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('attempted','blocked','sent','failed')),
  created_at TEXT NOT NULL,
  failure_reason TEXT,
  auth_evidence TEXT,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS receipts (
  receipt_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL,
  receipt_type TEXT NOT NULL CHECK (receipt_type IN ('decision','action','summary')),
  fields_present INTEGER NOT NULL,
  fields_expected INTEGER NOT NULL,
  receipt_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS data_issues (
  issue_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('missing_row','missing_confirmation','broken_fk','inconsistent_status','redaction_gap','other')),
  severity TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
  details TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
  FOREIGN KEY(step_id) REFERENCES steps(step_id) ON DELETE SET NULL
);
