"""Machine-checkable SEND_TIME_PASS_18_19_21_24 lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_pass_18_19_21_24_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_PASS,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.constants_v1 import (
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


SEND_TIME_PASS_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="P25_CASE_B",
        field="EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
        source_path=(
            "src/ops/section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1/"
            "contract_v1.py"
        ),
        status="current_bound_predecessor",
        semantic_object="P25_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="P25_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_SEND_TIME_PASS_WAS_NEXT_RESIDUAL",
    ),
    _seam(
        producer="Z2CO_CURRENT_SSOT_FOR_18_19_21_24_OFFLINE_BIND",
        field="EXECUTION_PREREQUISITE_18_NO_OTHER_TRADE_THROUGH_SAME_FLOW",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_producer",
        semantic_object="PREREQUISITE_18_OFFLINE_FLATTEN_FLOW",
        observed_value="OFFLINE_FLATTEN_FLOW_CONTRACT_BOUND_SEND_TIME_PASS_UNPROVEN",
        transformation="OFFLINE_BOUND_NOT_PROVEN_AT_SEND",
        output_object="PREREQUISITE_18_EVALUATION_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_BOUND_PROVEN_AT_SEND_FALSE",
    ),
    _seam(
        producer="Z2CO_CURRENT_SSOT_FOR_18_19_21_24_OFFLINE_BIND",
        field="EXECUTION_PREREQUISITE_19_MUTATION_LIMITED_TO_CANONICAL_SUI",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_producer",
        semantic_object="PREREQUISITE_19_CANONICAL_SUI_BINDING",
        observed_value="OFFLINE_CANONICAL_SUI_INSTRUMENT_BINDING_BOUND_SEND_TIME_PASS_UNPROVEN",
        transformation="OFFLINE_BOUND_NOT_PROVEN_AT_SEND",
        output_object="PREREQUISITE_19_EVALUATION_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_BOUND_PROVEN_AT_SEND_FALSE",
    ),
    _seam(
        producer="Z2CL_DUPLICATE_POST_FORBIDDEN",
        field="EXECUTION_PREREQUISITE_21_DUPLICATE_SUBMIT_PROTECTION",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_producer",
        semantic_object="PREREQUISITE_21_DUPLICATE_POST_FORBIDDEN",
        observed_value="CODE_BOUND_DUPLICATE_POST_FORBIDDEN_SEND_TIME_PASS_UNPROVEN",
        transformation="OFFLINE_BOUND_NOT_PROVEN_AT_SEND",
        output_object="PREREQUISITE_21_EVALUATION_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_BOUND_PROVEN_AT_SEND_FALSE",
    ),
    _seam(
        producer="Z2CO_CURRENT_SSOT_FOR_18_19_21_24_OFFLINE_BIND",
        field="EXECUTION_PREREQUISITE_24_AUDIT_TRAIL_SUFFICIENT",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_producer",
        semantic_object="PREREQUISITE_24_AUDIT_BOUNDARY",
        observed_value="OFFLINE_AUDIT_BOUNDARY_PRESENT_SEND_TIME_PASS_UNPROVEN",
        transformation="OFFLINE_BOUND_NOT_PROVEN_AT_SEND",
        output_object="PREREQUISITE_24_EVALUATION_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_BOUND_PROVEN_AT_SEND_FALSE",
    ),
    _seam(
        producer="evaluate_send_time_pass_18_19_21_24_v1",
        field="claimed_remaining_after_send_time_pass",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "send_time_pass_18_19_21_24_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NAMED_REMAINING_AFTER_SEND_TIME_PASS",
        observed_value=";".join(NAMED_REMAINING_AFTER_SEND_TIME_PASS),
        transformation="EXACT_SET_MATCH_OR_DENY",
        output_object="SEND_TIME_PASS_REMAINING_HIGHER_AUTHORITY_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED_NOT_CLOSED_BY_SEND_TIME_PASS",
    ),
    _seam(
        producer="evaluate_flatten_execute_authority_v1",
        field="owner_go",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_execute_authority_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="FLATTEN_EXECUTE_OWNER_GO",
        observed_value="IMPLEMENTATION_GO_FORBIDDEN",
        transformation="STP_GO_FORBIDDEN_AS_EXECUTE",
        output_object="FLATTEN_EXECUTE_REMAINS_SEPARATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_SEND_TIME_PASS_CONTRACT",
    ),
    _seam(
        producer="GatedProductiveFlattenTransportV1",
        field="network_session_authorized",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NETWORK_SESSION_AUTHORIZATION",
        observed_value="false",
        transformation="CLASS_NEVER_SETS_TRUE_DEFAULT_FALSE",
        output_object="PRODUCTIVE_NETWORK_SESSION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_SEND_TIME_PASS_CONTRACT",
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
        transformation="SEND_TIME_PASS_CLOSED_CLUSTER_REMAINDER_NEXT",
        output_object="AUTHENTICATED_PRODUCTIVE_TRANSPORT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_RUNTIME_AUTHORIZED",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="SEND_TIME_PASS_18_19_21_24",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PRE_SEND_SEND_TIME_PASS_GATE",
        observed_value="DENY_IF_18_19_21_24_FAIL_OR_PROVEN_AT_SEND_CLAIM",
        transformation="NAMED_GATE_INDEPENDENT_OF_GLOBAL_LIVE_AUTHORIZED",
        output_object="SEND_TIME_PASS_18_19_21_24_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_AUTHORITY_NOT_PERFORMED",
    ),
    _seam(
        producer="P25_CASE_B",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="WRONG_INSTRUMENT_DENY",
        output_object="SEND_TIME_PASS_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
)


def send_time_pass_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in SEND_TIME_PASS_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = send_time_pass_lineage_v1()
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
            or "HISTORICAL" in status
            or "PROVEN_AT_SEND_FALSE" in status
        ):
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
