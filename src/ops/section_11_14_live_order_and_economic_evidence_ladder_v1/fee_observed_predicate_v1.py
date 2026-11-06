"""Bound LIVE_FEE_OBSERVED proof criterion.

Applies the SSOT phrase "Current venue fee bound to the observed Live
fill/submit identity" onto GET /api/v5/trade/fills. Does not invent fee from
a static rate, fillPx times fillSz, fillPnl, historical fills, order-state,
position, or balance. Missing, empty, unparseable, or schema-ambiguous fee
fails closed. LIVE_POSITION_RECONCILED remains false.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FEE_OBSERVED_PRODUCER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    exact_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    decimal_or_none_v1,
    evaluate_fills_http_conjunction_v1,
    fills_http_constituents_from_evidence_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)

ADMISSIBLE_SOURCE_KIND = "GOVERNED_CURRENT_PRIVATE_GET"
INJECTED_EVIDENCE_SOURCE_KIND = "GOVERNED_OFFLINE_CONTRACT"
FEE_PRODUCER = LIVE_FEE_OBSERVED_PRODUCER
ADMISSIBLE_FEE_FIELD = "fee"
ADMISSIBLE_FEE_CCY_FIELD = "feeCcy"
COMPETING_FEE_AMOUNT_FIELDS = frozenset({"fillFee", "tradeFee", "feeAmt", "feeAmount", "fees"})
COMPETING_FEE_CCY_FIELDS = frozenset({"fillFeeCcy", "feeCurrency", "feeCcyAlt"})

FEE_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_FILL_OBSERVED",
    "CURRENT_GOVERNED_PRIVATE_FILLS_GET",
    "FILLS_HTTP_CONJUNCTION_SATISFIED",
    "AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW",
    "IDENTITY_BOUND_ACTUAL_FEE_PRESENT_PARSEABLE",
    "FEE_CCY_PRESENT_NONEMPTY",
    "NO_FEE_SCHEMA_AMBIGUITY",
    "ADMISSIBLE_PRIVATE_GET_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
    "FEE_NOT_INFERRED",
)
FEE_FIELD_CONSTITUENT_COUNT = 10


def _raw_field_present_nonempty_v1(row: Mapping[str, Any], field_name: str) -> bool:
    if field_name not in row:
        return False
    value = row.get(field_name)
    if value is None:
        return False
    return bool(str(value).strip())


def classify_identity_bound_fee_rows_v1(
    *,
    rows: list[Mapping[str, Any]],
    order_row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    schema_reasons: list[str] = []
    for item in rows:
        if not isinstance(item, Mapping):
            unmatched.append({"reason": "ROW_NOT_OBJECT"})
            continue
        identity = exact_identity_match_v1(
            ord_id=item.get("ordId"),
            clordid=item.get("clOrdId"),
            inst_id=item.get("instId"),
        )
        fee_present = _raw_field_present_nonempty_v1(item, ADMISSIBLE_FEE_FIELD)
        fee_raw = item.get(ADMISSIBLE_FEE_FIELD) if ADMISSIBLE_FEE_FIELD in item else None
        fee_parsed = decimal_or_none_v1(fee_raw) if fee_present else None
        fee_ccy_present = _raw_field_present_nonempty_v1(item, ADMISSIBLE_FEE_CCY_FIELD)
        competing_amount: dict[str, object] = {}
        competing_ccy: dict[str, object] = {}
        for key in COMPETING_FEE_AMOUNT_FIELDS:
            if _raw_field_present_nonempty_v1(item, key):
                competing_amount[key] = item.get(key)
        for key in COMPETING_FEE_CCY_FIELDS:
            if _raw_field_present_nonempty_v1(item, key):
                competing_ccy[key] = item.get(key)
        row_ambiguous = False
        if competing_amount:
            for key, raw in competing_amount.items():
                parsed = decimal_or_none_v1(raw)
                if fee_parsed is None or parsed is None or parsed != fee_parsed:
                    row_ambiguous = True
                    schema_reasons.append(f"COMPETING_FEE_AMOUNT_FIELD:{key}")
        if competing_ccy:
            fee_ccy_raw = str(item.get(ADMISSIBLE_FEE_CCY_FIELD) or "").strip()
            for key, raw in competing_ccy.items():
                if str(raw).strip() != fee_ccy_raw:
                    row_ambiguous = True
                    schema_reasons.append(f"COMPETING_FEE_CCY_FIELD:{key}")
        record = {
            "ordId": item.get("ordId"),
            "clOrdId": item.get("clOrdId"),
            "instId": item.get("instId"),
            "tradeId": item.get("tradeId"),
            "fillSz": item.get("fillSz"),
            "fillPx": item.get("fillPx"),
            "fee": fee_raw,
            "feeCcy": item.get(ADMISSIBLE_FEE_CCY_FIELD)
            if ADMISSIBLE_FEE_CCY_FIELD in item
            else None,
            "identity": identity,
            "FEE_FIELD_PRESENT_NONEMPTY": fee_present,
            "FEE_PARSEABLE": fee_parsed is not None,
            "FEE_CCY_PRESENT_NONEMPTY": fee_ccy_present,
            "ROW_SCHEMA_AMBIGUOUS": row_ambiguous,
            "COMPETING_FEE_AMOUNT_FIELDS": competing_amount,
            "COMPETING_FEE_CCY_FIELDS": competing_ccy,
        }
        if identity["ORDER_IDENTITY_MATCH"] is True:
            matched.append(record)
        else:
            unmatched.append(record)

    missing_fee = False
    unparseable = False
    missing_ccy = False
    for record in matched:
        if record["FEE_FIELD_PRESENT_NONEMPTY"] is not True:
            missing_fee = True
        elif record["FEE_PARSEABLE"] is not True:
            unparseable = True
        if record["FEE_CCY_PRESENT_NONEMPTY"] is not True:
            missing_ccy = True

    fee_ccy_values = {
        str(record.get("feeCcy") or "").strip()
        for record in matched
        if record["FEE_CCY_PRESENT_NONEMPTY"] is True
    }
    if len(fee_ccy_values) > 1:
        schema_reasons.append("IDENTITY_BOUND_ROWS_CONFLICTING_FEE_CCY")

    order_fee_conflict = False
    order_fee_raw = None
    order_fee_ccy = None
    if isinstance(order_row, Mapping) and order_row:
        order_identity = exact_identity_match_v1(
            ord_id=order_row.get("ordId"),
            clordid=order_row.get("clOrdId"),
            inst_id=order_row.get("instId"),
        )
        if order_identity["ORDER_IDENTITY_MATCH"] is True:
            order_fee_raw = (
                order_row.get(ADMISSIBLE_FEE_FIELD) if ADMISSIBLE_FEE_FIELD in order_row else None
            )
            order_fee_ccy = (
                order_row.get(ADMISSIBLE_FEE_CCY_FIELD)
                if ADMISSIBLE_FEE_CCY_FIELD in order_row
                else None
            )
            order_fee_parsed = (
                decimal_or_none_v1(order_fee_raw) if order_fee_raw not in (None, "") else None
            )
            if order_fee_parsed is not None and len(matched) == 1:
                fill_parsed = decimal_or_none_v1(matched[0].get("fee"))
                if fill_parsed is not None and fill_parsed != order_fee_parsed:
                    order_fee_conflict = True
                    schema_reasons.append("ORDER_FEE_CONTRADICTS_FILL_FEE")
            if (
                order_fee_ccy not in (None, "")
                and len(matched) == 1
                and matched[0]["FEE_CCY_PRESENT_NONEMPTY"] is True
                and str(order_fee_ccy).strip() != str(matched[0].get("feeCcy") or "").strip()
            ):
                order_fee_conflict = True
                schema_reasons.append("ORDER_FEE_CCY_CONTRADICTS_FILL_FEE_CCY")

    schema_ambiguous = bool(schema_reasons) or any(
        record["ROW_SCHEMA_AMBIGUOUS"] is True for record in matched
    )
    actual_fee_ok = bool(
        matched
        and not missing_fee
        and not unparseable
        and not missing_ccy
        and not schema_ambiguous
        and not order_fee_conflict
    )
    raw_fees = [record.get("fee") for record in matched] if matched else []
    raw_ccys = [record.get("feeCcy") for record in matched] if matched else []
    return {
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "RAW_FILL_ROW_COUNT": len(rows),
        "IDENTITY_BOUND_FILL_ROW_COUNT": len(matched),
        "UNMATCHED_ROW_COUNT": len(unmatched),
        "matched_rows": matched,
        "unmatched_rows": unmatched,
        "AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW": bool(matched),
        "IDENTITY_BOUND_ACTUAL_FEE_PRESENT_PARSEABLE": bool(
            matched and not missing_fee and not unparseable
        ),
        "FEE_CCY_PRESENT_NONEMPTY": bool(matched and not missing_ccy),
        "NO_FEE_SCHEMA_AMBIGUITY": bool(
            matched and not schema_ambiguous and not order_fee_conflict
        ),
        "FEE_FIELD_MISSING_OR_EMPTY": missing_fee,
        "FEE_UNPARSEABLE": unparseable,
        "FEE_CCY_MISSING_OR_EMPTY": missing_ccy,
        "SCHEMA_AMBIGUITY_REASONS": schema_reasons,
        "ORDER_FEE_CONFLICT": order_fee_conflict,
        "RAW_FEE_IF_OBSERVED": raw_fees[0] if actual_fee_ok and len(raw_fees) == 1 else None,
        "RAW_FEE_CCY_IF_OBSERVED": raw_ccys[0] if actual_fee_ok and len(raw_ccys) == 1 else None,
        "RAW_FEES_IF_OBSERVED": raw_fees if actual_fee_ok else None,
        "RAW_FEE_CCYS_IF_OBSERVED": raw_ccys if actual_fee_ok else None,
        "FEE_SUM_COMPUTED": False,
        "FEE_INFERRED_FROM_RATE": False,
        "FEE_INFERRED_FROM_PRICE_TIMES_QTY": False,
        "ORDER_FEE_IF_PRESENT": order_fee_raw,
        "ORDER_FEE_CCY_IF_PRESENT": order_fee_ccy,
        "ACTUAL_FEE_OBSERVED": actual_fee_ok,
    }


def evaluate_live_fee_observed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    refuse_forbidden_live_source_v1(field_name="LIVE_FEE_OBSERVED", source_kind=source_kind)
    if str(source_kind or "").strip() != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    missing = [name for name in FEE_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError("FEE_FIELD_CONSTITUENT_MISSING:" + ",".join(missing))
    false_required = [
        name for name in FEE_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "canonical_definition": LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
        "adjudication": "TRUE_LIVE_FEE_OBSERVED" if claim else "FALSE_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": FEE_FIELD_CONSTITUENT_COUNT,
        "false_required": false_required,
        "source_kind": source_kind,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
    }


def refuse_inferred_fee_v1(*, fill_px: object, fill_sz: object, proposed_fee: object) -> None:
    """Fail closed if a caller tries to treat price*qty as the venue fee."""

    px = decimal_or_none_v1(fill_px)
    sz = decimal_or_none_v1(fill_sz)
    fee = decimal_or_none_v1(proposed_fee)
    if px is None or sz is None or fee is None:
        return
    product = px * sz
    if product == fee:
        raise Section1114OfflineSurfaceError("FEE_INFERRED_FROM_PRICE_TIMES_QTY")
    try:
        _ = Decimal(str(proposed_fee))
    except (InvalidOperation, ValueError):
        return
