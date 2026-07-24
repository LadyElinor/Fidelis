import test from 'node:test';
import assert from 'node:assert/strict';

import { validateReceipt } from '../tools/cer-telemetry/receipt.js';

function validReceipt() {
  return {
    receipt_version: '0.1',
    runId: 'run-123',
    script: 'tmp_moltx_instrument_trending_v2.mjs',
    timestamp: '2026-07-23T00:00:00Z',
    phases: [{ phase: 'run_start' }],
    metrics: [{ metric: 'sample_rate', num: 1, den: 2, value: 0.5, low: 0.1, high: 0.9 }],
    invariants: { ok: true, violations: [] },
  };
}

test('validateReceipt accepts a minimally valid receipt', () => {
  const result = validateReceipt(validReceipt());
  assert.equal(result.ok, true);
  assert.deepEqual(result.errors, []);
});

test('validateReceipt rejects malformed receipt fields', () => {
  const receipt = validReceipt();
  receipt.metrics = [{ metric: '', num: 'one', den: 2 }];
  receipt.invariants = { ok: 'yes', violations: 'no' };

  const result = validateReceipt(receipt);
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /metrics\[0\]\.metric missing/);
  assert.match(result.errors.join('\n'), /metrics\[0\]\.num not a number/);
  assert.match(result.errors.join('\n'), /invariants\.ok must be boolean/);
  assert.match(result.errors.join('\n'), /invariants\.violations must be array/);
});
