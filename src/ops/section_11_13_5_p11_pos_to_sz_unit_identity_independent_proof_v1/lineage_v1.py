"""Machine-checkable pos->sz lineage after independent venue-unit proof."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.constants_v1 import (
    CONVERSION_FORMULA_VALUE,
    CURRENT_UNIT_CONTRACT_VALUE,
    POS_UNIT_VALUE,
    SZ_UNIT_VALUE,
    TARGET_POSITION_QTY_UNIT,
    UNIT_CHAIN_VERDICT_VALUE,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    NUMBER_OF_CONTRACTS,
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
        producer="OKX official GET /api/v5/account/positions",
        field="pos",
        source_path=(
            "src/ops/section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1/"
            "official_excerpts_v1.py"
        ),
        status="current_official_definition",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="NONE_VENUE_DEFINED",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="ctVal_NOTIONAL_ONLY_NOT_POS_TO_SZ",
        instrument_metadata_dependency="instType=FUTURES|SWAP|OPTION",
        evidence_reference="POS_REST_GET_POSITIONS_DEFINITION",
        epistemic_class="B",
        adjudication_status="POS_UNIT_NUMBER_OF_CONTRACTS_PROVEN",
    ),
    _seam(
        producer="OKX GET /api/v5/account/positions parser",
        field="pos|posSize",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="PARSE_DECIMAL_POS_PREFERRED_OVER_POSSIZE_NO_UNIT_REWRITE",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE_FAIL_CLOSED_ON_UNPARSEABLE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="pre_submit_state_v1._signed_observed_pos",
        epistemic_class="A",
        adjudication_status="PARSER_PRESERVES_NUMBER_OF_CONTRACTS",
    ),
    _seam(
        producer="classify_target_position_state_v1",
        field="signed_pos",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="FORMAT_DECIMAL_F_SIGN_PRESERVED",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="DECIMAL_FORMAT_F_NOT_QUANTIZED",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="instId match unique row",
        evidence_reference="TargetPositionStateClassificationV1.signed_pos",
        epistemic_class="A",
        adjudication_status="SIGNED_POS_SAME_UNIT",
    ),
    _seam(
        producer="adjudicate_prerequisite_08_window_v1",
        field="TARGET_POSITION_QTY",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="IDENTITY_COPY_SIGNED_POS",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="TARGET_POSITION_QTY_RAW=classified.signed_pos",
        epistemic_class="A",
        adjudication_status="TARGET_POSITION_QTY_UNIT_PROVEN",
    ),
    _seam(
        producer="observe_target_position_flatten_candidate_v1",
        field="candidate_flatten_qty",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
        ),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="ABS_SIGNED_POS_SIGN_ONLY_NOT_UNIT_CONVERSION",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="bound FUTURES xperp",
        evidence_reference="identity_flatten_sz_from_signed_pos_v1",
        epistemic_class="A",
        adjudication_status="FLATTEN_CANDIDATE_IDENTITY",
    ),
    _seam(
        producer="build_minimum_valid_canary_flatten_order_plan_v1",
        field="quantity",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="FORMAT_FLATTEN_QTY_FROM_ABS_POS",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="FORMAT_ONLY",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="NONE",
        evidence_reference="CanaryFlattenOrderPlanV1.quantity",
        epistemic_class="A",
        adjudication_status="FLATTEN_PLAN_QTY_NUMBER_OF_CONTRACTS",
    ),
    _seam(
        producer="build_venue_native_order_body_v1",
        field="sz",
        source_path=(
            "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
            "okx_response_mapper_v1.py"
        ),
        status="current",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="IDENTITY_SZ_EQUALS_QUANTITY_NO_CTVAL_NO_TGTCCY",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="FUTURES tgtCcy not applicable",
        evidence_reference="body[sz]=quantity plus official FUTURES sz domain",
        epistemic_class="A",
        adjudication_status="VENUE_NATIVE_SZ_NUMBER_OF_CONTRACTS",
    ),
    _seam(
        producer="OKX official Place Order / fill / minSz / maxLmtSz",
        field="sz",
        source_path=(
            "src/ops/section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1/"
            "official_excerpts_v1.py"
        ),
        status="current_official_definition",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="NONE_VENUE_DEFINED_FOR_FUTURES",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="ctVal_NOTIONAL_ONLY_NOT_POS_TO_SZ",
        instrument_metadata_dependency="instType=FUTURES derivatives contract",
        evidence_reference="FILL_SZ_DEFINITION+MIN_SZ_DEFINITION+MAX_LMT_SZ_DEFINITION+ALGO_SZ",
        epistemic_class="B",
        adjudication_status="SZ_UNIT_NUMBER_OF_CONTRACTS_PROVEN",
    ),
    _seam(
        producer="order-plan typed domain (rejected as alias)",
        field="ORDER_PLAN_QTY_UNIT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/venue_contract_count_v1.py"
        ),
        status="current_separate_object",
        input_unit="CONTRACTS_SZ",
        transformation="NOT_USED_AS_TARGET_POSITION_QTY_PROOF",
        output_unit="contracts / VENUE_CONTRACT_COUNT",
        rounding="NONE",
        contract_value_dependency="NOT_POS_TO_SZ",
        instrument_metadata_dependency="ENTRY order-plan only",
        evidence_reference="ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY",
        epistemic_class="C",
        adjudication_status="REJECTED_AS_ALIAS_PROOF",
    ),
    _seam(
        producer="P10 historical persist",
        field="TARGET_POSITION_QTY_UNIT",
        source_path=(
            "src/ops/section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1/"
            "constants_v1.py"
        ),
        status="historical_p10_unproven",
        input_unit="UNPROVEN",
        transformation="NONE_P10_OFFLINE_CENSUS_ONLY",
        output_unit="UNPROVEN",
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="SUI-USD_UM_XPERP-310404",
        evidence_reference="P10 TARGET_POSITION_QTY_UNIT=UNPROVEN",
        epistemic_class="D",
        adjudication_status="HISTORICAL_UNPROVEN_NOT_CURRENT",
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
    _seam(
        producer="Place Order request table underspecification",
        field="sz request param",
        source_path=(
            "src/ops/section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1/"
            "official_excerpts_v1.py"
        ),
        status="current_underspecified_table_not_competing_unit",
        input_unit=NUMBER_OF_CONTRACTS,
        transformation="NONE_TABLE_SAYS_QUANTITY_TO_BUY_OR_SELL_ONLY",
        output_unit=NUMBER_OF_CONTRACTS,
        rounding="NONE",
        contract_value_dependency="NONE",
        instrument_metadata_dependency="closed by minSz/maxLmtSz/fillSz/tgtCcy-SPOT-only",
        evidence_reference="PLACE_ORDER_SZ_REQUEST_DEFINITION",
        epistemic_class="H",
        adjudication_status="UNDERSPECIFIED_NOT_CONTRADICTION",
    ),
)


def target_position_qty_lineage_v1() -> list[dict[str, str]]:
    return [dict(row) for row in TARGET_POSITION_QTY_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    rows = target_position_qty_lineage_v1()
    counts: dict[str, int] = {}
    proven: list[str] = []
    for row in rows:
        klass = row["epistemic_class"]
        counts[klass] = counts.get(klass, 0) + 1
        if (
            row["field"] in {"pos", "signed_pos", "TARGET_POSITION_QTY", "sz"}
            and row["output_unit"] == NUMBER_OF_CONTRACTS
        ):
            proven.append(row["field"])
    return {
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
        "SEAM_COUNT": len(rows),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "TARGET_POSITION_QTY_PROVEN_UNITS_FOUND": sorted(set(proven)),
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "CURRENT_UNIT_CONTRACT": CURRENT_UNIT_CONTRACT_VALUE,
        "POS_UNIT": POS_UNIT_VALUE,
        "SZ_UNIT": SZ_UNIT_VALUE,
        "UNIT_CHAIN_VERDICT": UNIT_CHAIN_VERDICT_VALUE,
        "CONVERSION_FORMULA": CONVERSION_FORMULA_VALUE,
    }
