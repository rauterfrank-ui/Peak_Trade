"""Assemble deterministic offline §11.14 documents from repository state."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AUTHORITY_BOUNDARY_MAP_FILENAME,
    CANONICAL_BASE_SHA,
    CANONICAL_EVIDENCE_RUN_ID,
    CASE_ADJUDICATION,
    CONSTITUENT_MATRIX_FILENAME,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    FILL_OBSERVED_ADJUDICATION_FILENAME,
    FEE_OBSERVED_ADJUDICATION_FILENAME,
    POSITION_RECONCILED_ADJUDICATION_FILENAME,
    ACCOUNTING_RECONSTRUCTED_ADJUDICATION_FILENAME,
    RESTART_RECONSTRUCTED_ADJUDICATION_FILENAME,
    G12_DOES_NOT_AUTHORIZE_SECTION_11_14,
    G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS,
    G12_STATUS_REQUIRED,
    GATE_STATE_FILENAME,
    IMPLEMENTATION_SHA,
    LADDER_FIELD_COUNT,
    LADDER_FIELD_DEFAULTS,
    LADDER_FIELDS,
    LAST_CANONICALLY_CLOSED_STEP,
    LATER_FIELD_CENSUS_FILENAME,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_FILL_OBSERVED,
    LIVE_FEE_OBSERVED,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_POSITION_RECONCILED,
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_SUBMIT_ACK_OBSERVED,
    MANDATORY_LIVE_METRIC_COUNT,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    ORDER_PLAN_EVIDENCE_FILENAME,
    ORDER_PLAN_OBSERVED_ADJUDICATION_FILENAME,
    OWNER_GO,
    PATH_REACHABLE_ADJUDICATION_FILENAME,
    PREDECESSOR_SLICE,
    PREFLIGHT_FILENAME,
    PRIOR_OWNER_GO,
    PRIVATE_GET_BINDING_FILENAME,
    PRIVATE_GET_EVIDENCE_FILENAME,
    PRIVATE_READ_ONLY_ADJUDICATION_FILENAME,
    PRIVATE_READ_ONLY_GET_BINDING_FILENAME,
    PRIVATE_READ_ONLY_GET_EVIDENCE_FILENAME,
    RUNTIME_DEPENDENCY_GRAPH_FILENAME,
    RUNTIME_GATE_CLASSIFICATION_FILENAME,
    SCHEMA_VERSION,
    SECTION_11_14_AUTHORIZED,
    SECTION_11_14_COMPLETE,
    SECTION_11_14_OFFLINE_SURFACE_BOUND,
    STATIC_REACHABILITY_GRAPH_FILENAME,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.evidence_schema_v1 import (
    build_evidence_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.ladder_order_v1 import (
    assert_ladder_order_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.metrics_schema_v1 import (
    build_mandatory_live_metrics_schema_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reuse_vs_fresh_v1 import (
    build_reuse_vs_fresh_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_predicate_v1 import (
    build_constituent_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_graphs_v1 import (
    build_authority_boundary_map_v1,
    build_runtime_dependency_graph_v1,
    build_static_reachability_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.later_field_census_v1 import (
    build_later_field_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observed_adjudication_v1 import (
    adjudicate_live_order_plan_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_contract_v1 import (
    build_submit_ack_forensic_documents_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_adjudication_v1 import (
    adjudicate_live_submit_ack_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_adjudication_v1 import (
    adjudicate_live_fill_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fee_observed_adjudication_v1 import (
    adjudicate_live_fee_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_adjudication_v1 import (
    adjudicate_live_position_reconciled_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_adjudication_v1 import (
    adjudicate_live_accounting_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.private_read_only_gets_v1 import (
    bind_private_read_only_gets_before_request_v1,
    path_reachable_view_from_read_only_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_private_get_v1 import (
    bind_private_get_before_request_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.runtime_gate_classification_v1 import (
    classify_runtime_gates_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_field_adjudication_v1 import (
    adjudicate_static_fields_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.traceability_v1 import (
    build_traceability_matrix_v1,
)


def assemble_offline_surface_v1(
    *,
    repo_root: Path,
    origin_main_sha: str,
    private_get_evidence: Mapping[str, Any] | None = None,
    private_read_only_evidence: Mapping[str, Any] | None = None,
    order_plan_evidence: Mapping[str, Any] | None = None,
    submit_ack_evidence: Mapping[str, Any] | None = None,
    fill_evidence: Mapping[str, Any] | None = None,
    fee_evidence: Mapping[str, Any] | None = None,
    position_evidence: Mapping[str, Any] | None = None,
    accounting_evidence: Mapping[str, Any] | None = None,
    restart_evidence: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise RuntimeError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    assert_ladder_order_v1(LADDER_FIELD_DEFAULTS)
    ro_ev = dict(private_read_only_evidence) if private_read_only_evidence is not None else None
    if private_get_evidence is not None:
        path_ev: dict[str, Any] | None = dict(private_get_evidence)
    elif ro_ev is not None:
        path_ev = path_reachable_view_from_read_only_pack_v1(ro_ev)
    else:
        path_ev = None
    static_fields = adjudicate_static_fields_v1(
        repo_root=repo_root,
        private_get_evidence=path_ev,
        private_read_only_evidence=ro_ev,
    )
    path_claim = bool(static_fields["LIVE_EXECUTION_PATH_REACHABLE_VALUE"] is True)
    if path_claim is not bool(LIVE_EXECUTION_PATH_REACHABLE is True):
        raise RuntimeError("PATH_REACHABLE_CONSTANT_DRIFT_VS_ADJUDICATION")
    if path_claim and (path_ev is None or path_ev.get("POST_USED") is True):
        raise RuntimeError("PATH_REACHABLE_TRUE_WITHOUT_VALID_GET")
    if path_claim and path_ev.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is True:
        raise RuntimeError("GET_EVIDENCE_PROMOTED_LIVE_PRIVATE_READ_ONLY_PROVEN")
    ro_claim = bool(static_fields.get("LIVE_PRIVATE_READ_ONLY_PROVEN_VALUE") is True)
    if ro_claim is not bool(LIVE_PRIVATE_READ_ONLY_PROVEN is True):
        raise RuntimeError("PRIVATE_READ_ONLY_CONSTANT_DRIFT_VS_ADJUDICATION")
    if ro_claim and (ro_ev is None or ro_ev.get("POST_USED") is True):
        raise RuntimeError("PRIVATE_READ_ONLY_TRUE_WITHOUT_VALID_GET")
    if ro_claim and ro_ev.get("LIVE_ORDER_PLAN_OBSERVED") is True:
        raise RuntimeError("GET_EVIDENCE_PROMOTED_LIVE_ORDER_PLAN_OBSERVED")
    op_ev = dict(order_plan_evidence) if order_plan_evidence is not None else None
    order_plan_fields = adjudicate_live_order_plan_observed_v1(order_plan_evidence=op_ev)
    order_claim = bool(order_plan_fields.get("adjudicated_value") is True)
    if order_claim is not bool(LIVE_ORDER_PLAN_OBSERVED is True):
        raise RuntimeError("ORDER_PLAN_CONSTANT_DRIFT_VS_ADJUDICATION")
    if order_claim and (op_ev is None or op_ev.get("POST_USED") is True):
        raise RuntimeError("ORDER_PLAN_TRUE_WITHOUT_VALID_GATED_PATH")
    if order_claim and op_ev.get("LIVE_SUBMIT_ACK_OBSERVED") is True:
        raise RuntimeError("ORDER_PLAN_EVIDENCE_PROMOTED_SUBMIT_ACK")
    ack_ev = dict(submit_ack_evidence) if submit_ack_evidence is not None else None
    if LIVE_SUBMIT_ACK_OBSERVED is True and ack_ev is None:
        raise RuntimeError("ACK_TRUE_WITHOUT_LIVE_POST_EVIDENCE")
    ack_fields = adjudicate_live_submit_ack_observed_v1(submit_ack_evidence=ack_ev)
    ack_claim = bool(ack_fields.get("adjudicated_value") is True)
    if ack_claim is not bool(LIVE_SUBMIT_ACK_OBSERVED is True):
        raise RuntimeError("ACK_CONSTANT_DRIFT_VS_ADJUDICATION")
    if ack_claim and (
        ack_ev is None
        or ack_ev.get("POST_USED") is not True
        or ack_ev.get("historical_plan_reused") is True
        or str(ack_ev.get("source_kind") or "") != "GOVERNED_CURRENT_LIVE_POST"
    ):
        raise RuntimeError("ACK_TRUE_WITHOUT_VALID_LIVE_POST")
    if ack_claim and ack_ev.get("LIVE_FILL_OBSERVED") is True:
        raise RuntimeError("ACK_EVIDENCE_PROMOTED_FILL")
    fill_ev = dict(fill_evidence) if fill_evidence is not None else None
    if LIVE_FILL_OBSERVED is True and fill_ev is None:
        raise RuntimeError("FILL_TRUE_WITHOUT_LIVE_GET_EVIDENCE")
    fill_fields = adjudicate_live_fill_observed_v1(fill_evidence=fill_ev)
    fill_claim = bool(fill_fields.get("adjudicated_value") is True)
    if fill_claim is not bool(LIVE_FILL_OBSERVED is True):
        raise RuntimeError("FILL_CONSTANT_DRIFT_VS_ADJUDICATION")
    if fill_claim and (
        fill_ev is None
        or fill_ev.get("POST_USED") is True
        or str(fill_ev.get("source_kind") or "") != "GOVERNED_CURRENT_PRIVATE_GET"
    ):
        raise RuntimeError("FILL_TRUE_WITHOUT_VALID_LIVE_GET")
    if fill_claim and fill_ev.get("LIVE_FEE_OBSERVED") is True:
        raise RuntimeError("FILL_EVIDENCE_PROMOTED_FEE")
    fee_ev = dict(fee_evidence) if fee_evidence is not None else None
    if LIVE_FEE_OBSERVED is True and fee_ev is None:
        raise RuntimeError("FEE_TRUE_WITHOUT_LIVE_GET_EVIDENCE")
    fee_fields = adjudicate_live_fee_observed_v1(fee_evidence=fee_ev)
    fee_claim = bool(fee_fields.get("adjudicated_value") is True)
    if fee_claim is not bool(LIVE_FEE_OBSERVED is True):
        raise RuntimeError("FEE_CONSTANT_DRIFT_VS_ADJUDICATION")
    if fee_claim and (
        fee_ev is None
        or fee_ev.get("POST_USED") is True
        or str(fee_ev.get("source_kind") or "") != "GOVERNED_CURRENT_PRIVATE_GET"
    ):
        raise RuntimeError("FEE_TRUE_WITHOUT_VALID_LIVE_GET")
    if fee_claim and fee_ev.get("LIVE_POSITION_RECONCILED") is True:
        raise RuntimeError("FEE_EVIDENCE_PROMOTED_POSITION")
    position_ev = dict(position_evidence) if position_evidence is not None else None
    if LIVE_POSITION_RECONCILED is True and position_ev is None:
        raise RuntimeError("POSITION_TRUE_WITHOUT_LIVE_GET_EVIDENCE")
    position_fields = adjudicate_live_position_reconciled_v1(position_evidence=position_ev)
    position_claim = bool(position_fields.get("adjudicated_value") is True)
    if position_claim is not bool(LIVE_POSITION_RECONCILED is True):
        raise RuntimeError("POSITION_CONSTANT_DRIFT_VS_ADJUDICATION")
    if position_claim and (
        position_ev is None
        or position_ev.get("POST_USED") is True
        or str(position_ev.get("source_kind") or "") != "GOVERNED_CURRENT_PRIVATE_GET"
    ):
        raise RuntimeError("POSITION_TRUE_WITHOUT_VALID_LIVE_GET")
    if position_claim and position_ev.get("LIVE_ACCOUNTING_RECONSTRUCTED") is True:
        raise RuntimeError("POSITION_EVIDENCE_PROMOTED_ACCOUNTING")
    accounting_ev = dict(accounting_evidence) if accounting_evidence is not None else None
    if LIVE_ACCOUNTING_RECONSTRUCTED is True and accounting_ev is None:
        raise RuntimeError("ACCOUNTING_TRUE_WITHOUT_PERSISTED_PATH_EVIDENCE")
    accounting_fields = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=accounting_ev
    )
    accounting_claim = bool(accounting_fields.get("adjudicated_value") is True)
    if accounting_claim is not bool(LIVE_ACCOUNTING_RECONSTRUCTED is True):
        raise RuntimeError("ACCOUNTING_CONSTANT_DRIFT_VS_ADJUDICATION")
    if accounting_claim and (
        accounting_ev is None
        or accounting_ev.get("POST_USED") is True
        or accounting_ev.get("GET_PERFORMED") is True
        or accounting_ev.get("PRIVATE_GET_USED") is True
        or str(accounting_ev.get("source_kind") or "")
        != "GOVERNED_PERSISTED_IDENTITY_BOUND_LIVE_ECONOMIC_PATH"
    ):
        raise RuntimeError("ACCOUNTING_TRUE_WITHOUT_VALID_PERSISTED_PATH")
    if accounting_claim and accounting_ev.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise RuntimeError("ACCOUNTING_EVIDENCE_PROMOTED_RESTART")
    restart_ev = dict(restart_evidence) if restart_evidence is not None else None
    if LIVE_RESTART_RECONSTRUCTED is True and restart_ev is None:
        raise RuntimeError("RESTART_TRUE_WITHOUT_PERSISTED_HANDOFF_EVIDENCE")
    restart_fields = adjudicate_live_restart_reconstructed_v1(restart_evidence=restart_ev)
    restart_claim = bool(restart_fields.get("adjudicated_value") is True)
    if restart_claim is not bool(LIVE_RESTART_RECONSTRUCTED is True):
        raise RuntimeError("RESTART_CONSTANT_DRIFT_VS_ADJUDICATION")
    if restart_claim and (
        restart_ev is None
        or restart_ev.get("POST_USED") is True
        or restart_ev.get("GET_PERFORMED") is True
        or restart_ev.get("PRIVATE_GET_USED") is True
        or restart_ev.get("RESTART_EXECUTION") is True
        or str(restart_ev.get("source_kind") or "") != "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF"
    ):
        raise RuntimeError("RESTART_TRUE_WITHOUT_VALID_PERSISTED_HANDOFF")
    if restart_claim and restart_ev.get("LIVE_AUTONOMOUS_RECOVERY_OBSERVED") is True:
        raise RuntimeError("RESTART_EVIDENCE_PROMOTED_RECOVERY")
    metrics = build_mandatory_live_metrics_schema_v1()
    reuse = build_reuse_vs_fresh_matrix_v1()
    traceability = build_traceability_matrix_v1(
        ladder_values=LADDER_FIELD_DEFAULTS,
        metrics_schema=metrics,
    )
    evidence_records = []
    for field_name in LADDER_FIELDS:
        claim_true = bool(LADDER_FIELD_DEFAULTS[field_name] is True)
        if field_name == "LIVE_EXECUTION_PATH_REACHABLE":
            source_kind = (
                "GOVERNED_CURRENT_PRIVATE_GET" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_PRE_SUBMIT_PATH_REACHABLE" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R2_CONDITIONAL_PRIVATE_GET"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_EXECUTION_CODE_EXISTS":
            source_kind = "REPOSITORY_IMPLEMENTATION"
            status = "TRUE_STATIC_INTEGRATED_PRODUCTIVE_PATH"
            authority = "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
        elif field_name == "LIVE_PRIVATE_READ_ONLY_PROVEN":
            source_kind = (
                "GOVERNED_CURRENT_PRIVATE_GET" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_PRIVATE_READ_ONLY" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R2_CONDITIONAL_PRIVATE_GET"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_ORDER_PLAN_OBSERVED":
            source_kind = (
                "GOVERNED_CURRENT_GATED_SUBMIT_PATH" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_LIVE_ORDER_PLAN_OBSERVED" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R3_SESSION_GATED_SUBMIT_PATH_NO_POST"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_SUBMIT_ACK_OBSERVED":
            source_kind = (
                "GOVERNED_CURRENT_LIVE_POST" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_LIVE_SUBMIT_ACK_OBSERVED" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R4_EXACT_SINGLE_LIVE_ENTRY_SUBMIT_POST"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_FILL_OBSERVED":
            source_kind = (
                "GOVERNED_CURRENT_PRIVATE_GET" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_LIVE_FILL_OBSERVED" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R2_CONDITIONAL_PRIVATE_GET"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_FEE_OBSERVED":
            source_kind = (
                "GOVERNED_CURRENT_PRIVATE_GET" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_LIVE_FEE_OBSERVED" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R2_CONDITIONAL_PRIVATE_GET"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_POSITION_RECONCILED":
            source_kind = (
                "GOVERNED_CURRENT_PRIVATE_GET" if claim_true else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = "TRUE_CURRENT_LIVE_POSITION_RECONCILED" if claim_true else "FALSE_FAIL_CLOSED"
            authority = (
                "R2_CONDITIONAL_PRIVATE_GET"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        elif field_name == "LIVE_ACCOUNTING_RECONSTRUCTED":
            source_kind = (
                "GOVERNED_PERSISTED_IDENTITY_BOUND_LIVE_ECONOMIC_PATH"
                if claim_true
                else "GOVERNED_OFFLINE_CONTRACT"
            )
            status = (
                "TRUE_CURRENT_LIVE_ACCOUNTING_RECONSTRUCTED" if claim_true else "FALSE_FAIL_CLOSED"
            )
            authority = (
                "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
                if claim_true
                else "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
            )
        else:
            source_kind = "GOVERNED_OFFLINE_CONTRACT"
            status = "FALSE_FAIL_CLOSED"
            authority = "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
        observed_at_by_field = {
            "LIVE_RESTART_RECONSTRUCTED": (restart_ev or accounting_ev or {}).get(
                "RESPONSE_TIME_UTC"
            ),
            "LIVE_ACCOUNTING_RECONSTRUCTED": (accounting_ev or {}).get("RESPONSE_TIME_UTC"),
            "LIVE_POSITION_RECONCILED": (position_ev or fee_ev or fill_ev or {}).get(
                "RESPONSE_TIME_UTC"
            ),
            "LIVE_FEE_OBSERVED": (fee_ev or fill_ev or {}).get("RESPONSE_TIME_UTC"),
            "LIVE_FILL_OBSERVED": (fill_ev or {}).get("RESPONSE_TIME_UTC"),
            "LIVE_SUBMIT_ACK_OBSERVED": (ack_ev or op_ev or ro_ev or path_ev or {}).get(
                "RESPONSE_TIME_UTC"
            ),
            "LIVE_ORDER_PLAN_OBSERVED": (op_ev or ro_ev or path_ev or {}).get("RESPONSE_TIME_UTC"),
            "LIVE_PRIVATE_READ_ONLY_PROVEN": (ro_ev or path_ev or {}).get("RESPONSE_TIME_UTC"),
            "LIVE_EXECUTION_PATH_REACHABLE": (path_ev or {}).get("RESPONSE_TIME_UTC"),
        }
        evidence_records.append(
            build_evidence_record_v1(
                ladder_stage=field_name,
                claim_name=field_name,
                claim_value=claim_true,
                evidence_class="3_ALREADY_ADJUDICATED_CONCLUSION",
                source_kind=source_kind,
                source_path_or_runtime_source=(
                    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                ),
                observed_at=observed_at_by_field.get(field_name),
                predecessor_claims=[PREDECESSOR_SLICE],
                provenance=OWNER_GO,
                adjudication_status=status,
                contradiction_status="NONE",
                authority_scope=authority,
            )
        )
    ladder_state = {
        "schema_version": SCHEMA_VERSION,
        "fields": list(LADDER_FIELDS),
        "field_count": LADDER_FIELD_COUNT,
        "values": dict(LADDER_FIELD_DEFAULTS),
        "order_enforced": True,
    }
    get_used = False
    public_get_used = False
    venue_requests = 0
    mutation_boundary = {
        "VENUE_REQUESTS": venue_requests,
        "PUBLIC_GET": public_get_used,
        "PRIVATE_GET": get_used,
        "CREDENTIAL_USE": False,
        "POST": False,
        "PREDECESSOR_POST": True,
        "ORDER_SUBMIT": False,
        "CANCEL": False,
        "AMEND": False,
        "FLATTEN_EXECUTE": False,
        "FUNDING": False,
        "SECTION_11_14_RUNTIME_EXECUTION": False,
        "COLLECTOR_ACTIVATED": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
        "LIVE_SUBMIT_ACK_OBSERVED": ack_claim,
        "LIVE_FILL_OBSERVED": fill_claim,
        "LIVE_FEE_OBSERVED": fee_claim,
        "LIVE_POSITION_RECONCILED": position_claim,
        "LIVE_ACCOUNTING_RECONSTRUCTED": accounting_claim,
        "LIVE_RESTART_RECONSTRUCTED": restart_claim,
        "GATE_MUTATION": False,
        "SESSION_LIVE_GATE_ACTIVATION": False,
        "THIS_GO_GET": False,
        "PREDECESSOR_ORDER_PLAN_ATTACHED": op_ev is not None,
        "EARLIEST_MUTATION_BOUNDARY": "LIVE_RESTART_RECONSTRUCTED",
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "THIS_SLICE": THIS_SLICE,
        "G12_STATUS_REQUIRED": G12_STATUS_REQUIRED,
        "G12_DOES_NOT_AUTHORIZE_SECTION_11_14": G12_DOES_NOT_AUTHORIZE_SECTION_11_14,
        "G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS": (
            G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS
        ),
        "CANONICAL_BASE_SHA": CANONICAL_BASE_SHA,
        "IMPLEMENTATION_SHA": IMPLEMENTATION_SHA,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
    }
    adjudication = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "SECTION_11_14_AUTHORIZED": SECTION_11_14_AUTHORIZED,
        "SECTION_11_14_COMPLETE": SECTION_11_14_COMPLETE,
        "SECTION_11_14_OFFLINE_SURFACE_BOUND": SECTION_11_14_OFFLINE_SURFACE_BOUND,
        "STATIC_FIELDS": static_fields,
        "LADDER_VALUES": dict(LADDER_FIELD_DEFAULTS),
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
        "EVIDENCE_RECORDS": evidence_records,
    }
    summary = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_SUMMARY_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "CANONICAL_BASE_SHA": CANONICAL_BASE_SHA,
        "SECTION_11_14_OFFLINE_SURFACE_BOUND": True,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "LADDER_FIELD_COUNT": LADDER_FIELD_COUNT,
        "MANDATORY_LIVE_METRIC_COUNT": MANDATORY_LIVE_METRIC_COUNT,
        "LIVE_EXECUTION_CODE_EXISTS": True,
        "LIVE_EXECUTION_PATH_REACHABLE": path_claim,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
        "LIVE_SUBMIT_ACK_OBSERVED": LIVE_SUBMIT_ACK_OBSERVED,
        "LIVE_FILL_OBSERVED": fill_claim,
        "LIVE_FEE_OBSERVED": fee_claim,
        "LIVE_POSITION_RECONCILED": position_claim,
        "LIVE_ACCOUNTING_RECONSTRUCTED": accounting_claim,
        "LIVE_RESTART_RECONSTRUCTED": restart_claim,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "POST_USED": False,
        "GET_USED": False,
        "PUBLIC_GET_USED": False,
        "CREDENTIAL_USE": False,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "PREDECESSOR_ORDER_PLAN_ATTACHED": op_ev is not None,
    }
    claims = {
        **CLAIMS,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "LIVE_EXECUTION_PATH_REACHABLE": path_claim,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
        "LIVE_SUBMIT_ACK_OBSERVED": LIVE_SUBMIT_ACK_OBSERVED,
        "LIVE_FILL_OBSERVED": fill_claim,
        "LIVE_FEE_OBSERVED": fee_claim,
        "LIVE_POSITION_RECONCILED": position_claim,
        "LIVE_ACCOUNTING_RECONSTRUCTED": accounting_claim,
        "LIVE_RESTART_RECONSTRUCTED": restart_claim,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
    }
    assert_contract_invariants_v1(claims)
    assert_contract_invariants_v1(summary)
    graph = static_fields["LIVE_EXECUTION_CODE_EXISTS"].get("static_execution_graph") or {}
    classification = graph.get("classification_summary") or {}
    documents: dict[str, dict[str, Any]] = {
        "claims.json": claims,
        "SUMMARY.json": summary,
        "ADJUDICATION.json": adjudication,
        "TRACEABILITY.json": traceability,
        "REUSE_VS_FRESH.json": reuse,
        "MANDATORY_LIVE_METRICS_SCHEMA.json": metrics,
        "LADDER_STATE.json": ladder_state,
        "LINEAGE.json": lineage,
        "STATIC_FIELD_ADJUDICATION.json": static_fields,
        "STATIC_EXECUTION_GRAPH.json": graph,
        "COMPONENT_CLASSIFICATION.json": classification,
        "MUTATION_BOUNDARY.json": mutation_boundary,
        CONSTITUENT_MATRIX_FILENAME: build_constituent_matrix_v1(),
        STATIC_REACHABILITY_GRAPH_FILENAME: build_static_reachability_graph_v1(),
        RUNTIME_DEPENDENCY_GRAPH_FILENAME: build_runtime_dependency_graph_v1(),
        AUTHORITY_BOUNDARY_MAP_FILENAME: build_authority_boundary_map_v1(),
        RUNTIME_GATE_CLASSIFICATION_FILENAME: classify_runtime_gates_v1(),
        PRIVATE_GET_BINDING_FILENAME: bind_private_get_before_request_v1(),
        PATH_REACHABLE_ADJUDICATION_FILENAME: static_fields["LIVE_EXECUTION_PATH_REACHABLE"],
        PRIVATE_READ_ONLY_GET_BINDING_FILENAME: bind_private_read_only_gets_before_request_v1(),
        PRIVATE_READ_ONLY_ADJUDICATION_FILENAME: static_fields["LIVE_PRIVATE_READ_ONLY_PROVEN"],
        ORDER_PLAN_OBSERVED_ADJUDICATION_FILENAME: order_plan_fields,
        LATER_FIELD_CENSUS_FILENAME: build_later_field_census_v1(),
    }
    documents.update(build_submit_ack_forensic_documents_v1())
    documents["SUBMIT_ACK_OBSERVED_ADJUDICATION.json"] = ack_fields
    documents[FILL_OBSERVED_ADJUDICATION_FILENAME] = fill_fields
    documents[FEE_OBSERVED_ADJUDICATION_FILENAME] = fee_fields
    documents[POSITION_RECONCILED_ADJUDICATION_FILENAME] = position_fields
    documents[ACCOUNTING_RECONSTRUCTED_ADJUDICATION_FILENAME] = accounting_fields
    documents[RESTART_RECONSTRUCTED_ADJUDICATION_FILENAME] = restart_fields
    if path_ev is not None:
        documents[PRIVATE_GET_EVIDENCE_FILENAME] = dict(path_ev)
    if ro_ev is not None:
        documents[PRIVATE_READ_ONLY_GET_EVIDENCE_FILENAME] = dict(ro_ev)
    if op_ev is not None:
        documents[ORDER_PLAN_EVIDENCE_FILENAME] = dict(op_ev)
        documents[GATE_STATE_FILENAME] = {
            "BEFORE": op_ev.get("GATE_STATE_BEFORE"),
            "DURING": op_ev.get("GATE_STATE_DURING"),
            "AFTER": op_ev.get("GATE_STATE_AFTER"),
            "LIVE_GATE_ACTIVATION_USED": bool(op_ev.get("LIVE_GATE_ACTIVATION_USED") is True),
            "LIVE_GATES_RETURNED_FAIL_CLOSED": bool(
                op_ev.get("LIVE_GATES_RETURNED_FAIL_CLOSED") is True
            ),
            "STANDING_LIVE_ENABLED": False,
            "STANDING_LIVE_ARMED": False,
            "STANDING_SUBMIT_UNLOCKED": False,
            "STANDING_CANARY_AUTHORIZED": False,
        }
        documents[PREFLIGHT_FILENAME] = {
            "POST_USED": False,
            "WIRE_SEND_POST": False,
            "SUBMIT_USED": False,
            "SUBMIT_COUNT": 0,
            "RETRY_USED": False,
            "SECOND_SUBMIT_USED": False,
            "plan": op_ev.get("plan"),
            "submit_gate": op_ev.get("submit_gate"),
            "pre_submit_state": op_ev.get("pre_submit_state"),
            "CANARY_RESULT": op_ev.get("CANARY_RESULT"),
            "VENUE_REQUESTS": op_ev.get("VENUE_REQUESTS"),
            "RESPONSE_TIME_UTC": op_ev.get("RESPONSE_TIME_UTC"),
        }
    return documents
