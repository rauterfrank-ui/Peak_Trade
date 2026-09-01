"""Fail-closed pre-send gate object for productive flatten.

Every material predicate is independently recorded. A generic
allow_productive_wire_send flag is never sufficient. This evaluator
never GETs, never POSTs, and never claims LIVE_FLATTEN_PROVABILITY.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from src.ops.pre_submit_open_position_cap_v1 import (
    PreSubmitOpenPositionCapErrorV1,
    assert_pre_submit_open_position_cap_allows_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    FlattenPricePermitV1,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    CanaryFlattenOrderPlanV1,
    CanaryFlattenSubmitPermitV1,
    evaluate_canary_flatten_orchestration_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LiveCanaryFlattenSubmitTransportError,
    build_canary_flatten_submit_request_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PositionObservationFreshnessEvidenceV1,
    evaluate_position_observation_freshness_v1,
    resolve_monotonic_ms_clock_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    LiveCanaryPreSubmitStateError,
    TARGET_POSITION_NONZERO_PROVEN,
    classify_target_position_state_v1,
    observe_target_position_flatten_candidate_v1,
    open_order_instruments_v1,
)

GATE_NAMES: tuple[str, ...] = (
    "STANDING_LIVE_FLAGS",
    "LIVE_AUTHORIZED_CLAIM",
    "LIVE_ENABLED_CLAIM",
    "LIVE_ARMED_CLAIM",
    "FLATTEN_LIVE_WIRE_CLAIM",
    "ALLOW_PRODUCTIVE_WIRE_SEND",
    "FLATTEN_EXECUTE_AUTHORITY",
    "FLATTEN_EXECUTE_BOUND_SHA",
    "INSTRUMENT_BINDING",
    "TARGET_POSITION_STATE",
    "PRODUCTIVE_POSITION_OBSERVED",
    "PRE_POS_NONZERO",
    "SINGLE_SELECTED_INSTRUMENT",
    "OPEN_ORDER_CONFLICT",
    "B8_CAP",
    "CLOSE_SIDE",
    "FLATTEN_QTY",
    "REDUCE_ONLY",
    "LIMIT_ONLY",
    "QUOTE_FRESHNESS_5000MS",
    "POSITION_OBSERVATION_FRESHNESS",
    "LIMIT_PRICE_POLICY",
    "OVERSHOOT_FLIP",
    "ONE_SHOT_NO_RETRY",
    "DUPLICATE_POST_PROTECTION",
)


APPROVED_FLATTEN_METHOD = "POST"


def serialize_approved_flatten_body_text_v1(body: Mapping[str, Any] | None) -> str:
    """Exact JSON text the gated submit boundary will put on the wire."""
    if not isinstance(body, dict) or not body:
        return ""
    return json.dumps(body, separators=(",", ":"), ensure_ascii=True)


def flatten_approved_request_identity_v1(
    *,
    method: str,
    url: str,
    body_text: str,
) -> str:
    """SHA-256 of method, URL, and exact body text. Reuses wire-hash convention."""
    material = f"{str(method or '').strip().upper()}\n{str(url or '').strip()}\n{body_text or ''}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def canonical_flatten_approved_url_v1() -> str:
    return f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}"


@dataclass
class FlattenReceiptSendLeaseV1:
    """Mutable one-shot lease bound to one gate evaluation. Not a global singleton."""

    consumed: bool = False


@dataclass(frozen=True)
class FlattenPreSendGateInputV1:
    """Caller-supplied runtime claims and snapshots. No network fetch."""

    live_authorized: bool
    live_enabled: bool
    live_armed: bool
    flatten_live_wire_enabled: bool
    allow_productive_wire_send: bool
    flatten_execute_token: str | None
    flatten_execute_purpose: str | None
    flatten_execute_owner_go: str | None
    positions_payload: Mapping[str, Any]
    pending_orders_payload: Mapping[str, Any] | None
    price_input: FlattenPriceInputV1
    owner_go: str
    origin_main_sha: str
    flatten_execute_bound_origin_main_sha: str | None = None
    instrument_id: str = DEFAULT_INSTRUMENT_ID
    one_shot_no_retry: bool = True
    duplicate_post_protection: bool = True
    flatten_pre_send_decision_id: str | None = None
    position_observation_freshness_evidence: PositionObservationFreshnessEvidenceV1 | None = None
    monotonic_ms_clock: Callable[[], int] | None = None


@dataclass(frozen=True)
class FlattenPreSendGateReceiptV1:
    """Auditable pre-send decision. allowed=True is not venue proof."""

    allowed: bool
    reasons: tuple[str, ...]
    audit_decisions: tuple[tuple[str, str], ...]
    observed_signed_pos: str | None
    close_side: str | None
    qty: str | None
    reduce_only: bool
    ord_type: str | None
    limit_px: str | None
    td_mode: str | None
    request_body: dict[str, Any] | None
    permit: CanaryFlattenSubmitPermitV1 | None
    plan: CanaryFlattenOrderPlanV1 | None
    price_permit: FlattenPricePermitV1 | None
    gate_digest: str
    live_flatten_provability: str
    productive_venue_proof: bool
    approved_method: str = APPROVED_FLATTEN_METHOD
    approved_host: str = REUSED_BINDING_REST_HOST
    approved_endpoint: str = ENDPOINT_SUBMIT
    approved_url: str = ""
    approved_body_text: str = ""
    approved_request_identity: str = ""
    send_lease: FlattenReceiptSendLeaseV1 = field(default_factory=FlattenReceiptSendLeaseV1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "audit_decisions": [list(item) for item in self.audit_decisions],
            "observed_signed_pos": self.observed_signed_pos,
            "close_side": self.close_side,
            "qty": self.qty,
            "reduce_only": self.reduce_only,
            "ord_type": self.ord_type,
            "limit_px": self.limit_px,
            "td_mode": self.td_mode,
            "request_body": self.request_body,
            "gate_digest": self.gate_digest,
            "live_flatten_provability": self.live_flatten_provability,
            "productive_venue_proof": self.productive_venue_proof,
            "approved_request_identity": self.approved_request_identity,
            "approved_url": self.approved_url,
        }


def _decision(name: str, ok: bool, reason: str = "") -> tuple[str, str]:
    if ok:
        return (name, "PASS")
    return (name, f"DENY:{reason}")


def evaluate_flatten_pre_send_gate_v1(
    gate: FlattenPreSendGateInputV1,
) -> FlattenPreSendGateReceiptV1:
    """Evaluate the full productive flatten pre-send object. Never transmits."""
    decisions: list[tuple[str, str]] = []
    reasons: list[str] = []

    standing_ok = not (LIVE_AUTHORIZED or LIVE_ENABLED or LIVE_ARMED)
    standing_ok = standing_ok and (DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False)
    if not standing_ok:
        reasons.append("STANDING_LIVE_FLAGS_MUST_REMAIN_FALSE")
    decisions.append(_decision("STANDING_LIVE_FLAGS", standing_ok, "STANDING_LIVE_FLAGS_UNLOCKED"))

    if gate.live_authorized is not True:
        reasons.append("LIVE_AUTHORIZED_CLAIM_FALSE")
        decisions.append(_decision("LIVE_AUTHORIZED_CLAIM", False, "LIVE_AUTHORIZED_CLAIM_FALSE"))
    else:
        decisions.append(_decision("LIVE_AUTHORIZED_CLAIM", True))

    if gate.live_enabled is not True:
        reasons.append("LIVE_ENABLED_CLAIM_FALSE")
        decisions.append(_decision("LIVE_ENABLED_CLAIM", False, "LIVE_ENABLED_CLAIM_FALSE"))
    else:
        decisions.append(_decision("LIVE_ENABLED_CLAIM", True))

    if gate.live_armed is not True:
        reasons.append("LIVE_ARMED_CLAIM_FALSE")
        decisions.append(_decision("LIVE_ARMED_CLAIM", False, "LIVE_ARMED_CLAIM_FALSE"))
    else:
        decisions.append(_decision("LIVE_ARMED_CLAIM", True))

    if gate.flatten_live_wire_enabled is not True:
        reasons.append("FLATTEN_LIVE_WIRE_CLAIM_FALSE")
        decisions.append(
            _decision("FLATTEN_LIVE_WIRE_CLAIM", False, "FLATTEN_LIVE_WIRE_CLAIM_FALSE")
        )
    else:
        decisions.append(_decision("FLATTEN_LIVE_WIRE_CLAIM", True))

    if gate.allow_productive_wire_send is not True:
        reasons.append("ALLOW_PRODUCTIVE_WIRE_SEND_FALSE")
        decisions.append(
            _decision("ALLOW_PRODUCTIVE_WIRE_SEND", False, "ALLOW_PRODUCTIVE_WIRE_SEND_FALSE")
        )
    else:
        decisions.append(_decision("ALLOW_PRODUCTIVE_WIRE_SEND", True))

    auth_ok, auth_reasons = evaluate_flatten_execute_authority_v1(
        token=gate.flatten_execute_token,
        purpose=gate.flatten_execute_purpose,
        owner_go=gate.flatten_execute_owner_go,
    )
    if not auth_ok:
        reasons.extend(auth_reasons)
        decisions.append(
            _decision(
                "FLATTEN_EXECUTE_AUTHORITY",
                False,
                ",".join(auth_reasons) or "FLATTEN_EXECUTE_AUTHORITY_DENIED",
            )
        )
    else:
        decisions.append(_decision("FLATTEN_EXECUTE_AUTHORITY", True))

    bound = str(gate.flatten_execute_bound_origin_main_sha or "").strip().lower()
    expected_sha = str(gate.origin_main_sha or "").strip().lower()
    if not bound:
        reasons.append("FLATTEN_EXECUTE_BOUND_SHA_MISSING")
        decisions.append(
            _decision("FLATTEN_EXECUTE_BOUND_SHA", False, "FLATTEN_EXECUTE_BOUND_SHA_MISSING")
        )
    elif len(bound) != 40 or any(ch not in "0123456789abcdef" for ch in bound):
        reasons.append("FLATTEN_EXECUTE_BOUND_SHA_MALFORMED")
        decisions.append(
            _decision("FLATTEN_EXECUTE_BOUND_SHA", False, "FLATTEN_EXECUTE_BOUND_SHA_MALFORMED")
        )
    elif bound != expected_sha:
        reasons.append("FLATTEN_EXECUTE_BOUND_SHA_STALE")
        decisions.append(
            _decision("FLATTEN_EXECUTE_BOUND_SHA", False, "FLATTEN_EXECUTE_BOUND_SHA_STALE")
        )
    else:
        decisions.append(_decision("FLATTEN_EXECUTE_BOUND_SHA", True))

    target = str(gate.instrument_id or "").strip()
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=target)
        decisions.append(_decision("INSTRUMENT_BINDING", True))
    except LiveCanaryInstrumentBindingError as exc:
        reasons.append(f"INSTRUMENT_BINDING:{exc}")
        decisions.append(_decision("INSTRUMENT_BINDING", False, str(exc)))

    observed_pos: str | None = None
    close_side: str | None = None
    qty: str | None = None
    permit: CanaryFlattenSubmitPermitV1 | None = None
    plan: CanaryFlattenOrderPlanV1 | None = None
    price_permit: FlattenPricePermitV1 | None = None
    body: dict[str, Any] | None = None

    classified = classify_target_position_state_v1(
        positions_payload=gate.positions_payload,
        instrument_id=target or DEFAULT_INSTRUMENT_ID,
    )
    if classified.state == TARGET_POSITION_NONZERO_PROVEN:
        decisions.append(_decision("TARGET_POSITION_STATE", True))
    else:
        reasons.append(f"TARGET_POSITION_STATE:{classified.reason}")
        decisions.append(_decision("TARGET_POSITION_STATE", False, classified.reason))

    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=gate.positions_payload,
            instrument_id=target or DEFAULT_INSTRUMENT_ID,
        )
        observed_pos = format(observed.signed_pos, "f")
        close_side = observed.candidate_flatten_side
        qty = format(observed.candidate_flatten_qty, "f")
        if observed.signed_pos == 0:
            reasons.append("PRE_POS_ZERO")
            decisions.append(_decision("PRODUCTIVE_POSITION_OBSERVED", False, "PRE_POS_ZERO"))
            decisions.append(_decision("PRE_POS_NONZERO", False, "PRE_POS_ZERO"))
        else:
            decisions.append(_decision("PRODUCTIVE_POSITION_OBSERVED", True))
            decisions.append(_decision("PRE_POS_NONZERO", True))
        if observed.instrument_id != DEFAULT_INSTRUMENT_ID:
            reasons.append("SINGLE_SELECTED_INSTRUMENT_MISMATCH")
            decisions.append(
                _decision(
                    "SINGLE_SELECTED_INSTRUMENT",
                    False,
                    "SINGLE_SELECTED_INSTRUMENT_MISMATCH",
                )
            )
        else:
            decisions.append(_decision("SINGLE_SELECTED_INSTRUMENT", True))
    except LiveCanaryPositionObservationError as exc:
        reasons.append(f"POSITION_OBSERVATION:{exc}")
        decisions.append(_decision("PRODUCTIVE_POSITION_OBSERVED", False, str(exc)))
        decisions.append(_decision("PRE_POS_NONZERO", False, str(exc)))
        decisions.append(_decision("SINGLE_SELECTED_INSTRUMENT", False, str(exc)))

    if gate.pending_orders_payload is None:
        reasons.append("OPEN_ORDER_STATE_UNAVAILABLE")
        decisions.append(_decision("OPEN_ORDER_CONFLICT", False, "OPEN_ORDER_STATE_UNAVAILABLE"))
    else:
        try:
            open_inst = open_order_instruments_v1(gate.pending_orders_payload)
            if open_inst:
                reasons.append("OPEN_ORDER_CONFLICT")
                decisions.append(_decision("OPEN_ORDER_CONFLICT", False, "OPEN_ORDER_PRESENT"))
            else:
                decisions.append(_decision("OPEN_ORDER_CONFLICT", True))
        except LiveCanaryPreSubmitStateError as exc:
            reasons.append(f"OPEN_ORDER_STATE:{exc}")
            decisions.append(_decision("OPEN_ORDER_CONFLICT", False, str(exc)))

    try:
        assert_pre_submit_open_position_cap_allows_v1(
            target_instrument_id=target or DEFAULT_INSTRUMENT_ID,
            positions_payload=gate.positions_payload,
        )
        decisions.append(_decision("B8_CAP", True))
    except PreSubmitOpenPositionCapErrorV1 as exc:
        reasons.append(f"B8_CAP:{exc.reason_code}")
        decisions.append(_decision("B8_CAP", False, exc.reason_code))

    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=gate.positions_payload,
        owner_go=gate.owner_go,
        origin_main_sha=gate.origin_main_sha,
        instrument_id=target or DEFAULT_INSTRUMENT_ID,
    )
    if orch.permit is None or orch.flatten_plan is None:
        reasons.append("FLATTEN_ORCHESTRATION_DENIED")
        decisions.append(_decision("CLOSE_SIDE", False, "ORCHESTRATION_DENIED"))
        decisions.append(_decision("FLATTEN_QTY", False, "ORCHESTRATION_DENIED"))
    else:
        permit = orch.permit
        plan = orch.flatten_plan
        if close_side and plan.side != close_side:
            reasons.append("CLOSE_SIDE_MISMATCH")
            decisions.append(_decision("CLOSE_SIDE", False, "CLOSE_SIDE_MISMATCH"))
        else:
            decisions.append(_decision("CLOSE_SIDE", True))
        if qty and str(plan.quantity) != qty:
            reasons.append("FLATTEN_QTY_MISMATCH")
            decisions.append(_decision("FLATTEN_QTY", False, "FLATTEN_QTY_MISMATCH"))
        else:
            decisions.append(_decision("FLATTEN_QTY", True))

    price_decision = evaluate_canary_flatten_limit_price_contract_v1(gate.price_input)
    if price_decision.permit is None:
        reasons.extend(price_decision.reject_reasons or ("LIMIT_PRICE_POLICY_DENIED",))
        decisions.append(
            _decision(
                "LIMIT_PRICE_POLICY",
                False,
                ",".join(price_decision.reject_reasons) or "LIMIT_PRICE_POLICY_DENIED",
            )
        )
        freshness_fail = "STALE_QUOTE" in price_decision.reject_reasons
        decisions.append(
            _decision(
                "QUOTE_FRESHNESS_5000MS",
                not freshness_fail and price_decision.permit is not None,
                "STALE_OR_INVALID_QUOTE",
            )
        )
    else:
        price_permit = price_decision.permit
        decisions.append(_decision("LIMIT_PRICE_POLICY", True))
        decisions.append(_decision("QUOTE_FRESHNESS_5000MS", True))
        supplied_threshold = str(gate.price_input.freshness_threshold_ms or "").strip()
        if supplied_threshold and supplied_threshold != str(FRESHNESS_THRESHOLD_MS):
            reasons.append("FRESHNESS_THRESHOLD_NOT_CANONICAL")
            decisions[-1] = _decision(
                "QUOTE_FRESHNESS_5000MS", False, "FRESHNESS_THRESHOLD_NOT_CANONICAL"
            )

    if permit is not None and plan is not None and price_permit is not None:
        try:
            body = build_canary_flatten_submit_request_v1(
                permit=permit,
                plan=plan,
                price_permit=price_permit,
                positions_payload=gate.positions_payload,
                instrument_id=target or DEFAULT_INSTRUMENT_ID,
            )
            if body.get("reduceOnly") is not True:
                reasons.append("REDUCE_ONLY_REQUIRED")
                decisions.append(_decision("REDUCE_ONLY", False, "REDUCE_ONLY_REQUIRED"))
            else:
                decisions.append(_decision("REDUCE_ONLY", True))
            if str(body.get("ordType") or "").lower() != "limit":
                reasons.append("LIMIT_ONLY_REQUIRED")
                decisions.append(_decision("LIMIT_ONLY", False, "LIMIT_ONLY_REQUIRED"))
            else:
                decisions.append(_decision("LIMIT_ONLY", True))
        except LiveCanaryFlattenSubmitTransportError as exc:
            reasons.append(str(exc))
            if "OVERSIZE" in str(exc) or "PARTIAL" in str(exc):
                decisions.append(_decision("OVERSHOOT_FLIP", False, str(exc)))
            decisions.append(_decision("REDUCE_ONLY", False, str(exc)))
            decisions.append(_decision("LIMIT_ONLY", False, str(exc)))
    else:
        decisions.append(_decision("REDUCE_ONLY", False, "REQUEST_NOT_CONSTRUCTED"))
        decisions.append(_decision("LIMIT_ONLY", False, "REQUEST_NOT_CONSTRUCTED"))

    overshoot_ok = (
        body is not None
        and qty is not None
        and str(body.get("sz") or "") == qty
        and "OVERSIZE_FLATTEN" not in reasons
        and "PARTIAL_FLATTEN_FORBIDDEN" not in reasons
        and "OPEN_ORDER_CONFLICT" not in reasons
        and "B8_CAP" not in "".join(reasons)
    )
    if overshoot_ok:
        decisions.append(_decision("OVERSHOOT_FLIP", True))
    elif all(item[0] != "OVERSHOOT_FLIP" for item in decisions):
        decisions.append(_decision("OVERSHOOT_FLIP", False, "OVERSHOOT_OR_FLIP_UNPROVEN"))
        if "OVERSHOOT_OR_FLIP_UNPROVEN" not in reasons and body is None:
            reasons.append("OVERSHOOT_OR_FLIP_UNPROVEN")

    if gate.one_shot_no_retry is not True:
        reasons.append("ONE_SHOT_NO_RETRY_REQUIRED")
        decisions.append(_decision("ONE_SHOT_NO_RETRY", False, "ONE_SHOT_NO_RETRY_REQUIRED"))
    else:
        decisions.append(_decision("ONE_SHOT_NO_RETRY", True))

    if gate.duplicate_post_protection is not True:
        reasons.append("DUPLICATE_POST_PROTECTION_REQUIRED")
        decisions.append(
            _decision("DUPLICATE_POST_PROTECTION", False, "DUPLICATE_POST_PROTECTION_REQUIRED")
        )
    else:
        decisions.append(_decision("DUPLICATE_POST_PROTECTION", True))

    clock = resolve_monotonic_ms_clock_v1(gate.monotonic_ms_clock)
    evaluation_ms = clock()
    freshness = evaluate_position_observation_freshness_v1(
        evidence=gate.position_observation_freshness_evidence,
        evaluation_monotonic_ms=evaluation_ms,
        current_decision_id=gate.flatten_pre_send_decision_id,
    )
    if not freshness.allowed:
        reasons.append(freshness.reject_reason)
        decisions.append(
            _decision(
                "POSITION_OBSERVATION_FRESHNESS",
                False,
                freshness.reject_reason,
            )
        )
    else:
        decisions.append(_decision("POSITION_OBSERVATION_FRESHNESS", True))

    allowed = not reasons
    digest_material = json.dumps(
        {"allowed": allowed, "reasons": reasons, "decisions": decisions},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(digest_material.encode("utf-8")).hexdigest()
    approved_url = canonical_flatten_approved_url_v1()
    approved_body_text = serialize_approved_flatten_body_text_v1(body)
    approved_identity = ""
    if allowed and approved_body_text:
        approved_identity = flatten_approved_request_identity_v1(
            method=APPROVED_FLATTEN_METHOD,
            url=approved_url,
            body_text=approved_body_text,
        )
    return FlattenPreSendGateReceiptV1(
        allowed=allowed,
        reasons=tuple(reasons),
        audit_decisions=tuple(decisions),
        observed_signed_pos=observed_pos,
        close_side=close_side or (None if body is None else str(body.get("side") or "").upper()),
        qty=qty,
        reduce_only=bool(body is not None and body.get("reduceOnly") is True),
        ord_type=None if body is None else str(body.get("ordType") or ""),
        limit_px=None if body is None else str(body.get("px") or ""),
        td_mode=None if body is None else str(body.get("tdMode") or ""),
        request_body=body,
        permit=permit,
        plan=plan,
        price_permit=price_permit,
        gate_digest=digest,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        productive_venue_proof=False,
        approved_method=APPROVED_FLATTEN_METHOD,
        approved_host=REUSED_BINDING_REST_HOST,
        approved_endpoint=ENDPOINT_SUBMIT,
        approved_url=approved_url,
        approved_body_text=approved_body_text,
        approved_request_identity=approved_identity,
        send_lease=FlattenReceiptSendLeaseV1(),
    )
