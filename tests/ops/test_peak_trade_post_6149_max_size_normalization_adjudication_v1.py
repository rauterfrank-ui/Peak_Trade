"""Post-6149 MAX_SIZE normalization adjudication v1.

Static/docs guards. Reuses existing owner tests. No core runtime
mutation. No live authority. No consumer implementation. No freshness
policy. No venue GET/POST. No new official-doc fetch.
"""

from __future__ import annotations

from pathlib import Path

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
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    CanaryOrderPlanV1,
    extract_instrument_constraints_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
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
MAPPER = (
    REPO_ROOT
    / "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/okx_response_mapper_v1.py"
)
OWNER_GO = "PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1"
SEE_ALSO = (
    "SEE_ALSO_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION="
    "docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md"
)
EXPECTED_ORIGIN_MAIN_SHA = "01d3a8e51e60783370381eadce72bfb50f25fb43"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_spec_is_subordinate_and_does_not_grant_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "NO_LIVE_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "NETWORK_VENUE_GET_PERFORMED=false" in spec
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "NETWORK_DOCUMENTATION_READ_PERFORMED=false" in spec
    assert "AUTH_REQUIRED=false" in spec
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in spec
    assert "RUNTIME_MUTATION_JUSTIFIED=false" in spec
    assert "RUNTIME_MUTATION_PERFORMED=false" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md"
        in section
    )
    for text in (spec, section):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "MAX_SIZE_UNIT=contracts" in text
        assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in text
        assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in text
        assert "MAX_SIZE_CONSUMER_BOUND=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
        assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION" in text
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "NEXT_DISTINCT_SURFACE=MAX_SIZE_NORMALIZATION" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert (
        "SOURCE_ADJUDICATION_RESULT="
        "MAX_SIZE_NORMALIZATION_UNBOUND_DOMAIN_IDENTITY_UNPROVEN_IDENTITY_COPY_IS_IMPLEMENTATION_NOT_AUTHORITY"
        in spec
    )
    assert "NETWORK_DOCUMENTATION_READ_PERFORMED=false" in section
    assert "NETWORK_VENUE_GET_PERFORMED=false" in section


def test_historical_6149_unit_bound_normalization_unbound_remains() -> None:
    prior = PRIOR_6149.read_text(encoding="utf-8")
    assert "MAX_SIZE_UNIT=contracts" in prior
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in prior
    assert "PEAK_TRADE_ORDER_PLAN_QTY_DOMAIN_EQUALS_CONTRACTS=UNPROVEN" in prior
    assert "PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false" in prior
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION" in prior
    assert SEE_ALSO in prior
    assert "MAX_SIZE_UNIT=UNBOUND" in PRIOR_6148.read_text(encoding="utf-8")
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in LIMIT_GATES_SPEC.read_text(
        encoding="utf-8"
    )


def test_order_plan_qty_semantic_and_unit_split() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    assert "ORDER_PLAN_QTY_SEMANTIC_STATUS=BOUND" in spec
    assert (
        "ORDER_PLAN_QTY_SEMANTIC="
        "runtime_field_quantity_docs_alias_qty_canary_minimum_exposure_order_size_string_copied_from_instrument_min_sz"
        in spec
    )
    assert "ORDER_PLAN_V1_PYTHON_FIELD_NAME=quantity" in spec
    assert "ORDER_PLAN_V1_HAS_FIELD_NAMED_QTY=false" in spec
    assert "ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND" in spec
    assert "ORDER_PLAN_QTY_UNIT=UNBOUND" in spec
    assert "PEAK_TRADE_ORDER_PLAN_QTY_DOMAIN_EQUALS_CONTRACTS=UNPROVEN" in spec
    assert "FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true" in spec
    assert "MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY" in exposure
    assert "quantity: str" in order_plan
    assert "qty: str" not in order_plan
    assert "quantity" in CanaryOrderPlanV1.__dataclass_fields__
    assert "qty" not in CanaryOrderPlanV1.__dataclass_fields__
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"


def test_venue_sz_semantic_and_mapping_unbound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mapper = MAPPER.read_text(encoding="utf-8")
    assert "VENUE_ORDER_SZ_SEMANTIC_STATUS=BOUND" in spec
    assert (
        "VENUE_ORDER_SZ_SEMANTIC=official_place_order_request_parameter_quantity_to_buy_or_sell"
        in spec
    )
    assert "VENUE_ORDER_SZ_UNIT_STATUS=UNBOUND" in spec
    assert "PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false" in spec
    assert "ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=UNBOUND" in spec
    assert "ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING=UNBOUND" in spec
    assert "RUNTIME_STRING_COPY_QUANTITY_TO_SZ=true" in spec
    assert "RUNTIME_STRING_COPY_IS_NOT_DOMAIN_IDENTITY_PROOF=true" in spec
    assert "RUNTIME_QTY_TO_SZ_MAPPING_IS_CANONICAL_AUTHORITY=false" in spec
    assert '"sz": quantity' in mapper
    body = build_venue_native_order_body_v1(
        client_order_id="abc123",
        instrument=DEFAULT_INSTRUMENT_ID,
        order_type="LIMIT",
        side="BUY",
        quantity="1",
        px="0.1",
    )
    assert body["sz"] == "1"
    assert "ctVal" not in body
    assert "ctMult" not in body
    assert "ctType" not in body


def test_lot_size_and_ct_fields_separated() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    assert "LOT_SIZE_ROLE_STATUS=BOUND" in spec
    assert "LOTSZ_USED_AS_QTY_TO_SZ_TRANSFORM=false" in spec
    assert "LOTSZ_USED_AS_RUNTIME_MODULO_VALIDATION=true" in spec
    assert "ORDER_PLAN_QTY_QUANTIZED_BEFORE_TRANSPORT=false" in spec
    assert "CURRENT_SUI_LOTSZ_1_IS_NOT_CONTRACT_DOMAIN_PROOF=true" in spec
    assert "NORMALIZATION_REQUIRES_CTVAL=false" in spec
    assert "NORMALIZATION_REQUIRES_CTMULT=false" in spec
    assert "NORMALIZATION_REQUIRES_CTTYPE=false" in spec
    assert "CTVAL_IS_NOT_QTY_TO_SZ_FORMULA=true" in spec
    assert "ONE_CONTRACT_EQUALS_ONE_SUI=false" in spec
    assert "NO_NORMALIZATION_CTVAL_1_TO_ONE_CONTRACT_EQUALS_ONE_SUI=true" in spec
    assert "QUANTITY_NOT_MULTIPLE_OF_LOT_SZ" in exposure
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    assert "ctMult" not in order_plan
    assert extract_instrument_constraints_v1 is not None


def test_comparison_domain_and_edges_remain_unbound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "MAX_SIZE_COMPARISON_DOMAIN_STATUS=UNBOUND" in spec
    assert "MAX_SIZE_COMPARISON_DOMAIN=UNBOUND" in spec
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in spec
    assert "MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND" in spec
    assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in spec
    assert "MAX_SIZE_CONSUMER_BOUND=false" in spec
    assert "REQUIRED_METADATA_EDGE_COUNT=8" in spec
    assert "BOUND_METADATA_EDGE_COUNT=0" in spec
    assert "PARTIAL_METADATA_EDGE_COUNT=2" in spec
    assert "UNBOUND_METADATA_EDGE_COUNT=6" in spec
    assert "CONFLICTED_METADATA_EDGE_COUNT=0" in spec
    assert "PARTIAL_EDGE_IDS=MAX_SIZE,INSTRUMENT_STATE" in spec
    assert (
        "UNBOUND_EDGE_IDS=MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN"
        in spec
    )
    assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in spec
    assert "EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_NORMALIZATION" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION" in spec
    assert "CURRENT_STATUS=PROVEN" not in spec
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source


def test_sui_operative_sz_is_separate_object() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    master = MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert "SUI_OPERATIVE_ORDER_SZ_IS_NOT_ORDER_PLAN_QUANTITY_OBJECT_PROOF=true" in spec
    assert "SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ" in spec
    assert "SUI_OPERATIVE_QTY_DERIVED_FROM_MINSZ=false" in spec
    assert "Z2S_API_SZ_FUTURES_UNIT_IS_NOT_SUI_ORDER_PLAN_QTY_BIND=true" in spec
    assert "ONE_CANONICAL_ORDER_PLAN_QTY_UNIT_EQUALS_ONE_OKX_CONTRACT=UNPROVEN" in spec
    assert "QTY_1_OBSERVED_IS_NOT_ONE_CONTRACT_PROOF=true" in spec
    assert "SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ" in master
    assert "FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true" in master
    assert "ONE_CONTRACT_EQUALS_ONE_SUI=false" in master


def test_kraken_and_live_flags_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_EXCLUSION_CLOSED=true" in spec
    assert "KRAKEN_METADATA_REUSED=false" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1_PRESERVED=true" in parent
    assert "PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1" in mot
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
    assert "RUNTIME_ALIGNMENT_REQUIRED=unproven" in spec
    assert "RUNTIME_ALIGNMENT_REQUIRED=unproven" in section
