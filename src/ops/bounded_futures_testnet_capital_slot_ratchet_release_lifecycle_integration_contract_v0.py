"""Bounded Futures Testnet capital slot ratchet/release lifecycle integration (v0, PE-23).

Deterministic, offline, explicit-input-only contract binding PE-12 reconciliation_review
lifecycle matrix to existing double_play_capital_slot ratchet, release, inactivity, and
opportunity-cost semantics. Static integration only — no operative ratchet, slot release,
capital reallocation, reserve movement, network, testnet, runtime, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe22_lifecycle_matrix_digest,
    default_minimal_integration_input as default_pe22_minimal_integration_input,
    evaluate_risk_killswitch_lifecycle_integration,
)
from src.trading.master_v2.double_play_capital_slot import (
    DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
    CapitalSlotConfig,
    CapitalSlotReleaseReason,
    CapitalSlotState,
    CapitalSlotStatus,
    apply_loss_following_base,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_CAPITAL_SLOT_RATCHET_RELEASE_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"
CAPITAL_SLOT_SPEC_REFERENCE = "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"
CAPITAL_SLOT_CANONICAL_OWNER = "trading.master_v2.double_play_capital_slot"

GLOBAL_CAPITAL_SLOT_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_RATCHET_APPLIED = False
OPERATIVE_SLOT_RELEASE_EXECUTED = False
OPERATIVE_CAPITAL_REALLOCATION_EXECUTED = False
OPERATIVE_RESERVE_MOVEMENT_EXECUTED = False
ACCOUNT_STATE_QUERIED = False
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

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "capital_slot_layer": DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
    "pe22_upstream_safety": PE22_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    capital_slot_layer: str
    pe22_upstream_safety: str
    integration: str


@dataclass(frozen=True)
class CapitalSlotSpecProof:
    layer_version: str
    spec_reference: str
    spec_digest: str
    canonical_owner: str


@dataclass(frozen=True)
class SlotIdentityBinding:
    slot_id: str
    slot_digest: str
    selected_future: str


@dataclass(frozen=True)
class CapitalSlotConfigBinding:
    profit_step_pct: float
    cashflow_lock_fraction: float
    reinvest_fraction: float
    allow_auto_top_up: bool
    live_authorization: bool
    min_realized_volatility: float
    min_atr_or_range: float
    max_time_without_cashflow_step: int
    min_opportunity_score: float


@dataclass(frozen=True)
class EquityBasisBinding:
    current_slot_basis: float
    prior_valid_settled_basis: float
    new_settled_realized_equity: float
    unrealized_equity: float
    use_unrealized_as_reset_basis: bool
    basis_digest: str


@dataclass(frozen=True)
class RatchetStageBinding:
    ratchet_stage: float
    ratchet_target: float
    stage_digest: str


@dataclass(frozen=True)
class RatchetEvaluationProof:
    proof_digest: str
    proof_pass: bool
    can_ratchet: bool
    ratchet_target: float
    new_active_slot_base: float | None
    block_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ReserveTopupBlockProof:
    proof_digest: str
    proof_pass: bool
    reserve_topup_blocked: bool
    reserve_topup_attempted: bool
    allow_auto_top_up_declared: bool


@dataclass(frozen=True)
class ObservationWindowBinding:
    window_id: str
    window_digest: str
    start_epoch: int
    end_epoch: int
    duration_seconds: int


@dataclass(frozen=True)
class ActivityMetricsBinding:
    time_without_cashflow_step: int
    realized_volatility: float
    atr_or_range: float
    opportunity_score: float
    metrics_digest: str


@dataclass(frozen=True)
class CapitalSlotStateBinding:
    initial_slot_base: float
    active_slot_base: float
    realized_or_settled_slot_equity: float
    unrealized_pnl: float
    locked_cashflow: float
    survival_allows_slot: bool


@dataclass(frozen=True)
class ReleaseEligibilityProof:
    proof_digest: str
    proof_pass: bool
    release_eligible: bool
    release_reason_code: str | None
    released: bool


@dataclass(frozen=True)
class Pe22UpstreamSafetyProof:
    proof_id: str
    proof_digest: str
    pe22_contract_version: str
    integration_proof_digest: str
    pe22_integration_pass: bool
    lifecycle_matrix_digest: str


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
    capital_reallocation_authorized: bool
    reserve_topup_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class CapitalSlotRatchetReleaseLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    capital_slot_spec_proof: CapitalSlotSpecProof
    slot_identity: SlotIdentityBinding
    capital_slot_config: CapitalSlotConfigBinding
    capital_slot_state: CapitalSlotStateBinding
    equity_basis: EquityBasisBinding
    ratchet_stage: RatchetStageBinding
    ratchet_evaluation_proof: RatchetEvaluationProof
    reserve_topup_block_proof: ReserveTopupBlockProof
    inactivity_observation_window: ObservationWindowBinding
    opportunity_cost_observation_window: ObservationWindowBinding
    activity_metrics: ActivityMetricsBinding
    release_eligibility_proof: ReleaseEligibilityProof
    pe22_upstream_safety_proof: Pe22UpstreamSafetyProof
    lifecycle_state_before: LifecycleStateBinding
    declared_lifecycle_state_after: DeclaredLifecycleStateBinding
    lifecycle_matrix_proof: LifecycleMatrixProof
    safety_snapshot: IntegrationSafetySnapshot
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _finite_non_negative(value: float, field_name: str) -> list[str]:
    fail_reasons: list[str] = []
    if not math.isfinite(value):
        fail_reasons.append(f"{field_name} must be finite")
    elif value < 0:
        fail_reasons.append(f"{field_name} must be non-negative")
    return fail_reasons


def compute_capital_slot_spec_digest() -> str:
    """Deterministic digest of canonical capital-slot layer/spec identity."""
    spec = {
        "canonical_owner": CAPITAL_SLOT_CANONICAL_OWNER,
        "hash_algorithm": HASH_ALGORITHM,
        "layer_version": DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
        "spec_reference": CAPITAL_SLOT_SPEC_REFERENCE,
    }
    return hashlib.sha256(
        json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def _config_from_binding(binding: CapitalSlotConfigBinding) -> CapitalSlotConfig:
    return CapitalSlotConfig(
        profit_step_pct=binding.profit_step_pct,
        cashflow_lock_fraction=binding.cashflow_lock_fraction,
        reinvest_fraction=binding.reinvest_fraction,
        allow_auto_top_up=binding.allow_auto_top_up,
        live_authorization=binding.live_authorization,
        min_realized_volatility=binding.min_realized_volatility,
        min_atr_or_range=binding.min_atr_or_range,
        max_time_without_cashflow_step=binding.max_time_without_cashflow_step,
        min_opportunity_score=binding.min_opportunity_score,
    )


def _state_from_bindings(
    *,
    slot_identity: SlotIdentityBinding,
    state_binding: CapitalSlotStateBinding,
    activity_metrics: ActivityMetricsBinding,
) -> CapitalSlotState:
    return CapitalSlotState(
        selected_future=slot_identity.selected_future,
        initial_slot_base=state_binding.initial_slot_base,
        active_slot_base=state_binding.active_slot_base,
        realized_or_settled_slot_equity=state_binding.realized_or_settled_slot_equity,
        unrealized_pnl=state_binding.unrealized_pnl,
        locked_cashflow=state_binding.locked_cashflow,
        time_without_cashflow_step=activity_metrics.time_without_cashflow_step,
        realized_volatility=activity_metrics.realized_volatility,
        atr_or_range=activity_metrics.atr_or_range,
        opportunity_score=activity_metrics.opportunity_score,
        survival_allows_slot=state_binding.survival_allows_slot,
    )


def serialize_slot_identity_canonical(slot_identity: SlotIdentityBinding) -> str:
    payload = {
        "selected_future": slot_identity.selected_future,
        "slot_id": slot_identity.slot_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_slot_identity_digest(slot_identity: SlotIdentityBinding) -> str:
    return hashlib.sha256(
        serialize_slot_identity_canonical(slot_identity).encode("utf-8")
    ).hexdigest()


def serialize_equity_basis_canonical(equity_basis: EquityBasisBinding) -> str:
    payload = {
        "current_slot_basis": equity_basis.current_slot_basis,
        "new_settled_realized_equity": equity_basis.new_settled_realized_equity,
        "prior_valid_settled_basis": equity_basis.prior_valid_settled_basis,
        "unrealized_equity": equity_basis.unrealized_equity,
        "use_unrealized_as_reset_basis": equity_basis.use_unrealized_as_reset_basis,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_equity_basis_digest(equity_basis: EquityBasisBinding) -> str:
    return hashlib.sha256(
        serialize_equity_basis_canonical(equity_basis).encode("utf-8")
    ).hexdigest()


def serialize_ratchet_stage_canonical(ratchet_stage: RatchetStageBinding) -> str:
    payload = {
        "ratchet_stage": ratchet_stage.ratchet_stage,
        "ratchet_target": ratchet_stage.ratchet_target,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_ratchet_stage_digest(ratchet_stage: RatchetStageBinding) -> str:
    return hashlib.sha256(
        serialize_ratchet_stage_canonical(ratchet_stage).encode("utf-8")
    ).hexdigest()


def serialize_activity_metrics_canonical(metrics: ActivityMetricsBinding) -> str:
    payload = {
        "atr_or_range": metrics.atr_or_range,
        "opportunity_score": metrics.opportunity_score,
        "realized_volatility": metrics.realized_volatility,
        "time_without_cashflow_step": metrics.time_without_cashflow_step,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_activity_metrics_digest(metrics: ActivityMetricsBinding) -> str:
    return hashlib.sha256(serialize_activity_metrics_canonical(metrics).encode("utf-8")).hexdigest()


def serialize_observation_window_canonical(window: ObservationWindowBinding) -> str:
    payload = {
        "duration_seconds": window.duration_seconds,
        "end_epoch": window.end_epoch,
        "start_epoch": window.start_epoch,
        "window_id": window.window_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_observation_window_digest(window: ObservationWindowBinding) -> str:
    return hashlib.sha256(
        serialize_observation_window_canonical(window).encode("utf-8")
    ).hexdigest()


def serialize_pe22_upstream_safety_canonical(proof: Pe22UpstreamSafetyProof) -> str:
    payload = {
        "integration_proof_digest": proof.integration_proof_digest,
        "lifecycle_matrix_digest": proof.lifecycle_matrix_digest,
        "pe22_contract_version": proof.pe22_contract_version,
        "pe22_integration_pass": proof.pe22_integration_pass,
        "proof_id": proof.proof_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_pe22_upstream_safety_digest(proof: Pe22UpstreamSafetyProof) -> str:
    return hashlib.sha256(
        serialize_pe22_upstream_safety_canonical(proof).encode("utf-8")
    ).hexdigest()


def evaluate_ratchet_static_proof(
    *,
    config_binding: CapitalSlotConfigBinding,
    state_binding: CapitalSlotStateBinding,
    slot_identity: SlotIdentityBinding,
    activity_metrics: ActivityMetricsBinding,
) -> dict[str, Any]:
    """Compose existing evaluate_capital_slot_ratchet with explicit injected inputs only."""
    config = _config_from_binding(config_binding)
    state = _state_from_bindings(
        slot_identity=slot_identity,
        state_binding=state_binding,
        activity_metrics=activity_metrics,
    )
    decision = evaluate_capital_slot_ratchet(config, state)
    return {
        "can_ratchet": decision.can_ratchet,
        "ratchet_target": decision.ratchet_target,
        "new_active_slot_base": decision.new_active_slot_base,
        "block_reasons": tuple(reason.value for reason in decision.block_reasons),
        "proof_pass": decision.can_ratchet or not decision.block_reasons,
    }


def evaluate_release_static_proof(
    *,
    config_binding: CapitalSlotConfigBinding,
    state_binding: CapitalSlotStateBinding,
    slot_identity: SlotIdentityBinding,
    activity_metrics: ActivityMetricsBinding,
) -> dict[str, Any]:
    """Compose existing evaluate_capital_slot_release with explicit injected inputs only."""
    config = _config_from_binding(config_binding)
    state = _state_from_bindings(
        slot_identity=slot_identity,
        state_binding=state_binding,
        activity_metrics=activity_metrics,
    )
    decision = evaluate_capital_slot_release(config, state)
    release_reason = decision.release_reason.value if decision.release_reason is not None else None
    return {
        "released": decision.released,
        "release_eligible": decision.released,
        "release_reason_code": release_reason,
        "proof_pass": decision.released,
    }


def _integration_input_dict(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
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
        "capital_slot_spec_proof": asdict(integration_input.capital_slot_spec_proof),
        "slot_identity": asdict(integration_input.slot_identity),
        "capital_slot_config": asdict(integration_input.capital_slot_config),
        "capital_slot_state": asdict(integration_input.capital_slot_state),
        "equity_basis": asdict(integration_input.equity_basis),
        "ratchet_stage": asdict(integration_input.ratchet_stage),
        "ratchet_evaluation_proof": asdict(integration_input.ratchet_evaluation_proof),
        "reserve_topup_block_proof": asdict(integration_input.reserve_topup_block_proof),
        "inactivity_observation_window": asdict(integration_input.inactivity_observation_window),
        "opportunity_cost_observation_window": asdict(
            integration_input.opportunity_cost_observation_window
        ),
        "activity_metrics": asdict(integration_input.activity_metrics),
        "release_eligibility_proof": asdict(integration_input.release_eligibility_proof),
        "pe22_upstream_safety_proof": asdict(integration_input.pe22_upstream_safety_proof),
        "lifecycle_state_before": asdict(integration_input.lifecycle_state_before),
        "declared_lifecycle_state_after": asdict(integration_input.declared_lifecycle_state_after),
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_proof_dict(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    pe23_proven: bool = False,
    release_eligibility_proven: bool = False,
) -> dict[str, Any]:
    payload = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "lifecycle_matrix_digest": integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe12_capital_slot_ratchet_release_static_integration_proven": pe23_proven,
        "release_eligibility_proven": release_eligibility_proven,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_ratchet_applied": OPERATIVE_RATCHET_APPLIED,
        "operative_slot_release_executed": OPERATIVE_SLOT_RELEASE_EXECUTED,
        "operative_capital_reallocation_executed": OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
        "operative_reserve_movement_executed": OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "global_capital_slot_readiness": GLOBAL_CAPITAL_SLOT_READINESS,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_proof_canonical(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    *,
    pe23_proven: bool = False,
    release_eligibility_proven: bool = False,
) -> str:
    return json.dumps(
        _integration_proof_dict(
            integration_input,
            pe23_proven=pe23_proven,
            release_eligibility_proven=release_eligibility_proven,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    *,
    pe23_proven: bool = False,
    release_eligibility_proven: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_proof_canonical(
            integration_input,
            pe23_proven=pe23_proven,
            release_eligibility_proven=release_eligibility_proven,
        ).encode("utf-8")
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
        ("capital_reallocation_authorized", False),
        ("reserve_topup_allowed", False),
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


def _validate_capital_slot_spec_proof(spec_proof: CapitalSlotSpecProof) -> list[str]:
    fail_reasons: list[str] = []
    if spec_proof.layer_version != DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION:
        fail_reasons.append(
            f"capital_slot_spec_proof: layer_version must be {DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION!r}"
        )
    if spec_proof.spec_reference != CAPITAL_SLOT_SPEC_REFERENCE:
        fail_reasons.append(
            f"capital_slot_spec_proof: spec_reference must be {CAPITAL_SLOT_SPEC_REFERENCE!r}"
        )
    if spec_proof.canonical_owner != CAPITAL_SLOT_CANONICAL_OWNER:
        fail_reasons.append(
            f"capital_slot_spec_proof: canonical_owner must be {CAPITAL_SLOT_CANONICAL_OWNER!r}"
        )
    if not spec_proof.spec_digest:
        fail_reasons.append("capital_slot_spec_proof: spec_digest required")
    elif not _valid_sha256_digest(spec_proof.spec_digest):
        fail_reasons.append(
            "capital_slot_spec_proof: spec_digest must be 64-char lowercase sha256 hex"
        )
    elif spec_proof.spec_digest != compute_capital_slot_spec_digest():
        fail_reasons.append("capital_slot_spec_proof: spec_digest mismatch")
    return fail_reasons


def _validate_slot_identity(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    slot = integration_input.slot_identity
    if not slot.slot_id:
        fail_reasons.append("slot_identity: slot_id required")
    if not slot.slot_digest:
        fail_reasons.append("slot_identity: slot_digest required")
    elif not _valid_sha256_digest(slot.slot_digest):
        fail_reasons.append("slot_identity: slot_digest must be 64-char lowercase sha256 hex")
    elif slot.slot_digest != compute_slot_identity_digest(slot):
        fail_reasons.append("slot_identity: slot_digest mismatch")
    if slot.selected_future != integration_input.instrument:
        fail_reasons.append("slot_identity: selected_future must match instrument")
    return fail_reasons


def _validate_equity_basis(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    equity = integration_input.equity_basis
    state = integration_input.capital_slot_state

    fail_reasons.extend(
        _finite_non_negative(equity.current_slot_basis, "equity_basis: current_slot_basis")
    )
    fail_reasons.extend(
        _finite_non_negative(
            equity.prior_valid_settled_basis, "equity_basis: prior_valid_settled_basis"
        )
    )
    fail_reasons.extend(
        _finite_non_negative(
            equity.new_settled_realized_equity, "equity_basis: new_settled_realized_equity"
        )
    )
    if not math.isfinite(equity.unrealized_equity):
        fail_reasons.append("equity_basis: unrealized_equity must be finite")
    if equity.use_unrealized_as_reset_basis:
        fail_reasons.append("equity_basis: use_unrealized_as_reset_basis must be false")
    if not equity.basis_digest:
        fail_reasons.append("equity_basis: basis_digest required")
    elif not _valid_sha256_digest(equity.basis_digest):
        fail_reasons.append("equity_basis: basis_digest must be 64-char lowercase sha256 hex")
    elif equity.basis_digest != compute_equity_basis_digest(equity):
        fail_reasons.append("equity_basis: basis_digest mismatch")
    if state.realized_or_settled_slot_equity != equity.new_settled_realized_equity:
        fail_reasons.append("settled/realized equity mismatch between state and equity_basis")
    if state.unrealized_pnl != equity.unrealized_equity:
        fail_reasons.append("unrealized equity mismatch between state and equity_basis")
    if state.active_slot_base != equity.current_slot_basis:
        fail_reasons.append("current_slot_basis mismatch between state and equity_basis")

    if equity.new_settled_realized_equity < equity.prior_valid_settled_basis:
        expected_loss_base = apply_loss_following_base(
            equity.current_slot_basis, equity.new_settled_realized_equity
        )
        if equity.current_slot_basis > expected_loss_base + 1e-9:
            fail_reasons.append("slot basis must follow realized loss downward")
    elif equity.current_slot_basis > equity.new_settled_realized_equity + 1e-9:
        fail_reasons.append("unallowable slot basis increase without settled support")

    return fail_reasons


def _validate_ratchet_stage(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    stage = integration_input.ratchet_stage
    config = integration_input.capital_slot_config
    if not math.isfinite(stage.ratchet_stage):
        fail_reasons.append("ratchet_stage: ratchet_stage must be finite")
    elif stage.ratchet_stage != config.profit_step_pct:
        fail_reasons.append("ratchet_stage: ratchet_stage must match config profit_step_pct")
    if not math.isfinite(stage.ratchet_target):
        fail_reasons.append("ratchet_stage: ratchet_target must be finite")
    if not stage.stage_digest:
        fail_reasons.append("ratchet_stage: stage_digest required")
    elif not _valid_sha256_digest(stage.stage_digest):
        fail_reasons.append("ratchet_stage: stage_digest must be 64-char lowercase sha256 hex")
    elif stage.stage_digest != compute_ratchet_stage_digest(stage):
        fail_reasons.append("ratchet_stage: stage_digest mismatch")
    return fail_reasons


def _validate_ratchet_proof_chain(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.ratchet_evaluation_proof
    static_eval = evaluate_ratchet_static_proof(
        config_binding=integration_input.capital_slot_config,
        state_binding=integration_input.capital_slot_state,
        slot_identity=integration_input.slot_identity,
        activity_metrics=integration_input.activity_metrics,
    )

    if not proof.proof_digest:
        fail_reasons.append("ratchet_evaluation_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "ratchet_evaluation_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.can_ratchet != static_eval["can_ratchet"]:
        fail_reasons.append(
            "ratchet_evaluation_proof: can_ratchet mismatch with capital_slot model"
        )
    if abs(proof.ratchet_target - static_eval["ratchet_target"]) > 1e-9:
        fail_reasons.append(
            "ratchet_evaluation_proof: ratchet_target mismatch with capital_slot model"
        )
    if proof.new_active_slot_base != static_eval["new_active_slot_base"]:
        fail_reasons.append(
            "ratchet_evaluation_proof: new_active_slot_base mismatch with capital_slot model"
        )
    if tuple(proof.block_reasons) != static_eval["block_reasons"]:
        fail_reasons.append(
            "ratchet_evaluation_proof: block_reasons mismatch with capital_slot model"
        )
    if proof.proof_pass is not True:
        fail_reasons.append(
            "ratchet_evaluation_proof: proof_pass must be true for valid integration"
        )

    stage = integration_input.ratchet_stage
    if abs(proof.ratchet_target - stage.ratchet_target) > 1e-9:
        fail_reasons.append(
            "ratchet_evaluation_proof: ratchet_target mismatch with ratchet_stage binding"
        )

    if proof.can_ratchet and proof.new_active_slot_base is not None:
        equity = integration_input.equity_basis
        if proof.new_active_slot_base > equity.new_settled_realized_equity + 1e-9:
            fail_reasons.append("unallowable slot basis increase against settled equity")

    return fail_reasons


def _validate_reserve_topup_block_proof(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.reserve_topup_block_proof
    config = integration_input.capital_slot_config

    if config.allow_auto_top_up:
        fail_reasons.append("capital_slot_config: allow_auto_top_up must be false")
    if not proof.proof_digest:
        fail_reasons.append("reserve_topup_block_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "reserve_topup_block_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.reserve_topup_blocked is not True:
        fail_reasons.append("reserve_topup_block_proof: reserve_topup_blocked must be true")
    if proof.reserve_topup_attempted:
        fail_reasons.append("reserve_topup_block_proof: reserve_topup_attempted must be false")
    if proof.allow_auto_top_up_declared is not False:
        fail_reasons.append("reserve_topup_block_proof: allow_auto_top_up_declared must be false")
    if proof.proof_pass is not True:
        fail_reasons.append(
            "reserve_topup_block_proof: proof_pass must be true for valid integration"
        )
    return fail_reasons


def _validate_observation_window(
    window: ObservationWindowBinding,
    *,
    field_prefix: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if not window.window_id:
        fail_reasons.append(f"{field_prefix}: window_id required")
    if not window.window_digest:
        fail_reasons.append(f"{field_prefix}: window_digest required")
    elif not _valid_sha256_digest(window.window_digest):
        fail_reasons.append(f"{field_prefix}: window_digest must be 64-char lowercase sha256 hex")
    elif window.window_digest != compute_observation_window_digest(window):
        fail_reasons.append(f"{field_prefix}: window_digest mismatch")
    if window.start_epoch < 0 or window.end_epoch < 0:
        fail_reasons.append(f"{field_prefix}: start_epoch and end_epoch must be non-negative")
    if window.end_epoch <= window.start_epoch:
        fail_reasons.append(f"{field_prefix}: end_epoch must be greater than start_epoch")
    if window.duration_seconds != window.end_epoch - window.start_epoch:
        fail_reasons.append(f"{field_prefix}: duration_seconds mismatch with epoch window")
    if window.duration_seconds <= 0:
        fail_reasons.append(f"{field_prefix}: duration_seconds must be positive")
    return fail_reasons


def _validate_activity_metrics(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    metrics = integration_input.activity_metrics
    state = integration_input.capital_slot_state

    if metrics.time_without_cashflow_step < 0:
        fail_reasons.append("activity_metrics: time_without_cashflow_step must be non-negative")
    fail_reasons.extend(
        _finite_non_negative(metrics.realized_volatility, "activity_metrics: realized_volatility")
    )
    fail_reasons.extend(
        _finite_non_negative(metrics.atr_or_range, "activity_metrics: atr_or_range")
    )
    fail_reasons.extend(
        _finite_non_negative(metrics.opportunity_score, "activity_metrics: opportunity_score")
    )
    if not metrics.metrics_digest:
        fail_reasons.append("activity_metrics: metrics_digest required")
    elif not _valid_sha256_digest(metrics.metrics_digest):
        fail_reasons.append("activity_metrics: metrics_digest must be 64-char lowercase sha256 hex")
    elif metrics.metrics_digest != compute_activity_metrics_digest(metrics):
        fail_reasons.append("activity_metrics: metrics_digest mismatch")

    static_state = _state_from_bindings(
        slot_identity=integration_input.slot_identity,
        state_binding=state,
        activity_metrics=metrics,
    )
    if static_state.time_without_cashflow_step != metrics.time_without_cashflow_step:
        fail_reasons.append("activity_metrics: time_without_cashflow_step required")
    if abs(static_state.realized_volatility - metrics.realized_volatility) > 1e-9:
        fail_reasons.append("activity_metrics: realized_volatility required")
    if abs(static_state.atr_or_range - metrics.atr_or_range) > 1e-9:
        fail_reasons.append("activity_metrics: atr_or_range required")
    if abs(static_state.opportunity_score - metrics.opportunity_score) > 1e-9:
        fail_reasons.append("activity_metrics: opportunity_score required")
    return fail_reasons


def _validate_release_proof_chain(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.release_eligibility_proof
    static_eval = evaluate_release_static_proof(
        config_binding=integration_input.capital_slot_config,
        state_binding=integration_input.capital_slot_state,
        slot_identity=integration_input.slot_identity,
        activity_metrics=integration_input.activity_metrics,
    )

    if not proof.proof_digest:
        fail_reasons.append("release_eligibility_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "release_eligibility_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.release_eligible != static_eval["release_eligible"]:
        fail_reasons.append(
            "release_eligibility_proof: release_eligible mismatch with capital_slot model"
        )
    if proof.released != static_eval["released"]:
        fail_reasons.append("release_eligibility_proof: released mismatch with capital_slot model")
    if proof.release_reason_code != static_eval["release_reason_code"]:
        fail_reasons.append(
            "release_eligibility_proof: release_reason_code mismatch with capital_slot model"
        )
    if proof.release_eligible and proof.proof_pass is not True:
        fail_reasons.append(
            "release_eligibility_proof: proof_pass must be true when release_eligible is true"
        )
    if proof.release_eligible and not proof.release_reason_code:
        fail_reasons.append("release_eligibility_proof: release_reason_code required when eligible")
    if proof.release_reason_code and proof.release_reason_code not in {
        CapitalSlotReleaseReason.INACTIVITY.value,
        CapitalSlotReleaseReason.OPPORTUNITY_COST.value,
    }:
        fail_reasons.append("release_eligibility_proof: manipulated release_reason_code")
    return fail_reasons


def _validate_pe22_upstream_safety_proof(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe22_upstream_safety_proof

    if not proof.proof_id:
        fail_reasons.append("pe22_upstream_safety_proof: proof_id required")
    if not proof.proof_digest:
        fail_reasons.append("pe22_upstream_safety_proof: proof_digest required")
    elif not _valid_sha256_digest(proof.proof_digest):
        fail_reasons.append(
            "pe22_upstream_safety_proof: proof_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.proof_digest != compute_pe22_upstream_safety_digest(proof):
        fail_reasons.append("pe22_upstream_safety_proof: proof_digest mismatch")
    if proof.pe22_contract_version != PE22_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe22_upstream_safety_proof: pe22_contract_version must be {PE22_CONTRACT_VERSION!r}"
        )
    if not proof.integration_proof_digest:
        fail_reasons.append("pe22_upstream_safety_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe22_upstream_safety_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.pe22_integration_pass is not True:
        fail_reasons.append("pe22_upstream_safety_proof: pe22_integration_pass must be true")
    if not proof.lifecycle_matrix_digest:
        fail_reasons.append("pe22_upstream_safety_proof: lifecycle_matrix_digest required")
    elif proof.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("pe22_upstream_safety_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def validate_capital_slot_ratchet_release_lifecycle_integration_input(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
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

    fail_reasons.extend(
        _validate_capital_slot_spec_proof(integration_input.capital_slot_spec_proof)
    )
    fail_reasons.extend(_validate_slot_identity(integration_input))
    fail_reasons.extend(_validate_equity_basis(integration_input))
    fail_reasons.extend(_validate_ratchet_stage(integration_input))
    fail_reasons.extend(_validate_ratchet_proof_chain(integration_input))
    fail_reasons.extend(_validate_reserve_topup_block_proof(integration_input))
    fail_reasons.extend(
        _validate_observation_window(
            integration_input.inactivity_observation_window,
            field_prefix="inactivity_observation_window",
        )
    )
    fail_reasons.extend(
        _validate_observation_window(
            integration_input.opportunity_cost_observation_window,
            field_prefix="opportunity_cost_observation_window",
        )
    )
    fail_reasons.extend(_validate_activity_metrics(integration_input))
    fail_reasons.extend(_validate_release_proof_chain(integration_input))
    fail_reasons.extend(_validate_pe22_upstream_safety_proof(integration_input))

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
    if matrix.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_RECONCILIATION_REVIEW!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    before = integration_input.lifecycle_state_before
    after = integration_input.declared_lifecycle_state_after
    if before.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"lifecycle_state_before: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )
    if after.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"declared_lifecycle_state_after: assigned_lifecycle_phase must be {PHASE_RECONCILIATION_REVIEW!r}"
        )
    if before.adapter_id != integration_input.adapter_id:
        fail_reasons.append("lifecycle_state_before: adapter_id mismatch")
    if after.adapter_id != integration_input.adapter_id:
        fail_reasons.append("declared_lifecycle_state_after: adapter_id mismatch")

    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.capital_slot_config.live_authorization:
        fail_reasons.append("capital_slot_config: live_authorization must be false")

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_reconciliation_lifecycle_compatibility(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 reconciliation_review phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_RECONCILIATION_REVIEW]
    snapshot = integration_input.safety_snapshot
    release = integration_input.release_eligibility_proof

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: network_allowed true for reconciliation_review"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: orders_allowed true for reconciliation_review"
        )
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for reconciliation_review"
        )
    if snapshot.live_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: live_authorized true for reconciliation_review"
        )
    if snapshot.capital_reallocation_authorized:
        fail_reasons.append("lifecycle/gate contradiction: capital_reallocation_authorized true")
    if snapshot.reserve_topup_allowed:
        fail_reasons.append("lifecycle/gate contradiction: reserve_topup_allowed true")
    if release.release_eligible and release.released:
        if release.release_reason_code == CapitalSlotReleaseReason.INACTIVITY.value:
            if (
                integration_input.activity_metrics.realized_volatility
                >= integration_input.capital_slot_config.min_realized_volatility
                and integration_input.activity_metrics.atr_or_range
                >= integration_input.capital_slot_config.min_atr_or_range
                and integration_input.activity_metrics.time_without_cashflow_step
                <= integration_input.capital_slot_config.max_time_without_cashflow_step
            ):
                fail_reasons.append(
                    "lifecycle/slot contradiction: inactivity release without breach"
                )
        if release.release_reason_code == CapitalSlotReleaseReason.OPPORTUNITY_COST.value:
            if (
                integration_input.activity_metrics.opportunity_score
                >= integration_input.capital_slot_config.min_opportunity_score
            ):
                fail_reasons.append(
                    "lifecycle/slot contradiction: opportunity release without score breach"
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


def evaluate_capital_slot_ratchet_release_lifecycle_integration(
    integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_ratchet_proof_digest: str | None = None,
    expected_release_proof_digest: str | None = None,
    release_eligible_without_proof_chain: bool = False,
    capital_reallocation_authorized: bool = False,
    reserve_movement_authorized: bool = False,
    network_run_started: bool = False,
    runtime_started: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-12 reconciliation_review capital slot integration proof."""
    fail_reasons = validate_capital_slot_ratchet_release_lifecycle_integration_input(
        integration_input
    )

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_ratchet_proof_digest is not None:
        if integration_input.ratchet_evaluation_proof.proof_digest != expected_ratchet_proof_digest:
            fail_reasons.append("ratchet_evaluation_proof: proof_digest mismatch")

    if expected_release_proof_digest is not None:
        if (
            integration_input.release_eligibility_proof.proof_digest
            != expected_release_proof_digest
        ):
            fail_reasons.append("release_eligibility_proof: proof_digest mismatch")

    if release_eligible_without_proof_chain:
        fail_reasons.append("release_eligible=true without full proof chain is insufficient")
    if capital_reallocation_authorized:
        fail_reasons.append("capital_reallocation_authorized=true is not allowed")
    if reserve_movement_authorized:
        fail_reasons.append("reserve_movement_authorized=true is not allowed")
    if network_run_started:
        fail_reasons.append("network_run_started=true is not allowed")
    if runtime_started:
        fail_reasons.append("runtime_started=true is not allowed")
    if execution_authorized:
        fail_reasons.append("execution_authorized=true is not allowed")
    if live_authorized:
        fail_reasons.append("live_authorized=true is not allowed")
    if credentials_allowed:
        fail_reasons.append("credentials_allowed=true is not allowed")
    if orders_allowed:
        fail_reasons.append("orders_allowed=true is not allowed")

    if not fail_reasons:
        fail_reasons.extend(_validate_reconciliation_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    release_eligibility_proven = (
        integration_pass and integration_input.release_eligibility_proof.release_eligible
    )
    pe23_proven = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                pe23_proven=pe23_proven,
                release_eligibility_proven=release_eligibility_proven,
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe12_capital_slot_ratchet_release_static_integration_proven": pe23_proven,
        "release_eligibility_proven": release_eligibility_proven,
        "global_capital_slot_readiness": GLOBAL_CAPITAL_SLOT_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_ratchet_applied": OPERATIVE_RATCHET_APPLIED,
        "operative_slot_release_executed": OPERATIVE_SLOT_RELEASE_EXECUTED,
        "operative_capital_reallocation_executed": OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
        "operative_reserve_movement_executed": OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
        "account_state_queried": ACCOUNT_STATE_QUERIED,
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
        "capital_reallocation_authorized": False,
        "reserve_topup_allowed": False,
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
        capital_reallocation_authorized=False,
        reserve_topup_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def _default_capital_slot_spec_proof() -> CapitalSlotSpecProof:
    return CapitalSlotSpecProof(
        layer_version=DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
        spec_reference=CAPITAL_SLOT_SPEC_REFERENCE,
        spec_digest=compute_capital_slot_spec_digest(),
        canonical_owner=CAPITAL_SLOT_CANONICAL_OWNER,
    )


def _default_observation_window(
    *, window_id: str, start_epoch: int, end_epoch: int
) -> ObservationWindowBinding:
    window = ObservationWindowBinding(
        window_id=window_id,
        window_digest="",
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        duration_seconds=end_epoch - start_epoch,
    )
    return ObservationWindowBinding(
        window_id=window.window_id,
        window_digest=compute_observation_window_digest(window),
        start_epoch=window.start_epoch,
        end_epoch=window.end_epoch,
        duration_seconds=window.duration_seconds,
    )


def _default_pe22_upstream_safety_proof() -> Pe22UpstreamSafetyProof:
    pe22_input = default_pe22_minimal_integration_input()
    pe22_result = evaluate_risk_killswitch_lifecycle_integration(pe22_input)
    assert pe22_result["integration_pass"] is True
    integration_proof_digest = pe22_result["integration_proof_digest"]
    assert integration_proof_digest is not None
    proof = Pe22UpstreamSafetyProof(
        proof_id="pe22-upstream-safety-001",
        proof_digest="",
        pe22_contract_version=PE22_CONTRACT_VERSION,
        integration_proof_digest=integration_proof_digest,
        pe22_integration_pass=True,
        lifecycle_matrix_digest=compute_pe22_lifecycle_matrix_digest(),
    )
    return Pe22UpstreamSafetyProof(
        proof_id=proof.proof_id,
        proof_digest=compute_pe22_upstream_safety_digest(proof),
        pe22_contract_version=proof.pe22_contract_version,
        integration_proof_digest=proof.integration_proof_digest,
        pe22_integration_pass=proof.pe22_integration_pass,
        lifecycle_matrix_digest=proof.lifecycle_matrix_digest,
    )


def _build_ratchet_release_proofs(
    *,
    config_binding: CapitalSlotConfigBinding,
    state_binding: CapitalSlotStateBinding,
    slot_identity: SlotIdentityBinding,
    activity_metrics: ActivityMetricsBinding,
    equity_basis: EquityBasisBinding,
) -> tuple[
    RatchetStageBinding, RatchetEvaluationProof, ReserveTopupBlockProof, ReleaseEligibilityProof
]:
    static_ratchet = evaluate_ratchet_static_proof(
        config_binding=config_binding,
        state_binding=state_binding,
        slot_identity=slot_identity,
        activity_metrics=activity_metrics,
    )
    static_release = evaluate_release_static_proof(
        config_binding=config_binding,
        state_binding=state_binding,
        slot_identity=slot_identity,
        activity_metrics=activity_metrics,
    )
    ratchet_stage = RatchetStageBinding(
        ratchet_stage=config_binding.profit_step_pct,
        ratchet_target=static_ratchet["ratchet_target"],
        stage_digest="",
    )
    ratchet_stage = RatchetStageBinding(
        ratchet_stage=ratchet_stage.ratchet_stage,
        ratchet_target=ratchet_stage.ratchet_target,
        stage_digest=compute_ratchet_stage_digest(ratchet_stage),
    )
    ratchet_proof = RatchetEvaluationProof(
        proof_digest="",
        proof_pass=True,
        can_ratchet=static_ratchet["can_ratchet"],
        ratchet_target=static_ratchet["ratchet_target"],
        new_active_slot_base=static_ratchet["new_active_slot_base"],
        block_reasons=static_ratchet["block_reasons"],
    )
    ratchet_proof_digest = hashlib.sha256(
        json.dumps(
            {
                "block_reasons": list(ratchet_proof.block_reasons),
                "can_ratchet": ratchet_proof.can_ratchet,
                "new_active_slot_base": ratchet_proof.new_active_slot_base,
                "proof_pass": ratchet_proof.proof_pass,
                "ratchet_target": ratchet_proof.ratchet_target,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    ratchet_proof = RatchetEvaluationProof(
        proof_digest=ratchet_proof_digest,
        proof_pass=ratchet_proof.proof_pass,
        can_ratchet=ratchet_proof.can_ratchet,
        ratchet_target=ratchet_proof.ratchet_target,
        new_active_slot_base=ratchet_proof.new_active_slot_base,
        block_reasons=ratchet_proof.block_reasons,
    )
    reserve_proof = ReserveTopupBlockProof(
        proof_digest=hashlib.sha256(
            json.dumps(
                {
                    "allow_auto_top_up_declared": False,
                    "reserve_topup_attempted": False,
                    "reserve_topup_blocked": True,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        proof_pass=True,
        reserve_topup_blocked=True,
        reserve_topup_attempted=False,
        allow_auto_top_up_declared=False,
    )
    release_proof = ReleaseEligibilityProof(
        proof_digest="",
        proof_pass=static_release["proof_pass"] if static_release["release_eligible"] else True,
        release_eligible=static_release["release_eligible"],
        release_reason_code=static_release["release_reason_code"],
        released=static_release["released"],
    )
    release_proof_digest = hashlib.sha256(
        json.dumps(
            {
                "proof_pass": release_proof.proof_pass,
                "release_eligible": release_proof.release_eligible,
                "release_reason_code": release_proof.release_reason_code,
                "released": release_proof.released,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    release_proof = ReleaseEligibilityProof(
        proof_digest=release_proof_digest,
        proof_pass=release_proof.proof_pass,
        release_eligible=release_proof.release_eligible,
        release_reason_code=release_proof.release_reason_code,
        released=release_proof.released,
    )
    _ = equity_basis
    return ratchet_stage, ratchet_proof, reserve_proof, release_proof


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
    release_eligible: bool = False,
) -> CapitalSlotRatchetReleaseLifecycleIntegrationInput:
    """Minimal valid futures-generic integration input for offline tests."""
    slot_identity = SlotIdentityBinding(
        slot_id="capital-slot-001",
        slot_digest="",
        selected_future=instrument,
    )
    slot_identity = SlotIdentityBinding(
        slot_id=slot_identity.slot_id,
        slot_digest=compute_slot_identity_digest(slot_identity),
        selected_future=slot_identity.selected_future,
    )

    if release_eligible:
        config_binding = CapitalSlotConfigBinding(
            profit_step_pct=0.10,
            cashflow_lock_fraction=0.30,
            reinvest_fraction=0.70,
            allow_auto_top_up=False,
            live_authorization=False,
            min_realized_volatility=0.05,
            min_atr_or_range=0.05,
            max_time_without_cashflow_step=10_000,
            min_opportunity_score=0.2,
        )
        activity_metrics = ActivityMetricsBinding(
            time_without_cashflow_step=0,
            realized_volatility=0.01,
            atr_or_range=0.01,
            opportunity_score=0.8,
            metrics_digest="",
        )
        state_binding = CapitalSlotStateBinding(
            initial_slot_base=300.0,
            active_slot_base=300.0,
            realized_or_settled_slot_equity=300.0,
            unrealized_pnl=0.0,
            locked_cashflow=0.0,
            survival_allows_slot=True,
        )
    else:
        config_binding = CapitalSlotConfigBinding(
            profit_step_pct=0.10,
            cashflow_lock_fraction=0.30,
            reinvest_fraction=0.70,
            allow_auto_top_up=False,
            live_authorization=False,
            min_realized_volatility=0.05,
            min_atr_or_range=0.05,
            max_time_without_cashflow_step=10_000,
            min_opportunity_score=0.2,
        )
        activity_metrics = ActivityMetricsBinding(
            time_without_cashflow_step=0,
            realized_volatility=0.5,
            atr_or_range=0.5,
            opportunity_score=0.8,
            metrics_digest="",
        )
        state_binding = CapitalSlotStateBinding(
            initial_slot_base=300.0,
            active_slot_base=300.0,
            realized_or_settled_slot_equity=340.0,
            unrealized_pnl=0.0,
            locked_cashflow=0.0,
            survival_allows_slot=True,
        )

    activity_metrics = ActivityMetricsBinding(
        time_without_cashflow_step=activity_metrics.time_without_cashflow_step,
        realized_volatility=activity_metrics.realized_volatility,
        atr_or_range=activity_metrics.atr_or_range,
        opportunity_score=activity_metrics.opportunity_score,
        metrics_digest=compute_activity_metrics_digest(activity_metrics),
    )

    equity_basis = EquityBasisBinding(
        current_slot_basis=state_binding.active_slot_base,
        prior_valid_settled_basis=300.0,
        new_settled_realized_equity=state_binding.realized_or_settled_slot_equity,
        unrealized_equity=state_binding.unrealized_pnl,
        use_unrealized_as_reset_basis=False,
        basis_digest="",
    )
    equity_basis = EquityBasisBinding(
        current_slot_basis=equity_basis.current_slot_basis,
        prior_valid_settled_basis=equity_basis.prior_valid_settled_basis,
        new_settled_realized_equity=equity_basis.new_settled_realized_equity,
        unrealized_equity=equity_basis.unrealized_equity,
        use_unrealized_as_reset_basis=equity_basis.use_unrealized_as_reset_basis,
        basis_digest=compute_equity_basis_digest(equity_basis),
    )

    ratchet_stage, ratchet_proof, reserve_proof, release_proof = _build_ratchet_release_proofs(
        config_binding=config_binding,
        state_binding=state_binding,
        slot_identity=slot_identity,
        activity_metrics=activity_metrics,
        equity_basis=equity_basis,
    )

    matrix_digest = compute_lifecycle_matrix_digest()
    state_digest = lifecycle_state_digest or "e" * 64

    return CapitalSlotRatchetReleaseLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            capital_slot_layer=DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
            pe22_upstream_safety=PE22_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        capital_slot_spec_proof=_default_capital_slot_spec_proof(),
        slot_identity=slot_identity,
        capital_slot_config=config_binding,
        capital_slot_state=state_binding,
        equity_basis=equity_basis,
        ratchet_stage=ratchet_stage,
        ratchet_evaluation_proof=ratchet_proof,
        reserve_topup_block_proof=reserve_proof,
        inactivity_observation_window=_default_observation_window(
            window_id="inactivity-window-001",
            start_epoch=1_700_000_000,
            end_epoch=1_700_086_400,
        ),
        opportunity_cost_observation_window=_default_observation_window(
            window_id="opportunity-window-001",
            start_epoch=1_700_000_000,
            end_epoch=1_700_172_800,
        ),
        activity_metrics=activity_metrics,
        release_eligibility_proof=release_proof,
        pe22_upstream_safety_proof=_default_pe22_upstream_safety_proof(),
        lifecycle_state_before=LifecycleStateBinding(
            state_id="lifecycle-before-001",
            state_digest="b" * 64,
            assigned_lifecycle_phase=PHASE_TINY_ORDER,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=DeclaredLifecycleStateBinding(
            state_id="lifecycle-after-001",
            state_digest="a" * 64,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            adapter_id=adapter_id,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            lifecycle_state_digest=state_digest,
        ),
        safety_snapshot=default_minimal_safety_snapshot(),
    )
