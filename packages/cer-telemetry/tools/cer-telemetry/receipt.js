import fs from 'node:fs';
import path from 'node:path';

function resolveFromCwd(p) {
  if (!p) return p;
  if (path.isAbsolute(p)) return p;
  return path.resolve(process.cwd(), p);
}

function isNum(x) { return typeof x === 'number' && Number.isFinite(x); }

export function validateReceipt(receipt) {
  const errors = [];

  const runId = receipt?.runId ?? receipt?.run_id;
  const script = receipt?.script;
  const timestamp = receipt?.timestamp ?? receipt?.generated_at;
  const metrics = receipt?.metrics;
  const invariants = receipt?.invariants;
  const phases = receipt?.phases;

  if (receipt?.receipt_version !== '0.1') errors.push('receipt_version must be "0.1"');
  if (!runId || typeof runId !== 'string') errors.push('missing runId/run_id');
  if (!script || typeof script !== 'string') errors.push('missing script');
  if (!timestamp || typeof timestamp !== 'string') errors.push('missing timestamp/generated_at');

  if (!Array.isArray(phases) || phases.length === 0) errors.push('missing phases[]');

  if (!Array.isArray(metrics)) {
    errors.push('missing metrics[]');
  } else {
    for (let i = 0; i < metrics.length; i++) {
      const m = metrics[i];
      if (!m || typeof m !== 'object') { errors.push(`metrics[${i}] not an object`); continue; }
      if (typeof m.metric !== 'string' || !m.metric) errors.push(`metrics[${i}].metric missing`);
      if (!isNum(m.num)) errors.push(`metrics[${i}].num not a number`);
      if (!isNum(m.den)) errors.push(`metrics[${i}].den not a number`);
      if (m.value != null && !isNum(m.value)) errors.push(`metrics[${i}].value not a number`);
      if (m.low != null && !isNum(m.low)) errors.push(`metrics[${i}].low not a number`);
      if (m.high != null && !isNum(m.high)) errors.push(`metrics[${i}].high not a number`);
    }
  }

  if (!invariants || typeof invariants !== 'object') {
    errors.push('missing invariants');
  } else {
    if (typeof invariants.ok !== 'boolean') errors.push('invariants.ok must be boolean');
    if (!Array.isArray(invariants.violations)) errors.push('invariants.violations must be array');
  }

  if (receipt?.partial_results != null && typeof receipt.partial_results !== 'boolean') errors.push('partial_results must be boolean');
  if (receipt?.throttling != null) {
    if (typeof receipt.throttling !== 'object') errors.push('throttling must be object');
    const bc = receipt.throttling?.blocked403_count;
    if (bc != null && !isNum(bc)) errors.push('throttling.blocked403_count must be number');
  }

  return { ok: errors.length === 0, errors };
}

export function writeReceipt({ runId, receiptDir, receiptObj }) {
  const dir = resolveFromCwd(receiptDir ?? './outputs/receipts');
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${runId}.json`);

  const validation = validateReceipt(receiptObj);
  if (!validation.ok) {
    receiptObj.receipt_validation = validation;
    // visibility without blocking
    console.warn(`Receipt validation failed (${runId}): ${validation.errors.join('; ')}`);
  } else {
    receiptObj.receipt_validation = { ok: true, errors: [] };
  }

  fs.writeFileSync(p, JSON.stringify(receiptObj, null, 2), 'utf8');
  return p;
}
