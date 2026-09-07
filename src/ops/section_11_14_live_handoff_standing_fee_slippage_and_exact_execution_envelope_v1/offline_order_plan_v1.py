"""Offline exact order-plan serialization. Stops before wire transport."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    assert_request_pos_side_omitted_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    CLORDID_PLAN_SENTINEL,
    ENVELOPE_VERSION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)


class OfflineExactOrderPlanError(RuntimeError):
    """Fail-closed offline order-plan violation."""


def build_offline_exact_order_plan_v1(
    *,
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    if not envelope.get("EXACT_EXECUTION_ENVELOPE_COMPLETE"):
        raise OfflineExactOrderPlanError("ENVELOPE_INCOMPLETE")
    if envelope.get("OWNER_EXECUTION_AUTHORIZED") is True:
        raise OfflineExactOrderPlanError("OWNER_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE")
    if envelope.get("LIVE_EXECUTION_AUTHORIZED") is True:
        raise OfflineExactOrderPlanError("LIVE_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE")
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise OfflineExactOrderPlanError("STANDING_LIVE_FLAG_BLOCKS_PLAN_WIRE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED:
        raise OfflineExactOrderPlanError("RUNTIME_EXECUTION_BLOCKS_PLAN_WIRE")
    required = (
        "INSTRUMENT_ID",
        "SIDE",
        "ORDER_TYPE",
        "TD_MODE",
        "ORDER_QTY",
        "LIMIT_PRICE",
        "EXPECTED_FEE_AMOUNT",
        "WORST_FILL_PRICE",
        "WORST_CASE_COST",
    )
    missing = [name for name in required if not str(envelope.get(name) or "").strip()]
    if missing:
        raise OfflineExactOrderPlanError(f"ENVELOPE_FIELD_MISSING:{','.join(missing)}")
    unknown = [
        name
        for name in required
        if str(envelope.get(name) or "").strip() in {"UNKNOWN", CLORDID_PLAN_SENTINEL}
    ]
    if unknown:
        raise OfflineExactOrderPlanError(f"ENVELOPE_FIELD_UNKNOWN:{','.join(unknown)}")
    try:
        body = build_venue_native_order_body_v1(
            client_order_id=CLORDID_PLAN_SENTINEL,
            instrument=str(envelope["INSTRUMENT_ID"]),
            order_type=str(envelope["ORDER_TYPE"]),
            side=str(envelope["SIDE"]),
            quantity=str(envelope["ORDER_QTY"]),
            td_mode=str(envelope["TD_MODE"]),
            px=str(envelope["LIMIT_PRICE"]),
        )
    except OkxResponseMapperError as exc:
        raise OfflineExactOrderPlanError(f"VENUE_NATIVE_BODY:{exc}") from exc
    body["clOrdId"] = CLORDID_PLAN_SENTINEL
    assert_request_pos_side_omitted_v1(body)
    if "posSide" in body:
        raise OfflineExactOrderPlanError("POS_SIDE_MUST_BE_OMITTED_IN_NET_MODE")
    wire_blocked_reasons = [
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "CANARY_AUTHORIZED=false",
        "POST_ALLOWED=false",
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false",
        "OWNER_EXECUTION_AUTHORIZED=false",
        "LIVE_EXECUTION_AUTHORIZED=false",
        "CLORDID_STATUS=UNKNOWN_REQUIRES_FUTURE_EXECUTION_OWNER_GO",
    ]
    return {
        "PLAN_ONLY": True,
        "WIRE_SEND_EXECUTED": False,
        "WIRE_SEND_BLOCKED": True,
        "WIRE_BLOCK_REASONS": wire_blocked_reasons,
        "ENVELOPE_VERSION": ENVELOPE_VERSION,
        "VENUE_NATIVE_PAYLOAD": dict(body),
        "PAYLOAD_FIELD_PROVENANCE": {
            "instId": "envelope.INSTRUMENT_ID",
            "side": "envelope.SIDE",
            "ordType": "envelope.ORDER_TYPE",
            "sz": "envelope.ORDER_QTY",
            "tdMode": "envelope.TD_MODE",
            "px": "envelope.LIMIT_PRICE",
            "clOrdId": "NOT_BOUND_REQUIRES_FUTURE_EXECUTION_OWNER_GO",
        },
        "PRE_SUBMIT_COMPUTED": {
            "EXPECTED_FEE_AMOUNT": envelope.get("EXPECTED_FEE_AMOUNT"),
            "WORST_FILL_PRICE": envelope.get("WORST_FILL_PRICE"),
            "WORST_CASE_COST": envelope.get("WORST_CASE_COST"),
        },
        "OWNER_EXECUTION_AUTHORIZED": False,
        "LIVE_SUBMIT_EXECUTED": False,
    }
