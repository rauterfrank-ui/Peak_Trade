"""Canonical LIVE_SUBMIT_ACK_OBSERVED proof criterion.

This module is the unique §11.14 producer of the ACK *criterion*. It does not
POST. It does not set the standing ladder field true. Injected or fixture
evidence may satisfy the synchronous response conjunction without promoting
LIVE_SUBMIT_ACK_OBSERVED.

Explicit Owner-GO adjudication (not silent import):
- HTTP 200, top-level code=0, parseable JSON, and no redirect are adopted from
  the productive `_entry_submit_returned_payload_v1` transport-ok surface.
  Transport ok remains insufficient by itself.
- Exactly one data row and sCode=0 are adopted from the productive OKX order
  data-entry extractor plus this Owner-GO. Flatten's helper is supporting
  context, not SSOT.
- Nonempty ordId is adopted from this Owner-GO as the venue order identity
  required before LIVE_FILL_OBSERVED. Cap 11.12.8 is semantically different
  and is not the producer.
- Returned clOrdId must be nonempty and equal the sent clOrdId. Identity
  mismatch is UNKNOWN, not ACK and not REJECT.
- Read-only recon by clOrdId may resolve order existence after UNKNOWN. It
  does not reclassify the original submit response as an observed ACK.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_LIVE_SOURCE_KINDS,
    LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

ACK_RESPONSE_CONSTITUENTS: tuple[str, ...] = (
    "JSON_PARSE_OK",
    "HTTP_STATUS_200",
    "NO_REDIRECT",
    "TOP_LEVEL_CODE_0",
    "EXACTLY_ONE_DATA_ROW",
    "SCODE_0",
    "NONEMPTY_ORDID",
    "NONEMPTY_RETURNED_CLORDID",
    "RETURNED_CLORDID_EQUALS_SENT",
)
ACK_RESPONSE_CONSTITUENT_COUNT = 9
ACK_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_ORDER_PLAN_OBSERVED",
    "CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN",
    "SYNCHRONOUS_RESPONSE_CRITERION_SATISFIED",
    "ADMISSIBLE_LIVE_POST_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
)
ACK_FIELD_CONSTITUENT_COUNT = 5
ADMISSIBLE_SOURCE_KIND = "GOVERNED_CURRENT_LIVE_POST"
INJECTED_EVIDENCE_SOURCE_KIND = "INJECTED_OFFLINE_EVIDENCE"

CLASS_ACK_SUCCESS = "ACK_SUCCESS"
CLASS_EXPLICIT_REJECT = "EXPLICIT_REJECT"
CLASS_UNKNOWN = "UNKNOWN"


def _nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def classify_submit_response_v1(
    *,
    send_attempted: bool,
    entry_submit_count: int,
    http_status: int | None = None,
    okx_code: str | None = None,
    json_parse_ok: bool | None = None,
    redirect_followed: bool = False,
    redirectish: bool = False,
    data_count: int | None = None,
    s_code: str | None = None,
    ord_id: str | None = None,
    returned_clordid: str | None = None,
    sent_clordid: str | None = None,
    transport_error: str | None = None,
) -> dict[str, Any]:
    """Classify a synchronous submit response. Never promotes the ladder field."""

    err = str(transport_error or "")
    parsed = json_parse_ok is True
    code = str(okx_code) if okx_code is not None else ""
    scode = str(s_code) if s_code is not None else ""
    returned = str(returned_clordid or "").strip()
    sent = str(sent_clordid or "").strip()
    redirect = bool(redirect_followed) or bool(redirectish)

    if not send_attempted:
        classification = CLASS_UNKNOWN
        reason = "REQUEST_NOT_SENT_OR_LOCAL_ERROR_BEFORE_WIRE"
    elif "TIMEOUT" in err:
        classification = CLASS_UNKNOWN
        reason = "TIMEOUT_AFTER_POSSIBLE_SEND"
    elif "NETWORK" in err or "URLError" in err or "OSError" in err:
        classification = CLASS_UNKNOWN
        reason = "CONNECTION_FAILURE_AFTER_SEND_ATTEMPTED"
    elif redirect:
        classification = CLASS_UNKNOWN
        reason = "REDIRECT_IS_UNKNOWN_NOT_ACK"
    elif json_parse_ok is False:
        classification = CLASS_UNKNOWN
        reason = "PARSE_FAILURE"
    elif parsed and _nonempty(code) and code != "0":
        classification = CLASS_EXPLICIT_REJECT
        reason = "TOP_LEVEL_CODE_NOT_ZERO"
    elif parsed and code == "0" and data_count == 1 and _nonempty(scode) and scode != "0":
        classification = CLASS_EXPLICIT_REJECT
        reason = "SCODE_NOT_ZERO"
    elif http_status is not None and int(http_status) != 200:
        classification = CLASS_UNKNOWN
        reason = "HTTP_STATUS_NOT_200"
    elif not parsed:
        classification = CLASS_UNKNOWN
        reason = "RESPONSE_NOT_PARSEABLE"
    elif code != "0":
        classification = CLASS_UNKNOWN
        reason = "TOP_LEVEL_CODE_MISSING_OR_UNCLEAR"
    elif data_count != 1:
        classification = CLASS_UNKNOWN
        reason = "DATA_CARDINALITY_NOT_EXACTLY_ONE"
    elif scode != "0":
        classification = CLASS_UNKNOWN
        reason = "SCODE_MISSING_OR_UNCLEAR"
    elif not _nonempty(ord_id):
        classification = CLASS_UNKNOWN
        reason = "ORDID_MISSING"
    elif not _nonempty(returned):
        classification = CLASS_UNKNOWN
        reason = "RETURNED_CLORDID_MISSING"
    elif not _nonempty(sent) or returned != sent:
        classification = CLASS_UNKNOWN
        reason = "CLORDID_IDENTITY_MISMATCH"
    elif int(entry_submit_count) != 1:
        classification = CLASS_UNKNOWN
        reason = "SUBMIT_COUNT_NOT_ONE"
    else:
        classification = CLASS_ACK_SUCCESS
        reason = "SYNCHRONOUS_ACK_CRITERION_SATISFIED"

    return {
        "classification": classification,
        "reason": reason,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "RETRY_ALLOWED": False,
        "SECOND_SUBMIT_ALLOWED": False,
        "SEND_ATTEMPTED": bool(send_attempted),
        "ENTRY_SUBMIT_COUNT": int(entry_submit_count),
        "recon_may_resolve_existence_without_reclassifying_ack": classification == CLASS_UNKNOWN,
        "unknown_recon_is_not_live_submit_ack_observed": True,
    }


def evaluate_ack_response_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
) -> dict[str, Any]:
    missing = [name for name in ACK_RESPONSE_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "ACK_RESPONSE_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    false_required = [
        name for name in ACK_RESPONSE_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    satisfied = len(false_required) == 0
    return {
        "claim_value": satisfied,
        "false_required": false_required,
        "constituent_count": ACK_RESPONSE_CONSTITUENT_COUNT,
        "adjudication": (
            "SYNCHRONOUS_ACK_CRITERION_SATISFIED"
            if satisfied
            else "SYNCHRONOUS_ACK_CRITERION_FALSE"
        ),
    }


def evaluate_live_submit_ack_observed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(
            f"FORBIDDEN_LIVE_SOURCE:{kind}:LIVE_SUBMIT_ACK_OBSERVED"
        )
    if kind == INJECTED_EVIDENCE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    if kind != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError(f"INADMISSIBLE_SOURCE_KIND:{kind}")
    missing = [name for name in ACK_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError("ACK_FIELD_CONSTITUENT_MISSING:" + ",".join(missing))
    false_required = [
        name for name in ACK_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = len(false_required) == 0
    return {
        "canonical_definition": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION,
        "claim_value": claim,
        "adjudication": "TRUE_LIVE_SUBMIT_ACK_OBSERVED" if claim else "FALSE_FAIL_CLOSED",
        "false_required": false_required,
        "constituent_count": ACK_FIELD_CONSTITUENT_COUNT,
        "source_kind": kind,
    }


def response_constituents_from_evidence_v1(
    *,
    http_status: int | None,
    okx_code: str | None,
    json_parse_ok: bool | None,
    redirect_followed: bool,
    redirectish: bool,
    data_count: int | None,
    s_code: str | None,
    ord_id: str | None,
    returned_clordid: str | None,
    sent_clordid: str | None,
) -> dict[str, bool]:
    returned = str(returned_clordid or "").strip()
    sent = str(sent_clordid or "").strip()
    return {
        "JSON_PARSE_OK": json_parse_ok is True,
        "HTTP_STATUS_200": http_status == 200,
        "NO_REDIRECT": (not redirect_followed) and (not redirectish),
        "TOP_LEVEL_CODE_0": str(okx_code or "") == "0",
        "EXACTLY_ONE_DATA_ROW": data_count == 1,
        "SCODE_0": str(s_code or "") == "0",
        "NONEMPTY_ORDID": _nonempty(ord_id),
        "NONEMPTY_RETURNED_CLORDID": _nonempty(returned),
        "RETURNED_CLORDID_EQUALS_SENT": bool(returned) and bool(sent) and returned == sent,
    }
