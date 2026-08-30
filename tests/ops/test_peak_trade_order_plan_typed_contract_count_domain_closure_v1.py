"""Order-plan typed venue-contract-count domain closure v1.

Guards plus producer/identity/minSz/lotSz/max-size comparison tests.
No live authority. No venue GET/POST. No freshness policy. No consumer bind.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POSITION_COUNT_LIMIT,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    LiveCanaryExposureError,
    build_canary_exposure_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    CanaryOrderPlanV1,
    build_minimum_valid_canary_order_plan_v1,
    extract_instrument_constraints_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    CONTRACT_SIZING_FORMULA,
    FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1,
    MAX_SIZE_COMPARISON_DOMAIN,
    ONE_CONTRACT_EQUALS_ONE_SUI,
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_SEMANTIC,
    ORDER_PLAN_QTY_UNIT,
    SUI_OPERATIVE_ORDER_SZ,
    VENUE_ORDER_SZ_MAPPING,
    LiveCanaryVenueContractCountError,
    assert_identity_sz_after_contract_sizing_v1,
    assert_venue_contract_count_admissible_v1,
    canary_venue_contract_count_v1,
    compare_venue_contract_count_to_max_size_v1,
    select_max_size_field_for_order_type_v1,
    serialize_venue_sz_from_typed_contract_count_v1,
)
from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import (
    _max_available_plan_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md"
)
PRIOR_6150 = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md"
)
PRIOR_6149 = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md"
PRIOR_6148 = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md"
)
PRIOR_6147 = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md"
)
LIMIT_GATES_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md"
)
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
EXPOSURE = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exposure_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
OWNER_GO = "PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1"
SEE_ALSO = (
    "SEE_ALSO_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE="
    "docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md"
)
EXPECTED_ORIGIN_MAIN_SHA = "1d84bd4f0835b0ec719ce4d707f61252fb774a66"
INSTRUMENTS = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "instType": "FUTURES",
            "ruleType": "xperp",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.0001",
            "ctVal": "1",
            "ctValCcy": "SUI",
            "state": "live",
            "maxLmtSz": "100000000",
            "maxMktSz": "100000",
        }
    ],
}
TICKER = {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "last": "0.8209"}]}


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_spec_is_subordinate_and_names_owner_go() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "NO_LIVE_AUTHORITY=true" in spec
    assert "NETWORK_VENUE_GET_PERFORMED=false" in spec
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "NETWORK_DOCUMENTATION_READ_PERFORMED=false" in spec
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in spec
    assert "RUNTIME_MUTATION_JUSTIFIED=true" in spec
    assert "RUNTIME_MUTATION_PERFORMED=true" in spec
    assert "CANARY_VENUE_CONSTRAINT_PLAN_RUNTIME_MUTATION=true" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md"
        in section
    )
    for text in (spec, section):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "MAX_SIZE_UNIT=contracts" in text
        assert "MAX_SIZE_NORMALIZATION_STATUS=BOUND" in text
        assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in text
        assert "MAX_SIZE_CONSUMER_BOUND=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
        assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESHNESS_POLICY" in text
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "NEXT_DISTINCT_SURFACE=MAX_SIZE_FRESHNESS_POLICY" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert (
        "SOURCE_ADJUDICATION_RESULT="
        "MAX_SIZE_NORMALIZATION_BOUND_TYPED_VENUE_CONTRACT_COUNT_IDENTITY_AFTER_CONTRACT_SIZING_FRESHNESS_AND_CONSUMER_UNBOUND"
        in spec
    )


def test_historical_6150_unbound_mapping_remains() -> None:
    prior = PRIOR_6150.read_text(encoding="utf-8")
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in prior
    assert "ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND" in prior
    assert "ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=UNBOUND" in prior
    assert "MAX_SIZE_COMPARISON_DOMAIN_STATUS=UNBOUND" in prior
    assert "FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true" in prior
    assert SEE_ALSO in prior
    assert "MAX_SIZE_UNIT=contracts" in PRIOR_6149.read_text(encoding="utf-8")
    assert "MAX_SIZE_UNIT=UNBOUND" in PRIOR_6148.read_text(encoding="utf-8")
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in LIMIT_GATES_SPEC.read_text(
        encoding="utf-8"
    )


def test_typed_quantity_domain_contract() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    assert "ORDER_PLAN_QTY_SEMANTIC_STATUS=BOUND" in spec
    assert f"ORDER_PLAN_QTY_SEMANTIC={ORDER_PLAN_QTY_SEMANTIC}" in spec
    assert "ORDER_PLAN_V1_PYTHON_FIELD_NAME=quantity" in spec
    assert "ORDER_PLAN_V1_HAS_FIELD_NAMED_QTY=false" in spec
    assert "ORDER_PLAN_QTY_UNIT_STATUS=BOUND" in spec
    assert "ORDER_PLAN_QTY_UNIT=contracts" in spec
    assert "ORDER_PLAN_QTY_DOMAIN_STATUS=BOUND" in spec
    assert "ORDER_PLAN_QTY_DOMAIN=VENUE_CONTRACT_COUNT" in spec
    assert ORDER_PLAN_QTY_UNIT == "contracts"
    assert ORDER_PLAN_QTY_DOMAIN == "VENUE_CONTRACT_COUNT"
    assert "quantity: str" in order_plan
    assert "qty: str" not in order_plan
    assert "quantity" in CanaryOrderPlanV1.__dataclass_fields__
    assert "quantity_domain" in CanaryOrderPlanV1.__dataclass_fields__
    assert "qty" not in CanaryOrderPlanV1.__dataclass_fields__
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"
    assert POSITION_COUNT_LIMIT == 1


def test_producer_uses_operative_contract_count_not_minsz_copy() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    assert "CONTRACT_SIZING_FORMULA_STATUS=BOUND" in spec
    assert "CONTRACT_SIZING_FORMULA=venue_contract_count = SUI_OPERATIVE_ORDER_SZ" in spec
    assert CONTRACT_SIZING_FORMULA == "venue_contract_count = SUI_OPERATIVE_ORDER_SZ"
    assert canary_venue_contract_count_v1() == SUI_OPERATIVE_ORDER_SZ == "1"
    assert "qty_raw = instrument_min_sz if quantity is None" not in exposure
    assert "canary_venue_contract_count_v1" in exposure
    binding = build_canary_exposure_binding_v1(
        venue="OKX",
        account_scope="acct",
        instrument_min_sz="1",
        instrument_lot_sz="1",
        instrument_ct_val="1",
        instrument_tick_sz="0.0001",
        reference_price="0.8209",
    )
    assert binding.quantity == SUI_OPERATIVE_ORDER_SZ
    assert binding.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert binding.quantity_unit == ORDER_PLAN_QTY_UNIT
    with pytest.raises(LiveCanaryExposureError, match="OPERATIVE_CONTRACT_COUNT"):
        build_canary_exposure_binding_v1(
            venue="OKX",
            account_scope="acct",
            instrument_min_sz="1",
            instrument_lot_sz="1",
            instrument_ct_val="1",
            instrument_tick_sz="0.0001",
            quantity="2",
            reference_price="0.8209",
        )


def test_minsz_is_floor_not_quantity_source() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true" in spec
    assert FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1 is True
    assert (
        "MIN_SIZE_ROLE=venue_contract_count_lower_admissibility_floor_not_quantity_source" in spec
    )
    with pytest.raises(LiveCanaryVenueContractCountError, match="QUANTITY_BELOW_MIN_SZ"):
        assert_venue_contract_count_admissible_v1(
            venue_contract_count="1",
            instrument_min_sz="2",
            instrument_lot_sz="1",
        )
    admitted = assert_venue_contract_count_admissible_v1(
        venue_contract_count="1",
        instrument_min_sz="1",
        instrument_lot_sz="1",
    )
    assert admitted == "1"
    with pytest.raises(LiveCanaryExposureError, match="QUANTITY_BELOW_MIN_SZ"):
        build_canary_exposure_binding_v1(
            venue="OKX",
            account_scope="acct",
            instrument_min_sz="2",
            instrument_lot_sz="1",
            instrument_ct_val="1",
            instrument_tick_sz="0.0001",
            quantity="1",
            reference_price="0.8209",
        )


def test_lotsz_is_increment_admissibility_not_quantization_rewrite() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "LOT_SIZE_ROLE_STATUS=BOUND" in spec
    assert "LOTSZ_USED_AS_QTY_TO_SZ_TRANSFORM=false" in spec
    assert "LOT_SIZE_QUANTIZATION_STATUS=NOT_REQUIRED" in spec
    assert "NO_FLOOR_CEIL_ROUND_REWRITE" in spec
    with pytest.raises(LiveCanaryVenueContractCountError, match="QUANTITY_NOT_MULTIPLE_OF_LOT_SZ"):
        assert_venue_contract_count_admissible_v1(
            venue_contract_count="1",
            instrument_min_sz="1",
            instrument_lot_sz="2",
        )


def test_submit_transport_identity_after_contract_sizing() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=BOUND" in spec
    assert "ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING=IDENTITY_AFTER_CONTRACT_SIZING" in spec
    assert VENUE_ORDER_SZ_MAPPING == "IDENTITY_AFTER_CONTRACT_SIZING"
    sz = serialize_venue_sz_from_typed_contract_count_v1(
        venue_contract_count="1",
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
    )
    assert sz == "1"
    body = build_venue_native_order_body_v1(
        client_order_id="abc123",
        instrument=DEFAULT_INSTRUMENT_ID,
        order_type="LIMIT",
        side="BUY",
        quantity=sz,
        px="0.1",
    )
    assert body["sz"] == "1"
    assert "ctVal" not in body
    assert "ctMult" not in body
    assert "ctType" not in body
    assert_identity_sz_after_contract_sizing_v1(
        quantity="1",
        sz=body["sz"],
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
    )
    with pytest.raises(LiveCanaryVenueContractCountError, match="SZ_NOT_IDENTITY"):
        assert_identity_sz_after_contract_sizing_v1(
            quantity="1",
            sz="2",
            quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        )
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=INSTRUMENTS,
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        pretrade_decision_id="test-fresh-decision-typed-domain",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity == "1"
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.quantity_unit == ORDER_PLAN_QTY_UNIT
    assert plan.venue_native_payload["sz"] == plan.quantity == "1"


def test_max_size_comparison_is_venue_contract_count_and_order_type_specific() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "MAX_SIZE_COMPARISON_DOMAIN_STATUS=BOUND" in spec
    assert "MAX_SIZE_COMPARISON_DOMAIN=venue_contract_count" in spec
    assert MAX_SIZE_COMPARISON_DOMAIN == "venue_contract_count"
    assert select_max_size_field_for_order_type_v1(order_type="LIMIT") == "maxLmtSz"
    assert select_max_size_field_for_order_type_v1(order_type="MARKET") == "maxMktSz"
    with pytest.raises(LiveCanaryVenueContractCountError, match="UNSUPPORTED_ORDER_TYPE"):
        select_max_size_field_for_order_type_v1(order_type="POST_ONLY")
    limit_ok = compare_venue_contract_count_to_max_size_v1(
        venue_contract_count="1",
        order_type="LIMIT",
        max_lmt_sz="100000000",
        max_mkt_sz="100000",
    )
    assert limit_ok["ok"] is True
    assert limit_ok["max_size_field"] == "maxLmtSz"
    market_ok = compare_venue_contract_count_to_max_size_v1(
        venue_contract_count="1",
        order_type="MARKET",
        max_lmt_sz="100000000",
        max_mkt_sz="100000",
    )
    assert market_ok["max_size_field"] == "maxMktSz"
    with pytest.raises(LiveCanaryVenueContractCountError, match="MAXLMTSZ"):
        compare_venue_contract_count_to_max_size_v1(
            venue_contract_count="100000001",
            order_type="LIMIT",
            max_lmt_sz="100000000",
            max_mkt_sz="100000",
        )
    with pytest.raises(LiveCanaryVenueContractCountError, match="MAXMKTSZ"):
        compare_venue_contract_count_to_max_size_v1(
            venue_contract_count="100001",
            order_type="MARKET",
            max_lmt_sz="100000000",
            max_mkt_sz="100000",
        )


def test_one_contract_equals_one_sui_remains_false() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    master = MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert "ONE_CONTRACT_EQUALS_ONE_SUI=false" in spec
    assert "NO_NORMALIZATION_CTVAL_1_TO_ONE_CONTRACT_EQUALS_ONE_SUI=true" in spec
    assert "NORMALIZATION_REQUIRES_CTVAL=false" in spec
    assert "NORMALIZATION_REQUIRES_CTMULT=false" in spec
    assert "NORMALIZATION_REQUIRES_CTTYPE=false" in spec
    assert ONE_CONTRACT_EQUALS_ONE_SUI is False
    assert "ONE_CONTRACT_EQUALS_ONE_SUI=false" in master


def test_extractor_and_max_size_fields_remain_unconsumed() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal" in spec
    assert "EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true" in spec
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    assert "ctMult" not in order_plan
    assert extract_instrument_constraints_v1 is not None
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source
    assert "REQUIRED_METADATA_EDGE_COUNT=8" in spec
    assert "BOUND_METADATA_EDGE_COUNT=0" in spec
    assert "PARTIAL_METADATA_EDGE_COUNT=2" in spec
    assert "UNBOUND_METADATA_EDGE_COUNT=6" in spec
    assert "CONFLICTED_METADATA_EDGE_COUNT=0" in spec
    assert "EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_FRESHNESS_POLICY" in spec


def test_kraken_live_flags_and_navigation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_EXCLUSION_CLOSED=true" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1_PRESERVED=true" in parent
    assert "PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert SEE_ALSO in LIMIT_GATES_SPEC.read_text(encoding="utf-8")
    assert SEE_ALSO in PRIOR_6147.read_text(encoding="utf-8")
    assert SEE_ALSO in PRIOR_6148.read_text(encoding="utf-8")
    assert SEE_ALSO in PRIOR_6149.read_text(encoding="utf-8")
    assert "STRATEGY_LOGIC_CHANGED=false" in spec
    assert "MAX_POSITIONS_CHANGED=false" in spec
