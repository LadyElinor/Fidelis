import fs from 'node:fs';
import path from 'node:path';

import { openDb, ensureSchema, upsertRunStart, markRunEnd } from './db.js';

function nowIso() { return new Date().toISOString(); }

function resolveFromCwd(p) {
  if (!p) return p;
  if (path.isAbsolute(p)) return p;
  return path.resolve(process.cwd(), p);
}

function ensureDir(dir) {
  if (!dir) return;
  const p = resolveFromCwd(dir);
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function appendJsonl(filePath, obj) {
  const p = resolveFromCwd(filePath);
  fs.appendFileSync(p, JSON.stringify(obj) + '\n', 'utf8');
}

export function createEventLogger({ runId, script, config, meta } = {}) {
  const db = openDb(config?.db_path ?? './cer_telemetry.db');
  ensureSchema(db);

  const startedAt = nowIso();
  upsertRunStart(db, { runId, script, startedAt, config, meta });

  ensureDir(config?.jsonl_dir);
  const jsonlPath = path.join(resolveFromCwd(config?.jsonl_dir ?? './outputs/receipts_jsonl'), `${runId}.jsonl`);

  const stmStep = db.prepare('INSERT INTO cer_steps(run_id, ts, phase, data_json) VALUES (@run_id, @ts, @phase, @data_json)');
  const stmViol = db.prepare('INSERT INTO cer_violations(run_id, ts, layer, invariant, severity, message, data_json) VALUES (@run_id, @ts, @layer, @invariant, @severity, @message, @data_json)');
  const stmMetric = db.prepare('INSERT INTO cer_metrics(run_id, ts, metric, num, den, value, ci_low, ci_high, notes) VALUES (@run_id, @ts, @metric, @num, @den, @value, @ci_low, @ci_high, @notes)');

  function logStep(phase, data) {
    const evt = { kind: 'step', run_id: runId, script, ts: nowIso(), phase, data };
    appendJsonl(jsonlPath, evt);
    stmStep.run({ run_id: runId, ts: evt.ts, phase: String(phase ?? 'unknown'), data_json: data ? JSON.stringify(data) : null });
  }

  function logViolation(v) {
    const evt = { kind: 'violation', run_id: runId, script, ts: v.ts ?? nowIso(), ...v };
    appendJsonl(jsonlPath, evt);
    stmViol.run({
      run_id: runId,
      ts: evt.ts,
      layer: String(v.layer ?? 'unknown'),
      invariant: String(v.invariant ?? 'unknown'),
      severity: String(v.severity ?? 'warn'),
      message: String(v.message ?? ''),
      data_json: v.data ? JSON.stringify(v.data) : null,
    });
  }

  function logMetric({ metric, num, den, value, ci_low, ci_high, notes } = {}) {
    const evt = { kind: 'metric', run_id: runId, script, ts: nowIso(), metric, num, den, value, ci_low, ci_high, notes };
    appendJsonl(jsonlPath, evt);
    stmMetric.run({
      run_id: runId,
      ts: evt.ts,
      metric: String(metric ?? 'unknown'),
      num: Number(num ?? 0),
      den: Number(den ?? 0),
      value: value == null ? null : Number(value),
      ci_low: ci_low == null ? null : Number(ci_low),
      ci_high: ci_high == null ? null : Number(ci_high),
      notes: notes == null ? null : String(notes),
    });
  }

  function endRun({ meta: metaEnd } = {}) {
    const endedAt = nowIso();
    markRunEnd(db, { runId, endedAt, meta: metaEnd });
    appendJsonl(jsonlPath, { kind: 'run_end', run_id: runId, script, ts: endedAt });
    db.close();
  }

  function queryRollingMetric(metric, lookbackRuns = 20) {
    // Return aggregated (num, den) over the last N runs *before this run*.
    // We key by metric name; script is included to avoid cross-script drift.
    const stmt = db.prepare(`
      SELECT m.num, m.den, r.started_at
      FROM cer_metrics m
      JOIN cer_runs r ON r.run_id = m.run_id
      WHERE m.metric = @metric
        AND r.script = @script
        AND r.run_id != @run_id
      ORDER BY r.started_at DESC
      LIMIT @limit
    `);
    const rows = stmt.all({ metric, script, run_id: runId, limit: lookbackRuns });
    const num = rows.reduce((a, x) => a + (Number(x.num) || 0), 0);
    const den = rows.reduce((a, x) => a + (Number(x.den) || 0), 0);
    return { rows: rows.length, num, den };
  }

  return { db, jsonlPath, startedAt, logStep, logViolation, logMetric, endRun, queryRollingMetric };
}
