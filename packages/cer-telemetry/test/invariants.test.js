import test from 'node:test';
import assert from 'node:assert/strict';

import { checkInvariants } from '../tools/cer-telemetry/invariants.js';

function baseRow(overrides = {}) {
  return {
    run_id: 'run-1',
    fetched_at: '2026-07-23T00:00:00Z',
    source_endpoint: '/v1/posts?sort=top',
    id: 'post-1',
    post_url: 'https://example.test/post-1',
    impressions: 10,
    ...overrides,
  };
}

test('checkInvariants passes for well-formed rows', () => {
  const rows = [baseRow()];
  const result = checkInvariants({
    rowsAll: rows,
    eligible: rows,
    sampledUnique: rows,
    config: { invariantsPolicy: 'balanced', policy: { onInvariantFailure: 'warn' } },
  });

  assert.equal(result.ok, true);
  assert.equal(result.violations.length, 0);
});

test('checkInvariants reports provenance and dedupe violations', () => {
  const malformed = baseRow({ run_id: null, impressions: Number.NaN });
  const result = checkInvariants({
    rowsAll: [malformed],
    eligible: [malformed, malformed],
    sampledUnique: [baseRow(), baseRow()],
    config: { invariantsPolicy: 'balanced', policy: { onInvariantFailure: 'warn' } },
  });

  assert.equal(result.ok, false);
  const summary = result.violations.map(v => `${v.layer}:${v.invariant}`).join('\n');
  assert.match(summary, /measurement:monotonicity/);
  assert.match(summary, /measurement:denominator-hygiene/);
  assert.match(summary, /provenance:required-fields/);
  assert.match(summary, /measurement:dedupe/);
});
