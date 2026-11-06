"""Adjudicate LIVE_RESTART_RECONSTRUCTED from persisted Live restart handoff.

Does not GET. Does not POST. Does not execute a process restart.
Injected evidence cannot promote the live field. Accounting closure,
position reconciliation, Testnet restart, Cap 11.5/§11.12.6 fixtures, and
§11.17 LIVE_RESTART_PROVEN are not this field.
LIVE_AUTONOMOUS_RECOVERY_OBSERVED remains false even if restart were reconstructed.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    INJECTED_EVIDENCE_SOURCE_KIND,
    RESTART_FIELD_CONSTITUENT_COUNT,
    RESTART_FIELD_CONSTITUENTS,
    RESTART_IDENTITY_EQUATION,
    RESTART_PRODUCER,
    classify_restart_handoff_v1,
    evaluate_live_restart_reconstructed_conjunction_v1,
)

CENSUS_SOURCE_KIND = "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"


def adjudicate_live_restart_reconstructed_v1(
    *,
    restart_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if LIVE_ACCOUNTING_RECONSTRUCTED is not True:
        raise Section1114OfflineSurfaceError("ACCOUNTING_PREDECESSOR_FALSE")
    evidence = dict(restart_evidence or {})
    source_kind = str(evidence.get("source_kind") or INJECTED_EVIDENCE_SOURCE_KIND).strip()
    refuse_forbidden_live_source_v1(
        field_name="LIVE_RESTART_RECONSTRUCTED",
        source_kind=source_kind,
    )
    live_source = source_kind == ADMISSIBLE_SOURCE_KIND
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_RESTART_RECONSTRUCTION_GO")
    if evidence.get("GET_PERFORMED") is True or evidence.get("PRIVATE_GET_USED") is True:
        raise Section1114OfflineSurfaceError("PRIVATE_GET_INVOKED_BY_RESTART_RECONSTRUCTION_GO")
    if evidence.get("CANCEL_USED") is True or evidence.get("AMEND_USED") is True:
        raise Section1114OfflineSurfaceError("ORDER_MUTATION_INVOKED_BY_RESTART_RECONSTRUCTION_GO")
    if evidence.get("FLATTEN_EXECUTE_USED") is True:
        raise Section1114OfflineSurfaceError("FLATTEN_INVOKED_BY_RESTART_RECONSTRUCTION_GO")
    if evidence.get("RESTART_EXECUTION") is True or evidence.get("RESTART_USED") is True:
        raise Section1114OfflineSurfaceError(
            "RESTART_EXECUTION_INVOKED_BY_RESTART_RECONSTRUCTION_GO"
        )
    if evidence.get("LIVE_AUTONOMOUS_RECOVERY_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("RECOVERY_PROMOTED_BY_RESTART_RECONSTRUCTION")
    if not live_source and evidence.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("RESTART_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")

    durable_raw = evidence.get("durable_handoff")
    census_raw = evidence.get("census")
    durable_handoff = dict(durable_raw) if isinstance(durable_raw, Mapping) else None
    census = dict(census_raw) if isinstance(census_raw, Mapping) else {}
    classified = classify_restart_handoff_v1(
        durable_handoff=durable_handoff,
        census=census,
    )
    field_constituents: dict[str, bool | None] = {
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "DURABLE_PRE_RESTART_HANDOFF_PRESENT": bool(
            classified["DURABLE_PRE_RESTART_HANDOFF_PRESENT"] is True
        ),
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": bool(
            classified["HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH"] is True
        ),
        "POST_RESTART_IDENTITY_RECONSTRUCTABLE": bool(
            classified["POST_RESTART_IDENTITY_RECONSTRUCTABLE"] is True
        ),
        "IDENTITY_BOUND_HANDOFF_MATCHES_LIVE_SUBMIT": bool(
            classified["IDENTITY_BOUND_HANDOFF_MATCHES_LIVE_SUBMIT"] is True
        ),
        "NO_RESUBMIT": bool(evidence.get("POST_USED") is not True),
        "NO_SILENT_REINITIALIZATION": bool(classified["NO_SILENT_REINITIALIZATION"] is True),
        "ADMISSIBLE_PERSISTED_LIVE_RESTART_HANDOFF_SOURCE": live_source,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
    }
    if live_source:
        field_eval = evaluate_live_restart_reconstructed_conjunction_v1(
            constituent_values=field_constituents,
            source_kind=ADMISSIBLE_SOURCE_KIND,
        )
        claim = bool(
            field_eval["claim_value"] is True and classified["ACTUAL_RESTART_RECONSTRUCTED"] is True
        )
    else:
        field_eval = {
            "canonical_definition": LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
            "claim_value": False,
            "adjudication": "FALSE_FAIL_CLOSED_NO_PERSISTED_LIVE_RESTART_HANDOFF",
            "false_required": [
                name for name, value in field_constituents.items() if value is not True
            ],
            "source_kind": source_kind,
            "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
            "producer": RESTART_PRODUCER,
        }
        claim = False

    reason = (
        "IDENTITY_BOUND_LIVE_RESTART_HANDOFF_RECONSTRUCTED"
        if claim
        else classified["EPISTEMIC_CLASS"]
    )
    case = (
        "CASE_LIVE_RESTART_RECONSTRUCTED_RECOVERY_INELIGIBLE"
        if claim
        else "CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
    )
    return {
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": claim,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "LIVE_END_TO_END_EVIDENCE_PROVEN": False,
        "SECTION_11_14_COMPLETE": False,
        "CASE_ADJUDICATION": case,
        "adjudicated_value": claim,
        "claim_value": claim,
        "canonical_definition": LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
        "RESTART_PROOF_CRITERION": LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
        "RESTART_PRODUCER": RESTART_PRODUCER,
        "RESTART_SOURCE_KIND": source_kind
        if live_source
        else (source_kind or INJECTED_EVIDENCE_SOURCE_KIND),
        "RESTART_EVIDENCE_SOURCE": "PERSISTED_LIVE_RESTART_HANDOFF_CENSUS",
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "RESTART_SEMANTICS_STATUS": classified["EPISTEMIC_CLASS"],
        "LIVE_RESTART_RECONSTRUCTION_REASON": reason,
        "UNRESOLVED_REASON": None if claim else classified["EPISTEMIC_CLASS"],
        "EARLIEST_MISSING_FACT": None if claim else "DURABLE_LIVE_PRE_RESTART_HANDOFF",
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "RESTART_EXECUTION": False,
        "proof_criterion_bound": True,
        "producer": RESTART_PRODUCER,
        "field_constituents": list(RESTART_FIELD_CONSTITUENTS),
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "field_constituent_count": RESTART_FIELD_CONSTITUENT_COUNT,
        "path_classification": classified,
        "CENSUS_SOURCE_KIND": CENSUS_SOURCE_KIND,
        "TESTNET_RESTART_IS_NOT_THIS_FIELD": True,
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
        "CAP_11_5_FIXTURE_IS_NOT_THIS_FIELD": True,
        "SECTION_11_12_6_FIXTURE_IS_NOT_THIS_FIELD": True,
        "SECTION_11_17_LIVE_RESTART_PROVEN_IS_NOT_THIS_FIELD": True,
    }
