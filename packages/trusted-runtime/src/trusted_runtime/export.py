from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from trusted_runtime.l4_status import l4_status_interpretation
from trusted_runtime.shared.models import ExecutionDecision


def compact_verifier_provenance_summary(decision: ExecutionDecision) -> dict[str, JsonSafe]:
    verification = decision.vita_state.get("attest_bridge", {}).get("verification", {})
    enrichment = getattr(getattr(decision, "cer_bundle", None), "cer_enrichment", None)
    signature_identity = getattr(enrichment, "signature_verifier_identity", None) or verification.get("attest_signature_verifier_name") or "n/a"
    decision_effect = verification.get("attest_decision_effect", "n/a")
    profile_hash = getattr(enrichment, "profile_hash", None)
    profile_hash_short = profile_hash[:12] if isinstance(profile_hash, str) and profile_hash else None
    known_message_set_hash = getattr(enrichment, "known_message_set_hash", None)
    known_message_set_hash_short = known_message_set_hash[:12] if isinstance(known_message_set_hash, str) and known_message_set_hash else None
    verifier_hash = getattr(enrichment, "verifier_hash", None)
    verifier_hash_short = verifier_hash[:12] if isinstance(verifier_hash, str) and verifier_hash else None
    resolver_config_hash = getattr(enrichment, "resolver_config_hash", None)
    resolver_config_hash_short = resolver_config_hash[:12] if isinstance(resolver_config_hash, str) and resolver_config_hash else None
    stub_path = decision_effect == "UNVERIFIABLE" or str(signature_identity).startswith("stub-none")
    status_line = f"{signature_identity}:{decision_effect}"
    return {
        "status_line": status_line,
        "signature_verifier_identity": signature_identity,
        "decision_effect": decision_effect,
        "stub_path": stub_path,
        "profile_hash_short": profile_hash_short,
        "known_message_set_hash_short": known_message_set_hash_short,
        "verifier_hash_short": verifier_hash_short,
        "resolver_config_hash_short": resolver_config_hash_short,
    }




JsonSafe = dict[str, Any] | list[Any] | str | int | float | bool | None


def to_json_safe(obj: Any) -> JsonSafe:
    """Recursively normalize supported runtime objects into JSON-safe values."""

    if isinstance(obj, BaseModel):
        return to_json_safe(obj.model_dump(mode="json"))
    if is_dataclass(obj) and not isinstance(obj, type):
        return to_json_safe(asdict(obj))
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {str(key): to_json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(item) for item in obj]
    if isinstance(obj, tuple | set):
        return [to_json_safe(item) for item in obj]
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return {str(key): to_json_safe(value) for key, value in vars(obj).items()}
    return obj


def export_decision_payload(decision: ExecutionDecision) -> dict[str, JsonSafe]:
    """Canonical machine-readable decision payload for smoke, CI, and future JSON surfaces."""

    cer_bundle = to_json_safe(decision.cer_bundle)
    sophron_validation = cer_bundle.get("sophron_validation", {}) if isinstance(cer_bundle, dict) else {}
    validation_status = sophron_validation.get("validation_status", "UNAVAILABLE") if isinstance(sophron_validation, dict) else "UNAVAILABLE"
    interpretation = l4_status_interpretation(str(validation_status))
    if isinstance(sophron_validation, dict):
        sophron_validation["interpretation"] = interpretation

    return {
        "action_id": decision.action_id,
        "risk_state": decision.risk_state.value,
        "runtime_disposition": decision.runtime_disposition.value,
        "decision_integrity": decision.decision_integrity.value,
        "integration_mode_report": to_json_safe(decision.integration_mode_report),
        "cer_bundle": cer_bundle,
        "l4_interpretation": interpretation,
        "vita_state": to_json_safe(decision.vita_state),
        "process_provenance": to_json_safe(decision.process_provenance),
        "adapter_provenance": to_json_safe(decision.adapter_provenance),
        "correlation_report": to_json_safe(decision.correlation_report),
        "independently_corroborated": decision.independently_corroborated,
        "self_attested_evidence_only": decision.self_attested_evidence_only,
        "overall_receipt": to_json_safe(decision.overall_receipt),
    }
