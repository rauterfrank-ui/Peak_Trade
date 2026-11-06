"""Machine-checkable P25 no-additional-owner-decision lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.constants_v1 import (
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


NO_ADDITIONAL_OWNER_DECISION_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="P16_CASE_B",
        field="EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
        source_path=(
            "src/ops/section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1/"
            "contract_v1.py"
        ),
        status="current_bound_predecessor",
        semantic_object="P16_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="P16_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_RUNTIME_PERMIT_REMAINS_SEPARATE",
    ),
    _seam(
        producer="P20_CASE_B",
        field="EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
        source_path=(
            "src/ops/section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1/"
            "contract_v1.py"
        ),
        status="current_bound_predecessor",
        semantic_object="P20_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="P20_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_SEND_TIME_REOBSERVATION_REMAINS_SEPARATE",
    ),
    _seam(
        producer="Z2CB_HISTORICAL_MATRIX",
        field="EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="historical_snapshot_not_current_ssot",
        semantic_object="Z2CB_P25_FAIL_STRING",
        observed_value="FAIL_FLATTEN_EXECUTE_OWNER_GO_AND_URLLIB_SEND_REMAIN_SEPARATE",
        transformation="HISTORICAL_FAIL_NOT_PROMOTED_TO_CURRENT_PASS_MEANING",
        output_object="HISTORICAL_P25_FAIL_NOT_CURRENT_AUTHORITY",
        epistemic_class="FORENSIC_RAW",
        adjudication_status="PROVEN_HISTORICAL_NOT_USED_AS_CURRENT_PASS_CONDITION",
    ),
    _seam(
        producer="evaluate_no_additional_owner_decision_required_v1",
        field="additional_owner_decisions",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "no_additional_owner_decision_required_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="ADDITIONAL_UNSTATED_OWNER_DECISIONS",
        observed_value="EMPTY",
        transformation="NONEMPTY_ADDITIONAL_DENY",
        output_object="P25_ADDITIONAL_DECISION_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="evaluate_no_additional_owner_decision_required_v1",
        field="claimed_remaining_higher_authority",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "no_additional_owner_decision_required_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES",
        observed_value=";".join(NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES),
        transformation="EXACT_SET_MATCH_OR_DENY",
        output_object="P25_REMAINING_HIGHER_AUTHORITY_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED_NOT_CLOSED_BY_P25",
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
        transformation="P25_GO_FORBIDDEN_AS_EXECUTE",
        output_object="FLATTEN_EXECUTE_REMAINS_SEPARATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_P25_CONTRACT",
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
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_P25_CONTRACT",
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
        transformation="NUMBERED_MATRIX_25_CLOSED_CLUSTER_REMAINDER_NEXT",
        output_object="SEND_TIME_PASS_18_19_21_24",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_RUNTIME_AUTHORIZED",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PRE_SEND_P25_GATE",
        observed_value="DENY_IF_ADDITIONAL_DECISION_OR_AUTHORITY_CLAIM",
        transformation="NAMED_GATE_INDEPENDENT_OF_GLOBAL_LIVE_AUTHORIZED",
        output_object="NO_ADDITIONAL_OWNER_DECISION_REQUIRED_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_AUTHORITY_NOT_PERFORMED",
    ),
    _seam(
        producer="P20_CASE_B",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="WRONG_INSTRUMENT_DENY",
        output_object="P25_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
)


def no_additional_owner_decision_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in NO_ADDITIONAL_OWNER_DECISION_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = no_additional_owner_decision_lineage_v1()
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
        ):
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
