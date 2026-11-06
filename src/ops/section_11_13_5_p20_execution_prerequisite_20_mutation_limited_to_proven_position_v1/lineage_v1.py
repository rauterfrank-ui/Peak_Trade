"""Machine-checkable P20 mutation-limited-to-proven-position lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.constants_v1 import (
    FLATTEN_QTY_RULE_VALUE,
    MUTATION_OBJECT_VALUE,
    P08_CAPTURED_POSID,
    P08_CAPTURED_SIGNED_POS,
    P08_POSITION_OBSERVATION_CLASS,
    PROVEN_POSITION_CLASSIFIER_VALUE,
    PROVEN_POSITION_STATE_VALUE,
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


MUTATION_LIMITED_TO_PROVEN_POSITION_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="classify_target_position_state_v1",
        field="state",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PROVEN_POSITION_STATE",
        observed_value=PROVEN_POSITION_STATE_VALUE,
        transformation="EMPTY_NE_ZERO_ABSENT_NE_ZERO_ZERO_ROW_DISTINCT",
        output_object="TARGET_POSITION_CLASSIFICATION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_CLASSIFIER_SEND_TIME_REOBSERVATION_REQUIRED",
    ),
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="instrument_id",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PROVEN_POSITION_INSTRUMENT",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="UNIQUE_TARGET_ROW_OR_DENY",
        output_object="PROVEN_POSITION_INST_ID",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="signed_pos",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PROVEN_POSITION_SIGNED_POS",
        observed_value=P08_CAPTURED_SIGNED_POS,
        transformation="ABS_POS_IDENTITY_TO_SZ_FULL_FLATTEN_ONLY",
        output_object="CANDIDATE_FLATTEN_QTY",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_P08_CASE_A_NOT_SEND_TIME_INSTANCE",
    ),
    _seam(
        producer="flatten_order_side_from_signed_pos_v1",
        field="side",
        source_path=(
            "src/ops/section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1/"
            "contract_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="FLATTEN_ORDER_SIDE",
        observed_value="SELL_IF_OBSERVED_SIGNED_POS_GT_0_ELSE_BUY",
        transformation="SIDE_MUST_MATCH_PROVEN_SIGNED_POS_OR_DENY",
        output_object="MUTATION_SIDE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="evaluate_mutation_limited_to_proven_position_v1",
        field="mutation_body.instId",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "mutation_limited_to_proven_position_v1.py"
        ),
        status="current_bound_producer",
        semantic_object=MUTATION_OBJECT_VALUE,
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="WRONG_INSTRUMENT_DENY",
        output_object="MUTATION_INST_ID",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="evaluate_mutation_limited_to_proven_position_v1",
        field="mutation_body.sz",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "mutation_limited_to_proven_position_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="MUTATION_SZ",
        observed_value=FLATTEN_QTY_RULE_VALUE,
        transformation="PARTIAL_OR_OVERSIZE_OR_UNPARSEABLE_DENY",
        output_object="MUTATION_SZ",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="P08_CASE_A",
        field="posId",
        source_path=("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5-p08-case_a"),
        status="historical_captured_observation",
        semantic_object="P08_CAPTURED_POSID",
        observed_value=P08_CAPTURED_POSID,
        transformation="NOT_A_PLACE_ORDER_WIRE_FIELD_NOT_PROMOTED",
        output_object="POSID_NOT_COPIED_TO_MUTATION_BODY",
        epistemic_class="FORENSIC_RAW",
        adjudication_status="PROVEN_OBSERVED_NOT_USED_AS_WIRE_FIELD",
    ),
    _seam(
        producer="P08_CASE_A",
        field="POSITION_OBSERVATION_CLASS",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="historical_captured_observation",
        semantic_object="P08_CASE_A_TARGET_NONZERO",
        observed_value=P08_POSITION_OBSERVATION_CLASS,
        transformation="HISTORICAL_EMPTY_ENVELOPES_ARE_NOT_CURRENT_08_PROOF",
        output_object="OFFLINE_PROVEN_POSITION_DEFINITION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_P08_CLOSED_SEND_TIME_FRESHNESS_REMAINS",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="MUTATION_LIMITED_TO_PROVEN_POSITION",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PRE_SEND_P20_GATE",
        observed_value="DENY_IF_NO_PROVEN_POSITION_OR_SCOPE_MISMATCH",
        transformation="NAMED_GATE_INDEPENDENT_OF_GLOBAL_LIVE_AUTHORIZED",
        output_object="MUTATION_LIMITED_TO_PROVEN_POSITION_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_MUTATION_NOT_PERFORMED",
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
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_P20_CONTRACT",
    ),
)


def mutation_limited_to_proven_position_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in MUTATION_LIMITED_TO_PROVEN_POSITION_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = mutation_limited_to_proven_position_lineage_v1()
    counts: dict[str, int] = {}
    proven = 0
    not_promoted = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        status = str(seam.get("adjudication_status") or "")
        if status.startswith("PROVEN"):
            proven += 1
        if "NOT_USED" in status or "UNAUTHORIZED" in status or "NOT_PERFORMED" in status:
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
