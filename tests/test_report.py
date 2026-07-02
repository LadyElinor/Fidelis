from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.shared.models import ProposedAction


FIXED_TS = datetime(2026, 7, 1, 22, 11, tzinfo=timezone.utc)


def test_report_surfaces_attest_resolver_context():
    action = ProposedAction(
        id="test-report-attest-001",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        context={
            "change_type": "safety_invariant",
            "attest_known_message_refs": ["msg:root", "msg:support-1"],
            "attest_known_authority_refs": ["approval:ops-1"],
            "attest_authority_grants": {"approval:ops-1": {"scope": "deploy", "approved": True}},
        },
    )

    decision = assemble_execution_decision(action)
    report = render_markdown_report(decision)

    assert "## Attest bridge" in report
    assert "verifier provenance status" in report
    assert "grounds resolver" in report
    assert "authority resolver" in report
    assert "signature verifier" in report
    assert "known message refs" in report
    assert "known authority refs" in report
    assert "authority grants" in report
    assert "### CER verifier provenance" in report
    assert "evaluated at" in report
    assert "profile hash" in report
    assert "known message set hash" in report
    assert "signature verifier identity" in report
    assert "verifier hash" in report
    assert "resolver config hash" in report
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
    assert "Receipt Linkage:" in report
    assert "signal tiers" in report.lower()
