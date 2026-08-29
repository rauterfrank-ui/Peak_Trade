"""MAX_SIZE freshness Owner-policy decision v1.

Static/docs guards. Reuses existing owner tests. No runtime mutation.
No live authority. No consumer implementation. No venue GET/POST.
No TTL. No event-cache. No indefinite reuse.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
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
    extract_instrument_constraints_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md"
PRIOR_6151 = (
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
OWNER_GO = "PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1"
SEE_ALSO = (
    "SEE_ALSO_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION="
    "docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md"
)
EXPECTED_ORIGIN_MAIN_SHA = "ae302d2b4c0425c4d42ece494d1b5996a9e54243"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def _latest_persist(section: str) -> str:
    marker = "MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1=true"
    start = section.index(marker)
    end = section.index("Normative subordinate persist:", start)
    return section[start:end]


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
    assert "RUNTIME_MUTATION_PERFORMED=false" in spec
    assert "NEW_SEMANTIC_POLICY=true" in spec
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    latest = _latest_persist(section)
    assert "MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md" in section
    )
    for text in (spec, latest):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "MAX_SIZE_UNIT=contracts" in text
        assert "MAX_SIZE_NORMALIZATION_STATUS=BOUND" in text
        assert "MAX_SIZE_FRESHNESS_POLICY_STATUS=BOUND" in text
        assert "MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in text
        assert "MAX_SIZE_CONSUMER_BOUND=false" in text
        assert "MAX_SIZE_CONSUMER_CAN_NOW_BE_BOUND=true" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
        assert (
            "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING" in text
        )
        assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in text
        assert "CURRENT_REUSABLE_MAXMKTSZ_PROVEN=false" in text
        assert "NETWORK_VENUE_GET_PERFORMED=false" in text
        assert "NETWORK_POST_PERFORMED=false" in text
        assert "CHANGED_RUNTIME_FILES=NONE" in text
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "NEXT_DISTINCT_SURFACE=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert (
        "SOURCE_ADJUDICATION_RESULT="
        "MAX_SIZE_FRESHNESS_POLICY_BOUND_FRESH_GET_PER_PRETRADE_DECISION_HISTORICAL_WINDOW_NOT_OPERATIVE_CONSUMER_UNBOUND"
        in spec
    )


def test_option_a_chosen_and_option_b_rejected() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "OPTION_A=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "OPTION_B=FAIL_CLOSED_NO_OPERATIVE_REUSE_UNTIL_SEPARATELY_AUTHORIZED" in spec
    assert "CHOSEN_OPTION=A" in spec
    assert "REJECTED_OPTION=B" in spec
    assert (
        "REJECTED_OPTION_VALUE=FAIL_CLOSED_NO_OPERATIVE_REUSE_UNTIL_SEPARATELY_AUTHORIZED" in spec
    )
    assert "THIRD_OPTION_INVENTED=false" in spec
    assert "FIXED_TTL_OPTION_CONSIDERED=false" in spec
    assert "INDEFINITE_REUSE_OPTION_CONSIDERED=false" in spec
    assert "EVENT_INVALIDATED_CACHE_OPTION_CONSIDERED=false" in spec


def test_freshness_policy_semantics() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    latest = _latest_persist(_section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8")))
    for text in (spec, latest):
        assert "HISTORICAL_MAX_SIZE_REUSE_ALLOWED=false" in text
        assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in text
        assert "FIXED_TTL_DEFINED=false" in text
        assert "EVENT_INVALIDATED_CACHE_DEFINED=false" in text
        assert "FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true" in text
        assert "THIS_POLICY_AUTHORIZES_VENUE_GET=false" in text
        assert "THIS_POLICY_AUTHORIZES_TRADING=false" in text
        assert "NETWORK_ACCESS_REMAINS_SEPARATE_OWNER_GO=true" in text
        assert "MAX_SIZE_FRESHNESS_STATUS=POLICY_BOUND_HISTORICAL_WINDOW_NOT_OPERATIVE" in text
    assert "FAIL_CLOSED_ON_FRUSTRATED_FRESHNESS_EVIDENCE=true" in spec
    assert "FIXED_TTL_REJECTED=true" in spec
    assert "INDEFINITE_REUSE_REJECTED=true" in spec
    assert "EVENT_INVALIDATED_CACHE_REJECTED=true" in spec
    assert "AUTHORITATIVE_EVENT_COHERENCE_SEMANTICS_PROVEN=false" in spec
    assert "WEBSOCKET_COHERENCE_CONTRACT_ASSERTED=false" in spec
    assert "PERMANENT_CACHE_ASSERTED=false" in spec
    assert "UPCCHG_IS_NOT_FRESHNESS_POLICY=true" in spec
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"


def test_historical_6151_freshness_unbound_and_6148_window_remain() -> None:
    prior_6151 = PRIOR_6151.read_text(encoding="utf-8")
    prior_6148 = PRIOR_6148.read_text(encoding="utf-8")
    assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in prior_6151
    assert "MAX_SIZE_NORMALIZATION_STATUS=BOUND" in prior_6151
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESHNESS_POLICY" in prior_6151
    assert SEE_ALSO in prior_6151
    assert "MAX_SIZE_UNIT=UNBOUND" in prior_6148
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in prior_6148
    assert "MAX_SIZE_UNIT=contracts" in PRIOR_6149.read_text(encoding="utf-8")
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in PRIOR_6150.read_text(encoding="utf-8")
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in LIMIT_GATES_SPEC.read_text(
        encoding="utf-8"
    )


def test_historical_values_are_not_made_fresh() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in spec
    assert "CURRENT_REUSABLE_MAXMKTSZ_PROVEN=false" in spec
    assert "HISTORICAL_6148_WINDOW_REMAINS_NON_OPERATIVE=true" in spec
    assert "POLICY_BIND_DOES_NOT_REFRESH_HISTORICAL_VALUES=true" in spec
    assert "POLICY_BIND_DOES_NOT_FREEZE_CURRENT_NUMERIC=true" in spec
    assert "CURRENT_MAXLMTSZ_RAW_VALUE=100000000" in spec
    assert "CURRENT_MAXMKTSZ_RAW_VALUE=100000" in spec
    assert "POLICY_BIND_IS_NOT_CURRENT_NUMERIC_FREEZE=true" in spec


def test_consumer_remains_unbound_and_extractor_unchanged() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "MAX_SIZE_CONSUMER_BOUND=false" in spec
    assert "MAX_SIZE_CONSUMER_CAN_NOW_BE_BOUND=true" in spec
    assert "CONSUMER_WIRING_AUTHORIZED=false" in spec
    assert "EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal" in spec
    assert "EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true" in spec
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source
    assert extract_instrument_constraints_v1 is not None


def test_required_metadata_edge_counts_remain_partial() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
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
    assert "EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING" in spec
    assert "CURRENT_STATUS=PROVEN" not in spec
    assert "ONE_CONTRACT_EQUALS_ONE_SUI=false" in spec


def test_kraken_live_flags_and_navigation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_EXCLUSION_CLOSED=true" in spec
    assert "KRAKEN_METADATA_REUSED=false" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1_PRESERVED=true" in parent
    assert "CURRENT_MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in parent
    assert "PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1" in mot
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
    assert SEE_ALSO in PRIOR_6150.read_text(encoding="utf-8")
    assert "STRATEGY_LOGIC_CHANGED=false" in spec
    assert "MAX_POSITIONS_CHANGED=false" in spec
    assert "RECOVERY_MUTATION=false" in spec
    assert "TRADING_PERFORMED=false" in spec
