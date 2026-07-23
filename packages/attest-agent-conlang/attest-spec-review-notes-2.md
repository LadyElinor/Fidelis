# Attest Spec Review Notes 2 (2026-06-29)

This note captures the second major review pass over `attest-spec.md` after the first foundational patch.

## Main conclusions from the review

1. The three original blockers were genuinely closed:
   - canonicalization now functions as a v0.1 correctness requirement
   - ENDORSE resolves the relay-to-assertion contradiction
   - RETRACT now has proper append-only semantics

2. The hard/soft distinction in verifier checks materially improves the honesty of the spec.

3. Two new reachable edges were surfaced by the patch itself:
   - warrant laundering through ENDORSE
   - retract-ordering dependence without a mandatory ordering anchor in lineage

4. The larger inversion remains real:
   - hard guarantees cluster around integrity/form
   - soft guarantees cluster around the trust failures named in the motivating problem statement

The review judges that inversion to be likely a ceiling on what a wire format can do, not just an editing defect.

## New issues to close immediately

### A. ENDORSE warrant ceiling

Problem:
- an agent could endorse weakly sourced content and stamp it with a stronger warrant type than its lineage supports
- this would launder a weak source into a stronger apparent claim while preserving a formally valid grounds chain

Needed rule:
- ENDORSE may not strengthen warrant type relative to the adopted chain unless the endorser supplies new independent grounds

### B. RETRACT ordering anchor

Problem:
- the retract check in §18.3 depends on ordering
- current lineage fields do not require a timestamp or sequence anchor

Needed rule:
- each message must carry an ordering field sufficient for a verifier to compare retract time against derivation time

## Additional useful hardening noted by the review

### Confidence interval instrumentation rule

The review argues this could be hardened now rather than deferred:
- if a confidence interval lacks grounds that reference a method-producing artifact, it should be treated as ASSUMED-grade regardless of the numeric interval

This remains a recommended next patch even if not closed in the present edit.

## Recommended sequencing

1. close ENDORSE warrant ceiling
2. add RETRACT ordering anchor
3. then draft the adversarial corpus against the newly stabilized spec
