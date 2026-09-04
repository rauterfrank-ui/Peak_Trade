"""Machine-checkable SEND_TIME_POSITION_REOBSERVATION lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    CANONICAL_POSITION_GET_ENDPOINT,
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
    PRODUCER_CLASS_FAKE_OFFLINE,
    SEND_TIME_EVALUATION_POINT,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.constants_v1 import (
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


SEND_TIME_POSITION_REOBSERVATION_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="AUTHENTICATED_PRODUCTIVE_TRANSPORT_CASE_B",
        field="AUTHENTICATED_PRODUCTIVE_TRANSPORT",
        source_path=(
            "src/ops/section_11_13_5_authenticated_productive_transport_v1/contract_v1.py"
        ),
        status="current_bound_predecessor",
        semantic_object="APT_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="APT_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_SEND_TIME_POSITION_REOBSERVATION_WAS_NEXT_RESIDUAL",
    ),
    _seam(
        producer="classify_target_position_state_v1",
        field="state",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="TARGET_POSITION_STATE_CLASSIFICATION",
        observed_value="EMPTY_DATA_NOT_ZERO;NOT_OBSERVED_DISTINCT;ZERO_DISTINCT;NONZERO_DISTINCT",
        transformation="REUSE_EXISTING_CLASSIFIER_NO_NEW_ONTOLOGY",
        output_object="SEND_TIME_POSITION_STATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_CLASSIFIER_RUNTIME_GET_NOT_USED",
    ),
    _seam(
        producer="evaluate_position_observation_freshness_v1",
        field="AGE_EVALUATION_POINT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_observation_freshness_contract_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="SEND_TIME_FRESHNESS_CLOCK",
        observed_value=SEND_TIME_EVALUATION_POINT,
        transformation="LOCAL_MONOTONIC_MAX_AGE_5000MS_NOT_VENUE_UTIME",
        output_object="SEND_TIME_POSITION_FRESHNESS_VERDICT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_FRESHNESS_RUNTIME_GET_NOT_USED",
    ),
    _seam(
        producer="RecordingSendTimePositionReobservationProducerV1",
        field="producer_class",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "send_time_position_reobservation_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NO_WIRE_FAKE_REOBSERVATION_PRODUCER",
        observed_value=PRODUCER_CLASS_FAKE_OFFLINE,
        transformation="FAKE_MUST_NOT_COUNT_AS_RUNTIME_GET",
        output_object="SEND_TIME_POSITION_OBSERVATION_V1",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAKE_PRODUCER_SECRET_AND_NETWORK_ABSENT",
    ),
    _seam(
        producer="evaluate_send_time_position_reobservation_v1",
        field="claimed_remaining_after_send_time_position_reobservation",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "send_time_position_reobservation_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION",
        observed_value=";".join(NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION),
        transformation="EXACT_SET_MATCH_OR_DENY",
        output_object="SEND_TIME_POSITION_REOBSERVATION_REMAINING_HIGHER_AUTHORITY_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED_NOT_CLOSED_BY_SEND_TIME_POSITION_REOBSERVATION",
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
        transformation="STPR_GO_FORBIDDEN_AS_EXECUTE",
        output_object="FLATTEN_EXECUTE_REMAINS_SEPARATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_SEND_TIME_POSITION_REOBSERVATION_CONTRACT",
    ),
    _seam(
        producer="CANONICAL_POSITION_GET_ENDPOINT",
        field="ENDPOINT_ACCOUNT_POSITIONS",
        source_path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
        status="current_bound_producer",
        semantic_object="PRIVATE_POSITIONS_GET_ENDPOINT",
        observed_value=CANONICAL_POSITION_GET_ENDPOINT,
        transformation="ENDPOINT_NAMED_NOT_INVOKED",
        output_object="POSITION_GET_NOT_PERFORMED",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_ENDPOINT_BOUND_NETWORK_NOT_USED",
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
        transformation="SEND_TIME_POSITION_REOBSERVATION_CLOSED_CLUSTER_REMAINDER_NEXT",
        output_object="BOUNDED_RUNTIME_PERMIT_ISSUANCE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_RUNTIME_AUTHORIZED",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="SEND_TIME_POSITION_REOBSERVATION",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PRE_SEND_SEND_TIME_POSITION_REOBSERVATION_GATE",
        observed_value="DENY_IF_HISTORICAL_REUSE_OR_EMPTY_AS_ZERO_OR_RUNTIME_CLAIM",
        transformation="NAMED_GATE_INDEPENDENT_OF_GLOBAL_LIVE_AUTHORIZED",
        output_object="SEND_TIME_POSITION_REOBSERVATION_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_AUTHORITY_NOT_PERFORMED",
    ),
    _seam(
        producer="AUTHENTICATED_PRODUCTIVE_TRANSPORT_CASE_B",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="SCOPE_PRESERVED_NOT_MUTATED",
        output_object="SEND_TIME_POSITION_REOBSERVATION_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
)


def send_time_position_reobservation_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in SEND_TIME_POSITION_REOBSERVATION_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = send_time_position_reobservation_lineage_v1()
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
            or "NETWORK_NOT_USED" in status
            or "NETWORK_ABSENT" in status
        ):
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
