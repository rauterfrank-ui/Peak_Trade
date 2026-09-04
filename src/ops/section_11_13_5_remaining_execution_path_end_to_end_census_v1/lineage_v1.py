"""Machine-checkable remaining execution-path census lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.remaining_execution_path_census_v1 import (
    NAMED_REMAINING_AFTER_CENSUS,
    START_NODE,
    TERMINAL_EXECUTION_ENDPOINT,
    TERMINAL_ENDPOINT_PROOF,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    TARGET_INSTRUMENT_ID,
)

LINEAGE_FIELD_NAMES: tuple[str, ...] = (
    "producer",
    "field",
    "source_path",
    "status",
    "semantic_object",
    "observed_value",
    "transformation",
    "output_object",
    "epistemic_class",
    "adjudication_status",
)


def _seam(
    *,
    producer: str,
    field: str,
    source_path: str,
    status: str,
    semantic_object: str,
    observed_value: str,
    transformation: str,
    output_object: str,
    epistemic_class: str,
    adjudication_status: str,
) -> dict[str, str]:
    return {
        "producer": producer,
        "field": field,
        "source_path": source_path,
        "status": status,
        "semantic_object": semantic_object,
        "observed_value": observed_value,
        "transformation": transformation,
        "output_object": output_object,
        "epistemic_class": epistemic_class,
        "adjudication_status": adjudication_status,
    }


REMAINING_EXECUTION_PATH_CENSUS_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="SEND_TIME_POSITION_REOBSERVATION_CASE_B",
        field="SEND_TIME_POSITION_REOBSERVATION",
        source_path=("src/ops/section_11_13_5_send_time_position_reobservation_v1/contract_v1.py"),
        status="current_bound_predecessor",
        semantic_object="STPR_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="STPR_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_BOUNDED_RUNTIME_PERMIT_ISSUANCE_WAS_NEXT_RESIDUAL",
    ),
    _seam(
        producer="evaluate_bounded_runtime_permit_issuance_v1",
        field="BOUNDED_RUNTIME_PERMIT_ISSUANCE",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_runtime_permit_issuance_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="BRPI_ISSUANCE_CONTRACT",
        observed_value=START_NODE,
        transformation="CASE_B_CONTRACT_NOT_RUNTIME_ISSUANCE",
        output_object="BOUNDED_RUNTIME_PERMIT_ISSUANCE_PASS_OFFLINE_CONTRACT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_CONTRACT_RUNTIME_PERMIT_NOT_ISSUED",
    ),
    _seam(
        producer="evaluate_flatten_execute_authority_v1",
        field="FLATTEN_EXECUTE",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_execute_authority_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="FLATTEN_EXECUTE_CONFIRM_TOKEN_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="CENSUS_GO_FORBIDDEN_AS_EXECUTE",
        output_object="FLATTEN_EXECUTE_REMAINS_UNAUTHORIZED",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_ISSUANCE_CONTRACT",
    ),
    _seam(
        producer="GatedProductiveFlattenTransportV1",
        field="network_session_authorized",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NETWORK_SESSION_DEFAULT_DENY",
        observed_value="false",
        transformation="MODULE_NEVER_SETS_TRUE",
        output_object="NETWORK_SESSION_PASS_OFFLINE_CONTRACT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_GATE_NETWORK_NOT_USED",
    ),
    _seam(
        producer="remaining_execution_path_census_summary_v1",
        field="TERMINAL_EXECUTION_ENDPOINT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "remaining_execution_path_census_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="LIVE_FLATTEN_PROVABILITY_PROVEN",
        observed_value=TERMINAL_EXECUTION_ENDPOINT,
        transformation="POST_TRADE_ORDER_PLUS_POST_ACTION_POS_EQ_ZERO",
        output_object="TERMINAL_PRODUCTIVE_EXECUTION_ENDPOINT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_DEFINITION_RUNTIME_NOT_PERFORMED",
    ),
    _seam(
        producer="evaluate_bounded_runtime_permit_issuance_v1",
        field="claimed_remaining_after_census",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_runtime_permit_issuance_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NAMED_REMAINING_AFTER_CENSUS",
        observed_value=";".join(NAMED_REMAINING_AFTER_CENSUS),
        transformation="EXACT_SET_MATCH_OR_DENY",
        output_object="CENSUS_REMAINING_HIGHER_AUTHORITY_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED_NOT_CLOSED_BY_CENSUS",
    ),
    _seam(
        producer="adjudicate_prerequisite_08_window_v1",
        field="EARLIEST_UNRESOLVED_DEPENDENCY",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY",
        observed_value=EARLIEST_UNRESOLVED_DEPENDENCY,
        transformation="CENSUS_CLOSED_CLUSTER_REMAINDER_NEXT",
        output_object="AUTHENTICATED_PRIVATE_RUNTIME_READ",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_RUNTIME_AUTHORIZED",
    ),
    _seam(
        producer="LIVE_FLATTEN_PROVABILITY_STATUS",
        field="TERMINAL_ENDPOINT_PROOF",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_post_action_proof_contract_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="POST_ACTION_POSITION_CLOSED_CONTRACT",
        observed_value=TERMINAL_ENDPOINT_PROOF,
        transformation="HTTP_200_AND_OKX_CODE_0_NOT_SUCCESS",
        output_object="LIVE_FLATTEN_PROVABILITY_REMAINS_UNPROVEN",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_DEFINITION_NETWORK_NOT_USED",
    ),
    _seam(
        producer="SEND_TIME_POSITION_REOBSERVATION_CASE_B",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="SCOPE_PRESERVED_NOT_MUTATED",
        output_object="CENSUS_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
)


def remaining_execution_path_census_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in REMAINING_EXECUTION_PATH_CENSUS_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = remaining_execution_path_census_lineage_v1()
    counts: dict[str, int] = {}
    proven = 0
    not_promoted = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        status = str(seam.get("adjudication_status") or "")
        if status.startswith("PROVEN"):
            proven += 1
        if (
            "NOT_USED" in status
            or "UNAUTHORIZED" in status
            or "NOT_PERFORMED" in status
            or "NOT_ISSUED" in status
            or "NETWORK_NOT_USED" in status
        ):
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
