"""Post-6148 MAX_SIZE unit adjudication v1.

Static/docs guards. Reuses existing owner tests. No core runtime
mutation. No live authority. No consumer implementation. No freshness
policy. No venue GET/POST.
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
SPEC_PATH = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md"
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
OWNER_GO = "PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1"
SEE_ALSO = (
    "SEE_ALSO_POST_6148_MAX_SIZE_UNIT_ADJUDICATION="
    "docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md"
)
EXPECTED_ORIGIN_MAIN_SHA = "edcf0ff63446c5a456aa769c2e05dd53d9ccc9b4"


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
    assert "NETWORK_DOCUMENTATION_READ_PERFORMED=true" in spec
    assert "AUTH_REQUIRED=false" in spec
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1=true" in section
    assert "SPEC=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md" in section
    for text in (spec, section):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "MAX_SIZE_UNIT=contracts" in text
        assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in text
        assert "MAX_SIZE_CONSUMER_BOUND=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
        assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION" in text
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "NEXT_DISTINCT_SURFACE=MAX_SIZE_NORMALIZATION" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "SOURCE_ADJUDICATION_RESULT=MAX_SIZE_UNIT_BOUND_CONTRACTS_NORMALIZATION_UNBOUND" in spec
    assert "NETWORK_DOCUMENTATION_READ_PERFORMED=true" in section
    assert "NETWORK_VENUE_GET_PERFORMED=false" in section


def test_historical_6148_unit_unbound_remains() -> None:
    prior = PRIOR_6148.read_text(encoding="utf-8")
    assert "MAX_SIZE_UNIT=UNBOUND" in prior
    assert "MAXLMTSZ_NOT_PROVEN_CONTRACTS=true" in prior
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_UNIT" in prior
    assert "NETWORK_GET_PERFORMED=true" in prior
    assert SEE_ALSO in prior
    assert "MAX_SIZE_UNIT=UNBOUND" in PRIOR_6147.read_text(encoding="utf-8")
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in LIMIT_GATES_SPEC.read_text(
        encoding="utf-8"
    )


def test_unit_bind_from_official_eea_docs() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "MAXLMTSZ_UNIT_STATUS=BOUND" in spec
    assert "MAXLMTSZ_UNIT=contracts" in spec
    assert "MAXMKTSZ_UNIT_STATUS=BOUND" in spec
    assert "MAXMKTSZ_UNIT=contracts" in spec
    assert "MAX_SIZE_UNIT_STATUS=BOUND" in spec
    assert "MAX_SIZE_UNIT=contracts" in spec
    assert "GLOBAL_DOC_SEMANTICS_APPLICABLE_TO_OKX_EEA=true" in spec
    assert "OFFICIAL_PRODUCTION_TRADING_REST_URL=https:&#47;&#47;eea.okx.com" in spec
    assert "OFFICIAL_DOC_SURFACE=https:&#47;&#47;my.okx.com&#47;docs-v5&#47;en&#47;" in spec
    assert "number of contracts" in spec
    assert "UNIT_AUTHORITY_SOURCE_COUNT=3" in spec
    assert "THIRD_PARTY_BLOGS_USED_AS_AUTHORITY=false" in spec
    assert "WWW_OKX_AC_USED_AS_AUTHORITY=false" in spec
    assert "UNIT_REQUIRES_CTVAL=false" in spec
    assert "UNIT_REQUIRES_CTMULT=false" in spec
    assert "UNIT_REQUIRES_CTTYPE=false" in spec
    assert "XPERP_IS_OFFICIALLY_A_FUTURES_RULETYPE=true" in spec
    assert "DERIVATIVES_BRANCH_OF_MAXLMTSZ_DEFINITION_APPLIES=true" in spec
    assert "CURRENT_MAXLMTSZ_RAW_VALUE=100000000" in spec
    assert "CURRENT_MAXMKTSZ_RAW_VALUE=100000" in spec
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"


def test_normalization_freshness_consumer_remain_unbound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "MAX_SIZE_NORMALIZATION_STATUS=UNBOUND" in spec
    assert "PEAK_TRADE_ORDER_PLAN_QTY_DOMAIN_EQUALS_CONTRACTS=UNPROVEN" in spec
    assert "PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false" in spec
    assert "MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND" in spec
    assert "MAX_SIZE_FRESHNESS_POLICY=UNBOUND" in spec
    assert "UPCCHG_IS_NOT_FRESHNESS_POLICY=true" in spec
    assert "MAX_SIZE_CONSUMER_BOUND=false" in spec
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in spec
    assert "RUNTIME_ALIGNMENT_REQUIRED=false" in spec
    assert "UNIT_BIND_IS_NOT_NORMALIZATION_BIND=true" in spec
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
    assert "EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_NORMALIZATION" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION" in spec
    assert "CURRENT_STATUS=PROVEN" not in spec


def test_maxavail_and_upcchg_separation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "MAXAVAILSIZE_NOT_LISTED_ON_OFFICIAL_PUBLIC_INSTRUMENTS_RESPONSE_TABLE=true" in spec
    assert "OFFICIAL_MAX_AVAIL_SURFACE=GET &#47;api&#47;v5&#47;account&#47;max-avail-size" in spec
    assert "ACCOUNT_MAX_AVAIL_GET_PERFORMED=false" in spec
    assert "UPCCHG_NAMED_PARAMS_INCLUDE_MAXMKTSZ=true" in spec
    assert "UPCCHG_NAMED_PARAMS_INCLUDE_MAXLMTSZ=UNPROVEN" in spec
    assert "MAX_MKT_SZ_EDGE_STATUS=NOT_REQUIRED" in spec


def test_kraken_and_live_flags_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_EXCLUSION_CLOSED=true" in spec
    assert "KRAKEN_METADATA_REUSED=false" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1_PRESERVED=true" in parent
    assert "PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert SEE_ALSO in LIMIT_GATES_SPEC.read_text(encoding="utf-8")
    assert SEE_ALSO in PRIOR_6147.read_text(encoding="utf-8")
