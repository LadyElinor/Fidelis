import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const adapterScript = path.join(repoRoot, 'examples', 'adapter_from_cer_v01_receipts.js');

describe('adapter_from_cer_v01_receipts', () => {
  it('emits source-native per-signal validation tiers', () => {
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'sophron-adapter-test-'));
    const receiptsDir = path.join(tempRoot, 'receipts');
    const outPath = path.join(tempRoot, 'alignment-report.json');
    fs.mkdirSync(receiptsDir, { recursive: true });

    fs.writeFileSync(
      path.join(receiptsDir, 'fixture.json'),
      JSON.stringify({ kind: 'cer_telemetry_receipt_v0.1', run_id: 'fixture-run', manifest: {}, metrics: [] }),
      'utf8'
    );

    execFileSync('node', [adapterScript, '--receipts-dir', receiptsDir, '--out', outPath], {
      cwd: repoRoot,
      stdio: 'pipe',
      encoding: 'utf8',
    });

    const report = JSON.parse(fs.readFileSync(outPath, 'utf8'));
    assert.equal(report.kind, 'sophron_alignment_report_v0');
    assert.ok(report.signal_validation);
    assert.ok(report.signal_validation.signals);

    const signals = report.signal_validation.signals;
    for (const name of ['sophron.shift', 'sophron.game', 'sophron.decept', 'sophron.corrig', 'sophron.human']) {
      assert.ok(signals[name]);
      assert.equal(signals[name].tier_source, 'sophron-emitted');
      assert.equal(signals[name].source_layer, 'sophron-cer');
      assert.ok(['validated-sim', 'unvalidated'].includes(signals[name].tier));
    }
  });
});
