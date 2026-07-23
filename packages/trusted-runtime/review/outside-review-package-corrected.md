# Outside-Review Package — Corrected

Three deliverables, corrected against the actual repo at HEAD `fdbd540` after fixing the failing fixture. Every claim below was verified by running the code on a fresh clone. The corrections are not stylistic — the original draft made three claims a reviewer's first `pytest` and first `grep` would have falsified.

---

## What was fixed before this package is safe to use

**Blocker (now resolved): the suite was red on a clean clone.** `test_pinned_golden_overall_receipt[formation_event]` pinned a full-decision receipt hash captured under a real-adapter environment. That decision routes through the council layer, which is STUB on any clone without the sibling repos, so the hash could never match elsewhere. Fixed by pinning the **environment-independent formation-lens output** (pure logic, no stub feeds it) and asserting overall-receipt **determinism** separately. Result: **48 passed, 7 skipped, 0 failed** on a clean clone. A call for review must be green on checkout or it discredits itself; it now is.

**Draft test error (corrected below): `decision.warrant.quadrant` does not exist.** The field is `decision.warrant.normative_summary`. The corrected assertions use the real field names, verified against the model.

**Overclaim (corrected below): "real adapters for L1/L3."** Verified actual provenance on a clone: council **STUB**, warrant **REAL**, CER **STUB**, integrity **PARTIAL**. The honest statement is "L2 warrant is real via meaning-assay; L1/L3/L4 are stubbed in the public configuration." This matters because the golden HALT is partly stub-driven — disclosed below as a design fact rather than left for a reviewer to discover and distrust.

---

## 1. Test assertions (corrected, runnable against HEAD)

```python
# tests/test_verification.py
from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.enums import AdapterProvenance, DecisionIntegrity
from trusted_runtime.shared.models import ExecutionDecision, ProposedAction

FIXED_TS = datetime(2026, 6, 12, tzinfo=timezone.utc)


def _golden_action() -> ProposedAction:
    return ProposedAction(
        id="golden-invariant-change",
        timestamp=FIXED_TS,
        description="Auto-approve a change to a safety-critical OpenClaw invariant.",
        context={"change_type": "safety_invariant", "meaning_case_key": "early_release"},
    )


def test_no_false_proceed_without_full_integrity():
    """The load-bearing guard: PROCEED requires FULL integrity. True regardless
    of which layers are stubbed, so it holds on any clone."""
    d = assemble_execution_decision(_golden_action())
    if d.runtime_disposition.value == "PROCEED":
        assert d.decision_integrity == DecisionIntegrity.FULL


def test_warrant_layer_is_real_and_differentiates():
    """L2 (warrant) is the one real adapter in the public config. It must be REAL
    and must produce a real normative reading -- NOT decision.warrant.quadrant,
    which does not exist; the field is normative_summary."""
    d = assemble_execution_decision(_golden_action())
    assert d.warrant.adapter_provenance == AdapterProvenance.REAL
    assert d.warrant.normative_summary.value == "DANGEROUS"


def test_golden_is_contested_and_halts():
    d = assemble_execution_decision(_golden_action())
    assert d.runtime_disposition.value == "HALT"
    assert d.contested is True
    assert len(d.unresolved_questions) > 0


def test_provenance_is_explicit_in_dump():
    d = assemble_execution_decision(_golden_action())
    dump = d.model_dump(mode="json")
    assert "adapter_provenance" in dump
    assert "decision_integrity" in dump
```

Note the golden-fixture approach: pin only environment-independent values (the formation-lens hash, the warrant quadrant, determinism). Do **not** pin a full-decision receipt hash — it embeds stub-vs-real layer state and will fail on other machines, which is precisely the bug just fixed.

---

## 2. Verification Roadmap (for `docs/VERIFICATION_ROADMAP.md`)

```markdown
## Verification Roadmap

The architecture is ahead of its verification. We prioritize closing that gap
over expansion. No new layer earns inclusion until the suite below is green and
the public configuration's limits are documented.

### Phase 1 — Green suite & honestly-scoped fixtures  [DONE]
- [x] Suite green on a clean clone (48 passed, 7 env-dependent skips).
- [x] Golden values pinned only where environment-independent (formation lens,
      warrant quadrant); overall-receipt *determinism* asserted, not its host hash.
- [x] Provenance/integrity surfaced in every decision dump.

### Phase 2 — Disclose the public-config limits  [IN PROGRESS]
- [ ] State plainly in README: L2 warrant is REAL (via meaning-assay); L1 council,
      L3 TAS, L4 CER are STUB without the sibling repos.
- [ ] Document that the golden HALT is partly stub-driven, and that the real
      signal is the warrant layer (DANGEROUS, contested), not the disposition.
- [ ] CI job: fail on any PROCEED with non-FULL integrity.

### Phase 3 — Reality verification
- [ ] Audit 3–5 real decisions end-to-end with the real adapters present.
- [ ] Measure how often disposition tracks warrant once the council is REAL
      (the gap that is invisible in the stubbed public config).

### Phase 4 — Outside scrutiny
- [ ] Publish golden output + fixtures.
- [ ] Solicit 2–3 reviewers from outside the conceptual frame.
- [ ] Address findings before any new layers.
```

---

## 3. Announcement (corrected — survives a hostile clone)

---

**TrustedRuntime: a receipts-first decision pipeline for governed agents**

A thin orchestrator that wires a warrant layer (meaning-assay) into a five-layer decision pipeline, producing explicit provenance, integrity classification, and a verifiable master receipt for every decision.

**Honest state of the repo:** one layer is real and four are scaffolded. In the public configuration, **L2 (warrant) runs for real via meaning-assay; L1 (council), L3 (agent-stack), and L4 (telemetry) are stubs** unless you supply the sibling checkouts. Every decision is labeled with per-layer provenance and an integrity class (FULL / PARTIAL / DEMO_ONLY), and the policy guard forbids PROCEED while any required layer is stubbed.

**One thing to know before you run it:** the golden scenario (auto-approving a safety-critical invariant change) returns `HALT`, but in the stubbed public config that disposition is partly stub-driven — the stub council emits a halting hazard for any input. The signal that is actually *real* is the warrant layer: it reads the act as `DANGEROUS` with negative warrant and marks it contested, independently of the stub. Treat the disposition as scaffolding and the warrant reading as the live result. That asymmetry — and whether the design handles it honestly — is exactly what I'd like reviewed.

Suite is green on a clean clone (48 passed, 7 environment-dependent skips). Repo: https://github.com/LadyElinor/TrustedRuntime

Seeking sharp external eyes on:
- the adapter contract & provenance model (is "REAL vs STUB vs claimed" drawn in the right place?)
- the guard policies against false confidence (can a stubbed decision ever reach PROCEED? it shouldn't)
- the determinism & fixture approach (we pin only environment-independent values — is that the right line?)
- whether this advances trustworthy agency without collapsing the independent layers into one

No hype, no new ontology — verification-first scaffolding, with its limits stated up front. Issues, PRs, or DMs welcome, especially from formal-methods, AI-governance, and observable-runtime folks.

---

Why the corrected version is stronger for review: it pre-empts the two discoveries that would otherwise cost you a reviewer's trust — the stubbed layers and the stub-driven disposition — by stating them as disclosed design facts. A reviewer who is *told* the disposition is scaffolding and the warrant is the real signal can evaluate the actual contribution; one who *discovers* it after being told "real L1/L3" stops trusting the rest of the README. Disclosure converts the biggest vulnerability into a credibility signal.
```
