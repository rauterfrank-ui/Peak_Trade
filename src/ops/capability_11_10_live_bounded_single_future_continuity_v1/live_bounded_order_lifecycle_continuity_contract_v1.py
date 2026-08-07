"""Live bounded order-lifecycle continuity contracts (§11.19 Cap 11.10).

Fixture-only schema for bounded continuity lifecycle through RECONCILED.
No network submit, credential load, or real Live order execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_BOUNDED_ALLOWED_EXECUTION_MODE,
    LIVE_BOUNDED_FORBIDDEN_LIFECYCLE_STATES,
    LIVE_BOUNDED_LIFECYCLE_STATES,
    LIVE_BOUNDED_NETWORK_EFFECT,
    LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATED,
    LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_ACTIVATED,
    LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_BOUND,
    LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER,
    LIVE_BOUNDED_REQUIRED_FIELDS,
    LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_10,
    LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_10,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    OWNER,
    POSITION_COUNT_LIMIT,
)


class LiveBoundedOrderLifecycleContinuityError(RuntimeError):
    """Fail-closed Live bounded order-lifecycle continuity violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class LiveBoundedOrderLifecycleContinuityRecordV1:
    """Fixture-only Live bounded order-lifecycle continuity record (no real submit)."""

    stage: str
    continuity_session_id: str
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
    venue_native_bounded_payload: dict[str, Any]
    bounded_serialization_digest: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    submitted: bool = False
    execution_performed: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER


def build_live_bounded_order_lifecycle_continuity_record_v1(
    *,
    stage: str = "LIVE_BOUNDED_SINGLE_FUTURE",
    continuity_session_id: str = "bounded-continuity-fixture-v1",
    intent_id: str,
    order_plan_id: str,
    client_order_id: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    max_notional: str = "1",
    position_count_limit: int = POSITION_COUNT_LIMIT,
    lifecycle_state: str = "RECONCILED",
    execution_mode: str = LIVE_BOUNDED_ALLOWED_EXECUTION_MODE,
    source: str = "FIXTURE_ONLY",
) -> LiveBoundedOrderLifecycleContinuityRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"CAPABILITY_11_11_SURFACE_FORBIDDEN_IN_CAPABILITY_11_10:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"UNKNOWN_LIVE_BOUNDED_CONTINUITY_STAGE:{stage}"
        )
    if source != "FIXTURE_ONLY":
        raise LiveBoundedOrderLifecycleContinuityError(
            f"NON_FIXTURE_LIVE_BOUNDED_SOURCE_FORBIDDEN_IN_CAPABILITY_11_10:{source}"
        )
    if execution_mode != LIVE_BOUNDED_ALLOWED_EXECUTION_MODE:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"LIVE_BOUNDED_EXECUTION_MODE_FORBIDDEN:{execution_mode}"
        )
    if lifecycle_state in LIVE_BOUNDED_FORBIDDEN_LIFECYCLE_STATES:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"LIVE_BOUNDED_AMEND_CANCEL_PENDING_LIFECYCLE_FORBIDDEN:{lifecycle_state}"
        )
    if lifecycle_state not in LIVE_BOUNDED_LIFECYCLE_STATES:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"UNKNOWN_LIVE_BOUNDED_LIFECYCLE_STATE:{lifecycle_state}"
        )
    if position_count_limit != POSITION_COUNT_LIMIT:
        raise LiveBoundedOrderLifecycleContinuityError(
            f"LIVE_BOUNDED_POSITION_COUNT_LIMIT_FORBIDDEN:{position_count_limit}"
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
        "continuity_session_id": continuity_session_id,
    }
    for key in LIVE_BOUNDED_REQUIRED_FIELDS:
        if not fields.get(key):
            raise LiveBoundedOrderLifecycleContinuityError(
                f"LIVE_BOUNDED_ORDER_LIFECYCLE_FIELD_MISSING:{key}"
            )

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
        "continuity_session_id": continuity_session_id,
    }
    venue_native_bounded_payload = {
        "clOrdId": client_order_id,
        "instId": instrument_id,
        "side": side.lower(),
        "ordType": order_type.lower(),
        "sz": quantity,
        "tdMode": "cross",
        "boundedSingleFuture": True,
        "continuitySessionId": continuity_session_id,
        "submit": False,
        "maxNotional": max_notional,
        "positionCountLimit": position_count_limit,
    }
    return LiveBoundedOrderLifecycleContinuityRecordV1(
        stage=stage,
        continuity_session_id=continuity_session_id,
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
        venue_native_bounded_payload=venue_native_bounded_payload,
        bounded_serialization_digest=hashlib.sha256(
            _canonical_dumps(venue_native_bounded_payload).encode("utf-8")
        ).hexdigest(),
        source=source,
        network_effect=LIVE_BOUNDED_NETWORK_EFFECT,
        submitted=False,
        execution_performed=False,
    )


def refuse_live_bounded_order_lifecycle_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveBoundedOrderLifecycleContinuityError(
        "LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_10:"
        f"{claimed_action}"
    )


def refuse_live_bounded_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    raise LiveBoundedOrderLifecycleContinuityError(
        f"LIVE_BOUNDED_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_10:{client_order_id}"
    )


def refuse_live_bounded_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LiveBoundedOrderLifecycleContinuityError(
        f"LIVE_BOUNDED_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_10:{session_id}"
    )


def refuse_live_bounded_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveBoundedOrderLifecycleContinuityError(
        f"LIVE_BOUNDED_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_10:{claimed_action}"
    )


def prove_live_bounded_order_lifecycle_continuity_contract_v1() -> dict[str, Any]:
    record = build_live_bounded_order_lifecycle_continuity_record_v1(
        intent_id="intent-bounded-demo",
        order_plan_id="plan-bounded-demo",
        client_order_id="pt-coid-live-bounded-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )

    non_fixture_blocked = False
    try:
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-bad",
            order_plan_id="plan-bad",
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    except LiveBoundedOrderLifecycleContinuityError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    live_submit_mode_blocked = False
    try:
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-live",
            order_plan_id="plan-live",
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    except LiveBoundedOrderLifecycleContinuityError as exc:
        live_submit_mode_blocked = "EXECUTION_MODE_FORBIDDEN" in str(exc)

    amend_pending_blocked = False
    try:
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-amend",
            order_plan_id="plan-amend",
            client_order_id="pt-coid-amend",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            lifecycle_state="AMEND_PENDING",
        )
    except LiveBoundedOrderLifecycleContinuityError as exc:
        amend_pending_blocked = "AMEND_CANCEL_PENDING_LIFECYCLE_FORBIDDEN" in str(exc)

    multi_session_blocked = False
    try:
        build_live_bounded_order_lifecycle_continuity_record_v1(
            stage="LIVE_BOUNDED_MULTI_SESSION",
            intent_id="intent-multi",
            order_plan_id="plan-multi",
            client_order_id="pt-coid-multi",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    except LiveBoundedOrderLifecycleContinuityError as exc:
        multi_session_blocked = "CAPABILITY_11_11_SURFACE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_bounded_order_lifecycle_activation_v1(claimed_action="activate_bounded_lc")
    except LiveBoundedOrderLifecycleContinuityError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_live_bounded_order_submit_v1(client_order_id=record.client_order_id)
    except LiveBoundedOrderLifecycleContinuityError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_bounded_network_session_v1(session_id="live-bounded-session")
    except LiveBoundedOrderLifecycleContinuityError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_bounded_credential_access_v1(claimed_action="load_api_key")
    except LiveBoundedOrderLifecycleContinuityError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.submitted is False,
            record.execution_performed is False,
            record.network_effect == "NONE",
            record.lifecycle_state == "RECONCILED",
            record.venue_native_bounded_payload.get("boundedSingleFuture") is True,
            record.venue_native_bounded_payload.get("submit") is False,
            bool(record.canonical_order_plan_digest),
            bool(record.bounded_serialization_digest),
            non_fixture_blocked,
            live_submit_mode_blocked,
            amend_pending_blocked,
            multi_session_blocked,
            activation_blocked,
            submit_blocked,
            session_blocked,
            credential_blocked,
            LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_BOUND is True,
            LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_ACTIVATED is False,
            LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATED is False,
            LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_10 is False,
            LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_10 is False,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_BOUND": True,
        "LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_ACTIVATED": False,
        "LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATED": False,
        "LIVE_BOUNDED_NETWORK_EFFECT": "NONE",
        "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_10": False,
        "LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_10": False,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "lifecycle_states": list(LIVE_BOUNDED_LIFECYCLE_STATES),
        "forbidden_lifecycle_states": list(LIVE_BOUNDED_FORBIDDEN_LIFECYCLE_STATES),
        "non_fixture_blocked": non_fixture_blocked,
        "live_submit_mode_blocked": live_submit_mode_blocked,
        "amend_pending_blocked": amend_pending_blocked,
        "multi_session_stage_blocked": multi_session_blocked,
        "activation_blocked": activation_blocked,
        "submit_blocked": submit_blocked,
        "network_session_blocked": session_blocked,
        "credential_access_blocked": credential_blocked,
        "sample_canonical_digest": record.canonical_order_plan_digest,
        "sample_bounded_digest": record.bounded_serialization_digest,
        "OWNER": LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER,
    }
