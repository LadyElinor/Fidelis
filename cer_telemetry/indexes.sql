CREATE UNIQUE INDEX IF NOT EXISTS idx_steps_run_t ON steps(run_id, t);

CREATE INDEX IF NOT EXISTS idx_gate_checks_gate_decision ON gate_checks(gate, decision);
CREATE INDEX IF NOT EXISTS idx_gate_checks_step_id ON gate_checks(step_id);

CREATE INDEX IF NOT EXISTS idx_external_actions_status_type ON external_actions(status, type);
CREATE INDEX IF NOT EXISTS idx_external_actions_step_id ON external_actions(step_id);
CREATE INDEX IF NOT EXISTS idx_external_actions_target ON external_actions(target);

CREATE INDEX IF NOT EXISTS idx_confirmations_scope_confirmed ON confirmations(scope, confirmed);
CREATE INDEX IF NOT EXISTS idx_confirmations_step_id ON confirmations(step_id);

CREATE INDEX IF NOT EXISTS idx_tool_calls_step_id ON tool_calls(step_id);
CREATE INDEX IF NOT EXISTS idx_receipts_step_id ON receipts(step_id);
CREATE INDEX IF NOT EXISTS idx_data_issues_run_id ON data_issues(run_id);
CREATE INDEX IF NOT EXISTS idx_data_issues_kind_severity ON data_issues(kind, severity);
