"""Bounded Futures Testnet risk/killswitch lifecycle integration (v0, PE-22).

Deterministic, offline, explicit-input-only contract binding PE-12 tiny_order
lifecycle/gate matrix to existing Risk, KillSwitch, and Flatten reference surfaces.
Static integration only — no operative risk evaluation, KillSwitch trigger, flatten,
network, testnet, runtime, orders, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    OPERATOR_GO_TINY_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
    default_bounded_futures_normal_v0_spec,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FLATTEN_BINDING_REFERENCE,
    FOLLOWUP_RUN_GATE,
    KILLSWITCH_BINDING_REFERENCE,
    PE12_CONTRACT_VERSION,
    RISK_CONTRACT_REFERENCE,
)
from src.ops.gates.risk_gate import RiskContext, RiskLimits, evaluate_risk
from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
    FAIL_KILLSWITCH_STATES,
    PASS_KILLSWITCH_STATES,
    OrderCapabilityAbortBindingError,
    OrderCapabilityAbortBindingInput,
    OrderCapabilityBindingVerdict,
    OrderCapabilityKillSwitchSnapshot,
    OrderCapabilityPayloadSafetySummary,
    evaluate_order_capability_abort_binding,
)
from src.risk_layer.kill_switch.state import KillSwitchState

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RISK_KILLSWITCH_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_risk_killswitch_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_risk_killswitch_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

RISK_GATE_CONTRACT_VERSION = "ops.gates.risk_gate.v0"
KILLSWITCH_BINDING_CONTRACT_VERSION = "order_capability_killswitch_abort_binding.v1"
FLATTEN_BINDING_CONTRACT_VERSION = "bounded_futures_testnet_contract.v0"
PE22_ABORT_BINDING_NOW_UTC = "2026-06-09T13:00:00Z"
PE22_ABORT_BINDING_OBSERVED_UTC = "2026-06-09T12:59:30Z"
PE22_ABORT_BINDING_TTL_SECONDS = 120

GLOBAL_RISK_KILLSWITCH_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_RISK_EVALUATION_EXECUTED = False
OPERATIVE_KILLSWITCH_EXECUTED = False
OPERATIVE_FLATTEN_EXECUTED = False
POSITION_STATE_QUERIED = False
ORDER_STATE_QUERIED = False
EXCHANGE_STATE_QUERIED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_TRIGGERED_KILLSWITCH_STATES = frozenset(
    {
        KillSwitchState.KILLED.name,
        KillSwitchState.RECOVERING.name,
    }
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "risk_gate": RISK_GATE_CONTRACT_VERSION,
    "killswitch_binding": KILLSWITCH_BINDING_CONTRACT_VERSION,
    "flatten_binding": FLATTEN_BINDING_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    risk_gate: str
    killswitch_binding: str
    flatten_binding: str
    integration: str


@dataclass(frozen=True)
class RiskPolicyBinding:
    policy_id: str
    policy_digest: str
    contract_reference: str


@dataclass(frozen=True)
class RiskSnapshotBinding:
    snapshot_id: str
    snapshot_digest: str
    limits_enabled: bool
    kill_switch_limit: bool
    max_notional_usd: float
    max_order_size: float
    max_position: float
    max_session_loss_usd: float
    max_data_age_seconds: int


@dataclass(frozen=True)
class RiskContextBinding:
    now_epoch: int
    market_data_age_seconds: int
    session_pnl_usd: float
    current_position: float
    order_size: float
    order_notional_usd: float


@dataclass(frozen=True)
class RiskEvaluationProof:
    proof_digest: str
    proof_pass: bool
    evaluation_allow: bool
    deny_reason: str | None
    policy_digest: str
    snapshot_digest: str
    context_digest: str


@dataclass(frozen=True)
class KillSwitchPolicyBinding:
    policy_id: str
    policy_digest: str
    binding_reference: str


@dataclass(frozen=True)
class KillSwitchStateBinding:
    state_id: str
    state_digest: str
    killswitch_state: str


@dataclass(frozen=True)
class KillSwitchEvaluationProof:
    proof_digest: str
    proof_pass: bool
    killswitch_clear: bool
    policy_digest: str
    state_digest: str
    normalized_state: str


@dataclass(frozen=True)
class FlattenStateProof:
    proof_digest: str
    proof_pass: bool
    position_flattened_by_end: bool
    cancel_or_close_evidence_valid: bool
    position_quantity: float
    position_must_be_flattened: bool
    binding_reference: str


@dataclass(frozen=True)
class TinyOrderGateMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    tiny_order_gate_digest: str
    operator_go_token: str


@dataclass(frozen=True)
class LifecycleMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    assigned_lifecycle_phase: str
    lifecycle_state_digest: str


@dataclass(frozen=True)
class LifecycleStateBinding:
    state_id: str
    state_digest: str
    assigned_lifecycle_phase: str
    adapter_id: str


@dataclass(frozen=True)
class DeclaredLifecycleStateBinding:
    state_id: str
    state_digest: str
    assigned_lifecycle_phase: str
    adapter_id: str


@dataclass(frozen=True)
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class RiskKillswitchLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    risk_policy: RiskPolicyBinding
    risk_snapshot: RiskSnapshotBinding
    risk_context: RiskContextBinding
    risk_evaluation_proof: RiskEvaluationProof
    killswitch_policy: KillSwitchPolicyBinding
    killswitch_state: KillSwitchStateBinding
    killswitch_evaluation_proof: KillSwitchEvaluationProof
    flatten_state_proof: FlattenStateProof
    tiny_order_gate_proof: TinyOrderGateMatrixProof
    lifecycle_state_before: LifecycleStateBinding
    declared_lifecycle_state_after: DeclaredLifecycleStateBinding
    lifecycle_matrix_proof: LifecycleMatrixProof
    safety_snapshot: IntegrationSafetySnapshot
    abort_binding_input: OrderCapabilityAbortBindingInput
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _normalize_killswitch_state(state: str) -> str:
    return state.strip().upper().replace(" ", "_")


def compute_lifecycle_matrix_digest() -> str:
    """Deterministic digest of the canonical PE-12 lifecycle matrix identity."""
    matrix = {
        "hash_algorithm": HASH_ALGORITHM,
        "lifecycle_phase_order": list(LIFECYCLE_PHASE_ORDER),
        "network_execution_phases": sorted(NETWORK_EXECUTION_PHASES),
        "package_marker": PE12_PACKAGE_MARKER,
        "pe12_contract_version": PE12_CONTRACT_VERSION,
        "phase_descriptors": {
            phase_id: {
                "canonical_owner": descriptor.canonical_owner,
                "credentials_phase": descriptor.credentials_phase,
                "network_phase": descriptor.network_phase,
                "operator_go_token": descriptor.operator_go_token,
                "orders_phase": descriptor.orders_phase,
                "sequence_index": descriptor.sequence_index,
            }
            for phase_id, descriptor in sorted(LIFECYCLE_PHASE_DESCRIPTORS.items())
        },
    }
    return hashlib.sha256(
        json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_tiny_order_gate_digest() -> str:
    """Deterministic digest of PE-12 tiny_order gate matrix identity."""
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_TINY_ORDER]
    gate = {
        "flatten_binding_reference": FLATTEN_BINDING_REFERENCE,
        "hash_algorithm": HASH_ALGORITHM,
        "killswitch_binding_reference": KILLSWITCH_BINDING_REFERENCE,
        "operator_go_token": OPERATOR_GO_TINY_ORDER,
        "orders_phase": descriptor.orders_phase,
        "pe12_contract_version": PE12_CONTRACT_VERSION,
        "phase_id": PHASE_TINY_ORDER,
        "required_acknowledgments": [
            "durable_primary_evidence_capable",
            "flatten_binding_acknowledged",
            "risk_killswitch_binding_acknowledged",
        ],
        "risk_contract_reference": RISK_CONTRACT_REFERENCE,
    }
    return hashlib.sha256(
        json.dumps(gate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def serialize_risk_policy_canonical(policy: RiskPolicyBinding) -> str:
    payload = {
        "contract_reference": policy.contract_reference,
        "policy_id": policy.policy_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_risk_policy_digest(policy: RiskPolicyBinding) -> str:
    return hashlib.sha256(serialize_risk_policy_canonical(policy).encode("utf-8")).hexdigest()


def serialize_risk_snapshot_canonical(snapshot: RiskSnapshotBinding) -> str:
    payload = {
        "kill_switch_limit": snapshot.kill_switch_limit,
        "limits_enabled": snapshot.limits_enabled,
        "max_data_age_seconds": snapshot.max_data_age_seconds,
        "max_notional_usd": snapshot.max_notional_usd,
        "max_order_size": snapshot.max_order_size,
        "max_position": snapshot.max_position,
        "max_session_loss_usd": snapshot.max_session_loss_usd,
        "snapshot_id": snapshot.snapshot_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_risk_snapshot_digest(snapshot: RiskSnapshotBinding) -> str:
    return hashlib.sha256(serialize_risk_snapshot_canonical(snapshot).encode("utf-8")).hexdigest()


def serialize_risk_context_canonical(context: RiskContextBinding) -> str:
    payload = asdict(context)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_risk_context_digest(context: RiskContextBinding) -> str:
    return hashlib.sha256(serialize_risk_context_canonical(context).encode("utf-8")).hexdigest()


def serialize_killswitch_policy_canonical(policy: KillSwitchPolicyBinding) -> str:
    payload = {
        "binding_reference": policy.binding_reference,
        "policy_id": policy.policy_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_killswitch_policy_digest(policy: KillSwitchPolicyBinding) -> str:
    return hashlib.sha256(serialize_killswitch_policy_canonical(policy).encode("utf-8")).hexdigest()


def serialize_killswitch_state_canonical(state: KillSwitchStateBinding) -> str:
    payload = {
        "killswitch_state": state.killswitch_state,
        "state_id": state.state_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_killswitch_state_digest(state: KillSwitchStateBinding) -> str:
    return hashlib.sha256(serialize_killswitch_state_canonical(state).encode("utf-8")).hexdigest()


def serialize_flatten_state_canonical(proof: FlattenStateProof) -> str:
    payload = {
        "binding_reference": proof.binding_reference,
        "cancel_or_close_evidence_valid": proof.cancel_or_close_evidence_valid,
        "position_flattened_by_end": proof.position_flattened_by_end,
        "position_must_be_flattened": proof.position_must_be_flattened,
        "position_quantity": proof.position_quantity,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_flatten_state_digest(proof: FlattenStateProof) -> str:
    return hashlib.sha256(serialize_flatten_state_canonical(proof).encode("utf-8")).hexdigest()


def _risk_limits_from_snapshot(snapshot: RiskSnapshotBinding) -> RiskLimits:
    return RiskLimits(
        enabled=snapshot.limits_enabled,
        kill_switch=snapshot.kill_switch_limit,
        max_notional_usd=snapshot.max_notional_usd,
        max_order_size=snapshot.max_order_size,
        max_position=snapshot.max_position,
        max_session_loss_usd=snapshot.max_session_loss_usd,
        max_data_age_seconds=snapshot.max_data_age_seconds,
    )


def _risk_context_from_binding(context: RiskContextBinding) -> RiskContext:
    return RiskContext(
        now_epoch=context.now_epoch,
        market_data_age_seconds=context.market_data_age_seconds,
        session_pnl_usd=context.session_pnl_usd,
        current_position=context.current_position,
        order_size=context.order_size,
        order_notional_usd=context.order_notional_usd,
    )


def evaluate_risk_static_proof(
    *,
    snapshot: RiskSnapshotBinding,
    context: RiskContextBinding,
) -> dict[str, Any]:
    """Compose existing risk_gate.evaluate_risk with explicit injected inputs only."""
    decision = evaluate_risk(
        _risk_limits_from_snapshot(snapshot), _risk_context_from_binding(context)
    )
    deny_reason = decision.reason.value if decision.reason is not None else None
    return {
        "evaluation_allow": decision.allow,
        "deny_reason": deny_reason,
        "proof_pass": decision.allow,
    }


def _integration_input_dict(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "adapter_id": integration_input.adapter_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "risk_policy": asdict(integration_input.risk_policy),
        "risk_snapshot": asdict(integration_input.risk_snapshot),
        "risk_context": asdict(integration_input.risk_context),
        "risk_evaluation_proof": asdict(integration_input.risk_evaluation_proof),
        "killswitch_policy": asdict(integration_input.killswitch_policy),
        "killswitch_state": asdict(integration_input.killswitch_state),
        "killswitch_evaluation_proof": asdict(integration_input.killswitch_evaluation_proof),
        "flatten_state_proof": asdict(integration_input.flatten_state_proof),
        "tiny_order_gate_proof": asdict(integration_input.tiny_order_gate_proof),
        "lifecycle_state_before": asdict(integration_input.lifecycle_state_before),
        "declared_lifecycle_state_after": asdict(integration_input.declared_lifecycle_state_after),
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "abort_binding_input": {
            "expected_environment": integration_input.abort_binding_input.expected_environment,
            "expected_operator_go_token_binding": (
                integration_input.abort_binding_input.expected_operator_go_token_binding
            ),
            "kill_switch_snapshot": asdict(
                integration_input.abort_binding_input.kill_switch_snapshot
            ),
            "now_utc": integration_input.abort_binding_input.now_utc,
            "payload_summary": asdict(integration_input.abort_binding_input.payload_summary),
        },
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_proof_dict(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
) -> dict[str, Any]:
    payload = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "lifecycle_matrix_digest": integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe12_tiny_order_risk_killswitch_flatten_static_integration_proven": False,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_risk_evaluation_executed": OPERATIVE_RISK_EVALUATION_EXECUTED,
        "operative_killswitch_executed": OPERATIVE_KILLSWITCH_EXECUTED,
        "operative_flatten_executed": OPERATIVE_FLATTEN_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "global_risk_killswitch_readiness": GLOBAL_RISK_KILLSWITCH_READINESS,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_proof_canonical(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_proof_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_proof_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _validate_instrument_scope(instrument: str, market_type: str) -> list[str]:
    fail_reasons: list[str] = []
    if market_type != DEFAULT_MARKET_TYPE:
        fail_reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not instrument:
        fail_reasons.append("instrument required")
    if instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        fail_reasons.append(f"instrument {instrument!r} is a rejected futures placeholder")
    if instrument in SPOT_INSTRUMENTS:
        fail_reasons.append(f"instrument {instrument!r} is a spot instrument")
    for fragment in _FORBIDDEN_INSTRUMENT_FRAGMENTS:
        if fragment in instrument:
            fail_reasons.append(f"instrument {instrument!r} has forbidden orientation {fragment!r}")
    return fail_reasons


def _validate_safety_snapshot(snapshot: IntegrationSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("zero_order_authorized", False),
        ("network_allowed", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("futures_only", True),
        ("bitcoin_direction_allowed", False),
    )
    for field_name, expected in required_bools:
        actual = getattr(snapshot, field_name)
        if actual is not expected:
            fail_reasons.append(f"safety_snapshot: {field_name} must be {expected}")
    if snapshot.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"safety_snapshot: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")
    return fail_reasons


def _validate_risk_proof_chain(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    policy = integration_input.risk_policy
    snapshot = integration_input.risk_snapshot
    context = integration_input.risk_context
    proof = integration_input.risk_evaluation_proof

    if not policy.policy_id:
        fail_reasons.append("risk_policy: policy_id required")
    if not policy.policy_digest:
        fail_reasons.append("risk_policy: policy_digest required")
    elif not _valid_sha256_digest(policy.policy_digest):
        fail_reasons.append("risk_policy: policy_digest must be 64-char lowercase sha256 hex")
    elif policy.policy_digest != compute_risk_policy_digest(policy):
        fail_reasons.append("risk_policy: policy_digest mismatch")
    if policy.contract_reference != RISK_CONTRACT_REFERENCE:
        fail_reasons.append(f"risk_policy: contract_reference must be {RISK_CONTRACT_REFERENCE!r}")

    if not snapshot.snapshot_id:
        fail_reasons.append("risk_snapshot: snapshot_id required")
    if not snapshot.snapshot_digest:
        fail_reasons.append("risk_snapshot: snapshot_digest required")
    elif not _valid_sha256_digest(snapshot.snapshot_digest):
        fail_reasons.append("risk_snapshot: snapshot_digest must be 64-char lowercase sha256 hex")
    elif snapshot.snapshot_digest != compute_risk_snapshot_digest(snapshot):
        fail_reasons.append("risk_snapshot: snapshot_digest mismatch")

    if not proof.proof_digest:
        fail_reasons.append("risk_evaluation_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "risk_evaluation_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.policy_digest != policy.policy_digest:
        fail_reasons.append("risk_evaluation_proof: policy_digest mismatch")
    if proof.snapshot_digest != snapshot.snapshot_digest:
        fail_reasons.append("risk_evaluation_proof: snapshot_digest mismatch")
    context_digest = compute_risk_context_digest(context)
    if proof.context_digest != context_digest:
        fail_reasons.append("risk_evaluation_proof: context_digest mismatch")

    static_eval = evaluate_risk_static_proof(snapshot=snapshot, context=context)
    if proof.evaluation_allow != static_eval["evaluation_allow"]:
        fail_reasons.append("risk_evaluation_proof: evaluation_allow mismatch with risk_gate")
    deny_reason = static_eval["deny_reason"]
    if proof.deny_reason != deny_reason:
        fail_reasons.append("risk_evaluation_proof: deny_reason mismatch with risk_gate")
    if proof.proof_pass is not True:
        fail_reasons.append("risk_evaluation_proof: proof_pass must be true for valid integration")
    if not static_eval["proof_pass"]:
        fail_reasons.append("risk_evaluation_proof: risk gate evaluation failed")
    if deny_reason is not None and proof.evaluation_allow:
        fail_reasons.append("risk_evaluation_proof: violated risk invariant with allow=true")
    if not snapshot.limits_enabled:
        fail_reasons.append("risk_snapshot: limits_enabled must be true")
    if snapshot.kill_switch_limit:
        fail_reasons.append("risk_snapshot: kill_switch_limit must be false for tiny_order binding")

    return fail_reasons


def _validate_killswitch_proof_chain(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    policy = integration_input.killswitch_policy
    state = integration_input.killswitch_state
    proof = integration_input.killswitch_evaluation_proof

    if not policy.policy_id:
        fail_reasons.append("killswitch_policy: policy_id required")
    if not policy.policy_digest:
        fail_reasons.append("killswitch_policy: policy_digest required")
    elif not _valid_sha256_digest(policy.policy_digest):
        fail_reasons.append("killswitch_policy: policy_digest must be 64-char lowercase sha256 hex")
    elif policy.policy_digest != compute_killswitch_policy_digest(policy):
        fail_reasons.append("killswitch_policy: policy_digest mismatch")
    if policy.binding_reference != KILLSWITCH_BINDING_REFERENCE:
        fail_reasons.append(
            f"killswitch_policy: binding_reference must be {KILLSWITCH_BINDING_REFERENCE!r}"
        )

    if not state.state_id:
        fail_reasons.append("killswitch_state: state_id required")
    if not state.state_digest:
        fail_reasons.append("killswitch_state: state_digest required")
    elif not _valid_sha256_digest(state.state_digest):
        fail_reasons.append("killswitch_state: state_digest must be 64-char lowercase sha256 hex")
    elif state.state_digest != compute_killswitch_state_digest(state):
        fail_reasons.append("killswitch_state: state_digest mismatch")
    if not state.killswitch_state:
        fail_reasons.append("killswitch_state: killswitch_state required")

    normalized = _normalize_killswitch_state(state.killswitch_state)
    if proof.normalized_state != normalized:
        fail_reasons.append("killswitch_evaluation_proof: normalized_state mismatch")

    if not proof.proof_digest:
        fail_reasons.append("killswitch_evaluation_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "killswitch_evaluation_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.policy_digest != policy.policy_digest:
        fail_reasons.append("killswitch_evaluation_proof: policy_digest mismatch")
    if proof.state_digest != state.state_digest:
        fail_reasons.append("killswitch_evaluation_proof: state_digest mismatch")
    if proof.proof_pass is not True:
        fail_reasons.append(
            "killswitch_evaluation_proof: proof_pass must be true for valid integration"
        )

    if normalized in _TRIGGERED_KILLSWITCH_STATES:
        fail_reasons.append(f"killswitch_state: triggered state {normalized!r}")
    if normalized in FAIL_KILLSWITCH_STATES:
        fail_reasons.append(f"killswitch_state: active or tripped state {normalized!r}")
    if normalized not in PASS_KILLSWITCH_STATES and normalized != KillSwitchState.ACTIVE.name:
        fail_reasons.append(f"killswitch_state: unknown state {normalized!r}")

    killswitch_clear_expected = normalized in PASS_KILLSWITCH_STATES or (
        normalized == KillSwitchState.ACTIVE.name
    )
    if proof.killswitch_clear is not killswitch_clear_expected:
        fail_reasons.append("killswitch_evaluation_proof: killswitch_clear mismatch with state")
    if proof.killswitch_clear is not True:
        fail_reasons.append("killswitch_evaluation_proof: killswitch_clear must be true")
    if proof.killswitch_clear and normalized in FAIL_KILLSWITCH_STATES:
        fail_reasons.append("killswitch_evaluation_proof: killswitch_clear contradicts state")

    return fail_reasons


def _validate_flatten_proof_chain(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.flatten_state_proof
    spec = default_bounded_futures_normal_v0_spec()
    position_must_be_flattened = spec.position_must_be_flattened

    if not proof.proof_digest:
        fail_reasons.append("flatten_state_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "flatten_state_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.binding_reference != FLATTEN_BINDING_REFERENCE:
        fail_reasons.append(
            f"flatten_state_proof: binding_reference must be {FLATTEN_BINDING_REFERENCE!r}"
        )
    if proof.position_must_be_flattened is not position_must_be_flattened:
        fail_reasons.append("flatten_state_proof: position_must_be_flattened mismatch")
    if proof.proof_pass is not True:
        fail_reasons.append("flatten_state_proof: proof_pass must be true for valid integration")

    computed_digest = compute_flatten_state_digest(proof)
    proof_payload = FlattenStateProof(
        proof_digest=proof.proof_digest,
        proof_pass=proof.proof_pass,
        position_flattened_by_end=proof.position_flattened_by_end,
        cancel_or_close_evidence_valid=proof.cancel_or_close_evidence_valid,
        position_quantity=proof.position_quantity,
        position_must_be_flattened=proof.position_must_be_flattened,
        binding_reference=proof.binding_reference,
    )
    if proof.proof_digest != computed_digest:
        fail_reasons.append("flatten_state_proof: proof_digest mismatch")

    if position_must_be_flattened and not proof.position_flattened_by_end:
        fail_reasons.append("flatten_state_proof: position_flattened_by_end required")
    if position_must_be_flattened and proof.position_quantity != 0.0:
        fail_reasons.append("flatten_state_proof: position_quantity must be 0.0 when flat required")
    if proof.position_flattened_by_end and proof.position_quantity != 0.0:
        fail_reasons.append("flatten_state_proof: flatten/position contradiction")
    if not proof.cancel_or_close_evidence_valid:
        fail_reasons.append("flatten_state_proof: cancel_or_close_evidence_valid required")

    _ = proof_payload
    return fail_reasons


def _validate_tiny_order_gate_proof(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    gate = integration_input.tiny_order_gate_proof
    if gate.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"tiny_order_gate_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not gate.lifecycle_matrix_digest:
        fail_reasons.append("tiny_order_gate_proof: lifecycle_matrix_digest required")
    elif gate.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("tiny_order_gate_proof: lifecycle_matrix_digest mismatch")
    if not gate.tiny_order_gate_digest:
        fail_reasons.append("tiny_order_gate_proof: tiny_order_gate_digest required")
    elif gate.tiny_order_gate_digest != compute_tiny_order_gate_digest():
        fail_reasons.append("tiny_order_gate_proof: tiny_order_gate_digest mismatch")
    if gate.operator_go_token != OPERATOR_GO_TINY_ORDER:
        fail_reasons.append(
            f"tiny_order_gate_proof: operator_go_token must be {OPERATOR_GO_TINY_ORDER!r}"
        )
    return fail_reasons


def _pe22_abort_binding_correlation_id(adapter_id: str) -> str:
    return f"pe22-{adapter_id}"


def _default_abort_binding_input(adapter_id: str) -> OrderCapabilityAbortBindingInput:
    correlation_id = _pe22_abort_binding_correlation_id(adapter_id)
    return OrderCapabilityAbortBindingInput(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=correlation_id,
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment=ENVIRONMENT_TESTNET,
        ),
        expected_operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="pe22_offline_fixture",
            source_id=f"pe22-ks-{adapter_id}",
            source_kind="injected_offline_fixture",
            state="CLEAR",
            observed_at_utc=PE22_ABORT_BINDING_OBSERVED_UTC,
            ttl_seconds=PE22_ABORT_BINDING_TTL_SECONDS,
            correlation_id=correlation_id,
            environment=ENVIRONMENT_TESTNET,
        ),
        now_utc=PE22_ABORT_BINDING_NOW_UTC,
        expected_environment=ENVIRONMENT_TESTNET,
    )


def _evaluate_order_capability_abort_binding_fail_closed(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed PE-22 binding to canonical order-capability abort evaluation."""
    fail_reasons: list[str] = []
    abort_input = integration_input.abort_binding_input

    if abort_input.expected_operator_go_token_binding != OPERATOR_GO_TINY_ORDER:
        fail_reasons.append(
            "order_capability_abort_binding: expected_operator_go_token_binding drift from "
            f"PE-12 tiny_order gate (expected {OPERATOR_GO_TINY_ORDER!r})"
        )
    if abort_input.payload_summary.operator_go_token_binding != OPERATOR_GO_TINY_ORDER:
        fail_reasons.append(
            "order_capability_abort_binding: payload operator_go_token_binding owner drift"
        )

    correlation_id = abort_input.payload_summary.evidence_correlation_id.strip()
    if not correlation_id:
        fail_reasons.append("order_capability_abort_binding: binding_input required")
    elif integration_input.adapter_id not in correlation_id:
        fail_reasons.append("order_capability_abort_binding: lifecycle adapter_id identity drift")

    pe22_state = _normalize_killswitch_state(integration_input.killswitch_state.killswitch_state)
    abort_state = _normalize_killswitch_state(abort_input.kill_switch_snapshot.state)
    if pe22_state != abort_state:
        fail_reasons.append("order_capability_abort_binding: killswitch identity drift")

    try:
        first_verdict = evaluate_order_capability_abort_binding(abort_input)
        second_verdict = evaluate_order_capability_abort_binding(abort_input)
    except (OrderCapabilityAbortBindingError, ValueError, TypeError) as exc:
        fail_reasons.append(f"order_capability_abort_binding: evaluation_exception: {exc}")
        return fail_reasons

    if first_verdict is None or second_verdict is None:
        fail_reasons.append("order_capability_abort_binding: verdict_none")
        return fail_reasons

    if first_verdict != second_verdict:
        fail_reasons.append("order_capability_abort_binding: repeated evaluation inconsistency")

    verdict = first_verdict
    if verdict.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY:
        return fail_reasons

    if verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED:
        for code in verdict.reason_codes:
            fail_reasons.append(f"order_capability_abort_binding: {code}")
        if not verdict.reason_codes:
            fail_reasons.append("order_capability_abort_binding: fail_closed_without_reason")
        return fail_reasons

    fail_reasons.append(f"order_capability_abort_binding: verdict_{verdict.verdict.value.lower()}")
    return fail_reasons


def validate_risk_killswitch_lifecycle_integration_input(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit integration input bindings."""
    fail_reasons: list[str] = []

    if not integration_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(integration_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not integration_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif integration_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not integration_input.adapter_id:
        fail_reasons.append("adapter_id required")

    fail_reasons.extend(
        _validate_instrument_scope(integration_input.instrument, integration_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(integration_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    fail_reasons.extend(_validate_risk_proof_chain(integration_input))
    fail_reasons.extend(_validate_killswitch_proof_chain(integration_input))
    fail_reasons.extend(_validate_flatten_proof_chain(integration_input))
    fail_reasons.extend(_validate_tiny_order_gate_proof(integration_input))

    matrix = integration_input.lifecycle_matrix_proof
    if matrix.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not matrix.lifecycle_matrix_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest required")
    elif matrix.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest mismatch")
    if not matrix.lifecycle_state_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_state_digest required")
    elif not _valid_sha256_digest(matrix.lifecycle_state_digest):
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest must be 64-char lowercase sha256 hex"
        )
    if matrix.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    before = integration_input.lifecycle_state_before
    after = integration_input.declared_lifecycle_state_after
    if before.assigned_lifecycle_phase != PHASE_VALIDATE_ONLY:
        fail_reasons.append(
            f"lifecycle_state_before: assigned_lifecycle_phase must be {PHASE_VALIDATE_ONLY!r}"
        )
    if after.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"declared_lifecycle_state_after: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )
    if before.adapter_id != integration_input.adapter_id:
        fail_reasons.append("lifecycle_state_before: adapter_id mismatch")
    if after.adapter_id != integration_input.adapter_id:
        fail_reasons.append("declared_lifecycle_state_after: adapter_id mismatch")

    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_tiny_order_lifecycle_compatibility(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 tiny_order phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_TINY_ORDER]
    snapshot = integration_input.safety_snapshot

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append("lifecycle/gate contradiction: network_allowed true for tiny_order")
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append("lifecycle/gate contradiction: orders_allowed true for tiny_order")
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append("lifecycle/gate contradiction: credentials_allowed true for tiny_order")
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for tiny_order"
        )
    if snapshot.live_authorized:
        fail_reasons.append("lifecycle/gate contradiction: live_authorized true for tiny_order")
    if snapshot.zero_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: zero_order_authorized true for tiny_order"
        )

    if (
        integration_input.lifecycle_state_before.assigned_lifecycle_phase
        not in LIFECYCLE_PHASE_DESCRIPTORS
    ):
        fail_reasons.append("lifecycle_state_before: unsupported lifecycle phase")
    if (
        integration_input.declared_lifecycle_state_after.assigned_lifecycle_phase
        not in LIFECYCLE_PHASE_DESCRIPTORS
    ):
        fail_reasons.append("declared_lifecycle_state_after: unsupported lifecycle phase")

    return fail_reasons


def evaluate_risk_killswitch_lifecycle_integration(
    integration_input: RiskKillswitchLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_risk_proof_digest: str | None = None,
    expected_killswitch_proof_digest: str | None = None,
    expected_flatten_proof_digest: str | None = None,
    risk_ok_without_proof_chain: bool = False,
    killswitch_clear_without_proof_chain: bool = False,
    flat_without_proof_chain: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-12 tiny_order Risk/KillSwitch/Flatten integration proof."""
    fail_reasons = validate_risk_killswitch_lifecycle_integration_input(integration_input)
    fail_reasons.extend(_evaluate_order_capability_abort_binding_fail_closed(integration_input))

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_risk_proof_digest is not None:
        if integration_input.risk_evaluation_proof.proof_digest != expected_risk_proof_digest:
            fail_reasons.append("risk_evaluation_proof: proof_digest mismatch")

    if expected_killswitch_proof_digest is not None:
        if (
            integration_input.killswitch_evaluation_proof.proof_digest
            != expected_killswitch_proof_digest
        ):
            fail_reasons.append("killswitch_evaluation_proof: proof_digest mismatch")

    if expected_flatten_proof_digest is not None:
        if integration_input.flatten_state_proof.proof_digest != expected_flatten_proof_digest:
            fail_reasons.append("flatten_state_proof: proof_digest mismatch")

    if risk_ok_without_proof_chain:
        fail_reasons.append("risk_ok=true without full proof chain is insufficient")
    if killswitch_clear_without_proof_chain:
        fail_reasons.append("killswitch_clear=true without full proof chain is insufficient")
    if flat_without_proof_chain:
        fail_reasons.append("flat=true without full proof chain is insufficient")

    if not fail_reasons:
        fail_reasons.extend(_validate_tiny_order_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    pe22_proven = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(integration_input) if integration_pass else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "tiny_order_gate_digest": integration_input.tiny_order_gate_proof.tiny_order_gate_digest,
        "pe12_tiny_order_risk_killswitch_flatten_static_integration_proven": pe22_proven,
        "global_risk_killswitch_readiness": GLOBAL_RISK_KILLSWITCH_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_risk_evaluation_executed": OPERATIVE_RISK_EVALUATION_EXECUTED,
        "operative_killswitch_executed": OPERATIVE_KILLSWITCH_EXECUTED,
        "operative_flatten_executed": OPERATIVE_FLATTEN_EXECUTED,
        "position_state_queried": POSITION_STATE_QUERIED,
        "order_state_queried": ORDER_STATE_QUERIED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> IntegrationSafetySnapshot:
    return IntegrationSafetySnapshot(
        preflight_remains_blocked=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def _default_risk_bindings() -> tuple[
    RiskPolicyBinding,
    RiskSnapshotBinding,
    RiskContextBinding,
    RiskEvaluationProof,
]:
    policy = RiskPolicyBinding(
        policy_id="offline-risk-policy-001",
        policy_digest="",
        contract_reference=RISK_CONTRACT_REFERENCE,
    )
    policy = RiskPolicyBinding(
        policy_id=policy.policy_id,
        policy_digest=compute_risk_policy_digest(policy),
        contract_reference=policy.contract_reference,
    )
    snapshot = RiskSnapshotBinding(
        snapshot_id="offline-risk-snapshot-001",
        snapshot_digest="",
        limits_enabled=True,
        kill_switch_limit=False,
        max_notional_usd=100.0,
        max_order_size=1.0,
        max_position=1.0,
        max_session_loss_usd=50.0,
        max_data_age_seconds=60,
    )
    snapshot = RiskSnapshotBinding(
        snapshot_id=snapshot.snapshot_id,
        snapshot_digest=compute_risk_snapshot_digest(snapshot),
        limits_enabled=snapshot.limits_enabled,
        kill_switch_limit=snapshot.kill_switch_limit,
        max_notional_usd=snapshot.max_notional_usd,
        max_order_size=snapshot.max_order_size,
        max_position=snapshot.max_position,
        max_session_loss_usd=snapshot.max_session_loss_usd,
        max_data_age_seconds=snapshot.max_data_age_seconds,
    )
    context = RiskContextBinding(
        now_epoch=1_700_000_000,
        market_data_age_seconds=1,
        session_pnl_usd=0.0,
        current_position=0.0,
        order_size=0.1,
        order_notional_usd=5.0,
    )
    static_eval = evaluate_risk_static_proof(snapshot=snapshot, context=context)
    proof = RiskEvaluationProof(
        proof_digest="",
        proof_pass=True,
        evaluation_allow=static_eval["evaluation_allow"],
        deny_reason=static_eval["deny_reason"],
        policy_digest=policy.policy_digest,
        snapshot_digest=snapshot.snapshot_digest,
        context_digest=compute_risk_context_digest(context),
    )
    proof_digest = hashlib.sha256(
        json.dumps(
            {
                "context_digest": proof.context_digest,
                "deny_reason": proof.deny_reason,
                "evaluation_allow": proof.evaluation_allow,
                "policy_digest": proof.policy_digest,
                "proof_pass": proof.proof_pass,
                "snapshot_digest": proof.snapshot_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    proof = RiskEvaluationProof(
        proof_digest=proof_digest,
        proof_pass=proof.proof_pass,
        evaluation_allow=proof.evaluation_allow,
        deny_reason=proof.deny_reason,
        policy_digest=proof.policy_digest,
        snapshot_digest=proof.snapshot_digest,
        context_digest=proof.context_digest,
    )
    return policy, snapshot, context, proof


def _default_killswitch_bindings() -> tuple[
    KillSwitchPolicyBinding,
    KillSwitchStateBinding,
    KillSwitchEvaluationProof,
]:
    policy = KillSwitchPolicyBinding(
        policy_id="offline-killswitch-policy-001",
        policy_digest="",
        binding_reference=KILLSWITCH_BINDING_REFERENCE,
    )
    policy = KillSwitchPolicyBinding(
        policy_id=policy.policy_id,
        policy_digest=compute_killswitch_policy_digest(policy),
        binding_reference=policy.binding_reference,
    )
    state = KillSwitchStateBinding(
        state_id="offline-killswitch-state-001",
        state_digest="",
        killswitch_state="CLEAR",
    )
    state = KillSwitchStateBinding(
        state_id=state.state_id,
        state_digest=compute_killswitch_state_digest(state),
        killswitch_state=state.killswitch_state,
    )
    normalized = _normalize_killswitch_state(state.killswitch_state)
    proof = KillSwitchEvaluationProof(
        proof_digest="",
        proof_pass=True,
        killswitch_clear=True,
        policy_digest=policy.policy_digest,
        state_digest=state.state_digest,
        normalized_state=normalized,
    )
    proof_digest = hashlib.sha256(
        json.dumps(
            {
                "killswitch_clear": proof.killswitch_clear,
                "normalized_state": proof.normalized_state,
                "policy_digest": proof.policy_digest,
                "proof_pass": proof.proof_pass,
                "state_digest": proof.state_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    proof = KillSwitchEvaluationProof(
        proof_digest=proof_digest,
        proof_pass=proof.proof_pass,
        killswitch_clear=proof.killswitch_clear,
        policy_digest=proof.policy_digest,
        state_digest=proof.state_digest,
        normalized_state=proof.normalized_state,
    )
    return policy, state, proof


def _default_flatten_proof() -> FlattenStateProof:
    spec = default_bounded_futures_normal_v0_spec()
    proof = FlattenStateProof(
        proof_digest="",
        proof_pass=True,
        position_flattened_by_end=True,
        cancel_or_close_evidence_valid=True,
        position_quantity=0.0,
        position_must_be_flattened=spec.position_must_be_flattened,
        binding_reference=FLATTEN_BINDING_REFERENCE,
    )
    return FlattenStateProof(
        proof_digest=compute_flatten_state_digest(proof),
        proof_pass=proof.proof_pass,
        position_flattened_by_end=proof.position_flattened_by_end,
        cancel_or_close_evidence_valid=proof.cancel_or_close_evidence_valid,
        position_quantity=proof.position_quantity,
        position_must_be_flattened=proof.position_must_be_flattened,
        binding_reference=proof.binding_reference,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> RiskKillswitchLifecycleIntegrationInput:
    """Minimal valid futures-generic integration input for offline tests."""
    policy, snapshot, context, risk_proof = _default_risk_bindings()
    ks_policy, ks_state, ks_proof = _default_killswitch_bindings()
    flatten_proof = _default_flatten_proof()
    matrix_digest = compute_lifecycle_matrix_digest()
    gate_digest = compute_tiny_order_gate_digest()
    state_digest = lifecycle_state_digest or "e" * 64

    return RiskKillswitchLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            risk_gate=RISK_GATE_CONTRACT_VERSION,
            killswitch_binding=KILLSWITCH_BINDING_CONTRACT_VERSION,
            flatten_binding=FLATTEN_BINDING_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        risk_policy=policy,
        risk_snapshot=snapshot,
        risk_context=context,
        risk_evaluation_proof=risk_proof,
        killswitch_policy=ks_policy,
        killswitch_state=ks_state,
        killswitch_evaluation_proof=ks_proof,
        flatten_state_proof=flatten_proof,
        tiny_order_gate_proof=TinyOrderGateMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            tiny_order_gate_digest=gate_digest,
            operator_go_token=OPERATOR_GO_TINY_ORDER,
        ),
        lifecycle_state_before=LifecycleStateBinding(
            state_id="lifecycle-before-001",
            state_digest="b" * 64,
            assigned_lifecycle_phase=PHASE_VALIDATE_ONLY,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=DeclaredLifecycleStateBinding(
            state_id="lifecycle-after-001",
            state_digest="a" * 64,
            assigned_lifecycle_phase=PHASE_TINY_ORDER,
            adapter_id=adapter_id,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_TINY_ORDER,
            lifecycle_state_digest=state_digest,
        ),
        safety_snapshot=default_minimal_safety_snapshot(),
        abort_binding_input=_default_abort_binding_input(adapter_id),
    )
