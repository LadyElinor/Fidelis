import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { CANONICAL_JSON_VERSION, canonicalJson, deterministicHash, makeEnvelope } from './cerEmitter.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const vectorsPath = path.join(repoRoot, 'contracts', 'canonical_json_vectors_v0_1.json');
const outputPath = path.join(repoRoot, 'node_collector', 'demo_export.jsonl');

function loadVectors() {
  return JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));
}

function checkVectors() {
  const vectors = loadVectors();
  for (const vector of vectors) {
    const actualCanonical = canonicalJson(vector.payload);
    const actualHash = deterministicHash(vector.payload);
    if (actualCanonical !== vector.canonical_json) {
      throw new Error(`Canonical JSON mismatch for ${vector.name}`);
    }
    if (actualHash !== vector.sha256) {
      throw new Error(`Hash mismatch for ${vector.name}`);
    }
  }
  console.log(`Node parity OK (${vectors.length} vectors, ${CANONICAL_JSON_VERSION})`);
}

function writeDemoExport() {
  const exportTimestamp = '2026-05-30T21:30:00Z';
  const runId = 'run_bridge_demo_0001';
  const records = [
    makeEnvelope({
      runId,
      recordType: 'metric_observation',
      exportTimestamp,
      payload: {
        metric_name: 'latency_ms',
        value: 123.4,
        tags: ['demo', 'bridge'],
        window: { start: '2026-05-30T21:00:00Z', end: '2026-05-30T21:05:00Z' }
      }
    }),
    makeEnvelope({
      runId,
      recordType: 'gate_outcome',
      exportTimestamp,
      payload: {
        gate: 'least_privilege',
        decision: 'pass',
        confidence: 0.98,
        evidence: { scope_diff: [] }
      }
    }),
    makeEnvelope({
      runId,
      recordType: 'cohort_partition',
      exportTimestamp,
      payload: {
        cohort_name: 'high_risk_sessions',
        included_run_ids: ['run_bridge_demo_0001'],
        excluded_run_ids: [],
        overlap_count: 0
      }
    })
  ];

  fs.writeFileSync(outputPath, records.map(r => JSON.stringify(r)).join('\n') + '\n', 'utf8');
  console.log(`Wrote demo export: ${outputPath}`);
}

if (process.argv.includes('--check-vectors')) {
  checkVectors();
} else {
  checkVectors();
  writeDemoExport();
}
