"""§11.14 RECEIPT_MISSING: attachable pre-send receipt mint.

Offline attest. Reuses evaluate_flatten_pre_send_gate_v1 and
AuthenticatedGatedProductiveFlattenTransportV1.attach_pre_send_receipt.
Does not HMAC-sign. Does not generate OK-ACCESS headers. Does not HTTP
POST. Does not GET. Does not issue or consume wire-send or network-session
authority. Does not mutate standing Live flags.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    FlattenPreSendGateReceiptV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    LiveCanaryFlattenProductiveTransportError,
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

MINT_SOURCE = "mint_flatten_pre_send_attachable_receipt_v1"
FIRST_DENY_AFTER_ATTACHED_RECEIPT = "UNSIGNED_PRODUCTIVE_HEADERS"


class FlattenPreSendReceiptMissingError(RuntimeError):
    """Fail-closed RECEIPT_MISSING mint/attach violation."""


def _require_standing_live_flags_false() -> None:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenPreSendReceiptMissingError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")


def _norm_sha(value: Any) -> str:
    return str(value or "").strip().lower()


def mint_flatten_pre_send_attachable_receipt_v1(
    gate: FlattenPreSendGateInputV1 | None,
    *,
    expected_origin_main_sha: str = "",
) -> FlattenPreSendGateReceiptV1:
    """Mint an attachable allowed receipt. Offline. Fail-closed. No POST."""
    _require_standing_live_flags_false()
    if gate is None:
        raise FlattenPreSendReceiptMissingError("GATE_INPUT_MISSING")
    if not isinstance(gate, FlattenPreSendGateInputV1):
        raise FlattenPreSendReceiptMissingError("GATE_INPUT_TYPE_INVALID")
    expected_sha = _norm_sha(expected_origin_main_sha)
    actual_sha = _norm_sha(gate.origin_main_sha)
    if expected_sha:
        if not actual_sha:
            raise FlattenPreSendReceiptMissingError("ORIGIN_MAIN_SHA_MISSING")
        if actual_sha != expected_sha:
            raise FlattenPreSendReceiptMissingError("ORIGIN_MAIN_SHA_MISMATCH")
    receipt = evaluate_flatten_pre_send_gate_v1(gate)
    if not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenPreSendReceiptMissingError("RECEIPT_MISSING")
    if receipt.allowed is not True:
        raise FlattenPreSendReceiptMissingError("RECEIPT_NOT_ALLOWED")
    if not str(receipt.approved_request_identity or "").strip():
        raise FlattenPreSendReceiptMissingError("RECEIPT_REQUEST_IDENTITY_MISSING")
    if not isinstance(receipt.request_body, dict) or not receipt.request_body:
        raise FlattenPreSendReceiptMissingError("RECEIPT_REQUEST_IDENTITY_MISSING")
    if not str(receipt.approved_body_text or "").strip():
        raise FlattenPreSendReceiptMissingError("RECEIPT_REQUEST_IDENTITY_MISSING")
    if receipt.send_lease.consumed is True:
        raise FlattenPreSendReceiptMissingError("RECEIPT_LEASE_ALREADY_CONSUMED")
    return receipt


def attach_flatten_pre_send_receipt_once_v1(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
    receipt: FlattenPreSendGateReceiptV1 | None,
) -> FlattenPreSendGateReceiptV1:
    """Attach exactly once. Duplicate attach does not rewrite. No HMAC. No POST."""
    _require_standing_live_flags_false()
    if not isinstance(transport, AuthenticatedGatedProductiveFlattenTransportV1):
        raise FlattenPreSendReceiptMissingError("TRANSPORT_TYPE_INVALID")
    if receipt is None or not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenPreSendReceiptMissingError("RECEIPT_MISSING")
    if receipt.allowed is not True:
        raise FlattenPreSendReceiptMissingError("RECEIPT_NOT_ALLOWED")
    if receipt.send_lease.consumed is True:
        raise FlattenPreSendReceiptMissingError("RECEIPT_LEASE_ALREADY_CONSUMED")
    existing = getattr(transport, "_receipt", None)
    if existing is not None:
        raise FlattenPreSendReceiptMissingError("RECEIPT_ALREADY_ATTACHED_NO_REWRITE")
    try:
        transport.attach_pre_send_receipt(receipt)
    except LiveCanaryFlattenProductiveTransportError as exc:
        raise FlattenPreSendReceiptMissingError(str(exc)) from exc
    attached = getattr(transport, "_receipt", None)
    if attached is not receipt:
        raise FlattenPreSendReceiptMissingError("RECEIPT_ATTACH_FAILED")
    return receipt


def first_deny_after_attached_unsigned_send_v1(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
    receipt: FlattenPreSendGateReceiptV1,
    request: LiveCanaryHttpRequestV1 | None = None,
) -> str:
    """Send the unsigned receipt request. Must stop before HMAC, lease, urllib."""
    _require_standing_live_flags_false()
    if not isinstance(transport, AuthenticatedGatedProductiveFlattenTransportV1):
        raise FlattenPreSendReceiptMissingError("TRANSPORT_TYPE_INVALID")
    if receipt is None or not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenPreSendReceiptMissingError("RECEIPT_MISSING")
    if getattr(transport, "_receipt", None) is not receipt:
        raise FlattenPreSendReceiptMissingError("RECEIPT_NOT_ATTACHED")
    unsigned = request or live_canary_http_request_from_flatten_receipt_v1(receipt)
    if any(str(name).upper().startswith("OK-ACCESS-") for name in (unsigned.headers or {})):
        raise FlattenPreSendReceiptMissingError("HMAC_HEADERS_FORBIDDEN_IN_THIS_SLICE")
    try:
        transport.send(unsigned)
    except LiveCanaryFlattenProductiveTransportError as exc:
        deny = str(exc)
        if receipt.send_lease.consumed is True:
            raise FlattenPreSendReceiptMissingError("LEASE_CONSUMED_ON_PRE_HMAC_DENY") from exc
        if transport.last_wire_attempted is True or getattr(transport, "_sent", False) is True:
            raise FlattenPreSendReceiptMissingError("WIRE_ATTEMPTED_ON_PRE_HMAC_DENY") from exc
        if deny == "RECEIPT_MISSING":
            raise FlattenPreSendReceiptMissingError("RECEIPT_MISSING_AFTER_ATTACH") from exc
        return deny
    raise FlattenPreSendReceiptMissingError("SEND_SUCCEEDED_WITHOUT_HMAC_OR_POST_AUTHORITY")
