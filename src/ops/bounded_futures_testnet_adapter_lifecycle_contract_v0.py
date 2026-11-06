"""Repo-native bounded Futures Testnet adapter lifecycle contract (v0, PE-12).

Offline contract defining the allowed futures-testnet adapter lifecycle phase
sequence, transition gates, and composition hooks to PE-8/9/10/11 evaluators.
Does not authorize network, credentials, orders, runtime, scheduler, or live.
Default posture remains fail-closed; no phase auto-unlocks from static contract alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    PACKAGE_MARKER as PE11_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    ADAPTER_NETWORK_CALLS_ALLOWED,
    default_offline_adapter_binding,
    validate_futures_testnet_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    FUTURES_SESSION_AUTHORIZED_NOW,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    default_bounded_futures_normal_v0_spec,
)
from src.ops.bounded_futures_testnet_harness_contract_v0 import (
    HARNESS_EXECUTE_AUTHORIZED_NOW,
    default_offline_harness_config,
    evaluate_bounded_futures_testnet_harness_readiness,
)
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    RUNTIME_HARNESS_EXECUTE_ALLOWED,
    default_offline_runtime_harness_impl_descriptor,
    validate_futures_testnet_runtime_harness_impl_descriptor,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_LIFECYCLE_CONTRACT_V0=true"
LIFECYCLE_EXECUTE_AUTHORIZED_NOW = False
LIFECYCLE_NETWORK_AUTHORIZED_NOW = False
LIFECYCLE_ORDERS_AUTHORIZED_NOW = False
PREFLIGHT_REMAINS_BLOCKED = True
READY_FOR_OPERATOR_ARMING = False

PHASE_STATIC_PREFLIGHT = "static_preflight"
PHASE_ZERO_ORDER = "zero_order"
PHASE_PRIVATE_READONLY = "private_readonly"
PHASE_VALIDATE_ONLY = "validate_only"
PHASE_TINY_ORDER = "tiny_order"
PHASE_RECONCILIATION_REVIEW = "reconciliation_review"
PHASE_READINESS_DECISION = "readiness_decision"

LIFECYCLE_PHASE_ORDER: tuple[str, ...] = (
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
    PHASE_PRIVATE_READONLY,
    PHASE_VALIDATE_ONLY,
    PHASE_TINY_ORDER,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_READINESS_DECISION,
)

NETWORK_EXECUTION_PHASES: frozenset[str] = frozenset(
    {
        PHASE_ZERO_ORDER,
        PHASE_PRIVATE_READONLY,
        PHASE_VALIDATE_ONLY,
        PHASE_TINY_ORDER,
    }
)

OPERATOR_GO_STATIC_PREFLIGHT = "GO_BOUNDED_FUTURES_TESTNET_STATIC_PREFLIGHT_V0"
OPERATOR_GO_ZERO_ORDER = "GO_BOUNDED_FUTURES_TESTNET_ZERO_ORDER_V0"
OPERATOR_GO_PRIVATE_READONLY = "GO_BOUNDED_FUTURES_TESTNET_PRIVATE_READONLY_V0"
OPERATOR_GO_VALIDATE_ONLY = "GO_BOUNDED_FUTURES_TESTNET_VALIDATE_ONLY_V0"
OPERATOR_GO_TINY_ORDER = "GO_BOUNDED_FUTURES_TESTNET_TINY_ORDER_V0"
OPERATOR_GO_RECONCILIATION_REVIEW = "GO_BOUNDED_FUTURES_TESTNET_RECONCILIATION_REVIEW_V0"
OPERATOR_GO_READINESS_DECISION = "GO_BOUNDED_FUTURES_TESTNET_READINESS_DECISION_V0"

PHASE_OPERATOR_GO_TOKENS: dict[str, str] = {
    PHASE_STATIC_PREFLIGHT: OPERATOR_GO_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER: OPERATOR_GO_ZERO_ORDER,
    PHASE_PRIVATE_READONLY: OPERATOR_GO_PRIVATE_READONLY,
    PHASE_VALIDATE_ONLY: OPERATOR_GO_VALIDATE_ONLY,
    PHASE_TINY_ORDER: OPERATOR_GO_TINY_ORDER,
    PHASE_RECONCILIATION_REVIEW: OPERATOR_GO_RECONCILIATION_REVIEW,
    PHASE_READINESS_DECISION: OPERATOR_GO_READINESS_DECISION,
}

PHASE_CANONICAL_OWNERS: dict[str, str] = {
    PHASE_STATIC_PREFLIGHT: (
        "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md#2b.2 + "
        "bounded_futures_testnet_adapter_lifecycle_contract_v0"
    ),
    PHASE_ZERO_ORDER: "scripts/ops/archive_futures_testnet_harness_v0.py",
    PHASE_PRIVATE_READONLY: "src/ops/bounded_futures_private_readonly_contract_v0.py",
    PHASE_VALIDATE_ONLY: "src/ops/bounded_futures_testnet_contract_v0.py",
    PHASE_TINY_ORDER: "src/ops/bounded_futures_testnet_contract_v0.py",
    PHASE_RECONCILIATION_REVIEW: "src/ops/recon/reconcile.py",
    PHASE_READINESS_DECISION: "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md",
}


@dataclass(frozen=True)
class LifecyclePhaseDescriptor:
    phase_id: str
    sequence_index: int
    network_phase: bool
    orders_phase: bool
    credentials_phase: bool
    operator_go_token: str
    canonical_owner: str


def _build_phase_descriptors() -> dict[str, LifecyclePhaseDescriptor]:
    descriptors: dict[str, LifecyclePhaseDescriptor] = {}
    for index, phase_id in enumerate(LIFECYCLE_PHASE_ORDER):
        descriptors[phase_id] = LifecyclePhaseDescriptor(
            phase_id=phase_id,
            sequence_index=index,
            network_phase=phase_id in NETWORK_EXECUTION_PHASES,
            orders_phase=phase_id == PHASE_TINY_ORDER,
            credentials_phase=phase_id == PHASE_PRIVATE_READONLY,
            operator_go_token=PHASE_OPERATOR_GO_TOKENS[phase_id],
            canonical_owner=PHASE_CANONICAL_OWNERS[phase_id],
        )
    return descriptors


LIFECYCLE_PHASE_DESCRIPTORS: dict[str, LifecyclePhaseDescriptor] = _build_phase_descriptors()


@dataclass(frozen=True)
class AdapterLifecycleState:
    phases_completed: frozenset[str]
    reconciliations_completed: frozenset[str]
    instrument: str
    market_type: str


@dataclass(frozen=True)
class PhaseTransitionRequest:
    target_phase: str
    operator_go_token: str | None
    risk_killswitch_binding_acknowledged: bool = False
    flatten_binding_acknowledged: bool = False
    durable_primary_evidence_capable: bool = False
    manifest_verify_rc_zero: bool = False
    static_contract_self_check_pass: bool = False


def default_blocked_lifecycle_state(
    *,
    instrument: str | None = None,
) -> AdapterLifecycleState:
    spec = default_bounded_futures_normal_v0_spec()
    return AdapterLifecycleState(
        phases_completed=frozenset(),
        reconciliations_completed=frozenset(),
        instrument=instrument or spec.instrument,
        market_type=DEFAULT_MARKET_TYPE,
    )


def _prior_phase(phase_id: str) -> str | None:
    index = LIFECYCLE_PHASE_ORDER.index(phase_id)
    if index == 0:
        return None
    return LIFECYCLE_PHASE_ORDER[index - 1]


def _required_reconciliation_phase_for(phase_id: str) -> str | None:
    prior = _prior_phase(phase_id)
    if prior is not None and prior in NETWORK_EXECUTION_PHASES:
        return prior
    return None


def validate_lifecycle_instrument_binding(instrument: str, market_type: str) -> list[str]:
    reasons: list[str] = []
    if market_type != DEFAULT_MARKET_TYPE:
        reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not instrument:
        reasons.append("instrument required")
    if instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        reasons.append(f"instrument {instrument!r} is a rejected futures placeholder")
    return reasons


def evaluate_pe_contract_composition() -> dict[str, Any]:
    """Offline composition check across PE-8/9/10/11 surfaces (no I/O)."""
    binding = default_offline_adapter_binding()
    harness_config = default_offline_harness_config()
    runtime_descriptor = default_offline_runtime_harness_impl_descriptor()

    adapter_result = validate_futures_testnet_adapter_binding(binding)
    harness_result = evaluate_bounded_futures_testnet_harness_readiness(harness_config, binding)
    runtime_result = validate_futures_testnet_runtime_harness_impl_descriptor(runtime_descriptor)

    fail_reasons: list[str] = []
    if not adapter_result["adapter_binding_pass"]:
        fail_reasons.extend(adapter_result["fail_reasons"])
    if not harness_result["harness_contract_pass"]:
        fail_reasons.extend(harness_result["fail_reasons"])
    if not runtime_result["runtime_harness_impl_pass"]:
        fail_reasons.extend(runtime_result["fail_reasons"])
    if PE11_PACKAGE_MARKER != "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_V0=true":
        fail_reasons.append("PE-11 package marker missing or unexpected")

    return {
        "pe_composition_pass": not fail_reasons,
        "pe8_adapter_pass": adapter_result["adapter_binding_pass"],
        "pe9_harness_pass": harness_result["harness_contract_pass"],
        "pe10_runtime_pass": runtime_result["runtime_harness_impl_pass"],
        "pe11_private_readonly_marker_present": PE11_PACKAGE_MARKER
        == "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_V0=true",
        "fail_reasons": fail_reasons,
    }


def evaluate_phase_transition(
    state: AdapterLifecycleState,
    request: PhaseTransitionRequest,
) -> dict[str, Any]:
    """Fail-closed lifecycle transition evaluator (offline, non-authorizing)."""
    result: dict[str, Any] = {
        "transition_allowed": False,
        "target_phase": request.target_phase,
        "lifecycle_execute_authorized_now": LIFECYCLE_EXECUTE_AUTHORIZED_NOW,
        "futures_session_authorized_now": FUTURES_SESSION_AUTHORIZED_NOW,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "ready_for_operator_arming": READY_FOR_OPERATOR_ARMING,
        "fail_reasons": [],
    }

    if LIFECYCLE_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("LIFECYCLE_EXECUTE_AUTHORIZED_NOW must be false")
    if LIFECYCLE_NETWORK_AUTHORIZED_NOW:
        result["fail_reasons"].append("LIFECYCLE_NETWORK_AUTHORIZED_NOW must be false")
    if LIFECYCLE_ORDERS_AUTHORIZED_NOW:
        result["fail_reasons"].append("LIFECYCLE_ORDERS_AUTHORIZED_NOW must be false")
    if HARNESS_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("HARNESS_EXECUTE_AUTHORIZED_NOW must be false")
    if RUNTIME_HARNESS_EXECUTE_ALLOWED:
        result["fail_reasons"].append("RUNTIME_HARNESS_EXECUTE_ALLOWED must be false")
    if ADAPTER_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("ADAPTER_NETWORK_CALLS_ALLOWED must be false")
    if FUTURES_SESSION_AUTHORIZED_NOW:
        result["fail_reasons"].append("FUTURES_SESSION_AUTHORIZED_NOW must be false")

    target = request.target_phase
    if target not in LIFECYCLE_PHASE_DESCRIPTORS:
        result["fail_reasons"].append(f"unknown lifecycle phase: {target!r}")
        return result

    result["fail_reasons"].extend(
        validate_lifecycle_instrument_binding(state.instrument, state.market_type)
    )

    prior = _prior_phase(target)
    if prior is not None and prior not in state.phases_completed:
        result["fail_reasons"].append(f"prior phase not completed: {prior!r}")

    recon_phase = _required_reconciliation_phase_for(target)
    if recon_phase is not None and recon_phase not in state.reconciliations_completed:
        result["fail_reasons"].append(
            f"reconciliation required for prior network/execution phase: {recon_phase!r}"
        )

    expected_go = LIFECYCLE_PHASE_DESCRIPTORS[target].operator_go_token
    if request.operator_go_token != expected_go:
        result["fail_reasons"].append(
            f"operator_go_token must be {expected_go!r} for phase {target!r}"
        )

    if target == PHASE_STATIC_PREFLIGHT:
        if not request.static_contract_self_check_pass:
            result["fail_reasons"].append("static_contract_self_check_pass required")
        composition = evaluate_pe_contract_composition()
        if not composition["pe_composition_pass"]:
            result["fail_reasons"].extend(composition["fail_reasons"])

    if target == PHASE_TINY_ORDER:
        if not request.risk_killswitch_binding_acknowledged:
            result["fail_reasons"].append("risk_killswitch_binding_acknowledged required")
        if not request.flatten_binding_acknowledged:
            result["fail_reasons"].append("flatten_binding_acknowledged required")
        if not request.durable_primary_evidence_capable:
            result["fail_reasons"].append("durable_primary_evidence_capable required")

    if target in {PHASE_RECONCILIATION_REVIEW, PHASE_READINESS_DECISION}:
        if not request.manifest_verify_rc_zero:
            result["fail_reasons"].append("manifest_verify_rc_zero required")

    if target == PHASE_READINESS_DECISION:
        result["fail_reasons"].append(
            "readiness_decision is non-authorizing and does not grant live/arming"
        )

    result["transition_allowed"] = not result["fail_reasons"]
    return result


def mark_phase_completed(state: AdapterLifecycleState, phase_id: str) -> AdapterLifecycleState:
    """Pure state helper for offline tests; does not authorize execute."""
    if phase_id not in LIFECYCLE_PHASE_DESCRIPTORS:
        raise ValueError(f"unknown phase: {phase_id!r}")
    phases = set(state.phases_completed)
    phases.add(phase_id)
    return AdapterLifecycleState(
        phases_completed=frozenset(phases),
        reconciliations_completed=state.reconciliations_completed,
        instrument=state.instrument,
        market_type=state.market_type,
    )


def mark_reconciliation_completed(
    state: AdapterLifecycleState,
    phase_id: str,
) -> AdapterLifecycleState:
    """Record reconciliation for a completed network/execution phase (offline helper)."""
    if phase_id not in NETWORK_EXECUTION_PHASES:
        raise ValueError(f"reconciliation only applies to network/execution phases: {phase_id!r}")
    if phase_id not in state.phases_completed:
        raise ValueError(f"phase must be completed before reconciliation: {phase_id!r}")
    reconciliations = set(state.reconciliations_completed)
    reconciliations.add(phase_id)
    return AdapterLifecycleState(
        phases_completed=state.phases_completed,
        reconciliations_completed=frozenset(reconciliations),
        instrument=state.instrument,
        market_type=state.market_type,
    )
