"""Offline flatten permit and orchestration contract for §11.13.5 LF-03.

Not runtime-reachable. Does not POST, invent a LIMIT price, or activate lifecycle.
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
    observe_target_position_flatten_candidate_v1,
)

FLATTEN_PERMIT_KIND = "FLATTEN_SUBMIT"
FLATTEN_SUBMIT_UNREACHABLE_REASON = (
    "FLATTEN_LIMIT_PRICE_POLICY_UNBOUND:" + FLATTEN_LIMIT_PRICE_GATE_STATUS
)


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
