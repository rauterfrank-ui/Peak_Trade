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
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
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
        else:
            source_kind = "GOVERNED_OFFLINE_CONTRACT"
            status = "FALSE_FAIL_CLOSED"
            authority = "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK"
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
                observed_at=None
                if field_name
                not in {
                    "LIVE_EXECUTION_PATH_REACHABLE",
                    "LIVE_PRIVATE_READ_ONLY_PROVEN",
                    "LIVE_ORDER_PLAN_OBSERVED",
                }
                else (
                    (op_ev or ro_ev or path_ev or {}).get("RESPONSE_TIME_UTC")
                    if field_name == "LIVE_ORDER_PLAN_OBSERVED"
                    else ((ro_ev or path_ev or {}).get("RESPONSE_TIME_UTC"))
                ),
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
    get_used = bool((ro_ev or path_ev) and (ro_ev or path_ev).get("PRIVATE_GET_USED") is True)
    public_get_used = bool(op_ev and op_ev.get("PUBLIC_GET_USED") is True)
    venue_requests = int(
        (op_ev or ro_ev or path_ev or {}).get("VENUE_REQUESTS")
        or (ro_ev or path_ev or {}).get("VENUE_REQUESTS")
        or 0
    )
    mutation_boundary = {
        "VENUE_REQUESTS": venue_requests,
        "PUBLIC_GET": public_get_used,
        "PRIVATE_GET": get_used or bool(op_ev and op_ev.get("PRIVATE_GET_USED") is True),
        "CREDENTIAL_USE": False,
        "POST": False,
        "ORDER_SUBMIT": False,
        "CANCEL": False,
        "AMEND": False,
        "FLATTEN_EXECUTE": False,
        "FUNDING": False,
        "SECTION_11_14_RUNTIME_EXECUTION": False,
        "COLLECTOR_ACTIVATED": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
        "GATE_MUTATION": False,
        "SESSION_LIVE_GATE_ACTIVATION": False,
        "THIS_GO_GET": False,
        "PREDECESSOR_ORDER_PLAN_ATTACHED": op_ev is not None,
        "EARLIEST_MUTATION_BOUNDARY": (
            "LIVE_SUBMIT_ACK_OBSERVED" if order_claim else "LIVE_ORDER_PLAN_OBSERVED"
        ),
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
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_SUBMIT_ACK_PROOF_CRITERION_V1",
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
        "DOCUMENT_CLASS": "SECTION_11_14_SUBMIT_ACK_PROOF_CRITERION_SUMMARY_V1",
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
        "LIVE_SUBMIT_ACK_OBSERVED": False,
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
        "GET_PERFORMED": False,
        "PUBLIC_GET_USED": False,
        "CREDENTIAL_USE": False,
        "LIVE_EXECUTION_PATH_REACHABLE": path_claim,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": ro_claim,
        "LIVE_ORDER_PLAN_OBSERVED": order_claim,
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
    documents["SUBMIT_ACK_OBSERVED_ADJUDICATION.json"] = adjudicate_live_submit_ack_observed_v1()
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
