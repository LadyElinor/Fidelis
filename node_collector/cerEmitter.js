import crypto from 'crypto';

export const CANONICAL_JSON_VERSION = 'canonical-json-v1';
export const VALID_RECORD_TYPES = new Set(['metric_observation', 'gate_outcome', 'cohort_partition']);

function canonicalize(value) {
  if (value === null) return 'null';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error('Non-finite numbers are not allowed in canonical JSON');
    }
    return JSON.stringify(value);
  }
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'string') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map(key => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(',')}}`;
  }
  throw new Error(`Unsupported value type in canonical JSON: ${typeof value}`);
}

export function canonicalJson(payload) {
  return canonicalize(payload);
}

export function deterministicHash(payload) {
  return crypto.createHash('sha256').update(canonicalJson(payload), 'utf8').digest('hex');
}

export function makeEnvelope({ runId, recordType, exportTimestamp, payload }) {
  if (!VALID_RECORD_TYPES.has(recordType)) {
    throw new Error(`Invalid record_type: ${recordType}`);
  }
  return {
    contract_version: '0.1',
    schema_version: '0.1',
    canonical_json_version: CANONICAL_JSON_VERSION,
    run_id: runId,
    record_type: recordType,
    export_timestamp: exportTimestamp,
    provenance_hash: deterministicHash(payload),
    payload,
  };
}
