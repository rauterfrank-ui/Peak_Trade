"""Machine-checkable lineage for authenticated private read / permit issuance."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
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


def authenticated_private_runtime_read_lineage_v1(
    *,
    runtime_facts: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    permit_audit = runtime_facts.get("PERMIT_AUDIT") or {}
    observation = runtime_facts.get("OBSERVATION") or {}
    return (
        _seam(
            producer="REMAINING_EXECUTION_PATH_END_TO_END_CENSUS_CASE_B",
            field="REMAINING_EXECUTION_PATH_CENSUS",
            source_path=(
                "src/ops/section_11_13_5_remaining_execution_path_end_to_end_census_v1/"
                "contract_v1.py"
            ),
            status="current_bound_predecessor",
            semantic_object="CENSUS_PASS_OFFLINE_CONTRACT",
            observed_value="PASS_OFFLINE_CONTRACT",
            transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
            output_object="CENSUS_CLOSED_INPUT",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_PREDECESSOR_AUTHENTICATED_PRIVATE_RUNTIME_READ_WAS_NEXT",
        ),
        _seam(
            producer="execute_authenticated_private_runtime_read_and_permit_issuance_v1",
            field="AUTHENTICATED_PRIVATE_RUNTIME_READ",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_runtime_"
                "permit_issuance_v1/execute_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="GET_API_V5_ACCOUNT_POSITIONS",
            observed_value=str(runtime_facts.get("RESULT_CLASS") or ""),
            transformation="ONE_SHOT_HMAC_GET_NO_POST",
            output_object="POSITION_OBSERVATION",
            epistemic_class="FORENSIC_RAW",
            adjudication_status="PROVEN_GET_PERFORMED"
            if runtime_facts.get("GET_PERFORMED_THIS_PERSIST") is True
            else "GET_NOT_PERFORMED",
        ),
        _seam(
            producer="classify_position_observation_v1",
            field="POSITION_OBSERVATION_CLASS",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_runtime_"
                "permit_issuance_v1/execute_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="EMPTY_DATA_IS_NOT_ZERO",
            observed_value=str(observation.get("POSITION_OBSERVATION_CLASS") or ""),
            transformation="CLASSIFIER_NOT_EMPTY_AS_ZERO",
            output_object="OBSERVATION_CLASS",
            epistemic_class="INTERPRETATION",
            adjudication_status="PROVEN_SEMANTIC_SEPARATION",
        ),
        _seam(
            producer="evaluate_runtime_permit_issuance_v1",
            field="RUNTIME_PERMIT_ISSUANCE",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_runtime_"
                "permit_issuance_v1/runtime_permit_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="RUNTIME_ISSUED_PERMIT",
            observed_value="ISSUED" if permit_audit.get("issued") else "FAIL_CLOSED",
            transformation="FRESH_CASE_A_SIZE_AND_OBSERVATION_OR_DENY",
            output_object="PERMIT_OR_DENY_REASONS",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_ISSUANCE_OR_FAIL_CLOSED",
        ),
        _seam(
            producer="evaluate_runtime_permit_issuance_v1",
            field="NETWORK_SESSION_AUTHORIZED",
            source_path=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "flatten_productive_transport_v1.py"
            ),
            status="current_bound_negative",
            semantic_object="FLATTEN_NETWORK_SESSION_DEFAULT_DENY",
            observed_value="false",
            transformation="GET_TRANSPORT_IS_NOT_FLATTEN_SESSION_FLAG",
            output_object="NETWORK_SESSION_REMAINS_UNAUTHORIZED",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_FLATTEN_SESSION_NOT_SET",
        ),
        _seam(
            producer="adjudicate_gaps_v1",
            field="EARLIEST_UNRESOLVED_DEPENDENCY",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_runtime_"
                "permit_issuance_v1/gap_adjudication_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="NEXT_AUTHORITY_BOUNDARY",
            observed_value=EARLIEST_UNRESOLVED_DEPENDENCY,
            transformation="HARD_STOP_BEFORE_PRODUCTIVE_FLATTEN_POST",
            output_object="PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_NEXT_NOT_AUTHORIZED",
        ),
        _seam(
            producer="SEND_TIME_POSITION_REOBSERVATION_CASE_B",
            field="TARGET_INSTRUMENT_ID",
            source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            status="current_bound_scope",
            semantic_object="CANONICAL_INSTRUMENT_SCOPE",
            observed_value=TARGET_INSTRUMENT_ID,
            transformation="SCOPE_PRESERVED_NOT_MUTATED",
            output_object="PERMIT_INSTRUMENT_BINDING",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_FAIL_CLOSED",
        ),
    )


def lineage_summary_v1(*, runtime_facts: Mapping[str, Any]) -> dict[str, Any]:
    seams = authenticated_private_runtime_read_lineage_v1(runtime_facts=runtime_facts)
    class_counts: dict[str, int] = {}
    proven = 0
    for seam in seams:
        klass = str(seam["epistemic_class"])
        class_counts[klass] = class_counts.get(klass, 0) + 1
        if str(seam["adjudication_status"]).startswith("PROVEN_"):
            proven += 1
    return {
        "SEAM_COUNT": len(seams),
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
        "EPISTEMIC_CLASS_COUNTS": class_counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": len(seams) - proven,
    }
