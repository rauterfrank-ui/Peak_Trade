"""Productive wire-send orchestrator. Consumes evaluator results. Never sends.

Does not arm. Does not set network_session_authorized. Does not consume.
Does not invoke inner.send.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    FLATTEN_HTTP_ENDPOINT,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    verify_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_flatten_submit_send_adapter_v1 import (
    FlattenProductiveSendAdapterError,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.wrapper_v1 import (
    FlattenWrapperError,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_send_capable_v1 import (
    ProductiveTransportBindSendCapableV1,
    assert_productive_transport_bind_send_capable_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    verify_owner_productive_wire_send_authority_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

OPEN_GATE_ORDER_POINTS: tuple[str, ...] = (
    "FRESH_PRE_SUBMIT_GET",
    "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND",
    "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER",
    "DURABLE_CONSUME_SUCCESS_OBJECT",
)


class ProductiveWireSendOrchestratorError(RuntimeError):
    """Fail-closed productive wire-send orchestrator violation."""


class ProductiveWireSendOrchestratorV1:
    """Named orchestrator type. Runtime entry is run_productive_wire_send_orchestrator_v1."""


def run_productive_wire_send_orchestrator_v1(
    *,
    bind: ProductiveTransportBindSendCapableV1 | None,
    wire_send: Mapping[str, Any] | None,
    network_session: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
    session_armed: bool,
    endpoint: str = FLATTEN_HTTP_ENDPOINT,
    body: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate gates in order. Never invokes inner.send. Does not consume."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise ProductiveWireSendOrchestratorError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    gate_order: list[str] = []
    reasons: list[str] = []

    wire_verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=wire_send,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    gate_order.append("OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1")
    if wire_verdict.get("accepted") is not True:
        reasons.extend(str(item) for item in (wire_verdict.get("reasons") or []))

    session_verdict = verify_owner_network_session_authority_v1(
        issuance=network_session,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    gate_order.append("OWNER_NETWORK_SESSION_AUTHORITY_V1")
    if session_verdict.get("accepted") is not True:
        reasons.extend(str(item) for item in (session_verdict.get("reasons") or []))

    gate_order.append("SESSION_ARMED")
    if session_armed is not True:
        reasons.append("SESSION_NOT_ARMED")

    inner_authorized = False
    if bind is not None:
        inner_authorized = bind.adapter.inner.network_session_authorized is True
    gate_order.append("NETWORK_SESSION_AUTHORIZED")
    if inner_authorized is not True:
        reasons.append("PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED")

    bind_reasons = assert_productive_transport_bind_send_capable_v1(bind)
    gate_order.append("SEND_CAPABLE_BIND")
    reasons.extend(bind_reasons)
    if bind is not None:
        if str(bind.origin_main_sha).strip().lower() != str(origin_main_sha).strip().lower():
            reasons.append("WIRE_SEND_SHA_MISMATCH")
        if str(bind.instrument_id) != str(instrument_id):
            reasons.append("WIRE_SEND_INSTRUMENT_MISMATCH")
        if str(bind.exact_envelope_id) != str(exact_envelope_id):
            reasons.append("WIRE_SEND_ENVELOPE_MISMATCH")

    gate_order.append("SEND_PERMITTED")
    if bind is None or bind.send_permitted is not True:
        reasons.append("SEND_PERMITTED_FALSE")

    adapter_error = ""
    prepared: Mapping[str, Any] | None = None
    if bind is not None and not reasons:
        bind.adapter.wire_send_accepted = wire_verdict.get("accepted") is True
        bind.adapter.session_accepted = session_verdict.get("accepted") is True
        bind.adapter.session_armed = session_armed
        bind.adapter.send_permitted = bind.send_permitted is True
        try:
            bind.adapter.post(endpoint=endpoint, body=dict(body or {}))
        except FlattenWrapperError as exc:
            adapter_error = str(exc)
            reasons.append(adapter_error)
        except FlattenProductiveSendAdapterError as exc:
            adapter_error = str(exc)
            reasons.append(adapter_error)
        prepared = bind.adapter.prepared
        if bind.adapter.inner_send_executed is True:
            reasons.append("INNER_SEND_MUST_REMAIN_UNEXECUTED")

    first_reason = reasons[0] if reasons else "INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION"
    return {
        "accepted": False,
        "reasons": reasons,
        "FIRST_DENY": first_reason,
        "GATE_ORDER": gate_order,
        "OPEN_GATE_ORDER_POINTS": list(OPEN_GATE_ORDER_POINTS),
        "WIRE_SEND_AUTHORITY_ISSUED": wire_verdict.get("issued") is True,
        "WIRE_SEND_AUTHORITY_ACCEPTED": wire_verdict.get("accepted") is True,
        "WIRE_SEND_AUTHORITY_CONSUMED": wire_verdict.get("consumed") is True,
        "NETWORK_SESSION_AUTHORITY_ISSUED": session_verdict.get("issued") is True,
        "NETWORK_SESSION_AUTHORITY_ACCEPTED": session_verdict.get("accepted") is True,
        "NETWORK_SESSION_AUTHORIZED": inner_authorized,
        "NETWORK_SESSION_AUTHORIZED_CHANGED": False,
        "SESSION_ARMED": session_armed is True,
        "SESSION_ARMING_EXECUTED": False,
        "SEND_PERMITTED": bind.send_permitted is True if bind is not None else False,
        "INNER_SEND_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "REAL_POST_COUNT": 0,
        "POST_COUNT": 0,
        "DURABLE_CONSUMED": False,
        "PREPARED_REQUEST": prepared,
        "ADAPTER_ERROR": adapter_error,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "ORCHESTRATOR": "ProductiveWireSendOrchestratorV1",
    }
