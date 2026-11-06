"""Instance-flag seam for network_session_authorized. Not an Owner issuer.

Sets AuthenticatedGatedProductiveFlattenTransportV1.network_session_authorized
false -> true only on the exact send-capable bound inner. Does not arm.
Does not set send_permitted. Does not mint. Does not consume. Does not GET.
Does not POST. Does not invoke inner.send.

OWNER_NETWORK_SESSION_AUTHORITY_V1 issued/accepted
≠ network_session_authorized instance state
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenNetworkSessionInstanceAuthorizationError(RuntimeError):
    """Fail-closed network-session instance-authorization violation."""


def authorize_network_session_instance_v1(
    *,
    bind: ProductiveTransportBindSendCapableV1 | None,
    network_session: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> dict[str, Any]:
    """Authorize exactly the bound inner instance. Offline only. No I/O."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenNetworkSessionInstanceAuthorizationError(
            "STANDING_LIVE_FLAG_MUST_REMAIN_FALSE"
        )
    if SESSION_ARMING_STANDING is True:
        raise FlattenNetworkSessionInstanceAuthorizationError(
            "STANDING_SESSION_ARMING_MUST_REMAIN_FALSE"
        )
    session_verdict = verify_owner_network_session_authority_v1(
        issuance=network_session,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    reasons: list[str] = []
    reasons.extend(str(item) for item in (session_verdict.get("reasons") or []))
    reasons.extend(assert_productive_transport_bind_send_capable_v1(bind))
    inner_before = False
    inner = None
    if bind is not None:
        inner = bind.adapter.inner
        inner_before = inner.network_session_authorized is True
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
        recorded_id = str(bind.session_verdict.get("authority_id") or "")
        verified_id = str(session_verdict.get("authority_id") or "")
        if recorded_id and verified_id and recorded_id != verified_id:
            reasons.append("NETWORK_SESSION_AUTHORITY_ID_MISMATCH")
        if not isinstance(bind.adapter, ProductiveFlattenSubmitSendAdapterV1):
            reasons.append("PRODUCTIVE_TRANSPORT_BIND_ADAPTER_TYPE_MISMATCH")
    unique_reasons = list(dict.fromkeys(reasons))
    authorized = False
    changed = False
    if not unique_reasons and inner is not None and inner_before is not True:
        inner.network_session_authorized = True
        authorized = inner.network_session_authorized is True
        changed = authorized is True and inner_before is not True
        if authorized is not True:
            unique_reasons.append("PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED")
    inner_after = inner.network_session_authorized is True if inner is not None else False
    session_armed = bind.adapter.session_armed is True if bind is not None else False
    send_permitted = bind.send_permitted is True if bind is not None else False
    return {
        "authorized": authorized,
        "reasons": unique_reasons,
        "INSTANCE_BIND_VALIDATION": "PASS" if authorized else "DENY",
        "NETWORK_SESSION_AUTHORIZED_BEFORE": inner_before,
        "NETWORK_SESSION_AUTHORIZED": inner_after,
        "NETWORK_SESSION_AUTHORIZED_CHANGED": changed,
        "NETWORK_SESSION_AUTHORITY_ISSUED": session_verdict.get("issued") is True,
        "NETWORK_SESSION_AUTHORITY_ACCEPTED": session_verdict.get("accepted") is True,
        "NETWORK_SESSION_AUTHORITY_CONSUMED": (
            False if network_session is None else network_session.get("consumed") is True
        ),
        "BIND_NETWORK_SESSION_AUTHORIZED": (
            bind.network_session_authorized is True if bind is not None else False
        ),
        "SESSION_ARMED": session_armed,
        "SESSION_ARMING_EXECUTED": False,
        "SEND_PERMITTED": send_permitted,
        "ADAPTER_SEND_PERMITTED": (
            bind.adapter.send_permitted is True if bind is not None else False
        ),
        "INNER_SEND_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "REAL_POST_COUNT": 0,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "DURABLE_CONSUMED": False,
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "EVALUATOR_IS_NOT_ISSUER": True,
        "ISSUED_IS_NOT_AUTHORIZED": True,
    }
