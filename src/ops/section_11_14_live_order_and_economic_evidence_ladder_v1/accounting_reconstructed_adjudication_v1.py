"""Adjudicate LIVE_ACCOUNTING_RECONSTRUCTED from persisted fill/fee/position.

Does not GET. Does not POST. Injected evidence cannot promote the live field.
Balance change, unrealized PnL, inferred slippage, Cap 7.1 reconstruction,
and §11.17 LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN are not this field.
LIVE_RESTART_RECONSTRUCTED remains false even when accounting is reconstructed.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_identity_v1 import (
    ACCOUNTING_TOLERANCE,
    ACCOUNTING_TOLERANCE_AUTHORITY,
    ACCOUNTING_UNIT,
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_FEE_EVIDENCE_RUN_ID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    BOUND_POSITION_EVIDENCE_RUN_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_predicate_v1 import (
    ACCOUNTING_FIELD_CONSTITUENT_COUNT,
    ACCOUNTING_FIELD_CONSTITUENTS,
    ACCOUNTING_IDENTITY_EQUATION,
    ACCOUNTING_PRODUCER,
    ADMISSIBLE_SOURCE_KIND,
    INJECTED_EVIDENCE_SOURCE_KIND,
    classify_accounting_path_v1,
    evaluate_live_accounting_reconstructed_conjunction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
    LIVE_POSITION_RECONCILED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)


def adjudicate_live_accounting_reconstructed_v1(
    *,
    accounting_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if LIVE_POSITION_RECONCILED is not True:
        raise Section1114OfflineSurfaceError("POSITION_PREDECESSOR_FALSE")
    evidence = dict(accounting_evidence or {})
    source_kind = str(evidence.get("source_kind") or INJECTED_EVIDENCE_SOURCE_KIND).strip()
    refuse_forbidden_live_source_v1(
        field_name="LIVE_ACCOUNTING_RECONSTRUCTED",
        source_kind=source_kind,
    )
    live_source = source_kind == ADMISSIBLE_SOURCE_KIND
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_ACCOUNTING_RECONSTRUCTION_GO")
    if evidence.get("GET_PERFORMED") is True or evidence.get("PRIVATE_GET_USED") is True:
        raise Section1114OfflineSurfaceError("PRIVATE_GET_INVOKED_BY_ACCOUNTING_RECONSTRUCTION_GO")
    if evidence.get("CANCEL_USED") is True or evidence.get("AMEND_USED") is True:
        raise Section1114OfflineSurfaceError(
            "ORDER_MUTATION_INVOKED_BY_ACCOUNTING_RECONSTRUCTION_GO"
        )
    if evidence.get("FLATTEN_EXECUTE_USED") is True:
        raise Section1114OfflineSurfaceError("FLATTEN_INVOKED_BY_ACCOUNTING_RECONSTRUCTION_GO")
    if evidence.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("RESTART_PROMOTED_BY_ACCOUNTING_RECONSTRUCTION")
    if not live_source and evidence.get("LIVE_ACCOUNTING_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("ACCOUNTING_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")

    fill_raw = evidence.get("fill_row")
    position_raw = evidence.get("position_row")
    fill_row = dict(fill_raw) if isinstance(fill_raw, Mapping) else None
    position_row = dict(position_raw) if isinstance(position_raw, Mapping) else None
    classified = classify_accounting_path_v1(fill_row=fill_row, position_row=position_row)
    field_constituents: dict[str, bool | None] = {
        "LIVE_POSITION_RECONCILED": True,
        "IDENTITY_BOUND_REQUIRED_TERMS_PRESENT_PARSEABLE": bool(
            classified["IDENTITY_BOUND_REQUIRED_TERMS_PRESENT_PARSEABLE"] is True
        ),
        "FEE_CCY_EQUALS_POSITION_CCY": bool(classified["FEE_CCY_EQUALS_POSITION_CCY"] is True),
        "FILL_FEE_EQUALS_POSITION_FEE": bool(classified["FILL_FEE_EQUALS_POSITION_FEE"] is True),
        "FILL_PNL_EQUALS_POSITION_PNL": bool(classified["FILL_PNL_EQUALS_POSITION_PNL"] is True),
        "TRADE_ID_IDENTITY_MATCH": bool(classified["TRADE_ID_IDENTITY_MATCH"] is True),
        "REALIZED_PNL_IDENTITY_HOLDS": bool(classified["REALIZED_PNL_IDENTITY_HOLDS"] is True),
        "ADMISSIBLE_PERSISTED_LIVE_PATH_SOURCE": live_source,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "MISSING_NOT_REPLACED_BY_ZERO": bool(classified["MISSING_NOT_REPLACED_BY_ZERO"] is True),
    }
    if live_source:
        field_eval = evaluate_live_accounting_reconstructed_conjunction_v1(
            constituent_values=field_constituents,
            source_kind=ADMISSIBLE_SOURCE_KIND,
        )
        claim = bool(
            field_eval["claim_value"] is True
            and classified["ACTUAL_ACCOUNTING_RECONSTRUCTED"] is True
        )
    else:
        field_eval = {
            "canonical_definition": LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
            "claim_value": False,
            "adjudication": "FALSE_FAIL_CLOSED_NO_PERSISTED_LIVE_PATH",
            "false_required": [
                name for name, value in field_constituents.items() if value is not True
            ],
            "source_kind": source_kind,
            "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
            "producer": ACCOUNTING_PRODUCER,
        }
        claim = False

    reason = "IDENTITY_BOUND_REALIZED_PNL_RECONSTRUCTED" if claim else classified["EPISTEMIC_CLASS"]
    case = (
        "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE"
        if claim
        else "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_FAIL_CLOSED"
    )
    return {
        "LIVE_POSITION_RECONCILED": True,
        "LIVE_ACCOUNTING_RECONSTRUCTED": claim,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "SECTION_11_14_COMPLETE": False,
        "CASE_ADJUDICATION": case,
        "adjudicated_value": claim,
        "claim_value": claim,
        "canonical_definition": LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
        "ACCOUNTING_PROOF_CRITERION": LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
        "ACCOUNTING_PRODUCER": ACCOUNTING_PRODUCER,
        "ACCOUNTING_SOURCE_KIND": source_kind if live_source else INJECTED_EVIDENCE_SOURCE_KIND,
        "ACCOUNTING_EVIDENCE_SOURCE": "PERSISTED_IDENTITY_BOUND_FILL_FEE_POSITION_PATH",
        "ACCOUNTING_IDENTITY_EQUATION": ACCOUNTING_IDENTITY_EQUATION,
        "ACCOUNTING_RESULT": classified["ACCOUNTING_RESULT"] if claim else None,
        "ACCOUNTING_RESULT_UNIT": classified["ACCOUNTING_RESULT_UNIT"] if claim else None,
        "ACCOUNTING_RESIDUAL": classified["ACCOUNTING_RESIDUAL"]
        if claim
        else classified["ACCOUNTING_RESIDUAL"],
        "ACCOUNTING_RESIDUAL_UNIT": classified["ACCOUNTING_RESIDUAL_UNIT"],
        "ACCOUNTING_TOLERANCE": ACCOUNTING_TOLERANCE,
        "ACCOUNTING_TOLERANCE_AUTHORITY": ACCOUNTING_TOLERANCE_AUTHORITY,
        "ACCOUNTING_UNIT": ACCOUNTING_UNIT,
        "ACCOUNTING_SEMANTICS_STATUS": classified["EPISTEMIC_CLASS"],
        "LIVE_ACCOUNTING_RECONSTRUCTION_REASON": reason,
        "UNRESOLVED_REASON": None if claim else classified["EPISTEMIC_CLASS"],
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "BOUND_FEE_EVIDENCE_RUN_ID": BOUND_FEE_EVIDENCE_RUN_ID,
        "BOUND_POSITION_EVIDENCE_RUN_ID": BOUND_POSITION_EVIDENCE_RUN_ID,
        "RAW_FILL_FEE_IF_OBSERVED": classified["RAW_FILL_FEE_IF_OBSERVED"],
        "RAW_FILL_PNL_IF_OBSERVED": classified["RAW_FILL_PNL_IF_OBSERVED"],
        "RAW_POSITION_FEE_IF_OBSERVED": classified["RAW_POSITION_FEE_IF_OBSERVED"],
        "RAW_POSITION_PNL_IF_OBSERVED": classified["RAW_POSITION_PNL_IF_OBSERVED"],
        "RAW_REALIZED_PNL_IF_OBSERVED": classified["RAW_REALIZED_PNL_IF_OBSERVED"],
        "RAW_FUNDING_FEE_IF_OBSERVED": classified["RAW_FUNDING_FEE_IF_OBSERVED"],
        "RAW_SETTLED_PNL_IF_OBSERVED": classified["RAW_SETTLED_PNL_IF_OBSERVED"],
        "RAW_UPL_IF_OBSERVED": classified["RAW_UPL_IF_OBSERVED"],
        "UPL_IN_REALIZED_IDENTITY": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "proof_criterion_bound": True,
        "producer": ACCOUNTING_PRODUCER,
        "field_constituents": list(ACCOUNTING_FIELD_CONSTITUENTS),
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "field_constituent_count": ACCOUNTING_FIELD_CONSTITUENT_COUNT,
        "path_classification": classified,
        "FILL_SOURCE_PATH": evidence.get("fill_source_path"),
        "POSITION_SOURCE_PATH": evidence.get("position_source_path"),
    }
