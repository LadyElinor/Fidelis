import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { CERExportIngest } from '../src/cer-export-ingest.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const sourceJsonl = path.resolve('C:/Users/arren/.openclaw/workspace/repos/CER-Telemetry-clean-feature/outputs/mcp_fixture_for_sophron.jsonl');
const outputRoot = path.join(repoRoot, 'outputs', 'cer_export_ingest');

describe('CERExportIngest', () => {
  it('ingests a CER JSONL export and writes summary artifacts', () => {
    assert.equal(fs.existsSync(sourceJsonl), true, 'Expected CER export fixture JSONL to exist');

    const ingest = new CERExportIngest({}, console);
    const result = ingest.ingestAndWrite(sourceJsonl, outputRoot, {
      source: 'cer-export-ingest-test',
      runId: 'cer_export_ingest_test_0001'
    });

    assert.equal(result.summary.valid, true);
    assert.equal(result.summary.counts.run, 1);
    assert.equal(result.summary.counts.step, 4);
    assert.equal(result.summary.counts.gate_check, 4);
    assert.equal(result.summary.counts.tool_call, 4);
    assert.equal(result.summary.counts.receipt, 4);
    assert.equal(result.summary.counts.data_issue, 8);
    assert.ok(result.summary.riskFlags.includes('scope-escalation'));
    assert.equal(fs.existsSync(path.join(result.outputDir, 'meta.json')), true);
    assert.equal(fs.existsSync(path.join(result.outputDir, 'summary.json')), true);
    assert.equal(fs.existsSync(path.join(result.outputDir, 'records.json')), true);
  });
});
