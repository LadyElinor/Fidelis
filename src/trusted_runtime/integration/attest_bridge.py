from __future__ import annotations

"""Attest bridge seam for TrustedRuntime.

This module implements a first-pass Attest-shaped integration seam.
It captures and partially executes the contract for using Attest as the typed
message layer between TrustedRuntime components while preserving
TrustedRuntime as the runtime/orchestration layer and CER as the durable
receipt ledger.

Design constraints captured here:
- ENDORSE means adoption, not mere agreement.
- COMMIT is runtime-owned and must not be emitted by ordinary adapters.
- DISSENT is non-erasing and must survive into final review packets unless
  explicitly retracted or superseded by reference.
- Independence is computed and scored by TrustedRuntime, not assumed from the
  mere presence of multiple adapter outputs.
- CER receipts must store profile-relative Attest verification state, not only
  raw Attest IDs/hashes.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

import importlib.util
import sys

from trusted_runtime.authority_store import AuthorityGrantStore
from trusted_runtime.shared.models import ProposedAction


class AttestVerificationState(BaseModel):
    """Profile-relative verifier result to persist into review packets and CER."""

    message_id: str
    canonical_hash: str
    profile_id: str
    profile_version: str
    profile_hash: str
    verifier_version: str
    hard_fail: list[str] = Field(default_factory=list)
    soft_flag: list[str] = Field(default_factory=list)
    pass_scope_limit: list[str] = Field(default_factory=list)
    decision_effect: Literal["PASS", "REVIEW", "BLOCK", "UNVERIFIABLE"]
    known_message_set_hash: str
    grounds_resolver_name: str = "unconfigured"
    grounds_resolver_config_hash: str = ""
    authority_resolver_name: str = "unconfigured"
    authority_resolver_config_hash: str = ""
    signature_verifier_name: str = "unconfigured"
    signature_verifier_config_hash: str = ""
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AttestResolverInputs(BaseModel):
    """Resolver surface for a verification call, post grant-store split.

    Trust boundary (structural, not behavioral): authority resolution comes
    ONLY from the orchestrator-owned AuthorityGrantStore handed to the bridge
    at construction, and grounds resolution ONLY from a runtime-held check
    set. That check set is seeded by runtime_message_refs, which the runtime
    derives from its own observed evidence, and may be expanded by
    suggested_message_refs without making any suggestion resolved by virtue of
    being suggested. Nothing in this model can mark anything resolved, confer
    a grant, or override a status.

    Proposer influence is suggestion-only: suggested_*_refs expand what gets
    CHECKED (each suggestion is resolved against runtime-held state and the
    outcome reported), never what counts as RESOLVED. A suggestion that
    runtime-held state does not already resolve fails exactly as if the
    verifier had discovered the ref itself.

    injection_attempted_keys records retired proposer authority keys found in
    action context. Those keys are never consumed; their presence is surfaced
    as PROPOSER_AUTHORITY_INJECTION_ATTEMPTED:<key> soft flags, because
    probing a closed channel is itself signal.
    """

    runtime_message_refs: list[str] = Field(default_factory=list)
    suggested_message_refs: list[str] = Field(default_factory=list)
    suggested_authority_refs: list[str] = Field(default_factory=list)
    injection_attempted_keys: list[str] = Field(default_factory=list)

    def injection_flags(self) -> list[str]:
        return [
            f"PROPOSER_AUTHORITY_INJECTION_ATTEMPTED:{key}"
            for key in self.injection_attempted_keys
        ]


class IndependenceSignals(BaseModel):
    """Runtime-side independence scoring surface derived from Attest structure."""

    shared_grounds: list[str] = Field(default_factory=list)
    shared_parents: list[str] = Field(default_factory=list)
    same_signer: bool = False
    same_adapter_family: bool = False
    same_operator: bool = False
    shared_external_sources: list[str] = Field(default_factory=list)
    overlap_reasons: list[str] = Field(default_factory=list)
    independence_score: float = 0.0
    policy_result: Literal["independent", "correlated", "same-origin", "unknown"] = "unknown"


class AttestReviewPacket(BaseModel):
    """Augments a runtime review packet with Attest-layer governance state."""

    layer_name: str
    frame: Literal["REQUEST", "QUERY", "ASSERT", "HYPOTHESIZE", "DISSENT", "ENDORSE", "COMMIT", "RETRACT"]
    message_id: str
    verification: AttestVerificationState
    independence: IndependenceSignals | None = None
    unresolved_dissent_ids: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    adopts: list[str] = Field(default_factory=list)
    adoption_reason: str | None = None
    notes: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class AttestBridgeConfig:
    """Minimal bridge configuration surface.

    A real implementation should extend this with concrete import paths, active
    deployment profile selection, signer identity, profile pinning, and
    whitelists for any components explicitly permitted to emit COMMIT.
    """

    profile_id: str = "attest-default-v02"
    verifier_version: str = "trusted-runtime-attest-bridge-draft-0"
    runtime_signer: str = "trusted-runtime:orchestrator"
    commit_whitelist: tuple[str, ...] = ("trusted-runtime:orchestrator",)
    signature_verifier_mode: Literal["accept-all", "deterministic-test", "ed25519-profile"] = "accept-all"
    profile_path: Path | None = None


class AttestBridge:
    """First-pass TrustedRuntime <-> Attest integration seam.

    Responsibilities:
    1. Wrap ingress and adapter outputs into Attest-shaped messages.
    2. Verify those messages under the active Attest deployment profile.
    3. Compute independence/correlation signals from message structure.
    4. Surface profile-relative verification state into review packets.
    5. Emit CER-ready receipt fragments including Attest IDs, hashes, profile
       identity, and known-message-set hashing.

    Current truth boundary:
    - a real dynamic import/wiring path exists when AttestAgentConlang is present
    - fallback degrades explicitly to stub / UNVERIFIABLE when the dependency is absent or the real path fails
    - the current real-path verifier wiring is structural/profile-aware, but not yet a strong cryptographic trust claim by itself
    """

    def __init__(
        self,
        config: AttestBridgeConfig | None = None,
        *,
        attest_root: Path | None = None,
        authority_store: "AuthorityGrantStore | None" = None,
    ):
        self.config = config or AttestBridgeConfig()
        self.attest_root = attest_root
        # Runtime-owned trust root. Constructor-injected by the orchestrator;
        # never derived from message content or proposer context.
        self.authority_store = authority_store
        self._real_attest = self._load_real_attest() if attest_root is not None else None

    def _load_real_attest(self) -> dict[str, Any] | None:
        if self.attest_root is None:
            return None
        if not (self.attest_root / "attest_ref_impl.py").exists():
            return None
        module_path = self.attest_root / "attest_ref_impl.py"
        module_name = f"trusted_runtime_attest_ref_impl_{sha256(str(module_path).encode('utf-8')).hexdigest()[:12]}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            # The module must be registered in sys.modules BEFORE exec_module:
            # attest_ref_impl uses `from __future__ import annotations`, so all
            # pydantic models resolve their field types lazily via
            # sys.modules[cls.__module__]. Without this line, any model whose
            # validator builds after import (e.g. GroundsResolution) raises
            # PydanticUserError at first use, the bridge's bare except swallows
            # it, and verification silently degrades to the design stub. This
            # exact failure shipped as a green test suite once already.
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(module_name, None)
                raise
        except Exception:
            return None
        return {
            "AcceptAllSignatureVerifier": getattr(module, "AcceptAllSignatureVerifier"),
            "DeterministicSignatureVerifier": getattr(module, "DeterministicSignatureVerifier", None),
            "Ed25519SignatureVerifier": getattr(module, "Ed25519SignatureVerifier", None),
            "AttestMessage": getattr(module, "AttestMessage"),
            "AttestVerifier": getattr(module, "AttestVerifier"),
            "StaticAuthorityResolver": getattr(module, "StaticAuthorityResolver"),
            "AuthorityResolution": getattr(module, "AuthorityResolution"),
            "StaticGroundsResolver": getattr(module, "StaticGroundsResolver"),
            "load_profile": getattr(module, "load_profile"),
        }

    @property
    def real_available(self) -> bool:
        return self._real_attest is not None

    def _stub_verification(
        self,
        *,
        message_hash: str,
        known_hash: str,
        evaluated_at: datetime | None,
        resolver_inputs: AttestResolverInputs | None = None,
        extra_soft_flags: list[str] | None = None,
    ) -> AttestVerificationState:
        soft_flags = ["ATTEST_BRIDGE_DESIGN_STUB_ONLY"]
        if extra_soft_flags:
            soft_flags.extend(extra_soft_flags)
        resolver_inputs = resolver_inputs or AttestResolverInputs()
        soft_flags.extend(resolver_inputs.injection_flags())
        return AttestVerificationState(
            message_id=message_hash,
            canonical_hash=message_hash,
            profile_id=self.config.profile_id,
            profile_version="draft",
            profile_hash=sha256(self.config.profile_id.encode("utf-8")).hexdigest(),
            verifier_version=self.config.verifier_version,
            hard_fail=[],
            soft_flag=soft_flags,
            pass_scope_limit=[],
            decision_effect="UNVERIFIABLE",
            known_message_set_hash=known_hash,
            grounds_resolver_name="stub-none",
            grounds_resolver_config_hash=sha256(self._stable_json(sorted(resolver_inputs.runtime_message_refs)).encode("utf-8")).hexdigest(),
            authority_resolver_name="stub-none",
            authority_resolver_config_hash=(
                self.authority_store.state_digest(evaluated_at)
                if self.authority_store is not None
                else sha256(b"no-authority-store").hexdigest()
            ),
            signature_verifier_name=f"stub-none:{self.config.signature_verifier_mode}",
            signature_verifier_config_hash=sha256(self.config.signature_verifier_mode.encode("utf-8")).hexdigest(),
            evaluated_at=evaluated_at or datetime.now(timezone.utc),
        )

    def _build_signature_verifier(self, profile: Any) -> tuple[Any, str]:
        if self._real_attest is None:
            raise RuntimeError("real Attest path unavailable")

        mode = self.config.signature_verifier_mode
        if mode == "accept-all":
            verifier = self._real_attest["AcceptAllSignatureVerifier"]()
        elif mode == "deterministic-test":
            verifier_cls = self._real_attest.get("DeterministicSignatureVerifier")
            if verifier_cls is None:
                raise RuntimeError("DeterministicSignatureVerifier unavailable")
            verifier = verifier_cls()
        elif mode == "ed25519-profile":
            verifier_cls = self._real_attest.get("Ed25519SignatureVerifier")
            if verifier_cls is None:
                raise RuntimeError("Ed25519SignatureVerifier unavailable")
            verifier = verifier_cls(getattr(profile, "signer_public_keys", {}))
        else:
            raise RuntimeError(f"unsupported signature verifier mode: {mode}")

        return verifier, sha256(mode.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Message wrapping rules
    # ------------------------------------------------------------------

    def wrap_ingress_request(self, action: ProposedAction) -> dict[str, Any]:
        """Convert a runtime input into an Attest REQUEST/QUERY envelope.

        Policy intent:
        - external/operator/task ingress becomes REQUEST or QUERY
        - this is the root message for downstream adoption/provenance chains
        """
        return {
            "frame": "REQUEST",
            "mode": "legible",
            "from": "trusted-runtime:ingress",
            "to": "trusted-runtime:orchestrator",
            "parents": [],
            "ordering_anchor": [action.timestamp.isoformat().replace("+00:00", "Z"), 1],
            "content": {
                "action_id": action.id,
                "description": action.description,
                "context": action.context,
                "proposed_by": action.proposed_by,
            },
        }

    def wrap_adapter_assert(
        self,
        *,
        layer_name: str,
        content: dict[str, Any],
        grounds: list[str],
        parents: list[str],
        confidence_interval: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        """Emit an ASSERT for normal evaluator output.

        Adapters should default to ASSERT or DISSENT, not ENDORSE.
        """
        warrant: dict[str, Any] = {"type": "DERIVED", "grounds": grounds}
        if confidence_interval is not None:
            warrant["confidence"] = list(confidence_interval)
        return {
            "frame": "ASSERT",
            "mode": "legible",
            "from": f"trusted-runtime:{layer_name}",
            "to": "trusted-runtime:orchestrator",
            "parents": parents,
            "ordering_anchor": self.next_anchor(),
            "warrant": warrant,
            "content": content,
        }

    def wrap_adapter_dissent(
        self,
        *,
        layer_name: str,
        content: dict[str, Any],
        grounds: list[str],
        parents: list[str],
    ) -> dict[str, Any]:
        return {
            "frame": "DISSENT",
            "mode": "legible",
            "from": f"trusted-runtime:{layer_name}",
            "to": "trusted-runtime:orchestrator",
            "parents": parents,
            "ordering_anchor": self.next_anchor(),
            "warrant": {"type": "DERIVED", "grounds": grounds},
            "content": content,
        }

    def wrap_endorsement(
        self,
        *,
        layer_name: str,
        content: dict[str, Any],
        grounds: list[str],
        parents: list[str],
        adopts: list[str],
        adoption_reason: str,
    ) -> dict[str, Any]:
        """Emit ENDORSE only for explicit trust-boundary uptake.

        Integration invariant: ENDORSE is adoption, not agreement.
        A real implementation should reject ENDORSE generation unless both
        `adopts` and `adoption_reason` are non-empty.
        """
        if not adopts or not adoption_reason.strip():
            raise ValueError("ENDORSE requires adopts[] and adoption_reason")
        content = dict(content)
        content.setdefault("adopts", adopts)
        content.setdefault("adoption_reason", adoption_reason)
        return {
            "frame": "ENDORSE",
            "mode": "legible",
            "from": f"trusted-runtime:{layer_name}",
            "to": "trusted-runtime:orchestrator",
            "parents": parents,
            "ordering_anchor": self.next_anchor(),
            "warrant": {"type": "DERIVED", "grounds": grounds},
            "content": content,
        }

    def wrap_runtime_commit(
        self,
        *,
        runtime_actor: str,
        content: dict[str, Any],
        parents: list[str],
        action_scope: Literal["state_change", "package_install", "shell_exec", "network_fetch", "general"],
        deontic: dict[str, Any],
    ) -> dict[str, Any]:
        """Emit COMMIT only at the runtime/orchestrator boundary.

        Integration invariant: ordinary evaluators may not authorize execution.
        """
        if runtime_actor not in self.config.commit_whitelist:
            raise ValueError(f"COMMIT emitter not whitelisted: {runtime_actor}")
        return {
            "frame": "COMMIT",
            "mode": "legible",
            "from": runtime_actor,
            "to": "trusted-runtime:executor",
            "parents": parents,
            "ordering_anchor": self.next_anchor(),
            "action_scope": action_scope,
            "deontic": deontic,
            "content": content,
        }

    # ------------------------------------------------------------------
    # Verification / policy surface
    # ------------------------------------------------------------------

    def verify_for_runtime(
        self,
        message: dict[str, Any],
        known_messages: list[dict[str, Any]],
        *,
        resolver_inputs: AttestResolverInputs | None = None,
        evaluated_at: datetime | None = None,
    ) -> AttestVerificationState:
        """Placeholder verification entry point.

        Real implementation responsibilities:
        - canonicalize and compute Attest message ID/hash
        - hash active profile into `profile_hash`
        - hash known message set into `known_message_set_hash`
        - run AttestVerifier.verify(...)
        - map result into PASS / REVIEW / BLOCK / UNVERIFIABLE
        """
        resolver_inputs = resolver_inputs or AttestResolverInputs()
        message_blob = self._stable_json(message)
        message_hash = sha256(message_blob.encode("utf-8")).hexdigest()
        known_hash = sha256(self._stable_json(known_messages).encode("utf-8")).hexdigest()
        verification_instant = evaluated_at or datetime.now(timezone.utc)
        # Suggested message refs are CHECKED against runtime-held state and the
        # outcomes reported (see suggested_message_check_results in the engine
        # summary); they never enter the resolvable set. StaticGroundsResolver
        # membership IS resolution, so seeding it with suggestions would let a
        # proposer self-certify its own warrant grounds — the retired
        # attest_known_message_refs flow under a new key name.
        grounds_resolver_config = {
            "runtime_message_refs": sorted(resolver_inputs.runtime_message_refs),
        }

        if self._real_attest is not None:
            try:
                profile = self._real_attest["load_profile"](str(self.config.profile_path) if self.config.profile_path is not None else None)
                attest_message = self._real_attest["AttestMessage"].model_validate(message)
                attest_known_messages = [self._real_attest["AttestMessage"].model_validate(item) for item in known_messages]
                grounds_resolver = self._real_attest["StaticGroundsResolver"](
                    set(resolver_inputs.runtime_message_refs),
                )
                if self.authority_store is not None:
                    authority_resolver = _StoreAuthorityResolverAdapter(
                        module=self._real_attest,
                        store=self.authority_store,
                        at=verification_instant,
                    )
                    authority_resolver_hash = self.authority_store.state_digest(
                        verification_instant
                    )
                else:
                    authority_resolver = self._real_attest["StaticAuthorityResolver"](set())
                    authority_resolver_hash = sha256(b"no-authority-store").hexdigest()
                signature_verifier, signature_verifier_config_hash = self._build_signature_verifier(profile)
                verifier = self._real_attest["AttestVerifier"](
                    profile=profile,
                    grounds_resolver=grounds_resolver,
                    authority_resolver=authority_resolver,
                    signature_verifier=signature_verifier,
                )
                try:
                    # v0.3 Attest: inject the evaluation instant so the verdict,
                    # the receipt, and the store digest all bind the same time.
                    result = verifier.verify(
                        attest_message, known_messages=attest_known_messages, at=verification_instant
                    )
                except TypeError:
                    # pre-v0.3 sibling without injectable time
                    result = verifier.verify(attest_message, known_messages=attest_known_messages)
                # Retired proposer authority keys are never consumed, but the
                # attempt is surfaced and denies a clean PASS via the
                # soft-flag -> REVIEW rule.
                soft_flags_with_taint = list(result.get("soft_flag", [])) + resolver_inputs.injection_flags()
                decision_effect: Literal["PASS", "REVIEW", "BLOCK", "UNVERIFIABLE"] = "PASS"
                if result.get("hard_fail"):
                    decision_effect = "BLOCK"
                elif soft_flags_with_taint or result.get("pass_scope_limit"):
                    decision_effect = "REVIEW"
                return AttestVerificationState(
                    message_id=getattr(attest_message, "compute_id")(),
                    canonical_hash=message_hash,
                    profile_id=profile.name,
                    profile_version="loaded-runtime-profile",
                    profile_hash=sha256(self._stable_json(profile.model_dump(mode="json")).encode("utf-8")).hexdigest(),
                    verifier_version="attest_ref_impl",
                    hard_fail=list(result.get("hard_fail", [])),
                    soft_flag=soft_flags_with_taint,
                    pass_scope_limit=list(result.get("pass_scope_limit", [])),
                    decision_effect=decision_effect,
                    known_message_set_hash=known_hash,
                    grounds_resolver_name=type(grounds_resolver).__name__,
                    grounds_resolver_config_hash=sha256(self._stable_json(grounds_resolver_config).encode("utf-8")).hexdigest(),
                    authority_resolver_name=type(authority_resolver).__name__,
                    authority_resolver_config_hash=authority_resolver_hash,
                    signature_verifier_name=type(signature_verifier).__name__,
                    signature_verifier_config_hash=signature_verifier_config_hash,
                    evaluated_at=verification_instant,
                )
            except Exception as exc:
                return self._stub_verification(
                    message_hash=message_hash,
                    known_hash=known_hash,
                    evaluated_at=evaluated_at,
                    resolver_inputs=resolver_inputs,
                    extra_soft_flags=[f"ATTEST_REAL_PATH_FAILED:{type(exc).__name__}"],
                )

        return self._stub_verification(
            message_hash=message_hash,
            known_hash=known_hash,
            evaluated_at=evaluated_at,
            resolver_inputs=resolver_inputs,
        )

    def compute_independence(
        self,
        *,
        candidate_message: dict[str, Any],
        peer_messages: list[dict[str, Any]],
        candidate_signer: str | None = None,
        peer_signers: list[str] | None = None,
        candidate_adapter_family: str | None = None,
        peer_adapter_families: list[str] | None = None,
        candidate_operator: str | None = None,
        peer_operators: list[str] | None = None,
    ) -> IndependenceSignals:
        """Runtime-owned correlation surface.

        TrustedRuntime should compute overlap from grounds, parents, signer,
        adapter family, external source, and operator lineage. Attest exposes
        the structure; TrustedRuntime decides how much correlation is tolerable.
        """
        candidate_warrant = candidate_message.get("warrant") or {}
        candidate_grounds = set(candidate_warrant.get("grounds") or [])
        candidate_parents = set(candidate_message.get("parents") or [])

        shared_grounds: set[str] = set()
        shared_parents: set[str] = set()
        shared_external_sources: set[str] = set()

        for peer in peer_messages:
            peer_warrant = peer.get("warrant") or {}
            peer_grounds = set(peer_warrant.get("grounds") or [])
            peer_parents = set(peer.get("parents") or [])
            shared_grounds.update(candidate_grounds & peer_grounds)
            shared_parents.update(candidate_parents & peer_parents)
            shared_external_sources.update(
                g for g in (candidate_grounds & peer_grounds) if isinstance(g, str) and g.startswith("src:")
            )

        same_signer = bool(candidate_signer and peer_signers and candidate_signer in peer_signers)
        same_adapter_family = bool(candidate_adapter_family and peer_adapter_families and candidate_adapter_family in peer_adapter_families)
        same_operator = bool(candidate_operator and peer_operators and candidate_operator in peer_operators)

        overlap_reasons: list[str] = []
        if shared_grounds:
            overlap_reasons.append("shared_grounds")
        if shared_parents:
            overlap_reasons.append("shared_parents")
        if same_signer:
            overlap_reasons.append("same_signer")
        if same_adapter_family:
            overlap_reasons.append("same_adapter_family")
        if same_operator:
            overlap_reasons.append("same_operator")
        if shared_external_sources:
            overlap_reasons.append("shared_external_sources")

        if same_signer or same_operator:
            policy_result = "same-origin"
            score = 0.0
        elif overlap_reasons:
            policy_result = "correlated"
            score = 0.35
        elif not peer_messages:
            policy_result = "unknown"
            score = 0.1
        else:
            policy_result = "independent"
            score = 1.0

        return IndependenceSignals(
            shared_grounds=sorted(shared_grounds),
            shared_parents=sorted(shared_parents),
            same_signer=same_signer,
            same_adapter_family=same_adapter_family,
            same_operator=same_operator,
            shared_external_sources=sorted(shared_external_sources),
            overlap_reasons=overlap_reasons,
            independence_score=score,
            policy_result=policy_result,
        )

    def decision_effect(self, verification: AttestVerificationState, independence: IndependenceSignals | None = None) -> Literal["PASS", "REVIEW", "BLOCK", "UNVERIFIABLE"]:
        """Reference gate described in the integration contract."""
        if verification.decision_effect == "UNVERIFIABLE":
            return "UNVERIFIABLE"
        if verification.hard_fail:
            return "BLOCK"
        if independence is not None and independence.policy_result in {"same-origin", "unknown"}:
            return "REVIEW"
        if verification.soft_flag:
            return "REVIEW"
        return "PASS"

    # ------------------------------------------------------------------
    # CER integration surface
    # ------------------------------------------------------------------

    def cer_receipt_fragment(
        self,
        *,
        verification: AttestVerificationState,
        independence: IndependenceSignals | None = None,
    ) -> dict[str, Any]:
        """Receipt fragment to embed into CER bundles."""
        payload = {
            "attest_message_id": verification.message_id,
            "attest_canonical_hash": verification.canonical_hash,
            "attest_profile_id": verification.profile_id,
            "attest_profile_version": verification.profile_version,
            "attest_profile_hash": verification.profile_hash,
            "attest_verifier_version": verification.verifier_version,
            "attest_hard_fail": verification.hard_fail,
            "attest_soft_flag": verification.soft_flag,
            "attest_pass_scope_limit": verification.pass_scope_limit,
            "attest_decision_effect": verification.decision_effect,
            "attest_known_message_set_hash": verification.known_message_set_hash,
            "attest_grounds_resolver_name": verification.grounds_resolver_name,
            "attest_grounds_resolver_config_hash": verification.grounds_resolver_config_hash,
            "attest_authority_resolver_name": verification.authority_resolver_name,
            "attest_authority_resolver_config_hash": verification.authority_resolver_config_hash,
            "attest_signature_verifier_name": verification.signature_verifier_name,
            "attest_signature_verifier_config_hash": verification.signature_verifier_config_hash,
            "attest_evaluated_at": verification.evaluated_at.isoformat(),
        }
        if independence is not None:
            payload["attest_independence"] = independence.model_dump(mode="json")
        return payload

    # ------------------------------------------------------------------
    # Dissent preservation helpers
    # ------------------------------------------------------------------

    def unresolved_dissent_ids(self, packets: list[AttestReviewPacket]) -> list[str]:
        """Return dissent messages that remain live in the review packet set.

        Policy intent:
        - final review packets must include unresolved dissent IDs
        - or explicit RETRACT / supersession references that account for them
        """
        dissent_ids = {packet.message_id for packet in packets if packet.frame == "DISSENT"}
        resolved = set()
        for packet in packets:
            resolved.update(packet.supersedes)
        return sorted(dissent_ids - resolved)

    # ------------------------------------------------------------------
    # Local helpers
    # ------------------------------------------------------------------

    def next_anchor(self) -> list[Any]:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [now, 1]

    @staticmethod
    def _stable_json(value: Any) -> str:
        import json

        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class _StoreAuthorityResolverAdapter:
    """Adapts the orchestrator-owned grant store to Attest's AuthorityResolver
    protocol. Resolution is evaluation-time aware: the same `at` that goes
    into the receipt drives store resolution, which is what makes the
    receipt's authority digest replayable.

    Status mapping: resolved and expired map directly. `revoked` maps to
    Attest's `revoked` status when the loaded implementation supports it
    (v0.3+), else degrades to `unresolved` with the revocation detail
    preserved — the distinction is never silently dropped from the receipt
    because the store detail string carries it either way.
    """

    def __init__(self, *, module: dict[str, Any], store: AuthorityGrantStore, at: datetime) -> None:
        self._resolution_cls = module["AuthorityResolution"]
        self._store = store
        self._at = at

    def resolve(self, ref: str) -> Any:
        res = self._store.resolve(ref, self._at)
        status = res.status
        kwargs: dict[str, Any] = {"ref": ref, "detail": res.detail}
        if status == "resolved":
            kwargs.update(
                status="resolved",
                granted_type=res.granted_type,
                granted_scope=res.granted_scope,
                delegates_from=list(res.delegates_from),
            )
            # v0.3 fields, passed only when the loaded impl accepts them.
            for extra_field, value in (("expires", res.expires), ("strength", res.strength)):
                if extra_field in getattr(self._resolution_cls, "model_fields", {}):
                    kwargs[extra_field] = value
            return self._resolution_cls(**kwargs)
        if status == "expired":
            return self._resolution_cls(status="expired", **kwargs)
        if status == "revoked":
            try:
                return self._resolution_cls(status="revoked", **kwargs)
            except Exception:
                return self._resolution_cls(status="unresolved", **kwargs)
        return self._resolution_cls(status="unresolved", **kwargs)
