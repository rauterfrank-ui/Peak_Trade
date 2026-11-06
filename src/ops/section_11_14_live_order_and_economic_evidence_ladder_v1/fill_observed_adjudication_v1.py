"""Adjudicate LIVE_FILL_OBSERVED from the bound fills-row criterion.

Does not POST. Injected evidence cannot promote the live field. Order-state
labels, pending disappearance, position, balance, fee, and ACK are not this
field. LIVE_FEE_OBSERVED remains false even when fee fields are present.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_SUBMIT_ACK_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    exact_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    FILL_FIELD_CONSTITUENT_COUNT,
    FILL_FIELD_CONSTITUENTS,
    FILL_PRODUCER,
    FILLS_HTTP_CONSTITUENT_COUNT,
    FILLS_HTTP_CONSTITUENTS,
    INJECTED_EVIDENCE_SOURCE_KIND,
    LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
    classify_identity_bound_fill_rows_v1,
    decimal_or_none_v1,
    evaluate_fills_http_conjunction_v1,
    evaluate_live_fill_observed_conjunction_v1,
    fills_http_constituents_from_evidence_v1,
)


def adjudicate_live_fill_observed_v1(
    *,
    fill_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if LIVE_SUBMIT_ACK_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("ACK_PREDECESSOR_FALSE")
    evidence = dict(fill_evidence or {})
    source_kind = str(evidence.get("source_kind") or INJECTED_EVIDENCE_SOURCE_KIND).strip()
    live_source = source_kind == ADMISSIBLE_SOURCE_KIND
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_FILL_OBSERVATION_GO")
    if evidence.get("CANCEL_USED") is True or evidence.get("AMEND_USED") is True:
        raise Section1114OfflineSurfaceError("ORDER_MUTATION_INVOKED_BY_FILL_OBSERVATION_GO")
    if evidence.get("LIVE_FEE_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("FEE_PROMOTED_BY_FILL_OBSERVATION")
    if evidence.get("LIVE_POSITION_RECONCILED") is True:
        raise Section1114OfflineSurfaceError("POSITION_RECONCILED_PROMOTED_BY_FILL_OBSERVATION")
    if not live_source and evidence.get("LIVE_FILL_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("FILL_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")

    fills_rows_raw = evidence.get("fills_rows")
    fills_rows = [item for item in fills_rows_raw] if isinstance(fills_rows_raw, list) else []
    object_rows = [item for item in fills_rows if isinstance(item, Mapping)]
    classified_rows = classify_identity_bound_fill_rows_v1(rows=object_rows)
    http_constituents = fills_http_constituents_from_evidence_v1(
        http_status=evidence.get("fills_http_status"),
        okx_code=evidence.get("fills_okx_code"),
        json_parse_ok=evidence.get("fills_json_parse_ok"),
        redirect_followed=bool(evidence.get("fills_redirect_followed")),
        method=evidence.get("fills_method") or "GET",
    )
    http_eval = evaluate_fills_http_conjunction_v1(constituent_values=http_constituents)
    order_row = evidence.get("order_row") if isinstance(evidence.get("order_row"), Mapping) else {}
    order_identity = exact_identity_match_v1(
        ord_id=order_row.get("ordId") if order_row else None,
        clordid=order_row.get("clOrdId") if order_row else None,
        inst_id=order_row.get("instId") if order_row else None,
    )
    order_present = bool(order_row) and order_identity["ORDER_IDENTITY_MATCH"] is True
    order_state = str(order_row.get("state") or "") if order_row else ""
    acc_fill = str(order_row.get("accFillSz") or "") if order_row else ""
    order_sz = str(order_row.get("sz") or "") if order_row else ""
    remaining_supplied = order_row.get("remainingQty") if order_row else None
    if remaining_supplied is None and order_row:
        remaining_supplied = order_row.get("remaining")
    avg_px = order_row.get("avgPx") if order_row else None
    acc_fill_dec = decimal_or_none_v1(acc_fill) if acc_fill else None

    fills_get_ok = bool(
        live_source
        and evidence.get("FILLS_GET_PERFORMED") is True
        and http_eval["claim_value"] is True
    )
    at_least_one = bool(classified_rows["AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW"])
    field_constituents: dict[str, bool | None] = {
        "LIVE_SUBMIT_ACK_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_FILLS_GET": bool(
            live_source and evidence.get("FILLS_GET_PERFORMED") is True
        ),
        "FILLS_HTTP_CONJUNCTION_SATISFIED": bool(http_eval["claim_value"] is True),
        "AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW": at_least_one,
        "ADMISSIBLE_PRIVATE_GET_SOURCE": live_source,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
    }
    if live_source:
        field_eval = evaluate_live_fill_observed_conjunction_v1(
            constituent_values=field_constituents,
            source_kind=ADMISSIBLE_SOURCE_KIND,
        )
        claim = bool(field_eval["claim_value"] is True)
    else:
        field_eval = {
            "canonical_definition": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
            "claim_value": False,
            "adjudication": "FALSE_FAIL_CLOSED_NO_LIVE_GET",
            "false_required": [
                name for name in FILL_FIELD_CONSTITUENTS if field_constituents.get(name) is not True
            ],
            "constituent_count": FILL_FIELD_CONSTITUENT_COUNT,
            "source_kind": INJECTED_EVIDENCE_SOURCE_KIND,
            "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
        }
        claim = False

    contradictory = False
    unresolved_reason: str | None = None
    no_fill = False
    if classified_rows["EXECUTED_QTY_CONTRADICTS_SUBMITTED_SZ"] is True:
        contradictory = True
        unresolved_reason = "EXECUTED_QTY_CONTRADICTS_SUBMITTED_SZ"
        claim = False
    if (
        fills_get_ok
        and not at_least_one
        and order_present
        and acc_fill_dec is not None
        and acc_fill_dec > 0
    ):
        contradictory = True
        unresolved_reason = "ORDER_ACCFILLSZ_POSITIVE_WITHOUT_IDENTITY_BOUND_FILL_ROW"
        claim = False
    if fills_get_ok and not at_least_one and not contradictory:
        if order_present and (acc_fill_dec is None or acc_fill_dec == 0):
            no_fill = True
            unresolved_reason = None
        elif not order_present:
            unresolved_reason = "FILLS_EMPTY_AND_ORDER_IDENTITY_NOT_ON_WORKING_BOOK"
            no_fill = False
        else:
            unresolved_reason = "FILLS_EMPTY_ORDER_PRESENT_ACCFILLSZ_UNPARSEABLE"
    if not fills_get_ok and live_source:
        unresolved_reason = unresolved_reason or "FILLS_GET_HTTP_CONJUNCTION_FAILED"
        claim = False

    partial = bool(classified_rows["PARTIAL_FILL_OBSERVED"] is True and claim)
    full = bool(classified_rows["FULL_FILL_OBSERVED"] is True and claim)
    if claim and not partial and not full:
        # At least one admissible fill row exists; qty relation may be unparseable.
        unresolved_reason = unresolved_reason or "FILL_OBSERVED_PARTIAL_FULL_QTY_UNRESOLVED"
    if contradictory:
        partial = False
        full = False
        no_fill = False
        claim = False

    if claim:
        case = "CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE"
        reason = "IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW"
    elif contradictory:
        case = "CASE_LIVE_FILL_CONTRADICTORY_FAIL_CLOSED"
        reason = unresolved_reason or "CONTRADICTORY_FILL_EVIDENCE"
    elif no_fill:
        case = "CASE_NO_FILL_OBSERVED"
        reason = "FILLS_EMPTY_AND_BOUND_ORDER_UNFILLED_OR_WORKING"
    elif unresolved_reason:
        case = "CASE_LIVE_FILL_UNRESOLVED_FAIL_CLOSED"
        reason = unresolved_reason
    else:
        case = "CASE_LIVE_FILL_NOT_OBSERVED"
        reason = "CRITERION_NOT_SATISFIED"

    matched = list(classified_rows["matched_rows"])
    first = matched[0] if matched else {}
    remaining_qty = None
    if remaining_supplied is not None and str(remaining_supplied) != "":
        remaining_qty = remaining_supplied
    return {
        "canonical_definition": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
        "producer": FILL_PRODUCER,
        "FILL_PRODUCER": FILL_PRODUCER,
        "FILL_PROOF_CRITERION": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
        "proof_criterion_bound": True,
        "FILL_EVIDENCE_SOURCE": "/api/v5/trade/fills" if live_source else None,
        "fills_http_constituents": FILLS_HTTP_CONSTITUENTS,
        "fills_http_constituent_count": FILLS_HTTP_CONSTITUENT_COUNT,
        "fills_http_constituent_values": http_constituents,
        "fills_http_conjunction": http_eval,
        "field_constituents": FILL_FIELD_CONSTITUENTS,
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "FILL_PROOF_CONJUNCTION_STATUS": field_eval.get("adjudication"),
        "adjudicated_value": claim,
        "claim_value": claim,
        "LIVE_SUBMIT_ACK_OBSERVED": True,
        "LIVE_FILL_OBSERVED": claim,
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
        "SECTION_11_14_COMPLETE": False,
        "NO_FILL_OBSERVED": no_fill,
        "PARTIAL_FILL_OBSERVED": partial,
        "FULL_FILL_OBSERVED": full,
        "CONTRADICTORY_FILL_EVIDENCE": contradictory,
        "UNRESOLVED_REASON": unresolved_reason,
        "LIVE_FILL_ADJUDICATION_REASON": reason,
        "CASE_ADJUDICATION": case,
        "ORDER_IDENTITY_MATCH": bool(
            classified_rows["AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW"] or order_present
        ),
        "ORDID_MATCH": bool(
            any(row.get("identity", {}).get("ORDID_MATCH") is True for row in matched)
            or order_identity["ORDID_MATCH"]
        ),
        "CLORDID_MATCH": bool(
            any(row.get("identity", {}).get("CLORDID_MATCH") is True for row in matched)
            or order_identity["CLORDID_MATCH"]
        ),
        "INSTRUMENT_MATCH": bool(
            any(row.get("identity", {}).get("INSTRUMENT_MATCH") is True for row in matched)
            or order_identity["INSTRUMENT_MATCH"]
        ),
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "RAW_ORDER_STATE_IF_OBSERVED": order_state or None,
        "RAW_FILL_ROW_COUNT": classified_rows["RAW_FILL_ROW_COUNT"],
        "RAW_FILL_IDENTIFIERS": classified_rows["RAW_FILL_IDENTIFIERS"],
        "RAW_TRADE_IDENTIFIERS": classified_rows["RAW_TRADE_IDENTIFIERS"],
        "RAW_EXECUTED_QTY_IF_OBSERVED": classified_rows["RAW_EXECUTED_QTY_IF_OBSERVED"],
        "RAW_ORDER_SZ_IF_OBSERVED": order_sz or None,
        "RAW_REMAINING_QTY_IF_OBSERVED": remaining_qty,
        "RAW_AVG_FILL_PRICE_IF_OBSERVED": avg_px if order_present else None,
        "RAW_FILL_PRICE_IF_OBSERVED": first.get("fillPx"),
        "RAW_FILL_TIMESTAMP_IF_OBSERVED": first.get("fillTime"),
        "ORDER_GET_IDENTITY_MATCH": order_present,
        "ORDER_STATE": order_state or None,
        "ORDER_ACCFILLSZ": acc_fill or None,
        "row_classification": classified_rows,
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FILL_SOURCE_KIND": source_kind if live_source else INJECTED_EVIDENCE_SOURCE_KIND,
    }
