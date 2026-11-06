"""Bound LIVE_POSITION_RECONCILED proof criterion.

Applies the SSOT phrase "Current Live position reconciled to the observed
fill/fee path" onto GET /api/v5/account/positions. Empty data is not zero.
A pos=0 row is not a nonzero fillSz. Fill, fee, ACK, order-state, balance,
LIVE_RECONCILIATION_PROVEN, and historical position evidence are not this
field. LIVE_ACCOUNTING_RECONSTRUCTED remains false.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
    LIVE_POSITION_RECONCILED_PRODUCER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    position_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    FILLS_HTTP_CONSTITUENT_COUNT,
    FILLS_HTTP_CONSTITUENTS,
    decimal_or_none_v1,
    evaluate_fills_http_conjunction_v1,
    fills_http_constituents_from_evidence_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)

ADMISSIBLE_SOURCE_KIND = "GOVERNED_CURRENT_PRIVATE_GET"
INJECTED_EVIDENCE_SOURCE_KIND = "GOVERNED_OFFLINE_CONTRACT"
POSITION_PRODUCER = LIVE_POSITION_RECONCILED_PRODUCER
ADMISSIBLE_POS_FIELD = "pos"
COMPETING_POS_AMOUNT_FIELDS = frozenset({"posSize", "position", "positionSz", "sz"})
EMPTY_DATA_IS_ZERO = False
POSITION_ENDPOINT_PATH = "/api/v5/account/positions"
BOUND_FILL_SZ_DECIMAL = Decimal(BOUND_FILL_SZ)
ZERO = Decimal("0")

POSITION_HTTP_CONSTITUENTS = FILLS_HTTP_CONSTITUENTS
POSITION_HTTP_CONSTITUENT_COUNT = FILLS_HTTP_CONSTITUENT_COUNT

POSITION_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_FEE_OBSERVED",
    "CURRENT_GOVERNED_PRIVATE_POSITIONS_GET",
    "POSITIONS_HTTP_CONJUNCTION_SATISFIED",
    "EXACTLY_ONE_IDENTITY_BOUND_POSITION_ROW",
    "IDENTITY_BOUND_POS_PRESENT_PARSEABLE",
    "POS_EQUALS_BOUND_FILL_SZ",
    "EMPTY_DATA_NOT_TREATED_AS_ZERO",
    "ADMISSIBLE_PRIVATE_GET_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
    "NOT_INFERRED_FROM_FILL_FEE_OR_ORDER_STATE",
)
POSITION_FIELD_CONSTITUENT_COUNT = 10


def positions_http_constituents_from_evidence_v1(
    *,
    http_status: object,
    okx_code: object,
    json_parse_ok: object,
    redirect_followed: bool,
    method: object,
) -> dict[str, bool]:
    return fills_http_constituents_from_evidence_v1(
        http_status=http_status,
        okx_code=okx_code,
        json_parse_ok=json_parse_ok,
        redirect_followed=redirect_followed,
        method=method,
    )


def evaluate_positions_http_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool],
) -> dict[str, Any]:
    evaluated = evaluate_fills_http_conjunction_v1(constituent_values=constituent_values)
    adjudication = (
        "POSITIONS_HTTP_CONJUNCTION_SATISFIED"
        if evaluated["claim_value"] is True
        else "POSITIONS_HTTP_FAIL_CLOSED"
    )
    return {**evaluated, "adjudication": adjudication}


def _raw_field_present_nonempty_v1(row: Mapping[str, Any], field_name: str) -> bool:
    if field_name not in row:
        return False
    value = row.get(field_name)
    if value is None:
        return False
    return bool(str(value).strip())


def classify_identity_bound_position_rows_v1(
    *,
    rows: list[Mapping[str, Any]] | None,
    data_is_list: bool,
) -> dict[str, Any]:
    if EMPTY_DATA_IS_ZERO is True:
        raise Section1114OfflineSurfaceError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    object_rows = [item for item in (rows or []) if isinstance(item, Mapping)]
    raw_row_count = len(rows) if isinstance(rows, list) else 0
    empty_data = bool(data_is_list and raw_row_count == 0)
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    schema_reasons: list[str] = []
    for item in object_rows:
        identity = position_identity_match_v1(
            inst_id=item.get("instId"),
            pos_side=item.get("posSide"),
        )
        pos_present = _raw_field_present_nonempty_v1(item, ADMISSIBLE_POS_FIELD)
        pos_raw = item.get(ADMISSIBLE_POS_FIELD) if ADMISSIBLE_POS_FIELD in item else None
        pos_parsed = decimal_or_none_v1(pos_raw) if pos_present else None
        competing: dict[str, object] = {}
        row_ambiguous = False
        for key in COMPETING_POS_AMOUNT_FIELDS:
            if _raw_field_present_nonempty_v1(item, key):
                competing[key] = item.get(key)
                parsed = decimal_or_none_v1(item.get(key))
                if pos_parsed is None or parsed is None or parsed != pos_parsed:
                    row_ambiguous = True
                    schema_reasons.append(f"COMPETING_POS_AMOUNT_FIELD:{key}")
        record = {
            "instId": item.get("instId"),
            "instType": item.get("instType"),
            "posSide": item.get("posSide"),
            "posId": item.get("posId"),
            "pos": pos_raw,
            "mgnMode": item.get("mgnMode") if "mgnMode" in item else None,
            "availPos": item.get("availPos") if "availPos" in item else None,
            "identity": identity,
            "POS_FIELD_PRESENT_NONEMPTY": pos_present,
            "POS_PARSEABLE": pos_parsed is not None,
            "POS_PARSED": str(pos_parsed) if pos_parsed is not None else None,
            "POS_EQUALS_BOUND_FILL_SZ": bool(
                pos_parsed is not None and pos_parsed == BOUND_FILL_SZ_DECIMAL
            ),
            "POS_IS_ZERO": bool(pos_parsed is not None and pos_parsed == ZERO),
            "ROW_SCHEMA_AMBIGUOUS": row_ambiguous,
            "COMPETING_POS_AMOUNT_FIELDS": competing,
        }
        if identity["POSITION_IDENTITY_MATCH"] is True:
            matched.append(record)
        else:
            unmatched.append(record)

    schema_ambiguous = bool(schema_reasons) or any(
        record["ROW_SCHEMA_AMBIGUOUS"] is True for record in matched
    )
    exactly_one = len(matched) == 1
    unique = matched[0] if exactly_one else None
    pos_present_parseable = bool(
        unique is not None
        and unique["POS_FIELD_PRESENT_NONEMPTY"] is True
        and unique["POS_PARSEABLE"] is True
    )
    qty_match = bool(unique is not None and unique["POS_EQUALS_BOUND_FILL_SZ"] is True)
    pos_zero = bool(unique is not None and unique["POS_IS_ZERO"] is True)
    missing_or_empty = bool(unique is not None and unique["POS_FIELD_PRESENT_NONEMPTY"] is not True)
    unparseable = bool(
        unique is not None
        and unique["POS_FIELD_PRESENT_NONEMPTY"] is True
        and unique["POS_PARSEABLE"] is not True
    )
    qty_divergent = bool(
        pos_present_parseable and not qty_match and not pos_zero and not schema_ambiguous
    )
    epistemic = "NOT_OBSERVABLE"
    if empty_data:
        epistemic = "EMPTY_DATA_NOT_ZERO"
    elif not object_rows and data_is_list is False:
        epistemic = "SEMANTICALLY_UNCLEAR"
    elif len(matched) > 1:
        epistemic = "AMBIGUOUS_IDENTITY_BOUND_ROWS"
    elif not matched:
        epistemic = "IDENTITY_MISMATCH" if object_rows else "NO_ROW_OBSERVED"
    elif schema_ambiguous:
        epistemic = "SCHEMA_AMBIGUOUS"
    elif missing_or_empty:
        epistemic = "POS_MISSING_OR_EMPTY"
    elif unparseable:
        epistemic = "POS_UNPARSEABLE"
    elif pos_zero:
        epistemic = "ROW_WITH_POS_ZERO"
    elif qty_divergent:
        epistemic = "QTY_DIVERGENCE"
    elif qty_match and not schema_ambiguous:
        epistemic = "RECONCILED"
    else:
        epistemic = "SEMANTICALLY_UNCLEAR"

    raw_pos = unique.get("pos") if unique is not None else None
    raw_pos_id = unique.get("posId") if unique is not None else None
    raw_pos_side = unique.get("posSide") if unique is not None else None
    return {
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "RAW_POSITION_ROW_COUNT": raw_row_count,
        "IDENTITY_BOUND_POSITION_ROW_COUNT": len(matched),
        "UNMATCHED_ROW_COUNT": len(unmatched),
        "matched_rows": matched,
        "unmatched_rows": unmatched,
        "EMPTY_DATA_OBSERVED": empty_data,
        "EMPTY_DATA_IS_ZERO": False,
        "EXACTLY_ONE_IDENTITY_BOUND_POSITION_ROW": exactly_one,
        "IDENTITY_BOUND_POS_PRESENT_PARSEABLE": pos_present_parseable,
        "POS_EQUALS_BOUND_FILL_SZ": qty_match,
        "POS_IS_ZERO": pos_zero,
        "POS_FIELD_MISSING_OR_EMPTY": missing_or_empty,
        "POS_UNPARSEABLE": unparseable,
        "QTY_DIVERGENCE": qty_divergent,
        "NO_FEE_SCHEMA_AMBIGUITY": not schema_ambiguous,
        "NO_POS_SCHEMA_AMBIGUITY": not schema_ambiguous,
        "SCHEMA_AMBIGUITY_REASONS": schema_reasons,
        "EPISTEMIC_CLASS": epistemic,
        "RAW_POSITION_QTY_IF_OBSERVED": raw_pos if pos_present_parseable else None,
        "RAW_POSITION_STATE_IF_OBSERVED": epistemic,
        "RAW_POS_ID_IF_OBSERVED": raw_pos_id if unique is not None else None,
        "RAW_POS_SIDE_IF_OBSERVED": raw_pos_side if unique is not None else None,
        "POSITION_IDENTITY_MATCH": bool(exactly_one),
        "ACTUAL_POSITION_RECONCILED": bool(
            exactly_one
            and pos_present_parseable
            and qty_match
            and not schema_ambiguous
            and not empty_data
        ),
    }


def evaluate_live_position_reconciled_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    refuse_forbidden_live_source_v1(field_name="LIVE_POSITION_RECONCILED", source_kind=source_kind)
    if str(source_kind or "").strip() != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    missing = [name for name in POSITION_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "POSITION_FIELD_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    false_required = [
        name for name in POSITION_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "canonical_definition": LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
        "adjudication": "TRUE_LIVE_POSITION_RECONCILED" if claim else "FALSE_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": POSITION_FIELD_CONSTITUENT_COUNT,
        "false_required": false_required,
        "source_kind": source_kind,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
    }
