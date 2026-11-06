"""Live canary order-execution contracts (§11.19 Cap 11.9).

Fixture-only schema for canary lifecycle through ACKNOWLEDGED.
No network submit, credential load, or real Live order execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_CANARY_ALLOWED_EXECUTION_MODE,
    LIVE_CANARY_FORBIDDEN_LIFECYCLE_STATES,
    LIVE_CANARY_LIFECYCLE_STATES,
    LIVE_CANARY_NETWORK_EFFECT,
    LIVE_CANARY_ORDER_EXECUTION_ACTIVATED,
    LIVE_CANARY_ORDER_EXECUTION_CONTRACT_ACTIVATED,
    LIVE_CANARY_ORDER_EXECUTION_CONTRACT_BOUND,
    LIVE_CANARY_ORDER_EXECUTION_OWNER,
    LIVE_CANARY_REQUIRED_FIELDS,
    LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_9,
    LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_9,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    OWNER,
    POSITION_COUNT_LIMIT,
)


class LiveCanaryOrderExecutionError(RuntimeError):
    """Fail-closed Live canary order-execution violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class LiveCanaryOrderExecutionRecordV1:
    """Fixture-only Live canary order-execution record (no real submit)."""

    stage: str
    intent_id: str
    order_plan_id: str
    client_order_id: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    execution_mode: str
    lifecycle_state: str
    max_notional: str
    position_count_limit: int
    canonical_order_plan_digest: str
    venue_native_canary_payload: dict[str, Any]
    canary_serialization_digest: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    submitted: bool = False
    execution_performed: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_CANARY_ORDER_EXECUTION_OWNER


def build_live_canary_order_execution_record_v1(
    *,
    stage: str = "LIVE_CANARY_MINIMUM_EXPOSURE",
    intent_id: str,
    order_plan_id: str,
    client_order_id: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    max_notional: str = "1",
    position_count_limit: int = POSITION_COUNT_LIMIT,
    lifecycle_state: str = "ACKNOWLEDGED",
    execution_mode: str = LIVE_CANARY_ALLOWED_EXECUTION_MODE,
    source: str = "FIXTURE_ONLY",
) -> LiveCanaryOrderExecutionRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveCanaryOrderExecutionError(
            f"CAPABILITY_11_10_SURFACE_FORBIDDEN_IN_CAPABILITY_11_9:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveCanaryOrderExecutionError(f"UNKNOWN_LIVE_CANARY_STAGE:{stage}")
    if source != "FIXTURE_ONLY":
        raise LiveCanaryOrderExecutionError(
            f"NON_FIXTURE_LIVE_CANARY_SOURCE_FORBIDDEN_IN_CAPABILITY_11_9:{source}"
        )
    if execution_mode != LIVE_CANARY_ALLOWED_EXECUTION_MODE:
        raise LiveCanaryOrderExecutionError(
            f"LIVE_CANARY_EXECUTION_MODE_FORBIDDEN:{execution_mode}"
        )
    if lifecycle_state in LIVE_CANARY_FORBIDDEN_LIFECYCLE_STATES:
        raise LiveCanaryOrderExecutionError(
            f"LIVE_CANARY_FILL_LIFECYCLE_FORBIDDEN:{lifecycle_state}"
        )
    if lifecycle_state not in LIVE_CANARY_LIFECYCLE_STATES:
        raise LiveCanaryOrderExecutionError(
            f"UNKNOWN_LIVE_CANARY_LIFECYCLE_STATE:{lifecycle_state}"
        )
    if position_count_limit != POSITION_COUNT_LIMIT:
        raise LiveCanaryOrderExecutionError(
            f"LIVE_CANARY_POSITION_COUNT_LIMIT_FORBIDDEN:{position_count_limit}"
        )

    fields = {
        "intent_id": intent_id,
        "order_plan_id": order_plan_id,
        "client_order_id": client_order_id,
        "instrument_id": instrument_id,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "execution_mode": execution_mode,
        "max_notional": max_notional,
        "position_count_limit": str(position_count_limit),
    }
    for key in LIVE_CANARY_REQUIRED_FIELDS:
        if not fields.get(key):
            raise LiveCanaryOrderExecutionError(f"LIVE_CANARY_ORDER_EXECUTION_FIELD_MISSING:{key}")

    canonical_payload = {
        "intent_id": intent_id,
        "order_plan_id": order_plan_id,
        "client_order_id": client_order_id,
        "instrument_id": instrument_id,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "execution_mode": execution_mode,
        "lifecycle_state": lifecycle_state,
        "stage": stage,
        "max_notional": max_notional,
        "position_count_limit": position_count_limit,
    }
    venue_native_canary_payload = {
        "clOrdId": client_order_id,
        "instId": instrument_id,
        "side": side.lower(),
        "ordType": order_type.lower(),
        "sz": quantity,
        "tdMode": "cross",
        "canary": True,
        "submit": False,
        "maxNotional": max_notional,
        "positionCountLimit": position_count_limit,
    }
    return LiveCanaryOrderExecutionRecordV1(
        stage=stage,
        intent_id=intent_id,
        order_plan_id=order_plan_id,
        client_order_id=client_order_id,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        execution_mode=execution_mode,
        lifecycle_state=lifecycle_state,
        max_notional=max_notional,
        position_count_limit=position_count_limit,
        canonical_order_plan_digest=hashlib.sha256(
            _canonical_dumps(canonical_payload).encode("utf-8")
        ).hexdigest(),
        venue_native_canary_payload=venue_native_canary_payload,
        canary_serialization_digest=hashlib.sha256(
            _canonical_dumps(venue_native_canary_payload).encode("utf-8")
        ).hexdigest(),
        source=source,
        network_effect=LIVE_CANARY_NETWORK_EFFECT,
        submitted=False,
        execution_performed=False,
    )


def refuse_live_canary_order_execution_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveCanaryOrderExecutionError(
        f"LIVE_CANARY_ORDER_EXECUTION_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_9:{claimed_action}"
    )


def refuse_live_canary_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    raise LiveCanaryOrderExecutionError(
        f"LIVE_CANARY_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_9:{client_order_id}"
    )


def refuse_live_canary_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LiveCanaryOrderExecutionError(
        f"LIVE_CANARY_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_9:{session_id}"
    )


def refuse_live_canary_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveCanaryOrderExecutionError(
        f"LIVE_CANARY_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_9:{claimed_action}"
    )


def prove_live_canary_order_execution_contract_v1() -> dict[str, Any]:
    record = build_live_canary_order_execution_record_v1(
        intent_id="intent-canary-demo",
        order_plan_id="plan-canary-demo",
        client_order_id="pt-coid-live-canary-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )

    non_fixture_blocked = False
    try:
        build_live_canary_order_execution_record_v1(
            intent_id="intent-bad",
            order_plan_id="plan-bad",
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    except LiveCanaryOrderExecutionError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    live_submit_mode_blocked = False
    try:
        build_live_canary_order_execution_record_v1(
            intent_id="intent-live",
            order_plan_id="plan-live",
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    except LiveCanaryOrderExecutionError as exc:
        live_submit_mode_blocked = "EXECUTION_MODE_FORBIDDEN" in str(exc)

    fill_lifecycle_blocked = False
    try:
        build_live_canary_order_execution_record_v1(
            intent_id="intent-fill",
            order_plan_id="plan-fill",
            client_order_id="pt-coid-fill",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            lifecycle_state="FILLED",
        )
    except LiveCanaryOrderExecutionError as exc:
        fill_lifecycle_blocked = "FILL_LIFECYCLE_FORBIDDEN" in str(exc)

    bounded_stage_blocked = False
    try:
        build_live_canary_order_execution_record_v1(
            stage="LIVE_BOUNDED_SINGLE_FUTURE",
            intent_id="intent-bounded",
            order_plan_id="plan-bounded",
            client_order_id="pt-coid-bounded",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    except LiveCanaryOrderExecutionError as exc:
        bounded_stage_blocked = "CAPABILITY_11_10_SURFACE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_canary_order_execution_activation_v1(claimed_action="activate_canary_exec")
    except LiveCanaryOrderExecutionError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_live_canary_order_submit_v1(client_order_id=record.client_order_id)
    except LiveCanaryOrderExecutionError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_canary_network_session_v1(session_id="live-canary-session")
    except LiveCanaryOrderExecutionError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_canary_credential_access_v1(claimed_action="load_api_key")
    except LiveCanaryOrderExecutionError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.submitted is False,
            record.execution_performed is False,
            record.network_effect == "NONE",
            record.venue_native_canary_payload.get("canary") is True,
            record.venue_native_canary_payload.get("submit") is False,
            bool(record.canonical_order_plan_digest),
            bool(record.canary_serialization_digest),
            non_fixture_blocked,
            live_submit_mode_blocked,
            fill_lifecycle_blocked,
            bounded_stage_blocked,
            activation_blocked,
            submit_blocked,
            session_blocked,
            credential_blocked,
            LIVE_CANARY_ORDER_EXECUTION_CONTRACT_BOUND is True,
            LIVE_CANARY_ORDER_EXECUTION_CONTRACT_ACTIVATED is False,
            LIVE_CANARY_ORDER_EXECUTION_ACTIVATED is False,
            LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_9 is False,
            LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_9 is False,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_CANARY_ORDER_EXECUTION_CONTRACT_BOUND": True,
        "LIVE_CANARY_ORDER_EXECUTION_CONTRACT_ACTIVATED": False,
        "LIVE_CANARY_ORDER_EXECUTION_ACTIVATED": False,
        "LIVE_CANARY_NETWORK_EFFECT": "NONE",
        "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_9": False,
        "LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_9": False,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "lifecycle_states": list(LIVE_CANARY_LIFECYCLE_STATES),
        "forbidden_lifecycle_states": list(LIVE_CANARY_FORBIDDEN_LIFECYCLE_STATES),
        "non_fixture_blocked": non_fixture_blocked,
        "live_submit_mode_blocked": live_submit_mode_blocked,
        "fill_lifecycle_blocked": fill_lifecycle_blocked,
        "bounded_stage_blocked": bounded_stage_blocked,
        "activation_blocked": activation_blocked,
        "submit_blocked": submit_blocked,
        "network_session_blocked": session_blocked,
        "credential_access_blocked": credential_blocked,
        "sample_canonical_digest": record.canonical_order_plan_digest,
        "sample_canary_digest": record.canary_serialization_digest,
        "OWNER": LIVE_CANARY_ORDER_EXECUTION_OWNER,
    }
