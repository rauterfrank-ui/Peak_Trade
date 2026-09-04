"""Bound LIVE_FILL_OBSERVED proof criterion.

Applies the current SSOT phrase "Current venue fill bound to the Peak_Trade
Live submit identity" onto GET /api/v5/trade/fills. Does not invent order-state
labels, position size, balance change, ACK, fee, or disappearance from pending
as fill proof. Partial and full remain distinct from LIVE_FILL_OBSERVED.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FILL_OBSERVED_PRODUCER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_SUBMITTED_SZ,
    exact_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)

ADMISSIBLE_SOURCE_KIND = "GOVERNED_CURRENT_PRIVATE_GET"
INJECTED_EVIDENCE_SOURCE_KIND = "GOVERNED_OFFLINE_CONTRACT"
FILL_PRODUCER = LIVE_FILL_OBSERVED_PRODUCER

FILL_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_SUBMIT_ACK_OBSERVED",
    "CURRENT_GOVERNED_PRIVATE_FILLS_GET",
    "FILLS_HTTP_CONJUNCTION_SATISFIED",
    "AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW",
    "ADMISSIBLE_PRIVATE_GET_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
)
FILL_FIELD_CONSTITUENT_COUNT = 6

FILLS_HTTP_CONSTITUENTS: tuple[str, ...] = (
    "JSON_PARSE_OK",
    "HTTP_STATUS_200",
    "NO_REDIRECT",
    "TOP_LEVEL_CODE_0",
    "METHOD_GET",
)
FILLS_HTTP_CONSTITUENT_COUNT = 5

FILL_ENDPOINT_PATH = "/api/v5/trade/fills"
ORDER_ENDPOINT_PATH = "/api/v5/trade/order"


def decimal_or_none_v1(value: object) -> Decimal | None:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def fills_http_constituents_from_evidence_v1(
    *,
    http_status: object,
    okx_code: object,
    json_parse_ok: object,
    redirect_followed: bool,
    method: object,
) -> dict[str, bool]:
    status_ok = False
    try:
        status_ok = int(http_status) == 200  # type: ignore[arg-type]
    except (TypeError, ValueError):
        status_ok = False
    return {
        "JSON_PARSE_OK": json_parse_ok is True,
        "HTTP_STATUS_200": status_ok,
        "NO_REDIRECT": redirect_followed is False,
        "TOP_LEVEL_CODE_0": str(okx_code or "") == "0",
        "METHOD_GET": str(method or "") == "GET",
    }


def evaluate_fills_http_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool],
) -> dict[str, Any]:
    missing = [name for name in FILLS_HTTP_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError("FILLS_HTTP_CONSTITUENT_MISSING:" + ",".join(missing))
    false_required = [
        name for name in FILLS_HTTP_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "adjudication": "FILLS_HTTP_CONJUNCTION_SATISFIED" if claim else "FILLS_HTTP_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": FILLS_HTTP_CONSTITUENT_COUNT,
        "false_required": false_required,
    }


def classify_identity_bound_fill_rows_v1(
    *,
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            unmatched.append({"reason": "ROW_NOT_OBJECT"})
            continue
        identity = exact_identity_match_v1(
            ord_id=item.get("ordId"),
            clordid=item.get("clOrdId"),
            inst_id=item.get("instId"),
        )
        fill_sz = str(item.get("fillSz") or "")
        fill_sz_present = bool(fill_sz)
        record = {
            "ordId": item.get("ordId"),
            "clOrdId": item.get("clOrdId"),
            "instId": item.get("instId"),
            "tradeId": item.get("tradeId"),
            "fillSz": item.get("fillSz"),
            "fillPx": item.get("fillPx"),
            "fillTime": item.get("fillTime") or item.get("ts"),
            "side": item.get("side"),
            "posSide": item.get("posSide"),
            "fee": item.get("fee"),
            "feeCcy": item.get("feeCcy"),
            "identity": identity,
            "FILLSZ_PRESENT_NONEMPTY": fill_sz_present,
        }
        if identity["ORDER_IDENTITY_MATCH"] is True and fill_sz_present:
            matched.append(record)
        else:
            unmatched.append(record)
    executed = Decimal("0")
    executed_parse_ok = True
    for record in matched:
        parsed = decimal_or_none_v1(record.get("fillSz"))
        if parsed is None:
            executed_parse_ok = False
            continue
        executed += parsed
    submitted = decimal_or_none_v1(BOUND_SUBMITTED_SZ)
    partial = False
    full = False
    qty_contradictory = False
    if matched and executed_parse_ok and submitted is not None:
        if executed == submitted:
            full = True
        elif Decimal("0") < executed < submitted:
            partial = True
        elif executed > submitted:
            qty_contradictory = True
        elif executed == Decimal("0"):
            executed_parse_ok = False
    return {
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "RAW_FILL_ROW_COUNT": len(rows),
        "IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW_COUNT": len(matched),
        "UNMATCHED_OR_INSUFFICIENT_ROW_COUNT": len(unmatched),
        "matched_rows": matched,
        "unmatched_or_insufficient_rows": unmatched,
        "RAW_FILL_IDENTIFIERS": [row.get("tradeId") for row in matched],
        "RAW_TRADE_IDENTIFIERS": [row.get("tradeId") for row in matched],
        "RAW_EXECUTED_QTY_IF_OBSERVED": str(executed) if matched and executed_parse_ok else None,
        "RAW_AVG_FILL_PRICE_IF_OBSERVED": None,
        "EXECUTED_QTY_PARSE_OK": executed_parse_ok if matched else None,
        "SUBMITTED_SZ": BOUND_SUBMITTED_SZ,
        "PARTIAL_FILL_OBSERVED": partial,
        "FULL_FILL_OBSERVED": full,
        "EXECUTED_QTY_CONTRADICTS_SUBMITTED_SZ": qty_contradictory,
        "AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW": bool(matched),
    }


def evaluate_live_fill_observed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    refuse_forbidden_live_source_v1(field_name="LIVE_FILL_OBSERVED", source_kind=source_kind)
    if str(source_kind or "").strip() != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    missing = [name for name in FILL_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError("FILL_FIELD_CONSTITUENT_MISSING:" + ",".join(missing))
    false_required = [
        name for name in FILL_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "canonical_definition": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
        "adjudication": "TRUE_LIVE_FILL_OBSERVED" if claim else "FALSE_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": FILL_FIELD_CONSTITUENT_COUNT,
        "false_required": false_required,
        "source_kind": source_kind,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
    }
