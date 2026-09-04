"""Assemble deterministic offline §11.14 documents from repository state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_BASE_SHA,
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    G12_DOES_NOT_AUTHORIZE_SECTION_11_14,
    G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS,
    G12_STATUS_REQUIRED,
    IMPLEMENTATION_SHA,
    LADDER_FIELD_COUNT,
    LADDER_FIELD_DEFAULTS,
    LADDER_FIELDS,
    LAST_CANONICALLY_CLOSED_STEP,
    MANDATORY_LIVE_METRIC_COUNT,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    SCHEMA_VERSION,
    SECTION_11_14_AUTHORIZED,
    SECTION_11_14_COMPLETE,
    SECTION_11_14_OFFLINE_SURFACE_BOUND,
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
) -> dict[str, dict[str, Any]]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise RuntimeError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    assert_ladder_order_v1(LADDER_FIELD_DEFAULTS)
    static_fields = adjudicate_static_fields_v1(repo_root=repo_root)
    metrics = build_mandatory_live_metrics_schema_v1()
    reuse = build_reuse_vs_fresh_matrix_v1()
    traceability = build_traceability_matrix_v1(
        ladder_values=LADDER_FIELD_DEFAULTS,
        metrics_schema=metrics,
    )
    evidence_records = [
        build_evidence_record_v1(
            ladder_stage=field_name,
            claim_name=field_name,
            claim_value=False,
            evidence_class="3_ALREADY_ADJUDICATED_CONCLUSION",
            source_kind="GOVERNED_OFFLINE_CONTRACT",
            source_path_or_runtime_source=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            ),
            observed_at=None,
            predecessor_claims=[PREDECESSOR_SLICE],
            provenance=OWNER_GO,
            adjudication_status="FALSE_FAIL_CLOSED",
            contradiction_status="NONE",
            authority_scope="R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK",
        )
        for field_name in LADDER_FIELDS
    ]
    ladder_state = {
        "schema_version": SCHEMA_VERSION,
        "fields": list(LADDER_FIELDS),
        "field_count": LADDER_FIELD_COUNT,
        "values": dict(LADDER_FIELD_DEFAULTS),
        "order_enforced": True,
    }
    mutation_boundary = {
        "VENUE_REQUESTS": 0,
        "PUBLIC_GET": False,
        "PRIVATE_GET": False,
        "CREDENTIAL_USE": False,
        "POST": False,
        "ORDER_SUBMIT": False,
        "CANCEL": False,
        "AMEND": False,
        "FLATTEN_EXECUTE": False,
        "FUNDING": False,
        "SECTION_11_14_RUNTIME_EXECUTION": False,
        "COLLECTOR_ACTIVATED": False,
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
        "DOCUMENT_CLASS": "SECTION_11_14_OFFLINE_SURFACE_ADJUDICATION_V1",
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
        "EVIDENCE_RECORDS": evidence_records,
    }
    summary = {
        "DOCUMENT_CLASS": "SECTION_11_14_OFFLINE_SURFACE_SUMMARY_V1",
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
        "LIVE_EXECUTION_CODE_EXISTS": False,
        "LIVE_EXECUTION_PATH_REACHABLE": False,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "POST_USED": False,
        "GET_USED": False,
        "CREDENTIAL_USE": False,
    }
    claims = {
        **CLAIMS,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
    }
    assert_contract_invariants_v1(claims)
    assert_contract_invariants_v1(summary)
    return {
        "claims.json": claims,
        "SUMMARY.json": summary,
        "ADJUDICATION.json": adjudication,
        "TRACEABILITY.json": traceability,
        "REUSE_VS_FRESH.json": reuse,
        "MANDATORY_LIVE_METRICS_SCHEMA.json": metrics,
        "LADDER_STATE.json": ladder_state,
        "LINEAGE.json": lineage,
        "STATIC_FIELD_ADJUDICATION.json": static_fields,
        "MUTATION_BOUNDARY.json": mutation_boundary,
    }
