from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Protocol, Set, Tuple

from pydantic import BaseModel, Field, model_validator

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import VerifyKey
except Exception:  # pragma: no cover - optional import path for constrained environments
    BadSignatureError = Exception
    VerifyKey = None

FrameType = Literal["ASSERT", "REQUEST", "DELEGATE", "COMMIT", "HYPOTHESIZE", "QUERY", "RELAY", "ENDORSE", "DISSENT", "RETRACT"]
WarrantType = Literal["OBSERVED", "DERIVED", "RETRIEVED", "REPORTED", "ASSUMED"]
PayloadMode = Literal["legible", "opaque"]
GroundsStatus = Literal["resolved", "unresolved", "stale", "malformed", "inaccessible_under_profile"]
AuthorityStatus = Literal["resolved", "unresolved", "expired", "malformed", "inaccessible_under_profile"]
ResolutionPolicy = Literal["hard_fail", "soft_flag", "profile_unsupported"]


CANONICAL_FIELD_ORDER = [
    "frame",
    "mode",
    "from",
    "to",
    "in_reply_to",
    "parents",
    "targets",
    "ordering_anchor",
    "warrant",
    "authority_receipts",
    "content",
]

CORE_CANONICAL_FIELD_ORDER = [field for field in CANONICAL_FIELD_ORDER if field != "authority_receipts"]


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(k)): _normalize_json_value(v) for k, v in value.items()}
    return value


def canonicalize_json_bytes(value: Any) -> bytes:
    normalized = _normalize_json_value(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _parse_iso8601(value: str) -> Optional[datetime]:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class GroundsResolution(BaseModel):
    ref: str
    status: GroundsStatus
    detail: Optional[str] = None


class AuthorityResolution(BaseModel):
    ref: str
    status: AuthorityStatus
    detail: Optional[str] = None


class GroundsResolver(Protocol):
    def resolve(self, ref: str) -> GroundsResolution:
        ...


class AuthorityResolver(Protocol):
    def resolve(self, ref: str) -> AuthorityResolution:
        ...


class FailClosedResolver:
    def resolve(self, ref: str) -> GroundsResolution:
        return GroundsResolution(ref=ref, status="unresolved", detail="no resolver configured")


class FailClosedAuthorityResolver:
    def resolve(self, ref: str) -> AuthorityResolution:
        return AuthorityResolution(ref=ref, status="unresolved", detail="no authority resolver configured")


class StaticGroundsResolver:
    def __init__(self, known_refs: Optional[Set[str]] = None, status_overrides: Optional[Dict[str, GroundsStatus]] = None):
        self.known_refs = known_refs or set()
        self.status_overrides = status_overrides or {}

    def resolve(self, ref: str) -> GroundsResolution:
        if ref in self.status_overrides:
            return GroundsResolution(ref=ref, status=self.status_overrides[ref])
        if ref in self.known_refs:
            return GroundsResolution(ref=ref, status="resolved")
        return GroundsResolution(ref=ref, status="unresolved")


class StaticAuthorityResolver:
    def __init__(self, known_refs: Optional[Set[str]] = None, status_overrides: Optional[Dict[str, AuthorityStatus]] = None):
        self.known_refs = known_refs or set()
        self.status_overrides = status_overrides or {}

    def resolve(self, ref: str) -> AuthorityResolution:
        if ref in self.status_overrides:
            return AuthorityResolution(ref=ref, status=self.status_overrides[ref])
        if ref in self.known_refs:
            return AuthorityResolution(ref=ref, status="resolved")
        return AuthorityResolution(ref=ref, status="unresolved")


class SignatureVerifier(Protocol):
    def verify(self, sig: str, message_bytes: bytes, signer: str) -> bool:
        ...


class StubSignatureVerifier:
    def verify(self, sig: str, message_bytes: bytes, signer: str) -> bool:
        if not sig or not sig.startswith("ed25519:"):
            return False
        payload = sig.split(":", 1)[1]
        if len(payload) < 32:
            return False
        try:
            base64.b64decode(payload + "===", validate=False)
            return True
        except Exception:
            return False


class AcceptAllSignatureVerifier:
    def verify(self, sig: str, message_bytes: bytes, signer: str) -> bool:
        return True


class DeterministicSignatureVerifier:
    def verify(self, sig: str, message_bytes: bytes, signer: str) -> bool:
        digest = hashlib.sha256((signer + ":").encode("utf-8") + message_bytes).hexdigest()
        return sig == f"testsig:{digest}"


class Ed25519SignatureVerifier:
    def __init__(self, public_keys: Optional[Dict[str, str]] = None):
        self.public_keys = public_keys or {}

    def verify(self, sig: str, message_bytes: bytes, signer: str) -> bool:
        if VerifyKey is None or not sig.startswith("ed25519:"):
            return False
        key_material = self.public_keys.get(signer)
        if not key_material:
            return False
        try:
            verify_key = VerifyKey(base64.b64decode(key_material + "===", validate=False))
            verify_key.verify(message_bytes, base64.b64decode(sig.split(":", 1)[1] + "===", validate=False))
            return True
        except (BadSignatureError, ValueError, TypeError):
            return False


class Warrant(BaseModel):
    type: WarrantType
    confidence: Optional[Tuple[float, float]] = None
    grounds: List[str] = Field(default_factory=list)


class GroundsResolutionPolicy(BaseModel):
    unresolved_observed: ResolutionPolicy = "hard_fail"
    unresolved_derived: ResolutionPolicy = "hard_fail"
    unresolved_retrieved: ResolutionPolicy = "hard_fail"
    unresolved_reported: ResolutionPolicy = "hard_fail"
    confidence_without_method_artifact: ResolutionPolicy = "soft_flag"


class AuthorityReceipt(BaseModel):
    kind: Literal["human_approval", "local_policy", "sandbox_policy"]
    receipt_ref: str
    scope: Literal["state_change", "package_install", "shell_exec", "network_fetch", "general"] = "general"
    issuer: str
    bound_message_id: Optional[str] = None
    bound_parent_ids: List[str] = Field(default_factory=list)
    expires_at: Optional[str] = None
    nonce: Optional[str] = None


class AttestMessage(BaseModel):
    id: Optional[str] = None
    frame: FrameType
    mode: PayloadMode
    from_: str = Field(alias="from")
    to: Optional[str] = None
    in_reply_to: Optional[str] = None
    parents: List[str] = Field(default_factory=list)
    targets: List[str] = Field(default_factory=list)
    ordering_anchor: Tuple[str, int]
    warrant: Optional[Warrant] = None
    authority_receipts: List[AuthorityReceipt] = Field(default_factory=list)
    content: Any
    sig: Optional[str] = None

    def canonical_dict(self) -> Dict[str, Any]:
        canonical = {
            "frame": self.frame,
            "mode": self.mode,
            "from": self.from_,
            "to": self.to,
            "in_reply_to": self.in_reply_to,
            "parents": self.parents,
            "targets": self.targets,
            "ordering_anchor": list(self.ordering_anchor),
            "warrant": self.warrant.model_dump() if self.warrant else None,
            "authority_receipts": [receipt.model_dump() for receipt in self.authority_receipts],
            "content": self.content,
        }
        return {field: canonical[field] for field in CANONICAL_FIELD_ORDER}

    def canonical_core_dict(self) -> Dict[str, Any]:
        canonical = self.canonical_dict()
        return {field: canonical[field] for field in CORE_CANONICAL_FIELD_ORDER}

    def canonical_bytes(self) -> bytes:
        return canonicalize_json_bytes(self.canonical_dict())

    def canonical_core_bytes(self) -> bytes:
        return canonicalize_json_bytes(self.canonical_core_dict())

    def compute_id(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def compute_core_id(self) -> str:
        return hashlib.sha256(self.canonical_core_bytes()).hexdigest()

    @model_validator(mode="after")
    def check_id_consistency(self) -> "AttestMessage":
        if self.id is not None:
            computed = self.compute_id()
            if self.id != computed:
                raise ValueError(f"ID mismatch: provided {self.id}, computed {computed}")
        return self


class DeploymentProfile(BaseModel):
    name: str = "default"
    profile_id: Optional[str] = None
    profile_version: Optional[str] = None
    signature_required_frames: Set[FrameType] = Field(default_factory=lambda: {"ASSERT", "ENDORSE", "DISSENT"})
    signature_required_retract_when_warranted: bool = True
    signature_recommended_frames: Set[FrameType] = Field(default_factory=lambda: {"COMMIT"})
    state_changing_frames: Set[FrameType] = Field(default_factory=lambda: {"COMMIT"})
    authority_required_frames: Set[FrameType] = Field(default_factory=lambda: {"COMMIT", "ENDORSE"})
    accepted_authority_kinds: Set[str] = Field(default_factory=lambda: {"human_approval", "local_policy", "sandbox_policy"})
    require_local_authority_chain_for_state_change: bool = True
    external_authority_prefixes: List[str] = Field(default_factory=lambda: ["src:sentry-event", "src:external-issue", "src:ticket", "src:web", "src:github-issue"])
    local_authority_prefixes: List[str] = Field(default_factory=lambda: ["approval:", "policy:", "sandbox:", "receipt:"])
    grounds_namespaces: Dict[str, str] = Field(
        default_factory=lambda: {
            "msg": "message identifiers",
            "tool": "tool or execution receipts",
            "src": "external source citations",
            "doc": "document anchors",
            "receipt": "authority or execution receipts",
            "policy": "local policy artifacts",
        }
    )
    grounds_resolution_policy: GroundsResolutionPolicy = Field(default_factory=GroundsResolutionPolicy)
    warrant_strength_order: Dict[WarrantType, int] = Field(
        default_factory=lambda: {
            "OBSERVED": 5,
            "DERIVED": 4,
            "RETRIEVED": 3,
            "REPORTED": 2,
            "ASSUMED": 1,
        }
    )
    relay_parent_prefixes: List[str] = Field(default_factory=lambda: ["h:upstream-relay", "relay:hop:"])
    independence_policy_name: str = "declared-lineage-default"
    ordering_anchor_semantics: str = "timestamp-sequence-total-order"
    signer_public_keys: Dict[str, str] = Field(default_factory=dict)

    def strength_of(self, warrant_type: WarrantType) -> int:
        return self.warrant_strength_order.get(warrant_type, 0)

    def namespace_allowed(self, ref: str) -> bool:
        if ":" not in ref:
            return False
        namespace = ref.split(":", 1)[0]
        return namespace in self.grounds_namespaces


DEFAULT_PROFILE_PATH = Path(__file__).with_name("attest-profile-default-v02.json")


def load_profile(path: Optional[str] = None) -> DeploymentProfile:
    target = Path(path) if path else DEFAULT_PROFILE_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    return DeploymentProfile.model_validate(data)


class AttestVerifier:
    def __init__(
        self,
        profile: Optional[DeploymentProfile] = None,
        grounds_resolver: Optional[GroundsResolver] = None,
        authority_resolver: Optional[AuthorityResolver] = None,
        signature_verifier: Optional[SignatureVerifier] = None,
    ):
        self.profile = profile or load_profile()
        self.grounds_resolver = grounds_resolver or FailClosedResolver()
        self.authority_resolver = authority_resolver or FailClosedAuthorityResolver()
        self.signature_verifier = signature_verifier or Ed25519SignatureVerifier(self.profile.signer_public_keys)

    def max_chain_strength(self, chain: List[AttestMessage]) -> int:
        strengths = [self.profile.strength_of(m.warrant.type) for m in chain if m.warrant]
        return max(strengths, default=0)

    def _resolve_grounds(self, grounds: List[str]) -> List[GroundsResolution]:
        if not grounds:
            return []
        return [self.grounds_resolver.resolve(ref) for ref in grounds]

    def _grounds_all_resolved(self, resolutions: List[GroundsResolution]) -> bool:
        return bool(resolutions) and all(resolution.status == "resolved" for resolution in resolutions)

    def _signature_required(self, msg: AttestMessage) -> bool:
        if msg.frame in self.profile.signature_required_frames:
            return True
        if msg.frame == "RETRACT" and msg.warrant and self.profile.signature_required_retract_when_warranted:
            return True
        return False

    def _relay_parent_present(self, msg: AttestMessage) -> bool:
        return any(any(parent.startswith(prefix) for prefix in self.profile.relay_parent_prefixes) for parent in msg.parents)

    def _grounds_reference_external_authority(self, grounds: List[str]) -> bool:
        return any(any(g.startswith(prefix) for prefix in self.profile.external_authority_prefixes) for g in grounds)

    def _authority_receipt_binds_message(self, receipt: AuthorityReceipt, msg: AttestMessage, computed_core_id: str) -> bool:
        if receipt.bound_message_id != computed_core_id:
            return False
        if receipt.bound_parent_ids != msg.parents:
            return False
        return True

    def _authority_receipt_unexpired(self, receipt: AuthorityReceipt) -> bool:
        if receipt.expires_at is None:
            return True
        expires = _parse_iso8601(receipt.expires_at)
        if expires is None:
            return False
        return expires >= datetime.now(timezone.utc)

    def _evaluate_authority_receipts(self, msg: AttestMessage, computed_core_id: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if msg.frame not in self.profile.authority_required_frames:
            return True, errors
        if not msg.authority_receipts:
            errors.append("AUTHORITY_RECEIPT_REQUIRED")
            return False, errors

        valid_receipt_found = False
        for receipt in msg.authority_receipts:
            resolution = self.authority_resolver.resolve(receipt.receipt_ref)
            if resolution.status != "resolved":
                errors.append(f"AUTHORITY_RECEIPT_UNRESOLVED:{receipt.receipt_ref}")
                continue
            if receipt.kind not in self.profile.accepted_authority_kinds:
                errors.append(f"AUTHORITY_KIND_UNACCEPTED:{receipt.kind}")
                continue
            if not any(receipt.receipt_ref.startswith(prefix) for prefix in self.profile.local_authority_prefixes):
                errors.append(f"AUTHORITY_RECEIPT_PREFIX_INVALID:{receipt.receipt_ref}")
                continue
            if not self._authority_receipt_binds_message(receipt, msg, computed_core_id):
                errors.append("AUTHORITY_RECEIPT_BINDING_INVALID")
                continue
            if not self._authority_receipt_unexpired(receipt):
                errors.append("AUTHORITY_RECEIPT_EXPIRED")
                continue
            if not receipt.nonce:
                errors.append("AUTHORITY_RECEIPT_NONCE_REQUIRED")
                continue
            valid_receipt_found = True

        if not valid_receipt_found and not errors:
            errors.append("AUTHORITY_RECEIPT_REQUIRED")
        return valid_receipt_found, errors

    def _warrant_required(self, msg: AttestMessage) -> bool:
        if msg.frame in ("ASSERT", "HYPOTHESIZE", "ENDORSE", "DISSENT"):
            return True
        if msg.frame == "RETRACT":
            return True
        if msg.frame == "COMMIT":
            return True
        return False

    def _validate_ground_namespaces(self, grounds: List[str]) -> List[str]:
        issues: List[str] = []
        for ground in grounds:
            if not self.profile.namespace_allowed(ground):
                issues.append(f"GROUND_NAMESPACE_UNSUPPORTED:{ground}")
        return issues

    def _apply_ground_resolution_policy(self, warrant_type: WarrantType, unresolved: List[str], result: Dict[str, List[str]]) -> None:
        policy_map = {
            "OBSERVED": self.profile.grounds_resolution_policy.unresolved_observed,
            "DERIVED": self.profile.grounds_resolution_policy.unresolved_derived,
            "RETRIEVED": self.profile.grounds_resolution_policy.unresolved_retrieved,
            "REPORTED": self.profile.grounds_resolution_policy.unresolved_reported,
        }
        policy = policy_map.get(warrant_type, "hard_fail")
        if warrant_type == "OBSERVED":
            code = "OBSERVED_GROUNDS_NOT_ARTIFACT_BACKED"
        else:
            code = "GROUNDS_UNRESOLVED"
        if policy == "hard_fail":
            result["hard_fail"].append(code)
        elif policy == "soft_flag":
            result["soft_flag"].append(code)
        else:
            result["pass_scope_limit"].append(code)
        result["soft_flag"].append(f"GROUND_RESOLUTION_FAILURES:{','.join(unresolved)}")

    def _build_known_message_map(self, known_messages: List[AttestMessage]) -> Dict[str, AttestMessage]:
        message_map: Dict[str, AttestMessage] = {}
        for message in known_messages:
            message_map[message.compute_id()] = message
            if message.id:
                message_map[message.id] = message
            for target in message.targets:
                if message.frame == "RETRACT":
                    message_map.setdefault(target, message)
        return message_map

    def _is_retracted_at_or_before_message(self, parent_id: str, msg: AttestMessage, known_messages: List[AttestMessage]) -> bool:
        for candidate in known_messages:
            if candidate.frame != "RETRACT":
                continue
            if parent_id not in candidate.targets:
                continue
            if candidate.ordering_anchor <= msg.ordering_anchor:
                return True
        return False

    def _transitively_relies_on_retracted_target(self, msg: AttestMessage, known_messages: List[AttestMessage]) -> bool:
        if msg.frame not in ("ASSERT", "COMMIT", "ENDORSE"):
            return False
        known_map = self._build_known_message_map(known_messages)
        visited: Set[str] = set()
        queue = deque(msg.parents)
        while queue:
            parent_id = queue.popleft()
            if parent_id in visited:
                continue
            visited.add(parent_id)
            if self._is_retracted_at_or_before_message(parent_id, msg, known_messages):
                return True
            parent_message = known_map.get(parent_id)
            if parent_message:
                queue.extend(parent_message.parents)
        return False

    def verify(
        self,
        msg: AttestMessage,
        adopted_chain: Optional[List[AttestMessage]] = None,
        known_messages: Optional[List[AttestMessage]] = None,
    ) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {"hard_fail": [], "soft_flag": [], "pass_scope_limit": []}
        adopted_chain = adopted_chain or []
        known_messages = known_messages or []

        computed_id = msg.compute_id()
        computed_core_id = msg.compute_core_id()
        if msg.id is not None and msg.id != computed_id:
            result["hard_fail"].append("ID_MISMATCH")

        if self._warrant_required(msg) and msg.warrant is None:
            result["hard_fail"].append("WARRANT_REQUIRED")

        grounds = msg.warrant.grounds if msg.warrant else []
        result["hard_fail"].extend(self._validate_ground_namespaces(grounds))
        ground_resolutions = self._resolve_grounds(grounds)

        if msg.warrant and msg.warrant.type in ("OBSERVED", "RETRIEVED", "REPORTED") and not msg.warrant.grounds:
            result["hard_fail"].append("EVIDENTIAL_WARRANT_MISSING_GROUNDS")

        if msg.warrant and msg.warrant.type in ("OBSERVED", "DERIVED", "RETRIEVED", "REPORTED"):
            if msg.warrant.grounds and not self._grounds_all_resolved(ground_resolutions):
                unresolved = [resolution.ref for resolution in ground_resolutions if resolution.status != "resolved"]
                self._apply_ground_resolution_policy(msg.warrant.type, unresolved, result)
                if msg.warrant.confidence and self.profile.grounds_resolution_policy.confidence_without_method_artifact == "soft_flag":
                    result["soft_flag"].append("CONFIDENCE_DOWNGRADED_TO_ASSUMED")

        if msg.frame == "ENDORSE" and msg.warrant:
            declared = self.profile.strength_of(msg.warrant.type)
            chain_max = self.max_chain_strength(adopted_chain)
            if declared > chain_max:
                prior_grounds = [gg for m in adopted_chain for gg in (m.warrant.grounds if m.warrant else [])]
                new_grounds = [g for g in msg.warrant.grounds if g not in prior_grounds]
                new_ground_resolutions = self._resolve_grounds(new_grounds)
                if not new_grounds or not self._grounds_all_resolved(new_ground_resolutions):
                    result["hard_fail"].append("ENDORSE_CEILING_VIOLATION")
                else:
                    result["soft_flag"].append(f"ENDORSE_INDEPENDENCE_SHOULD_BE_CHECKED:{self.profile.independence_policy_name}")

        signature_enforced = bool(
            self.profile.signature_required_frames or self.profile.signature_recommended_frames or self.profile.signature_required_retract_when_warranted
        )
        if self._signature_required(msg):
            if not msg.sig:
                result["hard_fail"].append("SIGNATURE_REQUIRED_BY_PROFILE")
            elif not self.signature_verifier.verify(msg.sig, msg.canonical_bytes(), msg.from_):
                result["hard_fail"].append("SIGNATURE_INVALID")
        elif signature_enforced and msg.sig and not self.signature_verifier.verify(msg.sig, msg.canonical_bytes(), msg.from_):
            result["hard_fail"].append("SIGNATURE_INVALID")
        elif msg.frame in self.profile.signature_recommended_frames and not msg.sig:
            result["soft_flag"].append("SIGNATURE_RECOMMENDED_BY_PROFILE")

        if msg.frame == "COMMIT" and self._relay_parent_present(msg):
            result["soft_flag"].append("RELAY_UPTAKE_MISSING")

        authority_valid, authority_errors = self._evaluate_authority_receipts(msg, computed_core_id)
        result["hard_fail"].extend(authority_errors)

        has_external_grounds = bool(msg.warrant and self._grounds_reference_external_authority(msg.warrant.grounds))

        if (
            self.profile.require_local_authority_chain_for_state_change
            and msg.frame in self.profile.authority_required_frames
            and not authority_valid
        ):
            result["hard_fail"].append("LOCAL_AUTHORITY_CHAIN_REQUIRED")

        if msg.frame == "COMMIT" and has_external_grounds:
            if authority_valid:
                result["soft_flag"].append("EXTERNAL_EVIDENCE_PRESENT_WITH_LOCAL_AUTHORITY")
            else:
                result["soft_flag"].append("EXTERNAL_TELEMETRY_USED_AS_EXECUTION_AUTHORITY")

        if msg.frame == "ENDORSE" and has_external_grounds:
            if authority_valid:
                result["soft_flag"].append("EXTERNAL_EVIDENCE_PRESENT_WITH_LOCAL_AUTHORITY")
            else:
                result["soft_flag"].append("EXTERNAL_REMEDIATION_LAUNDERED_INTO_AUTHORITY")

        if self._transitively_relies_on_retracted_target(msg, known_messages):
            result["hard_fail"].append("RETRACTED_TARGET_STILL_RELIED_ON")

        relay_hops = [parent for parent in msg.parents if parent.startswith("relay:hop:")]
        if msg.frame == "ASSERT" and len(relay_hops) >= 2:
            result["pass_scope_limit"].append("RELAY_CHAIN_VISIBLE")

        if msg.mode == "opaque":
            result["pass_scope_limit"].append("OPAQUE_PAYLOAD_TRUTH_BINDING_LIMIT")

        return result
