function nowIso() { return new Date().toISOString(); }

export function checkInvariants({ rowsAll, eligible, sampledUnique, config, action } = {}) {
  const policy = config?.invariantsPolicy ?? 'balanced';
  const violations = [];
  const add = (layer, invariant, message, severity = 'warn', data) => {
    violations.push({ ts: nowIso(), layer, invariant, message, severity, data });
  };

  // Measurement invariants
  if (Array.isArray(rowsAll) && Array.isArray(eligible)) {
    if (eligible.length > rowsAll.length) add('measurement', 'monotonicity', 'Eligibility gate increased row count', 'error');
    const badDen = rowsAll.filter(r => r?.impressions == null || !Number.isFinite(r.impressions));
    if (badDen.length) add('measurement', 'denominator-hygiene', `${badDen.length} row(s) missing/invalid impressions`, 'error');
  }

  // Provenance invariants
  if (Array.isArray(rowsAll)) {
    const missingProv = rowsAll.filter(r => !r?.run_id || !r?.fetched_at || !r?.source_endpoint || !r?.id || !r?.post_url);
    if (missingProv.length) add('provenance', 'required-fields', `${missingProv.length} row(s) missing required provenance fields`, 'error');
  }

  // Sampling invariants
  if (sampledUnique && Array.isArray(sampledUnique)) {
    const ids = sampledUnique.map(r => r?.id).filter(Boolean);
    const uniq = new Set(ids);
    if (uniq.size !== ids.length) add('measurement', 'dedupe', 'sampledUnique contains duplicate ids', 'error');
  }

  // Action gating invariants (only when an outward action is attempted)
  // action shape (optional):
  // { type: 'post'|'reply'|'like'|'follow', risk_tier: 'low'|'med'|'high', confirmed_required: bool, confirmed_present: bool }
  if (action?.type) {
    const rt = action.risk_tier ?? 'low';
    const req = Boolean(action.confirmed_required);
    const pres = Boolean(action.confirmed_present);
    if (rt === 'high' && req && !pres) {
      add('safety', 'confirmation-gating', `High-risk ${action.type} attempted without confirmation`, 'warn', action);
    }
  }

  const ok = !violations.some(v => v.severity === 'error' || v.severity === 'fail');
  const shouldAbort = (() => {
    if (config?.policy?.onInvariantFailure === 'block') return violations.length > 0;
    if (policy === 'strict') return violations.length > 0;
    if (policy === 'permissive') return false;
    // balanced + warn policy: abort only on non-safety errors if block requested; otherwise do not abort.
    return false;
  })();

  return { policy, ok, shouldAbort, violations };
}
