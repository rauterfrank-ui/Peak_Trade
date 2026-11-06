"""Adjudicate LIVE_POSITION_RECONCILED from the bound positions-row criterion.

Does not POST. Injected evidence cannot promote the live field. Fill, fee,
ACK, order-state, balance, and LIVE_RECONCILIATION_PROVEN are not this field.
Empty data is not zero. LIVE_ACCOUNTING_RECONSTRUCTED remains false even when
the current position is reconciled.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED,
    LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    INJECTED_EVIDENCE_SOURCE_KIND,
    POSITION_ENDPOINT_PATH,
    POSITION_FIELD_CONSTITUENT_COUNT,
    POSITION_FIELD_CONSTITUENTS,
    POSITION_HTTP_CONSTITUENT_COUNT,
    POSITION_HTTP_CONSTITUENTS,
    POSITION_PRODUCER,
    classify_identity_bound_position_rows_v1,
    evaluate_live_position_reconciled_conjunction_v1,
    evaluate_positions_http_conjunction_v1,
    positions_http_constituents_from_evidence_v1,
)


def adjudicate_live_position_reconciled_v1(
    *,
    position_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if LIVE_FEE_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("FEE_PREDECESSOR_FALSE")
    evidence = dict(position_evidence or {})
    source_kind = str(evidence.get("source_kind") or INJECTED_EVIDENCE_SOURCE_KIND).strip()
    live_source = source_kind == ADMISSIBLE_SOURCE_KIND
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_POSITION_RECONCILIATION_GO")
    if evidence.get("CANCEL_USED") is True or evidence.get("AMEND_USED") is True:
        raise Section1114OfflineSurfaceError("ORDER_MUTATION_INVOKED_BY_POSITION_RECONCILIATION_GO")
    if evidence.get("FLATTEN_EXECUTE_USED") is True:
        raise Section1114OfflineSurfaceError("FLATTEN_INVOKED_BY_POSITION_RECONCILIATION_GO")
    if evidence.get("LIVE_ACCOUNTING_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("ACCOUNTING_PROMOTED_BY_POSITION_RECONCILIATION")
    if not live_source and evidence.get("LIVE_POSITION_RECONCILED") is True:
        raise Section1114OfflineSurfaceError("POSITION_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")

    rows_raw = evidence.get("position_rows")
    position_rows = [item for item in rows_raw] if isinstance(rows_raw, list) else []
    object_rows = [item for item in position_rows if isinstance(item, Mapping)]
    data_is_list = evidence.get("positions_data_is_list")
    if data_is_list is None:
        data_is_list = isinstance(rows_raw, list)
    classified = classify_identity_bound_position_rows_v1(
        rows=object_rows,
        data_is_list=bool(data_is_list),
    )
    http_constituents = positions_http_constituents_from_evidence_v1(
        http_status=evidence.get("positions_http_status"),
        okx_code=evidence.get("positions_okx_code"),
        json_parse_ok=evidence.get("positions_json_parse_ok"),
        redirect_followed=bool(evidence.get("positions_redirect_followed")),
        method=evidence.get("positions_method") or "GET",
    )
    http_eval = evaluate_positions_http_conjunction_v1(constituent_values=http_constituents)
    positions_get_ok = bool(
        live_source
        and evidence.get("POSITIONS_GET_PERFORMED") is True
        and http_eval["claim_value"] is True
    )
    field_constituents: dict[str, bool | None] = {
        "LIVE_FEE_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_POSITIONS_GET": bool(
            live_source and evidence.get("POSITIONS_GET_PERFORMED") is True
        ),
        "POSITIONS_HTTP_CONJUNCTION_SATISFIED": bool(http_eval["claim_value"] is True),
        "EXACTLY_ONE_IDENTITY_BOUND_POSITION_ROW": bool(
            classified["EXACTLY_ONE_IDENTITY_BOUND_POSITION_ROW"] is True
        ),
        "IDENTITY_BOUND_POS_PRESENT_PARSEABLE": bool(
            classified["IDENTITY_BOUND_POS_PRESENT_PARSEABLE"] is True
        ),
        "POS_EQUALS_BOUND_FILL_SZ": bool(classified["POS_EQUALS_BOUND_FILL_SZ"] is True),
        "EMPTY_DATA_NOT_TREATED_AS_ZERO": True,
        "ADMISSIBLE_PRIVATE_GET_SOURCE": live_source,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "NOT_INFERRED_FROM_FILL_FEE_OR_ORDER_STATE": True,
    }
    if live_source:
        field_eval = evaluate_live_position_reconciled_conjunction_v1(
            constituent_values=field_constituents,
            source_kind=ADMISSIBLE_SOURCE_KIND,
        )
        claim = bool(
            field_eval["claim_value"] is True and classified["ACTUAL_POSITION_RECONCILED"] is True
        )
    else:
        field_eval = {
            "canonical_definition": LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
            "claim_value": False,
            "adjudication": "FALSE_FAIL_CLOSED_NO_LIVE_GET",
            "false_required": [
                name
                for name in POSITION_FIELD_CONSTITUENTS
                if field_constituents.get(name) is not True
            ],
            "constituent_count": POSITION_FIELD_CONSTITUENT_COUNT,
            "source_kind": INJECTED_EVIDENCE_SOURCE_KIND,
            "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
        }
        claim = False

    unresolved_reason: str | None = None
    if not positions_get_ok and live_source:
        unresolved_reason = "POSITIONS_GET_HTTP_CONJUNCTION_FAILED"
        claim = False
    elif live_source and classified["EMPTY_DATA_OBSERVED"] is True:
        unresolved_reason = "EMPTY_DATA_NOT_ZERO"
        claim = False
    elif live_source and classified["EPISTEMIC_CLASS"] == "IDENTITY_MISMATCH":
        unresolved_reason = "NO_IDENTITY_BOUND_POSITION_ROW"
        claim = False
    elif live_source and classified["EPISTEMIC_CLASS"] == "AMBIGUOUS_IDENTITY_BOUND_ROWS":
        unresolved_reason = "AMBIGUOUS_IDENTITY_BOUND_POSITION_ROWS"
        claim = False
    elif live_source and classified["SCHEMA_AMBIGUITY_REASONS"]:
        unresolved_reason = str(classified["SCHEMA_AMBIGUITY_REASONS"][0])
        claim = False
    elif live_source and classified["POS_UNPARSEABLE"] is True:
        unresolved_reason = "POS_FIELD_UNPARSEABLE"
        claim = False
    elif live_source and classified["POS_FIELD_MISSING_OR_EMPTY"] is True:
        unresolved_reason = "POS_FIELD_MISSING_OR_EMPTY"
        claim = False
    elif live_source and classified["POS_IS_ZERO"] is True:
        unresolved_reason = "ROW_WITH_POS_ZERO_NOT_RECONCILED"
        claim = False
    elif live_source and classified["QTY_DIVERGENCE"] is True:
        unresolved_reason = "POS_QTY_DIVERGES_FROM_BOUND_FILL_SZ"
        claim = False
    elif live_source and not claim:
        unresolved_reason = "CRITERION_NOT_SATISFIED"

    if claim:
        case = "CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE"
        reason = "IDENTITY_BOUND_POS_EQUALS_BOUND_FILL_SZ"
    elif unresolved_reason == "EMPTY_DATA_NOT_ZERO":
        case = "CASE_EMPTY_DATA_NOT_ZERO"
        reason = unresolved_reason
    elif unresolved_reason == "ROW_WITH_POS_ZERO_NOT_RECONCILED":
        case = "CASE_POS_ZERO_ROW_NOT_RECONCILED"
        reason = unresolved_reason
    elif unresolved_reason == "NO_IDENTITY_BOUND_POSITION_ROW":
        case = "CASE_LIVE_POSITION_IDENTITY_MISMATCH_FAIL_CLOSED"
        reason = unresolved_reason
    elif unresolved_reason in {
        "POS_FIELD_MISSING_OR_EMPTY",
        "POS_FIELD_UNPARSEABLE",
        "POSITIONS_GET_HTTP_CONJUNCTION_FAILED",
        "CRITERION_NOT_SATISFIED",
        "POS_QTY_DIVERGES_FROM_BOUND_FILL_SZ",
    }:
        case = "CASE_LIVE_POSITION_NOT_RECONCILED"
        reason = unresolved_reason or "CRITERION_NOT_SATISFIED"
    elif unresolved_reason:
        case = "CASE_LIVE_POSITION_AMBIGUOUS_FAIL_CLOSED"
        reason = unresolved_reason
    else:
        case = "CASE_LIVE_POSITION_NOT_RECONCILED"
        reason = "CRITERION_NOT_SATISFIED"

    return {
        "canonical_definition": LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
        "producer": POSITION_PRODUCER,
        "POSITION_PRODUCER": POSITION_PRODUCER,
        "POSITION_PROOF_CRITERION": LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
        "proof_criterion_bound": True,
        "POSITION_EVIDENCE_SOURCE": POSITION_ENDPOINT_PATH if live_source else None,
        "positions_http_constituents": POSITION_HTTP_CONSTITUENTS,
        "positions_http_constituent_count": POSITION_HTTP_CONSTITUENT_COUNT,
        "positions_http_constituent_values": http_constituents,
        "positions_http_conjunction": http_eval,
        "field_constituents": POSITION_FIELD_CONSTITUENTS,
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "POSITION_PROOF_CONJUNCTION_STATUS": field_eval.get("adjudication"),
        "adjudicated_value": claim,
        "claim_value": claim,
        "LIVE_FEE_OBSERVED": True,
        "LIVE_POSITION_RECONCILED": claim,
        "LIVE_ACCOUNTING_RECONSTRUCTED": False,
        "SECTION_11_14_COMPLETE": False,
        "UNRESOLVED_REASON": unresolved_reason,
        "LIVE_POSITION_RECONCILIATION_REASON": reason,
        "CASE_ADJUDICATION": case,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "RAW_POSITION_ROW_COUNT": classified["RAW_POSITION_ROW_COUNT"],
        "RAW_POSITION_QTY_IF_OBSERVED": classified["RAW_POSITION_QTY_IF_OBSERVED"],
        "RAW_POSITION_STATE_IF_OBSERVED": classified["RAW_POSITION_STATE_IF_OBSERVED"],
        "RAW_POS_ID_IF_OBSERVED": classified["RAW_POS_ID_IF_OBSERVED"],
        "RAW_POS_SIDE_IF_OBSERVED": classified["RAW_POS_SIDE_IF_OBSERVED"],
        "POSITION_IDENTITY_MATCH": classified["POSITION_IDENTITY_MATCH"],
        "POSITION_SEMANTICS_STATUS": classified["EPISTEMIC_CLASS"],
        "EMPTY_DATA_IS_ZERO": False,
        "EMPTY_DATA_OBSERVED": classified["EMPTY_DATA_OBSERVED"],
        "row_classification": classified,
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "POSITION_SOURCE_KIND": source_kind if live_source else INJECTED_EVIDENCE_SOURCE_KIND,
    }
