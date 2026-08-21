"""Dedicated §11.13.5 flatten submit/transport path.

Offline/fake-transport only. Distinct from entry submit. Never uses
/trade/close-position, never MARKET, never raises ORDER_COUNT_LIMIT,
and never enables live productive wire under this implementation GO.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    LIVE_AUTHORIZED,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FlattenPricePermitV1,
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    FLATTEN_PERMIT_KIND,
    CanaryFlattenSubmitPermitV1,
    LiveCanaryFlattenOrchestrationError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    CanaryFlattenHttpPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    signed_wire_body_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    CanaryFlattenOrderPlanV1,
    LiveCanaryOrderPlanError,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)


class LiveCanaryFlattenSubmitTransportError(RuntimeError):
    """Fail-closed dedicated flatten-transport violation."""


DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED = True
DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED = False
REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED = True
FLATTEN_SUBMIT_ENDPOINT = ENDPOINT_SUBMIT
CLOSE_POSITION_ENDPOINT_ALLOWLISTED = False
LIVE_FLATTEN_PROVABILITY = LIVE_FLATTEN_PROVABILITY_STATUS


def _dec(raw: str, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryFlattenSubmitTransportError(f"INVALID_DECIMAL:{field}") from exc
    return value


def _assert_standing_safety(*, transport: LiveCanaryTransportV1) -> None:
    if LIVE_AUTHORIZED:
        raise LiveCanaryFlattenSubmitTransportError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_LIVE_WIRE_MUST_REMAIN_DISABLED")
    if ORDER_COUNT_LIMIT != 1:
        raise LiveCanaryFlattenSubmitTransportError("ORDER_COUNT_LIMIT_MUST_REMAIN_1")
    if POSITION_COUNT_LIMIT != 1:
        raise LiveCanaryFlattenSubmitTransportError("POSITION_COUNT_LIMIT_MUST_REMAIN_1")
    if ENDPOINT_SUBMIT not in POST_ENDPOINTS_GATED:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_ENDPOINT_NOT_ALLOWLISTED")
    if "/api/v5/trade/close-position" in POST_ENDPOINTS_GATED:
        raise LiveCanaryFlattenSubmitTransportError("CLOSE_POSITION_MUST_REMAIN_BLOCKED")
    if isinstance(transport, UrllibLiveCanaryTransportV1) or bool(
        getattr(transport, "venue_live_contact", False)
    ):
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PRODUCTIVE_WIRE_FORBIDDEN")


def validate_flatten_qty_against_observed_position_v1(
    *,
    permit: CanaryFlattenSubmitPermitV1,
    plan: CanaryFlattenOrderPlanV1,
    positions_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    requested_qty: str | None = None,
) -> None:
    """Full-flatten only: qty must equal abs(observed pos). Oversize/zero/mismatch fail."""
    if permit is None:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PERMIT_MISSING")
    if not isinstance(permit, CanaryFlattenSubmitPermitV1):
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PERMIT_MALFORMED")
    if permit.kind != FLATTEN_PERMIT_KIND:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PERMIT_KIND_INVALID")
    target = str(instrument_id or "").strip()
    if target != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryFlattenSubmitTransportError("INSTRUMENT_BINDING_MISMATCH")
    if permit.instrument_id != target or plan.instrument_id != target:
        raise LiveCanaryFlattenSubmitTransportError("INSTRUMENT_MISMATCH")
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=positions_payload,
            instrument_id=target,
        )
    except LiveCanaryPositionObservationError as exc:
        code = str(exc)
        if "ZERO_POSITION_NO_FLATTEN_ORDER" in code:
            raise LiveCanaryFlattenSubmitTransportError("ZERO_POSITION") from exc
        if "TARGET_INSTRUMENT_NOT_OBSERVED" in code:
            raise LiveCanaryFlattenSubmitTransportError("INSTRUMENT_MISMATCH") from exc
        raise LiveCanaryFlattenSubmitTransportError(f"POSITION_OBSERVATION:{exc}") from exc
    qty = _dec(permit.quantity, field="permit.quantity")
    plan_qty = _dec(plan.quantity, field="plan.quantity")
    requested = qty if requested_qty is None else _dec(requested_qty, field="requested_qty")
    observed_qty = observed.candidate_flatten_qty
    if requested > observed_qty:
        raise LiveCanaryFlattenSubmitTransportError("OVERSIZE_FLATTEN")
    if requested < observed_qty:
        raise LiveCanaryFlattenSubmitTransportError("PARTIAL_FLATTEN_FORBIDDEN")
    if qty != observed_qty or plan_qty != observed_qty:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_QTY_NOT_ABS_OBSERVED_POS")
    if (
        permit.side != observed.candidate_flatten_side
        or plan.side != observed.candidate_flatten_side
    ):
        raise LiveCanaryFlattenSubmitTransportError("SIDE_MISMATCH")
    if permit.side != plan.side:
        raise LiveCanaryFlattenSubmitTransportError("SIDE_MISMATCH")
    if permit.reduce_only is not True or plan.reduce_only is not True:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_REDUCE_ONLY_REQUIRED")
    if str(plan.order_type).upper() != "LIMIT":
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_MARKET_FORBIDDEN")


def build_canary_flatten_submit_request_v1(
    *,
    permit: CanaryFlattenSubmitPermitV1,
    plan: CanaryFlattenOrderPlanV1,
    price_permit: FlattenPricePermitV1,
    positions_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    requested_qty: str | None = None,
) -> dict[str, Any]:
    """Serialize a dedicated flatten LIMIT reduce-only body. No network."""
    if price_permit is None:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PRICE_PERMIT_MISSING")
    if not isinstance(price_permit, FlattenPricePermitV1):
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PRICE_PERMIT_MALFORMED")
    validate_flatten_qty_against_observed_position_v1(
        permit=permit,
        plan=plan,
        positions_payload=positions_payload,
        instrument_id=instrument_id,
        requested_qty=requested_qty,
    )
    if price_permit.flatten_side != permit.side:
        raise LiveCanaryFlattenSubmitTransportError("SIDE_MISMATCH")
    try:
        body = serialize_canary_flatten_venue_native_payload_v1(
            plan,
            price_permit=price_permit,
        )
    except LiveCanaryOrderPlanError as exc:
        raise LiveCanaryFlattenSubmitTransportError(str(exc)) from exc
    if body.get("reduceOnly") is not True:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_REDUCE_ONLY_REQUIRED")
    if str(body.get("ordType") or "").lower() != "limit":
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_MARKET_FORBIDDEN")
    if str(body.get("instId") or "") != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryFlattenSubmitTransportError("INSTRUMENT_MISMATCH")
    return body


def run_canary_flatten_submit_transport_v1(
    *,
    permit: CanaryFlattenSubmitPermitV1 | None,
    plan: CanaryFlattenOrderPlanV1 | None,
    price_permit: FlattenPricePermitV1 | None,
    positions_payload: Mapping[str, Any],
    transport: LiveCanaryTransportV1,
    rest_host: str = REUSED_BINDING_REST_HOST,
    rest_base: str = "https://eea.okx.com",
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    requested_qty: str | None = None,
    allow_productive_wire_send: bool = False,
    entry_permit: CanaryEntrySubmitPermitV1 | None = None,
) -> dict[str, Any]:
    """Dedicated flatten path. Fake/offline transport only. Never live POST."""
    if allow_productive_wire_send:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PRODUCTIVE_WIRE_FORBIDDEN")
    if permit is None:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PERMIT_MISSING")
    if plan is None:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PLAN_MISSING")
    if price_permit is None:
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_PRICE_PERMIT_MISSING")
    if entry_permit is not None:
        raise LiveCanaryFlattenSubmitTransportError("ENTRY_PERMIT_CANNOT_USE_FLATTEN_TRANSPORT")
    if isinstance(permit, CanaryEntrySubmitPermitV1):
        raise LiveCanaryFlattenSubmitTransportError("ENTRY_PERMIT_CANNOT_USE_FLATTEN_TRANSPORT")
    _assert_standing_safety(transport=transport)
    if not isinstance(transport, RecordingFakeCanaryTransportV1):
        raise LiveCanaryFlattenSubmitTransportError("FLATTEN_REQUIRES_NON_LIVE_FAKE_TRANSPORT")
    body = build_canary_flatten_submit_request_v1(
        permit=permit,
        plan=plan,
        price_permit=price_permit,
        positions_payload=positions_payload,
        instrument_id=instrument_id,
        requested_qty=requested_qty,
    )
    body_text = json.dumps(body, separators=(",", ":"), ensure_ascii=True)
    client = LiveCanaryHttpClientV1(rest_base=rest_base, rest_host=rest_host, transport=transport)
    http_permit = CanaryFlattenHttpPermitV1(
        owner_go=permit.owner_go,
        clordid=permit.clordid,
        permit_id=permit.permit_id,
    )
    try:
        response = client.post_flatten_order(
            permit=http_permit,
            body_text=body_text,
            headers={"User-Agent": "PeakTrade-Section-11-13-5-FlattenOffline/1"},
        )
    except LiveCanaryHttpError as exc:
        raise LiveCanaryFlattenSubmitTransportError(str(exc)) from exc
    except LiveCanaryFlattenOrchestrationError as exc:
        raise LiveCanaryFlattenSubmitTransportError(str(exc)) from exc
    signed_wire = signed_wire_body_evidence_v1(
        signed_body_text=body_text,
        wire_body_bytes=body_text.encode("utf-8"),
    )
    return {
        "ok": response.status_code == 200,
        "mode": "offline_fake_transport",
        "DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED": True,
        "FLATTEN_SUBMIT_ENDPOINT": FLATTEN_SUBMIT_ENDPOINT,
        "CLOSE_POSITION_ENDPOINT_ALLOWLISTED": False,
        "MARKET_PATH_USED": False,
        "REDUCE_ONLY": True,
        "ORDER_COUNT_LIMIT": ORDER_COUNT_LIMIT,
        "LIVE_AUTHORIZED": False,
        "LIVE_FLATTEN_PROVABILITY": LIVE_FLATTEN_PROVABILITY,
        "PRODUCTIVE_WIRE_SEND": False,
        "venue_live_contact": False,
        "body": body,
        "http_status": response.status_code,
        "signed_wire_body_evidence": signed_wire,
        "counters": client.counters.to_dict(),
    }
