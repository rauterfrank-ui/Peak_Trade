"""Build the exact venue-native flatten payload from an observed position.

Offline only. Reuses the already-bound observation, P11 side, P11 posSide
omission, P10/P11 sz identity, mapper, and serializer. Does not GET or POST.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_TD_MODE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    FlattenPricePermitV1,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    serialize_signed_post_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    evaluate_freshness_at_adjudication_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    assert_identity_sz_equals_abs_pos_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    assert_flatten_order_side_matches_signed_pos_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.constants_v1 import (
    CLORDID_SOURCE_CLASS_VALUE,
    OFFLINE_CONTRACT_PROOF_ASK,
    OFFLINE_CONTRACT_PROOF_BID,
    OFFLINE_CONTRACT_PROOF_EVAL_TS,
    OFFLINE_CONTRACT_PROOF_QUOTE_TS,
    OFFLINE_CONTRACT_PROOF_TICK_SZ,
    PX_SOURCE_CLASS_VALUE,
    STANDING_TD_MODE,
    TARGET_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.contract_v1 import (
    ExactFlattenPayloadError,
    assert_exact_flatten_payload_contract_v1,
)


@dataclass(frozen=True)
class ExactFlattenPayloadV1:
    """Typed exact flatten body. Not a send-time live instance."""

    body: dict[str, Any]
    canonical_json: str
    body_sha256: str
    instrument_id: str
    signed_pos: str
    flatten_side: str
    quantity: str
    clordid: str
    px: str
    freshness_status: str
    px_source_class: str
    clordid_source_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "body": dict(self.body),
            "canonical_json": self.canonical_json,
            "body_sha256": self.body_sha256,
            "instrument_id": self.instrument_id,
            "signed_pos": self.signed_pos,
            "flatten_side": self.flatten_side,
            "quantity": self.quantity,
            "clordid": self.clordid,
            "px": self.px,
            "freshness_status": self.freshness_status,
            "px_source_class": self.px_source_class,
            "clordid_source_class": self.clordid_source_class,
            "SEND_TIME_PX_MINTED": False,
            "LIVE_EXECUTION": False,
            "POST_PERFORMED": False,
        }


def offline_contract_proof_price_permit_v1(
    *,
    flatten_side: str,
    signed_pos: str,
) -> FlattenPricePermitV1:
    """Issue a labeled offline proof permit. Not a send-time quote."""
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        FlattenPriceInputV1(
            flatten_side=flatten_side,
            observed_signed_pos=signed_pos,
            bid=OFFLINE_CONTRACT_PROOF_BID,
            ask=OFFLINE_CONTRACT_PROOF_ASK,
            quote_timestamp_ms=OFFLINE_CONTRACT_PROOF_QUOTE_TS,
            evaluation_timestamp_ms=OFFLINE_CONTRACT_PROOF_EVAL_TS,
            tick_sz=OFFLINE_CONTRACT_PROOF_TICK_SZ,
            freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
        )
    )
    if decision.permit is None or not decision.permit_issued:
        reasons = ",".join(decision.reject_reasons) if decision.reject_reasons else "UNKNOWN"
        raise ExactFlattenPayloadError(f"OFFLINE_PROOF_PERMIT_NOT_ISSUED:{reasons}")
    return decision.permit


def build_exact_flatten_payload_from_observed_position_v1(
    *,
    positions_payload: Mapping[str, Any],
    price_permit: FlattenPricePermitV1,
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    td_mode: str = DEFAULT_TD_MODE,
    response_received_monotonic_ms: int | None = None,
    adjudication_monotonic_ms: int | None = None,
) -> ExactFlattenPayloadV1:
    """Map a unique observed position to the exact venue-native flatten body.

    Requires a bound FlattenPricePermitV1. Does not invent px from the
    position row. Does not GET or POST.
    """
    target = str(instrument_id or "").strip() or TARGET_INSTRUMENT_ID
    if str(td_mode or "").strip() != STANDING_TD_MODE:
        raise ExactFlattenPayloadError(f"INCORRECT_TD_MODE:{td_mode or 'MISSING'}")
    freshness = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=response_received_monotonic_ms,
        adjudication_monotonic_ms=adjudication_monotonic_ms,
    )
    freshness_status = str(freshness.get("FRESHNESS_STATUS") or "NOT_EVALUABLE")
    if freshness_status == "FAIL":
        reason = str(freshness.get("FRESHNESS_REJECT_REASON") or "STALE_POSITION_OBSERVATION")
        raise ExactFlattenPayloadError(f"STALE_OR_INVALID_POSITION_FRESHNESS:{reason}")
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=positions_payload,
            instrument_id=target,
        )
    except LiveCanaryPositionObservationError as exc:
        raise ExactFlattenPayloadError(f"FLATTEN_OBSERVATION:{exc}") from exc
    if observed.instrument_id != target:
        raise ExactFlattenPayloadError("INSTRUMENT_BINDING_MISMATCH")
    assert_identity_sz_equals_abs_pos_v1(
        signed_pos=observed.signed_pos,
        sz=observed.candidate_flatten_qty,
    )
    assert_flatten_order_side_matches_signed_pos_v1(
        side=observed.candidate_flatten_side,
        signed_pos=observed.signed_pos,
    )
    permit_side = str(price_permit.flatten_side).strip().upper()
    if permit_side != observed.candidate_flatten_side:
        raise ExactFlattenPayloadError("PRICE_PERMIT_SIDE_MISMATCH")
    try:
        plan = build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=positions_payload,
            owner_go=owner_go,
            origin_main_sha=origin_main_sha,
            instrument_id=target,
            td_mode=td_mode,
        )
        body = serialize_canary_flatten_venue_native_payload_v1(
            plan,
            price_permit=price_permit,
        )
    except LiveCanaryOrderPlanError as exc:
        raise ExactFlattenPayloadError(f"FLATTEN_PAYLOAD_BUILD:{exc}") from exc
    if Decimal(plan.quantity) != observed.candidate_flatten_qty:
        raise ExactFlattenPayloadError("PLAN_QTY_NOT_ABS_SIGNED_POS")
    if plan.side != observed.candidate_flatten_side:
        raise ExactFlattenPayloadError("PLAN_SIDE_NOT_DERIVED_SIDE")
    permit_px = str(price_permit.limit_price).strip()
    assert_exact_flatten_payload_contract_v1(
        body,
        instrument_id=observed.instrument_id,
        side=plan.side,
        quantity=plan.quantity,
        td_mode=plan.td_mode,
        px=permit_px,
        clordid=plan.clordid,
    )
    canonical_json = serialize_signed_post_body_v1(body)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return ExactFlattenPayloadV1(
        body=dict(body),
        canonical_json=canonical_json,
        body_sha256=digest,
        instrument_id=observed.instrument_id,
        signed_pos=format(observed.signed_pos, "f"),
        flatten_side=observed.candidate_flatten_side,
        quantity=plan.quantity,
        clordid=plan.clordid,
        px=permit_px,
        freshness_status=freshness_status,
        px_source_class=PX_SOURCE_CLASS_VALUE,
        clordid_source_class=CLORDID_SOURCE_CLASS_VALUE,
    )
