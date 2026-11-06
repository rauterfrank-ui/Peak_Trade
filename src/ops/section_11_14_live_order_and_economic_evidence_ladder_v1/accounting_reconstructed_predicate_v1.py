"""Bound LIVE_ACCOUNTING_RECONSTRUCTED proof criterion.

Applies the SSOT phrase "Current Live accounting reconstructed from the
observed Live economic path" onto the identity-bound persisted fill, fee,
and position artifacts. Missing, empty, or unparseable terms fail closed
and are not replaced by zero. A present Decimal-parseable 0 is observed
zero. Unrealized PnL, mark, balance, inferred slippage, Cap 7.1
ACCOUNTING_RECONSTRUCTION_MATCH, and §11.17 LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN
are not this field. LIVE_RESTART_RECONSTRUCTED remains false.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_identity_v1 import (
    ACCOUNTING_TOLERANCE,
    ACCOUNTING_TOLERANCE_AUTHORITY,
    ACCOUNTING_UNIT,
    BOUND_CLORDID,
    BOUND_FILL_FEE_CCY,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    BOUND_TRADE_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
    LIVE_ACCOUNTING_RECONSTRUCTED_PRODUCER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    exact_identity_match_v1,
    position_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    decimal_or_none_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)

ADMISSIBLE_SOURCE_KIND = "GOVERNED_PERSISTED_IDENTITY_BOUND_LIVE_ECONOMIC_PATH"
INJECTED_EVIDENCE_SOURCE_KIND = "GOVERNED_OFFLINE_CONTRACT"
ACCOUNTING_PRODUCER = LIVE_ACCOUNTING_RECONSTRUCTED_PRODUCER
ZERO = Decimal("0")
EXACT_TOLERANCE = Decimal(ACCOUNTING_TOLERANCE)


def _derived_decimal_str_v1(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


FILL_DECIMAL_FIELDS: tuple[str, ...] = ("fee", "fillPnl")
POSITION_DECIMAL_FIELDS: tuple[str, ...] = (
    "fee",
    "pnl",
    "realizedPnl",
    "fundingFee",
    "settledPnl",
)
COMPETING_FILL_FEE_FIELDS = frozenset({"fillFee", "tradeFee", "feeAmt", "feeAmount", "fees"})
COMPETING_REALIZED_FIELDS = frozenset({"realisedPnl", "realizedPNL", "rpnl"})

ACCOUNTING_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_POSITION_RECONCILED",
    "IDENTITY_BOUND_REQUIRED_TERMS_PRESENT_PARSEABLE",
    "FEE_CCY_EQUALS_POSITION_CCY",
    "FILL_FEE_EQUALS_POSITION_FEE",
    "FILL_PNL_EQUALS_POSITION_PNL",
    "TRADE_ID_IDENTITY_MATCH",
    "REALIZED_PNL_IDENTITY_HOLDS",
    "ADMISSIBLE_PERSISTED_LIVE_PATH_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
    "MISSING_NOT_REPLACED_BY_ZERO",
)
ACCOUNTING_FIELD_CONSTITUENT_COUNT = 10

ACCOUNTING_IDENTITY_EQUATION = (
    "reconstructed_realized_pnl[ccy] = fillPnl[feeCcy] + fee[feeCcy] "
    "+ fundingFee[position.ccy] + settledPnl[position.ccy]"
)


def _raw_field_present_nonempty_v1(row: Mapping[str, Any], field_name: str) -> bool:
    if field_name not in row:
        return False
    value = row.get(field_name)
    if value is None:
        return False
    return bool(str(value).strip())


def _decimal_term_v1(row: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    present = _raw_field_present_nonempty_v1(row, field_name)
    raw = row.get(field_name) if field_name in row else None
    parsed = decimal_or_none_v1(raw) if present else None
    return {
        "field": field_name,
        "present_nonempty": present,
        "raw": raw if present else None,
        "parsed": str(parsed) if parsed is not None else None,
        "parseable": parsed is not None,
        "observed_zero": bool(parsed is not None and parsed == ZERO),
        "missing_treated_as_zero": False,
        "decimal": parsed,
    }


def _string_term_v1(row: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    present = _raw_field_present_nonempty_v1(row, field_name)
    raw = row.get(field_name) if field_name in row else None
    text = str(raw).strip() if present else None
    return {
        "field": field_name,
        "present_nonempty": present,
        "raw": raw if present else None,
        "value": text,
    }


def classify_accounting_path_v1(
    *,
    fill_row: Mapping[str, Any] | None,
    position_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    fill = dict(fill_row or {})
    position = dict(position_row or {})
    fill_identity = exact_identity_match_v1(
        ord_id=fill.get("ordId"),
        clordid=fill.get("clOrdId"),
        inst_id=fill.get("instId"),
    )
    position_identity = position_identity_match_v1(
        inst_id=position.get("instId"),
        pos_side=position.get("posSide"),
    )
    fill_terms = {name: _decimal_term_v1(fill, name) for name in FILL_DECIMAL_FIELDS}
    position_terms = {name: _decimal_term_v1(position, name) for name in POSITION_DECIMAL_FIELDS}
    fill_fee_ccy = _string_term_v1(fill, "feeCcy")
    position_ccy = _string_term_v1(position, "ccy")
    fill_trade_id = _string_term_v1(fill, "tradeId")
    position_trade_id = _string_term_v1(position, "tradeId")
    upl = _decimal_term_v1(position, "upl")
    schema_reasons: list[str] = []
    for key in COMPETING_FILL_FEE_FIELDS:
        if _raw_field_present_nonempty_v1(fill, key):
            competing = decimal_or_none_v1(fill.get(key))
            fee_parsed = fill_terms["fee"]["decimal"]
            if fee_parsed is None or competing is None or competing != fee_parsed:
                schema_reasons.append(f"COMPETING_FILL_FEE_FIELD:{key}")
    for key in COMPETING_REALIZED_FIELDS:
        if _raw_field_present_nonempty_v1(position, key):
            competing = decimal_or_none_v1(position.get(key))
            realized = position_terms["realizedPnl"]["decimal"]
            if realized is None or competing is None or competing != realized:
                schema_reasons.append(f"COMPETING_REALIZED_FIELD:{key}")
    required_decimal = [fill_terms[name] for name in FILL_DECIMAL_FIELDS] + [
        position_terms[name] for name in POSITION_DECIMAL_FIELDS
    ]
    required_strings = [fill_fee_ccy, position_ccy, fill_trade_id, position_trade_id]
    missing_or_empty = any(
        item["present_nonempty"] is not True for item in required_decimal
    ) or any(item["present_nonempty"] is not True for item in required_strings)
    unparseable = any(
        item["present_nonempty"] is True and item["parseable"] is not True
        for item in required_decimal
    )
    schema_ambiguous = bool(schema_reasons)
    terms_ready = (
        not missing_or_empty
        and not unparseable
        and not schema_ambiguous
        and fill_identity["ORDER_IDENTITY_MATCH"] is True
        and position_identity["POSITION_IDENTITY_MATCH"] is True
    )
    fill_fee = fill_terms["fee"]["decimal"]
    fill_pnl = fill_terms["fillPnl"]["decimal"]
    pos_fee = position_terms["fee"]["decimal"]
    pos_pnl = position_terms["pnl"]["decimal"]
    realized = position_terms["realizedPnl"]["decimal"]
    funding = position_terms["fundingFee"]["decimal"]
    settled = position_terms["settledPnl"]["decimal"]
    ccy_match = bool(
        fill_fee_ccy["value"]
        and position_ccy["value"]
        and fill_fee_ccy["value"] == position_ccy["value"]
        and fill_fee_ccy["value"] == BOUND_FILL_FEE_CCY
        and position_ccy["value"] == ACCOUNTING_UNIT
    )
    fee_match = bool(fill_fee is not None and pos_fee is not None and fill_fee == pos_fee)
    pnl_match = bool(fill_pnl is not None and pos_pnl is not None and fill_pnl == pos_pnl)
    trade_match = bool(
        fill_trade_id["value"]
        and position_trade_id["value"]
        and fill_trade_id["value"] == position_trade_id["value"]
        and fill_trade_id["value"] == BOUND_TRADE_ID
    )
    reconstructed = None
    residual = None
    identity_holds = False
    if (
        terms_ready
        and fill_pnl is not None
        and fill_fee is not None
        and funding is not None
        and settled is not None
    ):
        reconstructed = fill_pnl + fill_fee + funding + settled
        if realized is not None:
            residual = realized - reconstructed
            identity_holds = bool(residual == EXACT_TOLERANCE)
    epistemic = "NOT_OBSERVABLE"
    if not fill or not position:
        epistemic = "REQUIRED_ROW_MISSING"
    elif fill_identity["ORDER_IDENTITY_MATCH"] is not True:
        epistemic = "FILL_IDENTITY_MISMATCH"
    elif position_identity["POSITION_IDENTITY_MATCH"] is not True:
        epistemic = "POSITION_IDENTITY_MISMATCH"
    elif missing_or_empty:
        epistemic = "REQUIRED_TERM_MISSING_OR_EMPTY"
    elif unparseable:
        epistemic = "REQUIRED_TERM_UNPARSEABLE"
    elif schema_ambiguous:
        epistemic = "SCHEMA_AMBIGUOUS"
    elif not ccy_match:
        epistemic = "CURRENCY_MISMATCH"
    elif not fee_match:
        epistemic = "FEE_PATH_DIVERGENCE"
    elif not pnl_match:
        epistemic = "PNL_PATH_DIVERGENCE"
    elif not trade_match:
        epistemic = "TRADE_ID_MISMATCH"
    elif residual is None:
        epistemic = "RESIDUAL_NOT_COMPUTABLE"
    elif identity_holds:
        epistemic = "RECONSTRUCTED"
    else:
        epistemic = "ACCOUNTING_RESIDUAL_NONZERO"
    claim = bool(
        terms_ready
        and ccy_match
        and fee_match
        and pnl_match
        and trade_match
        and identity_holds
        and epistemic == "RECONSTRUCTED"
    )
    return {
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_TRADE_ID": BOUND_TRADE_ID,
        "ACCOUNTING_IDENTITY_EQUATION": ACCOUNTING_IDENTITY_EQUATION,
        "ACCOUNTING_UNIT": ACCOUNTING_UNIT,
        "ACCOUNTING_TOLERANCE": ACCOUNTING_TOLERANCE,
        "ACCOUNTING_TOLERANCE_AUTHORITY": ACCOUNTING_TOLERANCE_AUTHORITY,
        "FILL_IDENTITY": fill_identity,
        "POSITION_IDENTITY": position_identity,
        "fill_terms": {
            name: {k: v for k, v in item.items() if k != "decimal"}
            for name, item in fill_terms.items()
        },
        "position_terms": {
            name: {k: v for k, v in item.items() if k != "decimal"}
            for name, item in position_terms.items()
        },
        "fill_fee_ccy": fill_fee_ccy,
        "position_ccy": position_ccy,
        "fill_trade_id": fill_trade_id,
        "position_trade_id": position_trade_id,
        "upl_observed": {k: v for k, v in upl.items() if k != "decimal"},
        "UPL_IN_REALIZED_IDENTITY": False,
        "IDENTITY_BOUND_REQUIRED_TERMS_PRESENT_PARSEABLE": bool(terms_ready),
        "FEE_CCY_EQUALS_POSITION_CCY": ccy_match,
        "FILL_FEE_EQUALS_POSITION_FEE": fee_match,
        "FILL_PNL_EQUALS_POSITION_PNL": pnl_match,
        "TRADE_ID_IDENTITY_MATCH": trade_match,
        "REALIZED_PNL_IDENTITY_HOLDS": identity_holds,
        "MISSING_OR_EMPTY": missing_or_empty,
        "UNPARSEABLE": unparseable,
        "SCHEMA_AMBIGUOUS": schema_ambiguous,
        "SCHEMA_AMBIGUITY_REASONS": schema_reasons,
        "MISSING_NOT_REPLACED_BY_ZERO": True,
        "RAW_FILL_FEE_IF_OBSERVED": fill_terms["fee"]["raw"]
        if fill_terms["fee"]["parseable"]
        else None,
        "RAW_FILL_PNL_IF_OBSERVED": fill_terms["fillPnl"]["raw"]
        if fill_terms["fillPnl"]["parseable"]
        else None,
        "RAW_POSITION_FEE_IF_OBSERVED": position_terms["fee"]["raw"]
        if position_terms["fee"]["parseable"]
        else None,
        "RAW_POSITION_PNL_IF_OBSERVED": position_terms["pnl"]["raw"]
        if position_terms["pnl"]["parseable"]
        else None,
        "RAW_REALIZED_PNL_IF_OBSERVED": (
            position_terms["realizedPnl"]["raw"]
            if position_terms["realizedPnl"]["parseable"]
            else None
        ),
        "RAW_FUNDING_FEE_IF_OBSERVED": (
            position_terms["fundingFee"]["raw"]
            if position_terms["fundingFee"]["parseable"]
            else None
        ),
        "RAW_SETTLED_PNL_IF_OBSERVED": (
            position_terms["settledPnl"]["raw"]
            if position_terms["settledPnl"]["parseable"]
            else None
        ),
        "RAW_UPL_IF_OBSERVED": upl["raw"] if upl["parseable"] else None,
        "RECONSTRUCTED_REALIZED_PNL": _derived_decimal_str_v1(reconstructed),
        "OBSERVED_REALIZED_PNL": _derived_decimal_str_v1(realized),
        "ACCOUNTING_RESIDUAL": _derived_decimal_str_v1(residual),
        "ACCOUNTING_RESIDUAL_UNIT": ACCOUNTING_UNIT if residual is not None else None,
        "ACCOUNTING_RESULT": _derived_decimal_str_v1(reconstructed),
        "ACCOUNTING_RESULT_UNIT": ACCOUNTING_UNIT if reconstructed is not None else None,
        "EPISTEMIC_CLASS": epistemic,
        "ACTUAL_ACCOUNTING_RECONSTRUCTED": claim,
    }


def evaluate_live_accounting_reconstructed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    refuse_forbidden_live_source_v1(
        field_name="LIVE_ACCOUNTING_RECONSTRUCTED",
        source_kind=source_kind,
    )
    if str(source_kind or "").strip() != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    missing = [name for name in ACCOUNTING_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "ACCOUNTING_FIELD_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    false_required = [
        name for name in ACCOUNTING_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "canonical_definition": LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
        "adjudication": "TRUE_LIVE_ACCOUNTING_RECONSTRUCTED" if claim else "FALSE_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": ACCOUNTING_FIELD_CONSTITUENT_COUNT,
        "false_required": false_required,
        "source_kind": source_kind,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
        "producer": ACCOUNTING_PRODUCER,
    }
