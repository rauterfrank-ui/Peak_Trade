"""Machine-checkable P12 position-side / request-posSide lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.constants_v1 import (
    FLATTEN_ORDER_SIDE_RULE,
    POSITION_ROW_POS_SIDE_OBSERVED_P08_VALUE,
    REQUEST_POS_SIDE_POLICY_VALUE,
    REQUEST_POS_SIDE_VALUE_CURRENT,
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


POSITION_SIDE_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="signed_pos",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="POSITION_DIRECTION_SIGNED_POS",
        observed_value="P08_CAPTURE_POS=1",
        transformation="NONE_SIGNED_POS_FROM_POSITIONS_ROW",
        output_object="SIGNED_POS",
        epistemic_class="CURRENT_AUTHORITATIVE_PRODUCER",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="flatten_order_side_from_signed_pos_v1",
        field="side",
        source_path=(
            "src/ops/section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1/"
            "contract_v1.py"
        ),
        status="current_bound_contract",
        semantic_object="FLATTEN_ORDER_SIDE",
        observed_value=FLATTEN_ORDER_SIDE_RULE,
        transformation="SELL_IF_SIGNED_POS_GT_0_ELSE_BUY",
        output_object="PLACE_ORDER_SIDE_BUY_OR_SELL",
        epistemic_class="CURRENT_AUTHORITATIVE_CONTRACT",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="build_venue_native_order_body_v1",
        field="posSide",
        source_path=(
            "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
            "okx_response_mapper_v1.py"
        ),
        status="current_bound_mapper_omits_field",
        semantic_object="REQUEST_POS_SIDE",
        observed_value=REQUEST_POS_SIDE_VALUE_CURRENT,
        transformation=REQUEST_POS_SIDE_POLICY_VALUE,
        output_object="VENUE_NATIVE_FLATTEN_BODY_WITHOUT_POSSIDE",
        epistemic_class="CURRENT_AUTHORITATIVE_MAPPER",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="AUTHORIZED_TARGET_ROW",
        field="posSide",
        source_path=(
            "src/ops/section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1/"
            "captured_payload_v1.py"
        ),
        status="historical_p08_position_row",
        semantic_object="POSITION_ROW_POS_SIDE",
        observed_value=POSITION_ROW_POS_SIDE_OBSERVED_P08_VALUE,
        transformation="NOT_COPIED_ONTO_PLACE_ORDER",
        output_object="NOT_REQUEST_POS_SIDE",
        epistemic_class="CLASS_B_OBSERVATION_NOT_REQUEST_PROOF",
        adjudication_status="NOT_PROMOTED",
    ),
    _seam(
        producer="apply_fresh_pos_mode_pretrade_gate_v1",
        field="posMode",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pos_mode_consumer_v1.py"
        ),
        status="separate_account_pos_mode_binding",
        semantic_object="ACCOUNT_POS_MODE",
        observed_value="net_mode_required_not_rewritten_to_request_posSide",
        transformation="POS_MODE_IS_NOT_REQUEST_POS_SIDE",
        output_object="NOT_REQUEST_POS_SIDE",
        epistemic_class="SEPARATE_CONTRACT_NOT_PREREQUISITE_11",
        adjudication_status="NOT_PROMOTED",
    ),
    _seam(
        producer="Z2CB_FLATTEN_POS_SIDE",
        field="FLATTEN_POS_SIDE",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="canonical_z2cb_already_bound",
        semantic_object="REQUEST_POS_SIDE_POLICY",
        observed_value="OMITTED_FROM_VENUE_NATIVE_BODY_MAPPER_DOES_NOT_EMIT",
        transformation="NONE_ALREADY_BOUND_EXPLICITLY_CLOSED_BY_P12",
        output_object="EXECUTION_PREREQUISITE_11_PASS",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN",
    ),
)


def position_side_lineage_v1() -> tuple[dict[str, str], ...]:
    return POSITION_SIDE_LINEAGE


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = position_side_lineage_v1()
    classes: dict[str, int] = {}
    for seam in seams:
        key = seam["epistemic_class"]
        classes[key] = classes.get(key, 0) + 1
    return {
        "SEAM_COUNT": len(seams),
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
        "EPISTEMIC_CLASS_COUNTS": classes,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "REQUEST_POS_SIDE_POLICY": REQUEST_POS_SIDE_POLICY_VALUE,
        "FLATTEN_ORDER_SIDE_RULE": FLATTEN_ORDER_SIDE_RULE,
        "PROVEN_SEAMS": [
            seam["field"] for seam in seams if seam["adjudication_status"] == "PROVEN"
        ],
        "NOT_PROMOTED_SEAMS": [
            seam["field"] for seam in seams if seam["adjudication_status"] == "NOT_PROMOTED"
        ],
    }
