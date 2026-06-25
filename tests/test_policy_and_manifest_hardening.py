from __future__ import annotations

from trusted_runtime.integration.engine import CerSophronTelemetryAdapter
from trusted_runtime.integration.policy import REQUIRED_REAL_FOR_PROCEED, guard_runtime_disposition
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction


def test_tas_is_required_for_proceed():
    assert "tas" in REQUIRED_REAL_FOR_PROCEED
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
            "tas": AdapterProvenance.STUB,
        },
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "required layers" in note


def test_metrics_manifest_no_longer_labels_description_digest_as_git_sha():
    receipt = CerSophronTelemetryAdapter()._render_cer_metrics_receipt(
        ProposedAction(id="m1", description="review governance change", context={}, proposed_by="op"),
        RuntimeDisposition.CONFIRM_HUMAN.value,
    )
    manifest = receipt["manifest"]
    assert "git_sha" not in manifest
    assert "action_description_digest" in manifest
    assert len(manifest["action_description_digest"]) == 64
