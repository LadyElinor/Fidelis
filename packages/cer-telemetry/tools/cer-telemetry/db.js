import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const Database = require('better-sqlite3');

function resolveFromCwd(p) {
  if (!p) return p;
  if (path.isAbsolute(p)) return p;
  return path.resolve(process.cwd(), p);
}

export function openDb(dbPath) {
  const p = resolveFromCwd(dbPath);
  const dir = path.dirname(p);
  if (dir && !fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const db = new Database(p);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  return db;
}

export function ensureSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS cer_runs (
      run_id TEXT PRIMARY KEY,
      script TEXT NOT NULL,
      started_at TEXT NOT NULL,
      ended_at TEXT,
      config_json TEXT,
      meta_json TEXT
    );

    CREATE TABLE IF NOT EXISTS cer_steps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id TEXT NOT NULL,
      ts TEXT NOT NULL,
      phase TEXT NOT NULL,
      data_json TEXT,
      FOREIGN KEY(run_id) REFERENCES cer_runs(run_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS cer_violations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id TEXT NOT NULL,
      ts TEXT NOT NULL,
      layer TEXT NOT NULL,
      invariant TEXT NOT NULL,
      severity TEXT NOT NULL,
      message TEXT NOT NULL,
      data_json TEXT,
      FOREIGN KEY(run_id) REFERENCES cer_runs(run_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS cer_metrics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id TEXT NOT NULL,
      ts TEXT NOT NULL,
      metric TEXT NOT NULL,
      num REAL NOT NULL,
      den REAL NOT NULL,
      value REAL,
      ci_low REAL,
      ci_high REAL,
      notes TEXT,
      FOREIGN KEY(run_id) REFERENCES cer_runs(run_id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_cer_steps_run_ts ON cer_steps(run_id, ts);
    CREATE INDEX IF NOT EXISTS idx_cer_metrics_metric_ts ON cer_metrics(metric, ts);
  `);
}

export function upsertRunStart(db, { runId, script, startedAt, config, meta }) {
  const stmt = db.prepare(`
    INSERT INTO cer_runs(run_id, script, started_at, config_json, meta_json)
    VALUES (@run_id, @script, @started_at, @config_json, @meta_json)
    ON CONFLICT(run_id) DO UPDATE SET
      script=excluded.script,
      started_at=excluded.started_at,
      config_json=excluded.config_json,
      meta_json=excluded.meta_json
  `);
  stmt.run({
    run_id: runId,
    script,
    started_at: startedAt,
    config_json: config ? JSON.stringify(config) : null,
    meta_json: meta ? JSON.stringify(meta) : null,
  });
}

export function markRunEnd(db, { runId, endedAt, meta }) {
  const stmt = db.prepare(`
    UPDATE cer_runs
    SET ended_at=@ended_at,
        meta_json=COALESCE(@meta_json, meta_json)
    WHERE run_id=@run_id
  `);
  stmt.run({
    run_id: runId,
    ended_at: endedAt,
    meta_json: meta ? JSON.stringify(meta) : null,
  });
}
