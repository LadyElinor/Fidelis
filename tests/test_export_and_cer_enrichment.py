from __future__ import annotations

from pathlib import Path

from trusted_runtime.export import export_decision_payload
from trusted_runtime.review import load_review_input
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.models import CERFragmentEnrichment


def test_cer_fragment_enrichment_defaults_empty_and_typed():
    enrichment = CERFragmentEnrichment()

    assert enrichment.evaluated_at is None
    assert enrichment.profile_hash is None
    assert enrichment.verifier_hash is None
    assert enrichment.resolver_config_hash is None
    assert enrichment.known_message_set_hash is None
    assert enrichment.signature_verifier_identity is None
    assert enrichment.replay_nonce is None


def test_export_decision_payload_includes_cer_enrichment():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    decision = assemble_execution_decision(load_review_input(case_path))

    payload = export_decision_payload(decision)
    enrichment = payload["cer_bundle"]["cer_enrichment"]
    verification = decision.vita_state["attest_bridge"]["verification"]

    assert "cer_bundle" in payload
    assert "cer_enrichment" in payload["cer_bundle"]
    assert enrichment["evaluated_at"] is not None
    assert enrichment["profile_hash"] == verification["attest_profile_hash"]
    assert enrichment["known_message_set_hash"] == verification["attest_known_message_set_hash"]
    assert enrichment["signature_verifier_identity"] == verification["attest_signature_verifier_name"]
    assert enrichment["replay_nonce"] is None
    assert len(enrichment["verifier_hash"]) == 64
    assert len(enrichment["resolver_config_hash"]) == 64
