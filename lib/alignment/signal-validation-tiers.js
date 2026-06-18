/**
 * Single source of truth for SOPHRON per-signal validation tiers.
 *
 * Extracted verbatim from examples/adapter_from_cer_v01_receipts.js so the
 * production adapter and the example emit identical signal_validation payloads,
 * and so the tier logic is importable rather than living only in an example.
 * TrustedRuntime's adapter prefers a native signal_validation.signals object
 * over its own derivation, so whatever code path produces the report TR ingests
 * should build that object from here.
 *
 * Tier honesty (unchanged): a signal earns 'validated-sim' only when it carries
 * evidence in the current simulation-backed adapter flow; 'field-validated' is
 * reserved for explicit upstream real-log/field emission and is never produced
 * by this derivation.
 */

export const SOPHRON_SIGNAL_NAMES = ['shift', 'game', 'decept', 'corrig', 'human'];

export const signalValidationTierPolicy = {
  validated_sim: 'signal has evidence in current simulation-backed adapter flow',
  field_validated: 'reserved for explicit upstream real-log/field evidence emission',
  unvalidated: 'signal absent or lacks evidence',
};

export function deriveSignalTier(signalPayload) {
  if (!signalPayload || typeof signalPayload !== 'object') return 'unvalidated';
  const evidence = Array.isArray(signalPayload.evidence) ? signalPayload.evidence : [];
  if (evidence.length === 0) return 'unvalidated';
  return 'validated-sim';
}

export function buildSignalValidationMap(signals) {
  if (!signals || typeof signals !== 'object') return {};
  const out = {};
  for (const signalName of SOPHRON_SIGNAL_NAMES) {
    const signalPayload = signals[signalName];
    if (!signalPayload || typeof signalPayload !== 'object') continue;
    out[`sophron.${signalName}`] = {
      signal_id: `sophron.${signalName}`,
      tier: deriveSignalTier(signalPayload),
      tier_source: 'sophron-emitted',
      source_layer: 'sophron-cer',
      rationale:
        'Emitted by SOPHRON-CER from alignment report evidence shape. Current adapter receipts provide simulation-backed calibration only; field validation must be emitted explicitly by upstream evidence pipelines.',
      evidence_refs: [],
      signal_payload: signalPayload,
    };
  }
  return out;
}

export function buildSignalValidation(signals) {
  return {
    signals: buildSignalValidationMap(signals),
    tier_policy: signalValidationTierPolicy,
  };
}
