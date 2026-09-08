"""Bound send_permitted seam. Not an Owner issuer. Not inner.send.

Sets ProductiveFlattenSubmitSendAdapterV1.send_permitted false -> true only
on the exact send-capable bind. Does not invoke inner.send. Does not GET.
Does not POST. Does not consume. Does not change session_armed or
network_session_authorized.

OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1 issued/accepted
≠ network_session_authorized
≠ session_armed
≠ send_permitted
≠ inner.send
≠ wire send
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    verify_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_flatten_submit_send_adapter_v1 import (
    ProductiveFlattenSubmitSendAdapterV1,
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


class FlattenSendPermissionError(RuntimeError):
    """Fail-closed bound send-permission violation."""


def permit_productive_send_v1(
    *,
    bind: ProductiveTransportBindSendCapableV1 | None,
    network_session: Mapping[str, Any] | None,
    wire_send: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> dict[str, Any]:
    """Permit exactly the bound send-capable adapter. Offline only. No I/O."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenSendPermissionError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if SESSION_ARMING_STANDING is True:
        raise FlattenSendPermissionError("STANDING_SESSION_ARMING_MUST_REMAIN_FALSE")
    session_verdict = verify_owner_network_session_authority_v1(
        issuance=network_session,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    wire_verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=wire_send,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    reasons: list[str] = []
    reasons.extend(str(item) for item in (session_verdict.get("reasons") or []))
    reasons.extend(str(item) for item in (wire_verdict.get("reasons") or []))
    reasons.extend(assert_productive_transport_bind_send_capable_v1(bind))
    inner_authorized_before = False
    armed_before = False
    permitted_before = False
    inner = None
    if bind is not None:
        inner = bind.adapter.inner
        inner_authorized_before = inner.network_session_authorized is True
        armed_before = bind.adapter.session_armed is True
        permitted_before = bind.adapter.send_permitted is True
        if str(bind.origin_main_sha).strip().lower() != str(origin_main_sha).strip().lower():
            reasons.append("NETWORK_SESSION_SHA_MISMATCH")
        if str(bind.instrument_id) != str(instrument_id):
            reasons.append("NETWORK_SESSION_INSTRUMENT_MISMATCH")
        if str(bind.exact_envelope_id) != str(exact_envelope_id):
            reasons.append("NETWORK_SESSION_ENVELOPE_MISMATCH")
        if bind.session_verdict.get("accepted") is not True:
            stored = [str(item) for item in (bind.session_verdict.get("reasons") or [])]
            if stored:
                reasons.extend(stored)
            else:
                reasons.append("NETWORK_SESSION_OWNER_AUTHORITY_MISSING")
        if bind.wire_send_verdict.get("accepted") is not True:
            stored_wire = [str(item) for item in (bind.wire_send_verdict.get("reasons") or [])]
            if stored_wire:
                reasons.extend(stored_wire)
            else:
                reasons.append("WIRE_SEND_OWNER_AUTHORITY_MISSING")
        recorded_session_id = str(bind.session_verdict.get("authority_id") or "")
        verified_session_id = str(session_verdict.get("authority_id") or "")
        if (
            recorded_session_id
            and verified_session_id
            and recorded_session_id != verified_session_id
        ):
            reasons.append("NETWORK_SESSION_AUTHORITY_ID_MISMATCH")
        recorded_wire_id = str(bind.wire_send_verdict.get("authority_id") or "")
        verified_wire_id = str(wire_verdict.get("authority_id") or "")
        if recorded_wire_id and verified_wire_id and recorded_wire_id != verified_wire_id:
            reasons.append("WIRE_SEND_AUTHORITY_ID_MISMATCH")
        if not isinstance(bind.adapter, ProductiveFlattenSubmitSendAdapterV1):
            reasons.append("PRODUCTIVE_TRANSPORT_BIND_ADAPTER_TYPE_MISMATCH")
        if inner_authorized_before is not True:
            reasons.append("PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED")
        if armed_before is not True:
            reasons.append("SESSION_NOT_ARMED")
    unique_reasons = list(dict.fromkeys(reasons))
    permitted = False
    changed = False
    if not unique_reasons and bind is not None and permitted_before is not True:
        bind.adapter.send_permitted = True
        permitted = bind.adapter.send_permitted is True
        changed = permitted is True and permitted_before is not True
        if permitted is not True:
            unique_reasons.append("SEND_PERMITTED_FALSE")
    permitted_after = bind.adapter.send_permitted is True if bind is not None else False
    armed_after = bind.adapter.session_armed is True if bind is not None else False
    inner_after = inner.network_session_authorized is True if inner is not None else False
    return {
        "permitted": permitted,
        "reasons": unique_reasons,
        "SEND_PERMISSION_BIND_VALIDATION": "PASS" if permitted else "DENY",
        "SEND_PERMITTED_BEFORE": permitted_before,
        "SEND_PERMITTED": permitted_after,
        "SEND_PERMISSION_CHANGED": changed,
        "BIND_SEND_PERMITTED": bind.send_permitted is True if bind is not None else False,
        "SESSION_ARMED_BEFORE": armed_before,
        "SESSION_ARMED": armed_after,
        "NETWORK_SESSION_AUTHORIZED_BEFORE": inner_authorized_before,
        "NETWORK_SESSION_AUTHORIZED": inner_after,
        "NETWORK_SESSION_AUTHORIZED_CHANGED": inner_after is not inner_authorized_before,
        "NETWORK_SESSION_AUTHORITY_ISSUED": session_verdict.get("issued") is True,
        "NETWORK_SESSION_AUTHORITY_ACCEPTED": session_verdict.get("accepted") is True,
        "WIRE_SEND_AUTHORITY_ISSUED": wire_verdict.get("issued") is True,
        "WIRE_SEND_AUTHORITY_ACCEPTED": wire_verdict.get("accepted") is True,
        "WIRE_SEND_AUTHORITY_CONSUMED": wire_verdict.get("consumed") is True,
        "INNER_SEND_EXECUTED": False,
        "FAKE_INNER_SEND_REACHED": False,
        "REAL_INNER_SEND_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION": False,
        "REAL_POST_COUNT": 0,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "REPRICE_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "SESSION_ARMING_STANDING": bool(SESSION_ARMING_STANDING),
        "EVALUATOR_IS_NOT_ISSUER": True,
        "PERMITTED_IS_NOT_SEND": True,
    }
