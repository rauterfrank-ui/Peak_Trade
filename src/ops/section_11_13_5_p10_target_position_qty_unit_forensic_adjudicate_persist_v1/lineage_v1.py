"""Machine-checkable TARGET_POSITION_QTY unit lineage. Authority none for this table."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.constants_v1 import (
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    TARGET_POSITION_QTY_UNIT,
)

# Epistemic classes (GO-required):
# A canonical authority
# B forensic raw evidence / original output
# C already-adjudicated conclusion
# D historical intermediate state
# E navigation/index evidence
# F interpretation
# G hypothesis
# H unresolved/conflicting evidence


def _seam(
    *,
    producer: str,
    field: str,
    source_path: str,
    status: str,
    input_unit: str,
    transformation: str,
    output_unit: str,
    rounding: str,
    contract_value_dependency: str,
    instrument_metadata_dependency: str,
    evidence_reference: str,
    epistemic_class: str,
    adjudication_status: str,
) -> dict[str, str]:
    return {
        "producer": producer,
        "field": field,
        "source_path": source_path,
        "status": status,
        "input_unit": input_unit,
        "transformation": transformation,
        "output_unit": output_unit,
        "rounding": rounding,
        "contract_value_dependency": contract_value_dependency,
        "instrument_metadata_dependency": instrument_metadata_dependency,
        "evidence_reference": evidence_reference,
        "epistemic_class": epistemic_class,
        "adjudication_status": adjudication_status,
    }


TARGET_POSITION_QTY_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="OKX GET /api/v5/account/positions",
        field="pos",
        source_path=(
            "src/ops/section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1/"
            "captured_payload_v1.py"
        ),
        status="current_raw_captured_authorized_forensic_fields",
        input_unit="UNPROVEN",
        transformation="NONE_CAPTURED_AS_STRING_1",
        output_unit="UNPROVEN",
        rounding="NONE_OBSERVED",
        contract_value_dependency="NONE_PROVEN",
        instrument_metadata_dependency="instId=SUI-USD_UM_XPERP-310404",
        evidence_reference=(
            "evidence/ops/section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1/"
            "20260903T223726Z/ADJUDICATION.json"
        ),
        epistemic_class="B",
        adjudication_status="RAW_POS_1_UNIT_UNPROVEN",
    ),
    _seam(
        producer="classify_target_position_state_v1._signed_observed_pos",
        field="pos|posSize",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="PARSE_DECIMAL_NO_UNIT_BIND_POS_PREFERRED_OVER_POSSIZE",
        output_unit="UNPROVEN",
        rounding="NONE_FAIL_CLOSED_ON_UNPARSEABLE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="pre_submit_state_v1._signed_observed_pos",
        epistemic_class="A",
        adjudication_status="PRODUCER_HAS_NO_UNIT_CONTRACT",
    ),
    _seam(
        producer="classify_target_position_state_v1",
        field="signed_pos",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="FORMAT_DECIMAL_F_NO_UNIT",
        output_unit="UNPROVEN",
        rounding="DECIMAL_FORMAT_F_NOT_QUANTIZED",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="instId match unique row",
        evidence_reference="TargetPositionStateClassificationV1.signed_pos",
        epistemic_class="A",
        adjudication_status="NUMERIC_SIGN_ONLY",
    ),
    _seam(
        producer="adjudicate_prerequisite_08_window_v1",
        field="TARGET_POSITION_QTY_RAW",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="IDENTITY_COPY_SIGNED_POS",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="TARGET_POSITION_QTY_RAW=classified.signed_pos",
        epistemic_class="A",
        adjudication_status="IDENTITY_COPY_UNIT_UNPROVEN",
    ),
    _seam(
        producer="qty_numeric_status_v1",
        field="TARGET_POSITION_QTY_NUMERIC",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="DECIMAL_PARSE_ONLY_NO_UNIT",
        output_unit="PASS_OR_FAIL_NUMERIC_STATUS_NOT_A_UNIT",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="P08 TARGET_POSITION_QTY_NUMERIC=PASS",
        epistemic_class="C",
        adjudication_status="NUMERIC_PASS_IS_NOT_UNIT_PROOF",
    ),
    _seam(
        producer="adjudicate_prerequisite_08_window_v1",
        field="TARGET_POSITION_QTY_UNIT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="HARDCODED_UNPROVEN",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="TARGET_POSITION_QTY_UNIT hardcoded UNPROVEN",
        epistemic_class="A",
        adjudication_status="CANONICAL_CURRENT_UNPROVEN",
    ),
    _seam(
        producer="execution_prerequisite_08_cluster_contract_v1",
        field="UNIT_CHAIN_VERDICT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "execution_prerequisite_08_cluster_contract_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="NONE_CONSTANT",
        output_unit="PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="UNIT_CHAIN_VERDICT constant",
        epistemic_class="A",
        adjudication_status="IDENTITY_EXPLICITLY_UNPROVEN",
    ),
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="candidate_flatten_qty",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="ABS_SIGNED_POS_NO_UNIT_CONVERSION",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="candidate_flatten_qty=abs(signed_pos)",
        epistemic_class="A",
        adjudication_status="IMPLICIT_NUMERIC_PASSTHROUGH_NOT_UNIT_PROOF",
    ),
    _seam(
        producer="build_minimum_valid_canary_flatten_order_plan_v1",
        field="quantity",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        status="current",
        input_unit="UNPROVEN",
        transformation="FORMAT_FLATTEN_QTY_FROM_ABS_POS",
        output_unit="UNPROVEN",
        rounding="FORMAT_ONLY",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="CanaryFlattenOrderPlanV1.quantity",
        epistemic_class="A",
        adjudication_status="FLATTEN_PLAN_QTY_UNIT_UNPROVEN",
    ),
    _seam(
        producer="build_venue_native_order_body_v1",
        field="sz",
        source_path=(
            "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
            "okx_response_mapper_v1.py"
        ),
        status="current",
        input_unit="UNPROVEN",
        transformation="IDENTITY_SZ_EQUALS_QUANTITY_NO_UNIT_CONVERSION",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference='body["sz"]=quantity',
        epistemic_class="A",
        adjudication_status="HIDDEN_IDENTITY_COPY_NOT_UNIT_PROOF",
    ),
    _seam(
        producer="venue_contract_count_v1 / exposure_v1 canary ENTRY order-plan",
        field="quantity / ORDER_PLAN_QTY_UNIT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/venue_contract_count_v1.py"
        ),
        status="current_separate_object",
        input_unit="CONTRACTS_SZ",
        transformation="venue_contract_count = SUI_OPERATIVE_ORDER_SZ",
        output_unit="contracts / VENUE_CONTRACT_COUNT",
        rounding="NO_FLOOR_CEIL_ROUND_FAIL_CLOSED_ON_MINSZ_LOTSZ",
        contract_value_dependency="ctVal_NOT_QTY_TO_SZ_FACTOR",
        instrument_metadata_dependency="minSz floor / lotSz increment admissibility only",
        evidence_reference="PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md",
        epistemic_class="C",
        adjudication_status="ADJUDICATED_FOR_ORDER_PLAN_NOT_TARGET_POSITION_QTY",
    ),
    _seam(
        producer="Z2BE/Z2BF SUI_OPERATIVE_ORDER_SZ",
        field="SUI_OPERATIVE_ORDER_SZ",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/venue_contract_count_v1.py"
        ),
        status="current_separate_object_historical_bind_consumed",
        input_unit="CONTRACTS_SZ",
        transformation="OWNER_RATIFIED_CANARY_ENTRY_COUNT_NOT_POSITION_POS",
        output_unit="CONTRACTS_SZ",
        rounding="NONE",
        contract_value_dependency="NOT_DERIVED_FROM_CTVAL",
        instrument_metadata_dependency="NOT_DERIVED_FROM_MINSZ",
        evidence_reference="SUI_OPERATIVE_ORDER_SZ=1 UNIT=CONTRACTS_SZ",
        epistemic_class="C",
        adjudication_status="NOT_TARGET_POSITION_QTY",
    ),
    _seam(
        producer="POST_6149 / #6151 MAX_SIZE_NORMALIZATION",
        field="ORDER_PLAN_QTY_DOMAIN",
        source_path="docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md",
        status="historical_adjudicated_for_order_plan",
        input_unit="UNTYPED_THEN_TYPED_VENUE_CONTRACT_COUNT",
        transformation="TYPED_SYSTEM_CONTRACT_NOT_MINSZ_COPY",
        output_unit="VENUE_CONTRACT_COUNT",
        rounding="FAIL_CLOSED_NO_REWRITE",
        contract_value_dependency="NORMALIZATION_REQUIRES_CTVAL=false",
        instrument_metadata_dependency="maxLmtSz/maxMktSz unit bound as contracts for ORDER PLAN",
        evidence_reference="#6150 UNBOUND historical; #6151 BOUND order-plan typed domain",
        epistemic_class="C",
        adjudication_status="NOT_APPLICABLE_TO_TARGET_POSITION_QTY",
    ),
    _seam(
        producer="STEP-29P capital_risk_sizing_v1",
        field="candidate_quantity / rounded_quantity",
        source_path="src/governance/capital_risk_sizing_v1.py",
        status="current_separate_no_order_graph",
        input_unit="UNPROVEN_AS_TARGET_POSITION_QTY",
        transformation="LOSS_BUDGET_AND_NOTIONAL_PER_UNIT_THEN_FLOOR_TO_LOT",
        output_unit="UNPROVEN_AS_TARGET_POSITION_QTY",
        rounding="FLOOR_TO_LOT",
        contract_value_dependency="instrument.contract_multiplier",
        instrument_metadata_dependency="lot_size / maximum_quantity",
        evidence_reference="STEP_29P_SOLE_PRODUCTIVE_RISK_SIZING_OWNER",
        epistemic_class="A",
        adjudication_status="NOT_TARGET_POSITION_QTY_PRODUCER",
    ),
    _seam(
        producer="STEP-29Q canonical_order_intent_v1",
        field="PLAN_ONLY intent quantity provenance",
        source_path="src/governance/canonical_order_intent_v1.py",
        status="current_separate_plan_only",
        input_unit="BOUND_TO_STEP_29P_PROVENANCE",
        transformation="NONE_NOT_DIRECTLY_SUBMITTABLE",
        output_unit="PLAN_ONLY_NOT_TARGET_POSITION_QTY",
        rounding="NONE_IN_THIS_CENSUS",
        contract_value_dependency="NONE_IN_THIS_CENSUS",
        instrument_metadata_dependency="NONE_IN_THIS_CENSUS",
        evidence_reference="STEP_29Q_QUANTITY_PROVENANCE_BOUND_TO_STEP_29P",
        epistemic_class="A",
        adjudication_status="NOT_TARGET_POSITION_QTY_PRODUCER",
    ),
    _seam(
        producer="SimulatedExecutionPortV1",
        field="quantity",
        source_path=(
            "src/ops/single_future_stateful_no_order_runtime_activation_v1/"
            "simulated_execution_port_v1.py"
        ),
        status="current_cap72_no_order_only",
        input_unit="UNPROVEN_AS_TARGET_POSITION_QTY",
        transformation="DELEGATE_TO_CANONICAL_ACCOUNTING_NO_VENUE_SZ",
        output_unit="SIMULATED_NOT_VENUE_POS",
        rounding="ACCOUNTING_DELEGATE",
        contract_value_dependency="NONE_FOR_TARGET_POSITION_QTY",
        instrument_metadata_dependency="NONE_FOR_TARGET_POSITION_QTY",
        evidence_reference="SimulatedExecutionPortV1.apply_intended_action",
        epistemic_class="A",
        adjudication_status="NOT_TARGET_POSITION_QTY_PRODUCER",
    ),
    _seam(
        producer="Master Runbook §11.13.5 P08 CASE_A persist",
        field="TARGET_POSITION_QTY_UNIT",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_canonical",
        input_unit="UNPROVEN",
        transformation="NONE",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="SUI-USD_UM_XPERP-310404",
        evidence_reference="TARGET_POSITION_QTY_UNIT=UNPROVEN after P08 close",
        epistemic_class="A",
        adjudication_status="CANONICAL_CURRENT_UNPROVEN",
    ),
    _seam(
        producer="P08 authorized captured row",
        field="posCcy",
        source_path=(
            "src/ops/section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1/"
            "captured_payload_v1.py"
        ),
        status="current_absent_from_authorized_forensic_fields",
        input_unit="NOT_CAPTURED",
        transformation="NOT_AVAILABLE",
        output_unit="NOT_AVAILABLE",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="AUTHORIZED_TARGET_ROW has no posCcy; original wire bytes unavailable",
        epistemic_class="H",
        adjudication_status="ABSENT_CANNOT_PROVE_UNIT",
    ),
    _seam(
        producer="historical BTC XPERP denomination / Z2AH",
        field="API_EXECUTION_DENOMINATION / OEM 0.01 BTC",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="historical_btc_path",
        input_unit="HISTORICAL_BTC_UNRESOLVED_FACE_VALUE",
        transformation="NOT_TRANSFERRED_TO_SUI",
        output_unit="NOT_APPLICABLE",
        rounding="NONE",
        contract_value_dependency="OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN",
        instrument_metadata_dependency="BTC-USD_UM_XPERP historical",
        evidence_reference="EXECUTION_PREREQUISITE_14_NO_BTC_TO_SUI_SEMANTIC_TRANSFER=PASS_NEGATIVE",
        epistemic_class="D",
        adjudication_status="HISTORICAL_NOT_CURRENT_SUI_TARGET_POSITION_QTY",
    ),
    _seam(
        producer="Map of Truth / Atlas",
        field="navigation references",
        source_path="docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        status="navigation_only",
        input_unit="NONE",
        transformation="NONE",
        output_unit="NONE",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS",
        epistemic_class="E",
        adjudication_status="ZERO_AUTHORITY",
    ),
)

LINEAGE_FIELD_NAMES: tuple[str, ...] = (
    "producer",
    "field",
    "source_path",
    "status",
    "input_unit",
    "transformation",
    "output_unit",
    "rounding",
    "contract_value_dependency",
    "instrument_metadata_dependency",
    "evidence_reference",
    "epistemic_class",
    "adjudication_status",
)


def target_position_qty_lineage_v1() -> list[dict[str, str]]:
    return [dict(row) for row in TARGET_POSITION_QTY_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    classes: dict[str, int] = {}
    for row in TARGET_POSITION_QTY_LINEAGE:
        classes[row["epistemic_class"]] = classes.get(row["epistemic_class"], 0) + 1
    proven_units = {
        row["output_unit"]
        for row in TARGET_POSITION_QTY_LINEAGE
        if row["field"]
        in {"TARGET_POSITION_QTY_UNIT", "TARGET_POSITION_QTY_RAW", "signed_pos", "pos"}
        and row["output_unit"] not in {TARGET_POSITION_QTY_UNIT, "UNPROVEN", "NOT_AVAILABLE"}
    }
    return {
        "SEAM_COUNT": len(TARGET_POSITION_QTY_LINEAGE),
        "EPISTEMIC_CLASS_COUNTS": classes,
        "TARGET_POSITION_QTY_PROVEN_UNITS_FOUND": sorted(proven_units),
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
