from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.shared.models import ExactApprovalTarget, ProposedAction


FIXED_TS = datetime(2026, 7, 1, 22, 11, tzinfo=timezone.utc)


def test_report_surfaces_attest_resolver_context():
    action = ProposedAction(
        id="test-report-attest-001",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        action_scope="network_fetch",
        source_digest="sha256:test-source-001",
        exact_approval_target=ExactApprovalTarget(
            connector="slack",
            destination="ops-alerts",
            arguments={"text": "deploy approved"},
        ),
        context={
            "change_type": "safety_invariant",
            "attest_known_message_refs": ["msg:root", "msg:support-1"],
            "attest_known_authority_refs": ["approval:ops-1"],
            "attest_authority_grants": {"approval:ops-1": {"scope": "deploy", "approved": True}},
        },
        exact_approval_identity="msg-core-001",
        idempotency_key="idem-report-001",
    )

    decision = assemble_execution_decision(action)
    report = render_markdown_report(decision)

    assert "## Attest bridge" in report
    assert "verifier provenance status" in report
    assert "grounds resolver" in report
    assert "authority resolver" in report
    assert "signature verifier" in report
    assert "exact approval identity" in report
    assert "exact approval scope" in report
    assert "idempotency key" in report
    assert "typed approval lifted from legacy" in report
    assert "input preference" in report
    assert "legacy context shaping is compatibility-only" in report
    assert "exact approval source digest" in report
    assert "exact approval connector" in report
    assert "exact approval destination" in report
    assert "exact approval arguments" in report
    assert "target requires connector" in report
    assert "target requires destination" in report
    assert "target requires arguments" in report
    assert "idempotency duplicate detected" in report
    assert "idempotency enforcement" in report
    assert "idempotency posture: process-local / ephemeral" in report
    assert "within the current runtime process" in report
    assert "known message refs" in report
    assert "known authority refs" in report
    assert "authority grants" in report
    assert "### Exact approval commit preview" in report
    assert "### Exact approval commit artifact" in report
    assert "### CER verifier provenance" in report
    assert "evaluated at" in report
    assert "profile hash" in report
    assert "known message set hash" in report
    assert "signature verifier identity" in report
    assert "verifier hash" in report
    assert "resolver config hash" in report
    assert "authority state digest" in report
    assert "msg-core-001" in report
    assert "sha256:test-source-001" in report
    assert "network_fetch" in report
    assert "preview frame" in report
    assert "preview source digest" in report
    assert "preview idempotency key" in report
    assert "preview connector" in report
    assert "preview destination" in report
    assert "preview arguments" in report
    assert "artifact emission state" in report
    assert "artifact source digest" in report
    assert "artifact idempotency key" in report
    assert "artifact connector" in report
    assert "artifact destination" in report
    assert "artifact arguments" in report
    assert "artifact emitted" in report
    assert "## Integration Mode (Computed)" in report
    assert "overall mode" in report.lower()
    assert "behavior_real" in report
    assert "## L2 closure" in report
    assert "enforcement maturity" in report
    assert "closure complete" in report
    assert "trace checkpoints" in report
    assert "## L4 evidence" in report
    assert "SOPHRON Validation" in report
    assert "Status:" in report
    assert "Interpretation:" in report
    assert "Receipt Linkage:" in report
    assert "signal tiers" in report.lower()
    assert "exact approval commit artifact" in report
    assert "artifact governance state" in report


def test_report_interprets_l4_status_plainly():
    action = ProposedAction(
        id="test-report-l4-001",
        description="general governance review task",
        timestamp=FIXED_TS,
        context={},
    )

    decision = assemble_execution_decision(action)
    report = render_markdown_report(decision)

    assert "Interpretation:" in report
    if "Status: **FAILED**" in report:
        assert "adapter failed" in report
    elif "Status: **CALIBRATING**" in report:
        assert "advisory/calibrating" in report
    elif "Status: **VALIDATED**" in report:
        assert "validated SOPHRON evidence" in report
    elif "Status: **UNAVAILABLE**" in report:
        assert "no validated or partial SOPHRON evidence is available" in report


# Preferred-path report coverage: the typed example should render the native-typed preference clearly.
def test_report_for_typed_exact_approval_example_shows_preferred_path_note():
    from pathlib import Path
    from trusted_runtime.review import load_review_input

    action = load_review_input(Path(__file__).resolve().parents[1] / "examples" / "typed_exact_approval_review.json")
    decision = assemble_execution_decision(action)
    report = render_markdown_report(decision)

    assert "typed approval lifted from legacy: `False`" in report
    assert "native typed approval fields are preferred" in report
    assert "network_fetch" in report
    assert "typed-example-room" in report
