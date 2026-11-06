"""Typed productive-send success object for §11.14 durable consume.

Durable COMPLETED consume on the productive inner.send path may run only
after this object is minted. This module does not HTTP POST, does not
HMAC-sign, does not mint a receipt, and does not consume Owner Flatten-GO.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_gated_submit_v1 import (
    _venue_acceptance_from_response,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateReceiptV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpResponseV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
    FlattenDurableConsumeError,
    persist_flatten_durable_consume_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

CLASSIFICATION_VENUE_SUCCESS = "VENUE_SUCCESS"
MINT_SOURCE = "mint_flatten_productive_send_success_object_v1"
OUTCOME_VENUE_SUCCESS = "VENUE_SUCCESS"


class FlattenProductiveSendSuccessObjectError(RuntimeError):
    """Fail-closed success-object or success-gated consume violation."""


@dataclass(frozen=True)
class FlattenProductiveSendSuccessObjectV1:
    """Explicit venue-success evidence bound to envelope/request identity."""

    envelope_id: str
    origin_main_sha: str
    authority_id: str
    approved_request_identity: str
    http_status: int
    venue_code: str
    venue_s_code: str
    ord_id: str
    returned_cl_ord_id: str
    sent_cl_ord_id: str
    classification: str = CLASSIFICATION_VENUE_SUCCESS
    mint_source: str = MINT_SOURCE


def _nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def _norm_sha(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_venue_payload(response: LiveCanaryHttpResponseV1) -> dict[str, Any] | None:
    raw = response.body_bytes or b""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _data_row(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1:
        return None
    row = data[0]
    if not isinstance(row, dict):
        return None
    return row


def _assert_identity(
    *,
    actual: str,
    expected: str,
    missing_code: str,
    mismatch_code: str,
) -> None:
    actual_n = str(actual or "").strip()
    expected_n = str(expected or "").strip()
    if not expected_n:
        if not actual_n:
            raise FlattenProductiveSendSuccessObjectError(missing_code)
        return
    if actual_n != expected_n:
        raise FlattenProductiveSendSuccessObjectError(mismatch_code)


def mint_flatten_productive_send_success_object_v1(
    *,
    receipt: FlattenPreSendGateReceiptV1 | None,
    response: LiveCanaryHttpResponseV1 | None,
    envelope_id: str,
    origin_main_sha: str,
    authority_id: str = "",
    expected_envelope_id: str = "",
    expected_origin_main_sha: str = "",
    expected_authority_id: str = "",
    expected_request_identity: str = "",
    transport_error: str | None = None,
) -> FlattenProductiveSendSuccessObjectV1:
    """Mint a typed success object. Fail-closed. Does not consume. Does not POST."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveSendSuccessObjectError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if receipt is None or not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenProductiveSendSuccessObjectError("RECEIPT_MISSING")
    if receipt.allowed is not True:
        raise FlattenProductiveSendSuccessObjectError("RECEIPT_NOT_ALLOWED")
    request_identity = str(receipt.approved_request_identity or "").strip()
    if not request_identity:
        raise FlattenProductiveSendSuccessObjectError("RECEIPT_REQUEST_IDENTITY_MISSING")
    err = str(transport_error or "").strip()
    if err:
        raise FlattenProductiveSendSuccessObjectError("TRANSPORT_FAILURE")
    if response is None or not isinstance(response, LiveCanaryHttpResponseV1):
        raise FlattenProductiveSendSuccessObjectError("RESPONSE_MISSING")
    if bool(response.redirect_followed) is True:
        raise FlattenProductiveSendSuccessObjectError("REDIRECT_IS_NOT_SUCCESS")
    try:
        http_status = int(response.status_code)
    except (TypeError, ValueError) as exc:
        raise FlattenProductiveSendSuccessObjectError("MALFORMED_SUCCESS_PAYLOAD") from exc
    if http_status != 200:
        raise FlattenProductiveSendSuccessObjectError("HTTP_STATUS_NOT_200")
    payload = _parse_venue_payload(response)
    if payload is None:
        raise FlattenProductiveSendSuccessObjectError("MALFORMED_SUCCESS_PAYLOAD")
    venue_code = str(payload.get("code") or "")
    row = _data_row(payload)
    venue_s_code = ""
    if row is not None:
        venue_s_code = str(row.get("sCode") or row.get("s_code") or "")
    if _nonempty(venue_code) and venue_code != "0":
        raise FlattenProductiveSendSuccessObjectError("VENUE_REJECT")
    if row is not None and _nonempty(venue_s_code) and venue_s_code != "0":
        raise FlattenProductiveSendSuccessObjectError("VENUE_REJECT")
    if _venue_acceptance_from_response(response) is not True:
        raise FlattenProductiveSendSuccessObjectError("MALFORMED_SUCCESS_PAYLOAD")
    if row is None:
        raise FlattenProductiveSendSuccessObjectError("MALFORMED_SUCCESS_PAYLOAD")
    ord_id = str(row.get("ordId") or "").strip()
    if not ord_id:
        raise FlattenProductiveSendSuccessObjectError("ORD_ID_MISSING")
    sent_cl = str((receipt.request_body or {}).get("clOrdId") or "").strip()
    returned_cl = str(row.get("clOrdId") or "").strip()
    if sent_cl and returned_cl != sent_cl:
        raise FlattenProductiveSendSuccessObjectError("CLORDID_IDENTITY_MISMATCH")
    bound_envelope = str(envelope_id or "").strip()
    bound_sha = _norm_sha(origin_main_sha)
    bound_authority = str(authority_id or "").strip()
    _assert_identity(
        actual=bound_envelope,
        expected=str(expected_envelope_id or "").strip() or bound_envelope,
        missing_code="ENVELOPE_ID_MISSING",
        mismatch_code="ENVELOPE_IDENTITY_MISMATCH",
    )
    if not bound_envelope:
        raise FlattenProductiveSendSuccessObjectError("ENVELOPE_ID_MISSING")
    expected_sha = _norm_sha(expected_origin_main_sha) or bound_sha
    if not bound_sha:
        raise FlattenProductiveSendSuccessObjectError("ORIGIN_MAIN_SHA_MISSING")
    if bound_sha != expected_sha:
        raise FlattenProductiveSendSuccessObjectError("ORIGIN_MAIN_SHA_MISMATCH")
    expected_auth = str(expected_authority_id or "").strip()
    if expected_auth and bound_authority != expected_auth:
        raise FlattenProductiveSendSuccessObjectError("AUTHORITY_IDENTITY_MISMATCH")
    expected_req = str(expected_request_identity or "").strip()
    if expected_req and request_identity != expected_req:
        raise FlattenProductiveSendSuccessObjectError("REQUEST_IDENTITY_MISMATCH")
    return FlattenProductiveSendSuccessObjectV1(
        envelope_id=bound_envelope,
        origin_main_sha=bound_sha,
        authority_id=bound_authority,
        approved_request_identity=request_identity,
        http_status=http_status,
        venue_code="0",
        venue_s_code="0",
        ord_id=ord_id,
        returned_cl_ord_id=returned_cl,
        sent_cl_ord_id=sent_cl,
        classification=CLASSIFICATION_VENUE_SUCCESS,
        mint_source=MINT_SOURCE,
    )


def consume_flatten_durable_on_success_object_v1(
    *,
    store_root: Path | str,
    success: FlattenProductiveSendSuccessObjectV1,
    expected_envelope_id: str = "",
    expected_origin_main_sha: str = "",
    expected_authority_id: str = "",
) -> dict[str, Any]:
    """COMPLETED durable consume. Requires a minted success object. Exactly-once."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveSendSuccessObjectError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if not isinstance(success, FlattenProductiveSendSuccessObjectV1):
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_TYPE_INVALID")
    if success.mint_source != MINT_SOURCE:
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_MINT_SOURCE_INVALID")
    if success.classification != CLASSIFICATION_VENUE_SUCCESS:
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_NOT_VENUE_SUCCESS")
    if not _nonempty(success.envelope_id) or not _nonempty(success.origin_main_sha):
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_IDENTITY_MISSING")
    if not _nonempty(success.approved_request_identity) or not _nonempty(success.ord_id):
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_CORRELATION_MISSING")
    if int(success.http_status) != 200 or success.venue_code != "0" or success.venue_s_code != "0":
        raise FlattenProductiveSendSuccessObjectError("SUCCESS_OBJECT_NOT_VENUE_SUCCESS")
    expected_env = str(expected_envelope_id or "").strip()
    if expected_env and expected_env != success.envelope_id:
        raise FlattenProductiveSendSuccessObjectError("ENVELOPE_IDENTITY_MISMATCH")
    expected_sha = _norm_sha(expected_origin_main_sha)
    if expected_sha and expected_sha != success.origin_main_sha:
        raise FlattenProductiveSendSuccessObjectError("ORIGIN_MAIN_SHA_MISMATCH")
    expected_auth = str(expected_authority_id or "").strip()
    if expected_auth and expected_auth != success.authority_id:
        raise FlattenProductiveSendSuccessObjectError("AUTHORITY_IDENTITY_MISMATCH")
    try:
        return persist_flatten_durable_consume_v1(
            store_root=store_root,
            envelope_id=success.envelope_id,
            origin_main_sha=success.origin_main_sha,
            durable_state="COMPLETED",
            post_count=1,
            outcome=OUTCOME_VENUE_SUCCESS,
            raw_response={
                "code": success.venue_code,
                "sCode": success.venue_s_code,
                "ordId": success.ord_id,
            },
            authority_id=success.authority_id,
        )
    except FlattenDurableConsumeError:
        raise
