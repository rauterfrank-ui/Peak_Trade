"""HMAC-signed productive send path: Owner network-session bind seam.

Wires OWNER_NETWORK_SESSION_AUTHORITY_V1 onto the exact
AuthenticatedGatedProductiveFlattenTransportV1 used after HMAC. Reuses
verify_owner_network_session_authority_v1 and
authorize_network_session_instance_v1. Does not GET. Does not POST.
Does not consume the session artifact, wire-send authority, or send lease.
Does not invoke urllib. HMAC_PRESENT, receipt.allowed, LIVE_* flags, and
a bare network_session_authorized boolean cannot substitute.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateReceiptV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_generation_v1 import (
    AuthenticatedProductiveFlattenHeadersV1,
    first_deny_after_hmac_signed_send_v1,
    hmac_signed_request_from_artifact_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_instance_authorization_v1 import (
    authorize_network_session_instance_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_send_capable_v1 import (
    prepare_productive_transport_bind_send_capable_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

BIND_ATTR = "_hmac_signed_network_session_bind_v1"
PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED = "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
NEXT_GATE_AFTER_BIND = "SEND_LEASE_CONSUME"
CANONICAL_REST_HOST = REUSED_BINDING_REST_HOST


class FlattenHmacSignedNetworkSessionBindError(RuntimeError):
    """Fail-closed HMAC-signed network-session bind violation."""


def _require_standing_live_flags_false() -> None:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenHmacSignedNetworkSessionBindError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")


def _deny(**extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "bound": False,
        "authorized": False,
        "reasons": [],
        "first_deny": PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED,
        "send_invoked": False,
        "lease_consumed": False,
        "wire_send_consumed": False,
        "network_session_consumed": False,
        "WIRE_SEND_EXECUTED": False,
        "REAL_GET_COUNT": 0,
        "REAL_POST_COUNT": 0,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "HMAC_PRESENT_IS_NOT_SESSION_AUTHORITY": True,
        "RECEIPT_ALLOWED_IS_NOT_SESSION_AUTHORITY": True,
        "LIVE_FLAGS_ARE_NOT_SESSION_AUTHORITY": True,
        "SESSION_FLAG_IS_NOT_OWNER_AUTHORITY": True,
        "NEXT_GATE_AFTER_BIND": NEXT_GATE_AFTER_BIND,
    }
    payload.update(extra)
    return payload


def _bind_record(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
) -> dict[str, Any] | None:
    record = getattr(transport, BIND_ATTR, None)
    if isinstance(record, dict) and record.get("bound") is True:
        return record
    return None


def bind_hmac_signed_productive_network_session_v1(
    *,
    transport: AuthenticatedGatedProductiveFlattenTransportV1 | None,
    receipt: FlattenPreSendGateReceiptV1 | None,
    artifact: AuthenticatedProductiveFlattenHeadersV1 | None,
    network_session: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> dict[str, Any]:
    """Bind Owner network-session authority to the HMAC transport. No I/O."""
    _require_standing_live_flags_false()
    if not isinstance(transport, AuthenticatedGatedProductiveFlattenTransportV1):
        return _deny(reasons=["TRANSPORT_TYPE_INVALID"], first_deny="TRANSPORT_TYPE_INVALID")
    if receipt is None or not isinstance(receipt, FlattenPreSendGateReceiptV1):
        return _deny(reasons=["RECEIPT_MISSING"], first_deny="RECEIPT_MISSING")
    if artifact is None or not isinstance(artifact, AuthenticatedProductiveFlattenHeadersV1):
        return _deny(
            reasons=["HMAC_ARTIFACT_TYPE_INVALID"], first_deny="HMAC_ARTIFACT_TYPE_INVALID"
        )
    if getattr(transport, "_receipt", None) is not receipt:
        return _deny(reasons=["RECEIPT_NOT_ATTACHED"], first_deny="RECEIPT_NOT_ATTACHED")
    if receipt.allowed is not True:
        return _deny(reasons=["RECEIPT_NOT_ALLOWED"], first_deny="RECEIPT_NOT_ALLOWED")
    if receipt.send_lease.consumed is True:
        return _deny(
            reasons=["RECEIPT_LEASE_ALREADY_CONSUMED"],
            first_deny="RECEIPT_LEASE_ALREADY_CONSUMED",
        )
    if artifact.request_identity != receipt.approved_request_identity:
        return _deny(
            reasons=["HMAC_NETWORK_SESSION_REQUEST_IDENTITY_MISMATCH"],
            first_deny="HMAC_NETWORK_SESSION_REQUEST_IDENTITY_MISMATCH",
        )
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    host = str(receipt.approved_host or "").strip()
    signed_host = str(signed.host or "").strip()
    if host != CANONICAL_REST_HOST or signed_host != CANONICAL_REST_HOST:
        return _deny(
            reasons=["HMAC_NETWORK_SESSION_HOST_MISMATCH"],
            first_deny="HMAC_NETWORK_SESSION_HOST_MISMATCH",
        )
    if _bind_record(transport) is not None:
        return _deny(
            reasons=["HMAC_NETWORK_SESSION_ALREADY_BOUND"],
            first_deny="HMAC_NETWORK_SESSION_ALREADY_BOUND",
            network_session_consumed=False,
        )
    if transport.network_session_authorized is True:
        return _deny(
            reasons=["PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"],
            first_deny=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED,
        )
    bind = prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
        wire_send=None,
        network_session=network_session,
        inner=transport,
    )
    instance = authorize_network_session_instance_v1(
        bind=bind,
        network_session=network_session,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    reasons = [str(item) for item in (instance.get("reasons") or [])]
    consumed = False if network_session is None else network_session.get("consumed") is True
    if instance.get("authorized") is not True or reasons:
        if not reasons:
            reasons.append(PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED)
        return _deny(
            reasons=reasons,
            first_deny=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED,
            network_session_consumed=consumed,
            NETWORK_SESSION_AUTHORITY_ACCEPTED=instance.get("NETWORK_SESSION_AUTHORITY_ACCEPTED"),
        )
    record = {
        "bound": True,
        "authority_id": str((network_session or {}).get("authority_id") or ""),
        "request_identity": str(receipt.approved_request_identity),
        "host": CANONICAL_REST_HOST,
        "origin_main_sha": str(origin_main_sha).strip().lower(),
        "instrument_id": str(instrument_id),
        "exact_envelope_id": str(exact_envelope_id),
        "consumed": False,
    }
    setattr(transport, BIND_ATTR, record)
    return {
        "bound": True,
        "authorized": True,
        "reasons": [],
        "first_deny": None,
        "send_invoked": False,
        "lease_consumed": False,
        "wire_send_consumed": False,
        "network_session_consumed": False,
        "NETWORK_SESSION_AUTHORIZED": transport.network_session_authorized is True,
        "NETWORK_SESSION_AUTHORITY_ACCEPTED": True,
        "HOST": CANONICAL_REST_HOST,
        "PROXY_FALLBACK": False,
        "WIRE_SEND_EXECUTED": False,
        "REAL_GET_COUNT": 0,
        "REAL_POST_COUNT": 0,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "HMAC_PRESENT_IS_NOT_SESSION_AUTHORITY": True,
        "RECEIPT_ALLOWED_IS_NOT_SESSION_AUTHORITY": True,
        "LIVE_FLAGS_ARE_NOT_SESSION_AUTHORITY": True,
        "SESSION_FLAG_IS_NOT_OWNER_AUTHORITY": True,
        "NEXT_GATE_AFTER_BIND": NEXT_GATE_AFTER_BIND,
        "authority_id": record["authority_id"],
    }


def hmac_signed_send_network_session_gate_v1(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
    receipt: FlattenPreSendGateReceiptV1,
    artifact: AuthenticatedProductiveFlattenHeadersV1,
) -> dict[str, Any]:
    """HMAC-signed send gate. Bound session does not invoke send or urllib."""
    _require_standing_live_flags_false()
    record = _bind_record(transport)
    flag = transport.network_session_authorized is True
    if flag is True and record is None:
        return _deny(
            reasons=["PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"],
            first_deny=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED,
        )
    if record is None:
        deny = first_deny_after_hmac_signed_send_v1(transport, receipt, artifact)
        return _deny(
            reasons=[deny],
            first_deny=deny,
            send_invoked=True,
            lease_consumed=receipt.send_lease.consumed is True,
        )
    return {
        "bound": True,
        "authorized": True,
        "reasons": [],
        "first_deny": None,
        "send_invoked": False,
        "lease_consumed": receipt.send_lease.consumed is True,
        "wire_send_consumed": False,
        "network_session_consumed": False,
        "NETWORK_SESSION_AUTHORIZED": True,
        "WIRE_SEND_EXECUTED": False,
        "REAL_GET_COUNT": 0,
        "REAL_POST_COUNT": 0,
        "NEXT_GATE_AFTER_BIND": NEXT_GATE_AFTER_BIND,
        "EVALUATOR_IS_NOT_ISSUER": True,
    }
