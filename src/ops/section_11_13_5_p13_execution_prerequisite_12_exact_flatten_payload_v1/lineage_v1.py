"""Machine-checkable P13 exact flatten payload lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.constants_v1 import (
    CLORDID_SOURCE_CLASS_VALUE,
    CONTRACT_BOUNDARY_VALUE,
    OFFLINE_CONTRACT_PROOF_PX_CLASS,
    PX_SOURCE_CLASS_VALUE,
    REQUEST_POS_SIDE,
    SZ_UNIT_VALUE,
    TARGET_INSTRUMENT_ID,
    VENUE_NATIVE_ORD_TYPE_VALUE,
    VENUE_NATIVE_TD_MODE_VALUE,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.contract_v1 import (
    CLORDID_TRANSFORMATION,
    INST_ID_TRANSFORMATION,
    ORD_TYPE_TRANSFORMATION,
    PX_TRANSFORMATION,
    REDUCE_ONLY_TRANSFORMATION,
    SIDE_TRANSFORMATION,
    SZ_TRANSFORMATION,
    TD_MODE_TRANSFORMATION,
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


EXACT_FLATTEN_PAYLOAD_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="instId",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="OBSERVED_POSITION_INSTRUMENT",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation=INST_ID_TRANSFORMATION,
        output_object="VENUE_NATIVE_INST_ID",
        epistemic_class="CURRENT_AUTHORITATIVE_PRODUCER",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="identity_flatten_sz_from_signed_pos_v1",
        field="sz",
        source_path=(
            "src/ops/section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1/"
            "contract_v1.py"
        ),
        status="current_bound_contract",
        semantic_object="FLATTEN_SZ_NUMBER_OF_CONTRACTS",
        observed_value=SZ_UNIT_VALUE,
        transformation=SZ_TRANSFORMATION,
        output_object="VENUE_NATIVE_SZ",
        epistemic_class="CURRENT_AUTHORITATIVE_CONTRACT",
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
        observed_value=SIDE_TRANSFORMATION,
        transformation=SIDE_TRANSFORMATION,
        output_object="VENUE_NATIVE_SIDE",
        epistemic_class="CURRENT_AUTHORITATIVE_CONTRACT",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="require_canonical_execution_td_mode_v1",
        field="tdMode",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        status="standing_configuration",
        semantic_object="FLATTEN_TD_MODE",
        observed_value=VENUE_NATIVE_TD_MODE_VALUE,
        transformation=TD_MODE_TRANSFORMATION,
        output_object="VENUE_NATIVE_TD_MODE",
        epistemic_class="STANDING_CONFIGURATION_NOT_ROW_MGNMODE",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="serialize_canary_flatten_venue_native_payload_v1",
        field="ordType",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        status="standing_configuration",
        semantic_object="FLATTEN_ORD_TYPE",
        observed_value=VENUE_NATIVE_ORD_TYPE_VALUE,
        transformation=ORD_TYPE_TRANSFORMATION,
        output_object="VENUE_NATIVE_ORD_TYPE",
        epistemic_class="STANDING_CONFIGURATION",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="build_venue_native_order_body_v1",
        field="reduceOnly",
        source_path=(
            "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
            "okx_response_mapper_v1.py"
        ),
        status="standing_z2cb_mandatory_json_boolean",
        semantic_object="FLATTEN_REDUCE_ONLY",
        observed_value="true_JSON_BOOLEAN_WIRE_TYPE_UNPROVEN",
        transformation=REDUCE_ONLY_TRANSFORMATION,
        output_object="VENUE_NATIVE_REDUCE_ONLY",
        epistemic_class="STANDING_CONFIGURATION_WIRE_TYPE_UNPROVEN",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="FlattenPricePermitV1",
        field="px",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_limit_price_contract_v1.py"
        ),
        status="bound_external_input_not_from_observed_position",
        semantic_object="FLATTEN_LIMIT_PX",
        observed_value=PX_SOURCE_CLASS_VALUE,
        transformation=PX_TRANSFORMATION,
        output_object="VENUE_NATIVE_PX",
        epistemic_class="BOUND_EXTERNAL_INPUT",
        adjudication_status="PROVEN_AS_REQUIRED_INPUT_SEND_TIME_NOT_MINTED",
    ),
    _seam(
        producer="serialize_canary_flatten_clordid_v1",
        field="clOrdId",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        status="deterministic_generated",
        semantic_object="FLATTEN_CLORDID",
        observed_value=CLORDID_SOURCE_CLASS_VALUE,
        transformation=CLORDID_TRANSFORMATION,
        output_object="VENUE_NATIVE_CLORDID",
        epistemic_class="GENERATED_NOT_FROM_POSITION",
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
        observed_value=REQUEST_POS_SIDE,
        transformation="OMITTED_FROM_VENUE_NATIVE_BODY",
        output_object="VENUE_NATIVE_FLATTEN_BODY_WITHOUT_POSSIDE",
        epistemic_class="CURRENT_AUTHORITATIVE_MAPPER",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="serialize_signed_post_body_v1",
        field="CONTRACT_BOUNDARY",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/okx_live_canary_signer_v1.py"
        ),
        status="canonical_json_before_hmac",
        semantic_object="EXACT_PAYLOAD_CONTRACT_BOUNDARY",
        observed_value=CONTRACT_BOUNDARY_VALUE,
        transformation="JSON_DUMPS_SEPARATORS_COMMA_COLON_ENSURE_ASCII",
        output_object="CANONICAL_JSON_THEN_SHA256",
        epistemic_class="SERIALIZATION_BEFORE_TRANSPORT_METADATA",
        adjudication_status="PROVEN",
    ),
    _seam(
        producer="offline_contract_proof_price_permit_v1",
        field="px_fixture",
        source_path=(
            "src/ops/section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1/"
            "payload_builder_v1.py"
        ),
        status="offline_regression_fixture",
        semantic_object="OFFLINE_PROOF_PX",
        observed_value=OFFLINE_CONTRACT_PROOF_PX_CLASS,
        transformation="NOT_PROMOTED_TO_SEND_TIME_PX",
        output_object="NOT_SEND_TIME_PX",
        epistemic_class="CLASS_B_FIXTURE_NOT_LIVE_QUOTE",
        adjudication_status="NOT_PROMOTED",
    ),
)


def exact_flatten_payload_lineage_v1() -> tuple[dict[str, str], ...]:
    return EXACT_FLATTEN_PAYLOAD_LINEAGE


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = exact_flatten_payload_lineage_v1()
    classes: dict[str, int] = {}
    for seam in seams:
        key = seam["epistemic_class"]
        classes[key] = classes.get(key, 0) + 1
    return {
        "SEAM_COUNT": len(seams),
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
        "EPISTEMIC_CLASS_COUNTS": classes,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CONTRACT_BOUNDARY": CONTRACT_BOUNDARY_VALUE,
        "PX_SOURCE_CLASS": PX_SOURCE_CLASS_VALUE,
        "REQUEST_POS_SIDE": REQUEST_POS_SIDE,
        "PROVEN_SEAMS": [
            seam["field"] for seam in seams if seam["adjudication_status"].startswith("PROVEN")
        ],
        "NOT_PROMOTED_SEAMS": [
            seam["field"] for seam in seams if seam["adjudication_status"] == "NOT_PROMOTED"
        ],
    }
