"""Offline flatten permit and orchestration contract for §11.13.5 LF-03/LF-04.

Not runtime-reachable. Does not POST, invent a LIMIT price, or activate lifecycle.
LF-04 evaluates offline failure/race classes against this same contract.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    ALLOWED_LIFECYCLE_STATES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
    CanaryFlattenOrderPlanV1,
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    serialize_canary_clordid_v1,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    classify_unknown_submit_from_exchange_v1,
    observe_target_position_flatten_candidate_v1,
)

FLATTEN_PERMIT_KIND = "FLATTEN_SUBMIT"
FLATTEN_SUBMIT_UNREACHABLE_REASON = (
    "FLATTEN_LIMIT_PRICE_POLICY_UNBOUND:" + FLATTEN_LIMIT_PRICE_GATE_STATUS
)
LIFECYCLE_FLATTEN_RUNTIME_REACHABLE = False
LIVE_FLATTEN_PROVABILITY_STATUS = "UNPROVEN"
NETWORK_EFFECT_NONE = "none"
ORDER_EFFECT_NONE = "none"
ACCOUNT_MUTATION_EFFECT_NONE = "none"
LF04_FAILURE_CLASSES: tuple[str, ...] = (
    "PARTIAL_ENTRY_FILL",
    "CANCEL_RACE",
    "CANCEL_TIMEOUT",
    "STALE_POSITION_OBSERVATION",
    "FLATTEN_REJECT",
    "FLATTEN_TIMEOUT",
    "PARTIAL_FLATTEN",
    "DUPLICATE_ORCHESTRATION",
    "RESTART_RECONSTRUCTED_STATE",
    "UNKNOWN_SUBMIT",
)
_CANCEL_BLOCKING_STATUSES = frozenset({"PENDING", "TIMEOUT", "RACE"})
_ENTRY_UNKNOWN_OUTCOMES = frozenset({"UNKNOWN", "UNKNOWN_SUBMIT"})
_FLATTEN_NO_RETRY_OUTCOMES = frozenset({"REJECTED", "TIMEOUT", "UNKNOWN", "PARTIAL"})


class LiveCanaryFlattenOrchestrationError(RuntimeError):
    """Fail-closed offline flatten permit/orchestration violation."""


@dataclass(frozen=True)
class CanaryFlattenSubmitPermitV1:
    """Typed flatten permit. Does not authorize Entry POST or flatten transport."""

    owner_go: str
    clordid: str
    permit_id: str
    instrument_id: str
    side: str
    quantity: str
    reduce_only: bool
    price_gate_status: str
    submitted_entry_sz_used: bool
    submit_reachable: bool = False
    kind: str = FLATTEN_PERMIT_KIND

    def __post_init__(self) -> None:
        if self.kind != FLATTEN_PERMIT_KIND:
            raise LiveCanaryFlattenOrchestrationError("FLATTEN_PERMIT_KIND_INVALID")
        if self.submit_reachable is not False:
            raise LiveCanaryFlattenOrchestrationError("FLATTEN_SUBMIT_REACHABLE_FORBIDDEN")
        if self.reduce_only is not True:
            raise LiveCanaryFlattenOrchestrationError("FLATTEN_PERMIT_REDUCE_ONLY_REQUIRED")
        if self.price_gate_status != FLATTEN_LIMIT_PRICE_GATE_STATUS:
            raise LiveCanaryFlattenOrchestrationError("FLATTEN_PRICE_GATE_STATUS_INVALID")
        if self.submitted_entry_sz_used is not False:
            raise LiveCanaryFlattenOrchestrationError("SUBMITTED_ENTRY_SZ_CANNOT_AUTHORIZE_FLATTEN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go": self.owner_go,
            "clordid": self.clordid,
            "permit_id": self.permit_id,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": self.quantity,
            "reduce_only": self.reduce_only,
            "price_gate_status": self.price_gate_status,
            "submitted_entry_sz_used": self.submitted_entry_sz_used,
            "submit_reachable": self.submit_reachable,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class CanaryFlattenOrchestrationVerdictV1:
    """Offline orchestration result. Never a transport or execute authorization."""

    entry_lifecycle_context: str
    observation_status: str
    flatten_plan_derivable: bool
    permit_issued: bool
    permit: CanaryFlattenSubmitPermitV1 | None
    flatten_plan: CanaryFlattenOrderPlanV1 | None
    submit_reachable: bool
    serialization_reachable: bool
    transport_invoked: bool
    market_fallback_used: bool
    submitted_entry_qty_used_as_authority: bool
    blocking_reasons: tuple[str, ...]
    contract_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_lifecycle_context": self.entry_lifecycle_context,
            "observation_status": self.observation_status,
            "flatten_plan_derivable": self.flatten_plan_derivable,
            "permit_issued": self.permit_issued,
            "permit": None if self.permit is None else self.permit.to_dict(),
            "flatten_plan": None if self.flatten_plan is None else self.flatten_plan.to_dict(),
            "submit_reachable": self.submit_reachable,
            "serialization_reachable": self.serialization_reachable,
            "transport_invoked": self.transport_invoked,
            "market_fallback_used": self.market_fallback_used,
            "submitted_entry_qty_used_as_authority": self.submitted_entry_qty_used_as_authority,
            "blocking_reasons": list(self.blocking_reasons),
            "contract_state": self.contract_state,
        }


def _flatten_permit_id(*, owner_go: str, clordid: str) -> str:
    material = f"FLATTEN_PERMIT:{owner_go}:{clordid}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:32]


def _blocked_verdict(
    *,
    entry_lifecycle_context: str,
    observation_status: str,
    blocking_reasons: tuple[str, ...],
    contract_state: str,
) -> CanaryFlattenOrchestrationVerdictV1:
    return CanaryFlattenOrchestrationVerdictV1(
        entry_lifecycle_context=entry_lifecycle_context,
        observation_status=observation_status,
        flatten_plan_derivable=False,
        permit_issued=False,
        permit=None,
        flatten_plan=None,
        submit_reachable=False,
        serialization_reachable=False,
        transport_invoked=False,
        market_fallback_used=False,
        submitted_entry_qty_used_as_authority=False,
        blocking_reasons=blocking_reasons,
        contract_state=contract_state,
    )


def _assert_plan_is_offline_flatten(plan: CanaryFlattenOrderPlanV1) -> None:
    if plan.reduce_only is not True:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_PLAN_REDUCE_ONLY_REQUIRED")
    if str(plan.order_type).upper() != "LIMIT":
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_MARKET_FALLBACK_FORBIDDEN")
    if str(DEFAULT_ORDER_TYPE).upper() != "LIMIT":
        raise LiveCanaryFlattenOrchestrationError("ENTRY_ORDER_TYPE_NOT_LIMIT")
    if plan.limit_price is not None or plan.venue_native_payload is not None:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_LIMIT_PRICE_POLICY_BOUND_FORBIDDEN")
    if plan.price_gate_status != FLATTEN_LIMIT_PRICE_GATE_STATUS:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_PRICE_GATE_STATUS_INVALID")
    if plan.submitted_entry_sz_used is not False:
        raise LiveCanaryFlattenOrchestrationError("SUBMITTED_ENTRY_SZ_CANNOT_AUTHORIZE_FLATTEN")


def issue_canary_flatten_submit_permit_v1(
    *,
    positions_payload: Mapping[str, Any],
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    submitted_entry_sz: str | None = None,
    entry_clordid: str | None = None,
) -> CanaryFlattenSubmitPermitV1:
    """Issue an inert flatten permit from observed position. Submit remains unreachable."""
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryFlattenOrchestrationError(f"INSTRUMENT_BINDING:{exc}") from exc
    try:
        plan = build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=positions_payload,
            owner_go=owner_go,
            origin_main_sha=origin_main_sha,
            instrument_id=instrument_id,
            submitted_entry_sz=submitted_entry_sz,
        )
    except LiveCanaryOrderPlanError as exc:
        raise LiveCanaryFlattenOrchestrationError(f"FLATTEN_PERMIT_BLOCKED:{exc}") from exc
    _assert_plan_is_offline_flatten(plan)
    if entry_clordid is not None and plan.clordid == entry_clordid:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_CLORDID_ALIASES_ENTRY")
    return CanaryFlattenSubmitPermitV1(
        owner_go=owner_go,
        clordid=plan.clordid,
        permit_id=_flatten_permit_id(owner_go=owner_go, clordid=plan.clordid),
        instrument_id=plan.instrument_id,
        side=plan.side,
        quantity=plan.quantity,
        reduce_only=True,
        price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
        submitted_entry_sz_used=False,
        submit_reachable=False,
        kind=FLATTEN_PERMIT_KIND,
    )


def refuse_canary_flatten_submit_transport_v1(
    permit: CanaryFlattenSubmitPermitV1,
    *,
    px: str | None = None,
) -> None:
    """Refuse flatten POST/serialization. Never calls a transport."""
    del px
    if permit.kind != FLATTEN_PERMIT_KIND:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_PERMIT_KIND_INVALID")
    if permit.submit_reachable is not False:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_SUBMIT_REACHABLE_FORBIDDEN")
    raise LiveCanaryFlattenOrchestrationError(FLATTEN_SUBMIT_UNREACHABLE_REASON)


def evaluate_canary_flatten_orchestration_contract_v1(
    *,
    positions_payload: Mapping[str, Any],
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    submitted_entry_sz: str | None = None,
    entry_lifecycle_context: str = "ENTRY_LIFECYCLE_CONTEXT",
) -> CanaryFlattenOrchestrationVerdictV1:
    """ENTRY context → observe → optional permit. Submit/serialization stay unreachable."""
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    except LiveCanaryInstrumentBindingError as exc:
        return _blocked_verdict(
            entry_lifecycle_context=entry_lifecycle_context,
            observation_status="INSTRUMENT_BINDING_FAILED",
            blocking_reasons=(f"INSTRUMENT_BINDING:{exc}",),
            contract_state="FLATTEN_FAIL_CLOSED",
        )
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=positions_payload,
            instrument_id=instrument_id,
        )
    except LiveCanaryPositionObservationError as exc:
        code = str(exc)
        if "ZERO_POSITION_NO_FLATTEN_ORDER" in code:
            status = "ZERO_POSITION"
            state = "NO_FLATTEN_ZERO_POSITION"
        elif "TARGET_INSTRUMENT_NOT_OBSERVED" in code:
            status = "TARGET_INSTRUMENT_NOT_OBSERVED"
            state = "FLATTEN_FAIL_CLOSED"
        elif "AMBIGUOUS_TARGET_POSITION_ROWS" in code:
            status = "AMBIGUOUS_TARGET_POSITION_ROWS"
            state = "FLATTEN_FAIL_CLOSED"
        elif "POSITION_SIZE_" in code:
            status = "MALFORMED_POSITION"
            state = "FLATTEN_FAIL_CLOSED"
        else:
            status = "OBSERVATION_FAIL_CLOSED"
            state = "FLATTEN_FAIL_CLOSED"
        return _blocked_verdict(
            entry_lifecycle_context=entry_lifecycle_context,
            observation_status=status,
            blocking_reasons=(code,),
            contract_state=state,
        )
    try:
        plan = build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=positions_payload,
            owner_go=owner_go,
            origin_main_sha=origin_main_sha,
            instrument_id=instrument_id,
            submitted_entry_sz=submitted_entry_sz,
        )
    except LiveCanaryOrderPlanError as exc:
        return _blocked_verdict(
            entry_lifecycle_context=entry_lifecycle_context,
            observation_status="OBSERVED_NONZERO",
            blocking_reasons=(f"FLATTEN_PLAN:{exc}",),
            contract_state="FLATTEN_FAIL_CLOSED",
        )
    _assert_plan_is_offline_flatten(plan)
    if observed.candidate_flatten_qty != abs(observed.signed_pos):
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_QTY_NOT_ABS_OBSERVED_POS")
    if Decimal(plan.quantity) != observed.candidate_flatten_qty:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_QTY_NOT_ABS_OBSERVED_POS")
    if plan.side != observed.candidate_flatten_side:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_SIDE_NOT_FROM_OBSERVED_SIGN")
    entry_clordid = serialize_canary_clordid_v1(owner_go=owner_go, origin_main_sha=origin_main_sha)
    if plan.clordid == entry_clordid:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_CLORDID_ALIASES_ENTRY")
    permit = CanaryFlattenSubmitPermitV1(
        owner_go=owner_go,
        clordid=plan.clordid,
        permit_id=_flatten_permit_id(owner_go=owner_go, clordid=plan.clordid),
        instrument_id=plan.instrument_id,
        side=plan.side,
        quantity=plan.quantity,
        reduce_only=True,
        price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
        submitted_entry_sz_used=False,
        submit_reachable=False,
        kind=FLATTEN_PERMIT_KIND,
    )
    serialization_blocked = False
    try:
        serialize_canary_flatten_venue_native_payload_v1(plan, px=None)
    except LiveCanaryOrderPlanError:
        serialization_blocked = True
    if not serialization_blocked:
        raise LiveCanaryFlattenOrchestrationError("FLATTEN_SERIALIZATION_UNEXPECTEDLY_REACHABLE")
    return CanaryFlattenOrchestrationVerdictV1(
        entry_lifecycle_context=entry_lifecycle_context,
        observation_status="OBSERVED_NONZERO",
        flatten_plan_derivable=True,
        permit_issued=True,
        permit=permit,
        flatten_plan=plan,
        submit_reachable=False,
        serialization_reachable=False,
        transport_invoked=False,
        market_fallback_used=False,
        submitted_entry_qty_used_as_authority=False,
        blocking_reasons=(FLATTEN_SUBMIT_UNREACHABLE_REASON,),
        contract_state="FLATTEN_PERMIT_ISSUED_SUBMIT_BLOCKED_PRICE_POLICY",
    )


@dataclass(frozen=True)
class CanaryFlattenLifecycleObservationV1:
    """One offline observation. Never a live GET or submit."""

    positions_payload: Mapping[str, Any]
    pending_orders_payload: Mapping[str, Any] | None = None
    history_payload: Mapping[str, Any] | None = None
    observation_fresh: bool = True
    entry_submit_outcome: str | None = None
    flatten_submit_outcome: str | None = None
    cancel_status: str | None = None
    reconstructed: bool = False
    claimed_flat: bool = False
    entry_clordid: str | None = None


@dataclass(frozen=True)
class CanaryFlattenLifecycleFailureMatrixVerdictV1:
    """Offline LF-04 matrix result. Never a transport or execute authorization."""

    case: str
    initial_state: str
    permit_issued: bool
    permit: CanaryFlattenSubmitPermitV1 | None
    expected_action: str
    terminal_or_intermediate_state: str
    reason: str
    fail_closed: bool
    submit_reachable: bool
    flatten_action_authorized: bool
    second_effect_authorized: bool
    position_flip_authorized: bool
    implicit_runtime_authorization: bool
    claimed_flat: bool
    network_effect: str
    order_effect: str
    account_mutation_effect: str
    live_flatten_provability: str
    lifecycle_flatten_runtime_reachable: bool
    blocking_reasons: tuple[str, ...]
    orchestration_verdict: CanaryFlattenOrchestrationVerdictV1 | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case,
            "initial_state": self.initial_state,
            "permit_issued": self.permit_issued,
            "permit": None if self.permit is None else self.permit.to_dict(),
            "expected_action": self.expected_action,
            "terminal_or_intermediate_state": self.terminal_or_intermediate_state,
            "reason": self.reason,
            "fail_closed": self.fail_closed,
            "submit_reachable": self.submit_reachable,
            "flatten_action_authorized": self.flatten_action_authorized,
            "second_effect_authorized": self.second_effect_authorized,
            "position_flip_authorized": self.position_flip_authorized,
            "implicit_runtime_authorization": self.implicit_runtime_authorization,
            "claimed_flat": self.claimed_flat,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "account_mutation_effect": self.account_mutation_effect,
            "live_flatten_provability": self.live_flatten_provability,
            "lifecycle_flatten_runtime_reachable": self.lifecycle_flatten_runtime_reachable,
            "blocking_reasons": list(self.blocking_reasons),
            "orchestration_verdict": (
                None if self.orchestration_verdict is None else self.orchestration_verdict.to_dict()
            ),
        }


def _matrix_blocked_verdict(
    *,
    case: str,
    initial_state: str,
    reason: str,
    terminal_or_intermediate_state: str,
    blocking_reasons: tuple[str, ...] | None = None,
    claimed_flat: bool = False,
) -> CanaryFlattenLifecycleFailureMatrixVerdictV1:
    return CanaryFlattenLifecycleFailureMatrixVerdictV1(
        case=case,
        initial_state=initial_state,
        permit_issued=False,
        permit=None,
        expected_action="NONE",
        terminal_or_intermediate_state=terminal_or_intermediate_state,
        reason=reason,
        fail_closed=True,
        submit_reachable=False,
        flatten_action_authorized=False,
        second_effect_authorized=False,
        position_flip_authorized=False,
        implicit_runtime_authorization=False,
        claimed_flat=claimed_flat,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        lifecycle_flatten_runtime_reachable=LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
        blocking_reasons=blocking_reasons if blocking_reasons is not None else (reason,),
        orchestration_verdict=None,
    )


def _try_signed_observed_pos(
    observation: CanaryFlattenLifecycleObservationV1,
    *,
    instrument_id: str,
) -> Decimal | None:
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=observation.positions_payload,
            instrument_id=instrument_id,
        )
    except LiveCanaryPositionObservationError as exc:
        if "ZERO_POSITION_NO_FLATTEN_ORDER" in str(exc):
            return Decimal("0")
        return None
    return observed.signed_pos


def _pending_payload_unusable(payload: Mapping[str, Any] | None) -> bool:
    if payload is None:
        return False
    if str(payload.get("code") or "") != "0":
        return True
    return not isinstance(payload.get("data"), list)


def _target_open_order_present(
    payload: Mapping[str, Any] | None,
    *,
    instrument_id: str,
) -> bool:
    if payload is None:
        return False
    data = payload.get("data")
    if not isinstance(data, list):
        return False
    return any(
        isinstance(row, Mapping)
        and str(row.get("instId") or row.get("instID") or "") == instrument_id
        for row in data
    )


def evaluate_canary_flatten_lifecycle_failure_matrix_v1(
    *,
    case: str,
    initial_state: str,
    observation_sequence: tuple[CanaryFlattenLifecycleObservationV1, ...],
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    submitted_entry_sz: str | None = None,
    prior_flatten_orchestration_attempts: int = 0,
    reconstructed_permit: CanaryFlattenSubmitPermitV1 | None = None,
) -> CanaryFlattenLifecycleFailureMatrixVerdictV1:
    """Evaluate offline lifecycle failure classes against the LF-03 contract.

    Flatten ACTION remains unauthorized. Reconstruction does not issue a permit.
    Unknown or timed-out submits do not retry. Submit stays unreachable.
    """
    del reconstructed_permit
    if not observation_sequence:
        raise LiveCanaryFlattenOrchestrationError("OBSERVATION_SEQUENCE_REQUIRED")
    if initial_state not in ALLOWED_LIFECYCLE_STATES:
        raise LiveCanaryFlattenOrchestrationError(f"UNGATED_LIFECYCLE_STATE:{initial_state}")
    last = observation_sequence[-1]

    def _blocked(
        reason: str,
        state: str,
        extra: tuple[str, ...] = (),
    ) -> CanaryFlattenLifecycleFailureMatrixVerdictV1:
        reasons = (reason,) + extra
        return _matrix_blocked_verdict(
            case=case,
            initial_state=initial_state,
            reason=reason,
            terminal_or_intermediate_state=state,
            blocking_reasons=reasons,
            claimed_flat=last.claimed_flat,
        )

    if last.reconstructed:
        return _blocked(
            "RESTART_RECONSTRUCTION_DOES_NOT_ISSUE_PERMIT",
            initial_state,
        )
    if prior_flatten_orchestration_attempts >= 1:
        return _blocked(
            "DUPLICATE_FLATTEN_ORCHESTRATION_FORBIDDEN",
            "FLATTEN_PENDING",
        )
    if last.entry_submit_outcome in _ENTRY_UNKNOWN_OUTCOMES or initial_state == "UNKNOWN_SUBMIT":
        extra: tuple[str, ...] = ()
        if last.pending_orders_payload is not None:
            clordid = last.entry_clordid or serialize_canary_clordid_v1(
                owner_go=owner_go,
                origin_main_sha=origin_main_sha,
            )
            extra = (
                classify_unknown_submit_from_exchange_v1(
                    pending_orders_payload=last.pending_orders_payload,
                    history_payload=last.history_payload,
                    clordid=clordid,
                ),
            )
        return _blocked(
            "UNKNOWN_SUBMIT_NO_AUTOMATIC_RETRY_NO_FLATTEN",
            "UNKNOWN_SUBMIT",
            extra,
        )
    if last.cancel_status in _CANCEL_BLOCKING_STATUSES or (
        initial_state == "CANCEL_PENDING" and last.cancel_status != "CANCELED"
    ):
        reason_by_status = {
            "RACE": "CANCEL_RACE_ELIGIBILITY_UNPROVEN_NO_FLATTEN",
            "TIMEOUT": "CANCEL_TIMEOUT_ELIGIBILITY_UNPROVEN_NO_FLATTEN",
            "PENDING": "CANCEL_PENDING_ELIGIBILITY_UNPROVEN_NO_FLATTEN",
        }
        status_key = last.cancel_status or "PENDING"
        return _blocked(
            reason_by_status.get(status_key, "CANCEL_ELIGIBILITY_UNPROVEN_NO_FLATTEN"),
            "CANCEL_PENDING",
        )
    if _pending_payload_unusable(last.pending_orders_payload):
        return _blocked("PENDING_ORDERS_OBSERVATION_FAIL_CLOSED", "HALTED")
    if _target_open_order_present(last.pending_orders_payload, instrument_id=instrument_id):
        state = "PARTIAL_FILL" if initial_state == "PARTIAL_FILL" else "CANCEL_PENDING"
        return _blocked("OPEN_ORDER_REMAINDER_CANCEL_ELIGIBILITY_UNPROVEN", state)
    if initial_state == "PARTIAL_FILL" and last.pending_orders_payload is None:
        return _blocked("PARTIAL_ENTRY_FILL_CANCEL_ELIGIBILITY_UNPROVEN", "PARTIAL_FILL")
    if any(not item.observation_fresh for item in observation_sequence):
        return _blocked("STALE_POSITION_OBSERVATION", "HALTED")
    signs: set[int] = set()
    for item in observation_sequence:
        signed = _try_signed_observed_pos(item, instrument_id=instrument_id)
        if signed is None or signed == 0:
            continue
        signs.add(1 if signed > 0 else -1)
    if 1 in signs and -1 in signs:
        return _blocked("CONTRADICTORY_POSITION_SIGN_FLIP_FAIL_CLOSED", "HALTED")
    if last.flatten_submit_outcome in _FLATTEN_NO_RETRY_OUTCOMES or last.claimed_flat:
        signed = _try_signed_observed_pos(last, instrument_id=instrument_id)
        if last.flatten_submit_outcome == "REJECTED":
            return _blocked("FLATTEN_REJECT_NO_RETRY_TRANSPORT_UNPROVEN", "HALTED")
        if last.flatten_submit_outcome == "TIMEOUT":
            return _blocked("FLATTEN_TIMEOUT_NO_RETRY_DUPLICATE_RISK", "HALTED")
        if last.flatten_submit_outcome == "UNKNOWN":
            return _blocked("FLATTEN_SUBMIT_UNKNOWN_NO_RETRY_DUPLICATE_RISK", "HALTED")
        if signed is None:
            return _blocked("PARTIAL_FLATTEN_OBSERVATION_UNPROVEN", "HALTED")
        if signed != 0:
            return _blocked(
                "PARTIAL_FLATTEN_REMAINING_POSITION_NOT_FLAT",
                "FLATTEN_PENDING",
            )
        return _blocked("FLAT_UNPROVEN_UNGATED_LIFECYCLE", "HALTED")

    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=last.positions_payload,
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        submitted_entry_sz=submitted_entry_sz,
        entry_lifecycle_context=initial_state,
    )
    reason = orch.blocking_reasons[0] if orch.blocking_reasons else "FLATTEN_FAIL_CLOSED"
    action = "ISSUE_INERT_PERMIT_SUBMIT_BLOCKED" if orch.permit_issued else "NONE"
    return CanaryFlattenLifecycleFailureMatrixVerdictV1(
        case=case,
        initial_state=initial_state,
        permit_issued=orch.permit_issued,
        permit=orch.permit,
        expected_action=action,
        terminal_or_intermediate_state=orch.contract_state,
        reason=reason,
        fail_closed=True,
        submit_reachable=False,
        flatten_action_authorized=False,
        second_effect_authorized=False,
        position_flip_authorized=False,
        implicit_runtime_authorization=False,
        claimed_flat=last.claimed_flat,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        lifecycle_flatten_runtime_reachable=LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
        blocking_reasons=orch.blocking_reasons,
        orchestration_verdict=orch,
    )
