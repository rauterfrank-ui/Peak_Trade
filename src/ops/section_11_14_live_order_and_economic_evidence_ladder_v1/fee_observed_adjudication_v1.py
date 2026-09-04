"""Adjudicate LIVE_FEE_OBSERVED from the bound fills-row fee criterion.

Does not POST. Injected evidence cannot promote the live field. Fill quantity,
fill price, fillPnl, static rate, historical fills, ACK, order-state,
position, and balance are not this field. LIVE_POSITION_RECONCILED remains
false even when an actual fee is observed.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FILL_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fee_observed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    FEE_FIELD_CONSTITUENT_COUNT,
    FEE_FIELD_CONSTITUENTS,
    FEE_PRODUCER,
    INJECTED_EVIDENCE_SOURCE_KIND,
    classify_identity_bound_fee_rows_v1,
    evaluate_live_fee_observed_conjunction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    FILLS_HTTP_CONSTITUENT_COUNT,
    FILLS_HTTP_CONSTITUENTS,
    evaluate_fills_http_conjunction_v1,
    fills_http_constituents_from_evidence_v1,
)


def adjudicate_live_fee_observed_v1(
    *,
    fee_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if LIVE_FILL_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("FILL_PREDECESSOR_FALSE")
    evidence = dict(fee_evidence or {})
    source_kind = str(evidence.get("source_kind") or INJECTED_EVIDENCE_SOURCE_KIND).strip()
    live_source = source_kind == ADMISSIBLE_SOURCE_KIND
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_FEE_OBSERVATION_GO")
    if evidence.get("CANCEL_USED") is True or evidence.get("AMEND_USED") is True:
        raise Section1114OfflineSurfaceError("ORDER_MUTATION_INVOKED_BY_FEE_OBSERVATION_GO")
    if evidence.get("LIVE_POSITION_RECONCILED") is True:
        raise Section1114OfflineSurfaceError("POSITION_RECONCILED_PROMOTED_BY_FEE_OBSERVATION")
    if not live_source and evidence.get("LIVE_FEE_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("FEE_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")

    fills_rows_raw = evidence.get("fills_rows")
    fills_rows = [item for item in fills_rows_raw] if isinstance(fills_rows_raw, list) else []
    object_rows = [item for item in fills_rows if isinstance(item, Mapping)]
    order_row = evidence.get("order_row") if isinstance(evidence.get("order_row"), Mapping) else {}
    classified = classify_identity_bound_fee_rows_v1(rows=object_rows, order_row=order_row)
    http_constituents = fills_http_constituents_from_evidence_v1(
        http_status=evidence.get("fills_http_status"),
        okx_code=evidence.get("fills_okx_code"),
        json_parse_ok=evidence.get("fills_json_parse_ok"),
        redirect_followed=bool(evidence.get("fills_redirect_followed")),
        method=evidence.get("fills_method") or "GET",
    )
    http_eval = evaluate_fills_http_conjunction_v1(constituent_values=http_constituents)
    fills_get_ok = bool(
        live_source
        and evidence.get("FILLS_GET_PERFORMED") is True
        and http_eval["claim_value"] is True
    )
    field_constituents: dict[str, bool | None] = {
        "LIVE_FILL_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_FILLS_GET": bool(
            live_source and evidence.get("FILLS_GET_PERFORMED") is True
        ),
        "FILLS_HTTP_CONJUNCTION_SATISFIED": bool(http_eval["claim_value"] is True),
        "AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW": bool(
            classified["AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW"] is True
        ),
        "IDENTITY_BOUND_ACTUAL_FEE_PRESENT_PARSEABLE": bool(
            classified["IDENTITY_BOUND_ACTUAL_FEE_PRESENT_PARSEABLE"] is True
        ),
        "FEE_CCY_PRESENT_NONEMPTY": bool(classified["FEE_CCY_PRESENT_NONEMPTY"] is True),
        "NO_FEE_SCHEMA_AMBIGUITY": bool(classified["NO_FEE_SCHEMA_AMBIGUITY"] is True),
        "ADMISSIBLE_PRIVATE_GET_SOURCE": live_source,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "FEE_NOT_INFERRED": True,
    }
    if live_source:
        field_eval = evaluate_live_fee_observed_conjunction_v1(
            constituent_values=field_constituents,
            source_kind=ADMISSIBLE_SOURCE_KIND,
        )
        claim = bool(
            field_eval["claim_value"] is True and classified["ACTUAL_FEE_OBSERVED"] is True
        )
    else:
        field_eval = {
            "canonical_definition": LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
            "claim_value": False,
            "adjudication": "FALSE_FAIL_CLOSED_NO_LIVE_GET",
            "false_required": [
                name for name in FEE_FIELD_CONSTITUENTS if field_constituents.get(name) is not True
            ],
            "constituent_count": FEE_FIELD_CONSTITUENT_COUNT,
            "source_kind": INJECTED_EVIDENCE_SOURCE_KIND,
            "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
        }
        claim = False

    unresolved_reason: str | None = None
    if not fills_get_ok and live_source:
        unresolved_reason = "FILLS_GET_HTTP_CONJUNCTION_FAILED"
        claim = False
    elif live_source and not classified["AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW"]:
        unresolved_reason = "NO_IDENTITY_BOUND_FILL_ROW"
        claim = False
    elif live_source and classified["ORDER_FEE_CONFLICT"] is True:
        unresolved_reason = "ORDER_FEE_CONTRADICTS_FILL_FEE"
        claim = False
    elif live_source and classified["SCHEMA_AMBIGUITY_REASONS"]:
        unresolved_reason = str(classified["SCHEMA_AMBIGUITY_REASONS"][0])
        claim = False
    elif live_source and classified["FEE_UNPARSEABLE"] is True:
        unresolved_reason = "FEE_FIELD_UNPARSEABLE"
        claim = False
    elif live_source and classified["FEE_FIELD_MISSING_OR_EMPTY"] is True:
        unresolved_reason = "FEE_FIELD_MISSING_OR_EMPTY"
        claim = False
    elif live_source and classified["FEE_CCY_MISSING_OR_EMPTY"] is True:
        unresolved_reason = "FEE_CCY_MISSING_OR_EMPTY"
        claim = False
    elif live_source and not claim:
        unresolved_reason = "CRITERION_NOT_SATISFIED"

    if claim:
        case = "CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE"
        reason = "IDENTITY_BOUND_ACTUAL_FEE_AND_FEE_CCY"
    elif unresolved_reason == "NO_IDENTITY_BOUND_FILL_ROW":
        case = "CASE_LIVE_FEE_IDENTITY_MISMATCH_FAIL_CLOSED"
        reason = unresolved_reason
    elif unresolved_reason in {
        "FEE_FIELD_MISSING_OR_EMPTY",
        "FEE_CCY_MISSING_OR_EMPTY",
        "FEE_FIELD_UNPARSEABLE",
        "FILLS_GET_HTTP_CONJUNCTION_FAILED",
        "CRITERION_NOT_SATISFIED",
    }:
        case = "CASE_LIVE_FEE_NOT_OBSERVED"
        reason = unresolved_reason or "CRITERION_NOT_SATISFIED"
    elif unresolved_reason:
        case = "CASE_LIVE_FEE_AMBIGUOUS_FAIL_CLOSED"
        reason = unresolved_reason
    else:
        case = "CASE_LIVE_FEE_NOT_OBSERVED"
        reason = "CRITERION_NOT_SATISFIED"

    return {
        "canonical_definition": LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
        "producer": FEE_PRODUCER,
        "FEE_PRODUCER": FEE_PRODUCER,
        "FEE_PROOF_CRITERION": LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
        "proof_criterion_bound": True,
        "FEE_EVIDENCE_SOURCE": "/api/v5/trade/fills" if live_source else None,
        "fills_http_constituents": FILLS_HTTP_CONSTITUENTS,
        "fills_http_constituent_count": FILLS_HTTP_CONSTITUENT_COUNT,
        "fills_http_constituent_values": http_constituents,
        "fills_http_conjunction": http_eval,
        "field_constituents": FEE_FIELD_CONSTITUENTS,
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "FEE_PROOF_CONJUNCTION_STATUS": field_eval.get("adjudication"),
        "adjudicated_value": claim,
        "claim_value": claim,
        "LIVE_FILL_OBSERVED": True,
        "LIVE_FEE_OBSERVED": claim,
        "LIVE_POSITION_RECONCILED": False,
        "SECTION_11_14_COMPLETE": False,
        "UNRESOLVED_REASON": unresolved_reason,
        "LIVE_FEE_ADJUDICATION_REASON": reason,
        "CASE_ADJUDICATION": case,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "RAW_FILL_ROW_COUNT": classified["RAW_FILL_ROW_COUNT"],
        "RAW_FEE_IF_OBSERVED": classified["RAW_FEE_IF_OBSERVED"],
        "RAW_FEE_CCY_IF_OBSERVED": classified["RAW_FEE_CCY_IF_OBSERVED"],
        "RAW_FEES_IF_OBSERVED": classified["RAW_FEES_IF_OBSERVED"],
        "RAW_FEE_CCYS_IF_OBSERVED": classified["RAW_FEE_CCYS_IF_OBSERVED"],
        "FEE_SUM_COMPUTED": False,
        "FEE_INFERRED_FROM_RATE": False,
        "FEE_INFERRED_FROM_PRICE_TIMES_QTY": False,
        "row_classification": classified,
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FEE_SOURCE_KIND": source_kind if live_source else INJECTED_EVIDENCE_SOURCE_KIND,
    }
