"""Post-restoration venue pretrade metadata-binding alignment adjudication v1.

Static/docs/source-order guards. Reuses existing owner tests; does not
duplicate their runtime proofs. Does not repair the preexisting Cap 3.1
CALL_GRAPH tuple equality test. No core runtime mutation. No live authority.
No productive enforcement. No GET/POST.
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
    DEFAULT_RULE_TYPE,
    DEMO_XPERP_INSTRUMENT_ID,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    TESTNET_AUTHORIZED,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    build_canary_exposure_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    ABSENT_TARGET_ROW_IS_NOT_ZERO,
    EMPTY_DATA_IS_NOT_ZERO,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
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
LIVE_SAFETY_SPEC = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md"
)
SIM_EXEC_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md"
)
ACCOUNTING_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md"
)
REMAINING_P0_SPEC = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md"
)
PARALLEL_OWNER_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
EXPOSURE = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exposure_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
ECONOMIC_BASELINE = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/xperp_310404_economic_baseline_contract_v1.py"
)
KRAKEN_LIVE = REPO_ROOT / "src/exchange/kraken_live.py"
PREEXISTING_CALL_GRAPH_TEST = (
    REPO_ROOT / "tests/ops/test_productive_futures_accounting_runtime_binding_v1.py"
)

_REUSED_GUARDS = (
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py",
    REPO_ROOT / "tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py",
    REPO_ROOT
    / "tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py",
    REPO_ROOT / "tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py",
    REPO_ROOT / "tests/ops/test_capability_11_9_live_canary_order_execution_v1.py",
    REPO_ROOT / "tests/ops/test_section_11_13_5_canary_submit_transport_v1.py",
)

_SEE_ALSO = (
    "SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION="
    "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md"
)


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_spec_is_subordinate_and_does_not_grant_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3" in spec
    assert "CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "NEW_STAGE=false" in spec
    assert "NEW_ABSTRACTION_REQUIRED=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true" in spec
    assert "NO_LIVE_AUTHORITY=true" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec
    assert "NETWORK_GET_PERFORMED=false" in spec
    assert "NETWORK_POST_PERFORMED=false" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL" in text
        assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in text
        assert "ALL_REQUIRED_METADATA_EDGES_BOUND=false" in text
        assert "EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE" in text
        assert "EARLIEST_REMAINING_CONFLICT=NONE" in text
        assert "NETWORK_GET_REQUIRED=true" in text
        assert "NETWORK_GET_PERFORMED=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "RUNTIME_MUTATION_JUSTIFIED=false" in text
        assert "RESTORATION_REOPEN_REQUIRED=false" in text
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
    assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md"
        in section
    )
    assert "ADJUDICATION_RESULT=PARTIAL" in spec
    assert "ADJUDICATION_RESULT=COMPLETE" not in spec
    assert "ADJUDICATION_RESULT=BLOCKED_BY_MISSING_SOURCE" not in spec
    assert "ADJUDICATION_RESULT=BLOCKED_BY_CONFLICT" not in spec
    assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=COMPLETE" not in spec
    assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=COMPLETE" not in section
    assert "MAX_SIZE_BINDING_STATUS=PROVEN" not in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "NETWORK_GET_REQUIRED_IS_NOT_NETWORK_GET_AUTHORIZATION=true" in spec
    assert "METADATA_BINDING_PARTIAL_IS_NOT_RUNTIME_MUTATION_AUTHORIZATION=true" in spec
    assert "METADATA_BINDING_PARTIAL_IS_NOT_RUNTIME_MUTATION_NECESSITY=true" in spec


def test_current_venue_and_instrument_remain_okx_eea_sui() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404" in text
        assert "CURRENT_VENUE=OKX_EEA" in text
        assert "INSTRUMENT_BIND_PROVEN=true" in text
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == "SUI-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert DEFAULT_RULE_TYPE == "xperp"
    assert REUSED_BINDING_VENUE == "OKX"
    assert REUSED_BINDING_REST_HOST == "eea.okx.com"
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == "BTC-USD_UM_XPERP-310404"
    assert HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID == "BTC-USDT-SWAP"
    assert DEMO_XPERP_INSTRUMENT_ID == "BTC-USD_UM_XPERP-310328"
    assert DEFAULT_INSTRUMENT_ID != HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
    assert "BTC_MUST_NOT_BE_CURRENT_INSTRUMENT_RESURRECTED=true" in spec
    assert "NO_BTC_TO_SUI_EVIDENCE_SUBSTITUTION=true" in spec
    assert "CURRENT_SELECTED_INSTRUMENT=BTC-USD_UM_XPERP-310404" not in spec
    assert "CURRENT_VENUE=KRAKEN" not in spec
    assert "CURRENT_VENUE=KRAKEN" not in section


def test_kraken_and_btc_firewall_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false" in spec
    assert "KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true" in spec
    assert "BTC_METADATA_REUSED=false" in spec
    assert "SUI_OTHER_INSTRUMENT_METADATA_REUSED=false" in spec
    assert "FAMILY_SCOPED_METADATA_REUSED=false" in spec
    assert "VENUE_GLOBAL_METADATA_REUSED=false" in spec
    assert "KRAKEN_METADATA_REUSED=false" in spec
    assert "KRAKEN_NOT_CURRENT_CANONICAL_VENUE=true" in parent
    assert REUSED_BINDING_VENUE != "KRAKEN"
    kraken = KRAKEN_LIVE.read_text(encoding="utf-8")
    assert "def place_order(" in kraken
    assert "lotSz" not in kraken
    assert "maxAvailSize" not in kraken
    assert "maxLmtSz" not in kraken


def test_max_size_is_partially_bound_not_current_numeric() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    master = MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert "MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND" in spec
    assert "CURRENT_STATUS=PARTIALLY_BOUND" in spec
    assert "MAX_SIZE_RAW_FIELD=maxLmtSz" in spec
    assert "MAX_SIZE_RAW_VALUE=100000000" in spec
    assert "MAX_SIZE_UNIT=UNBOUND" in spec
    assert "MAX_SIZE_FRESHNESS_STATUS=UNBOUND" in spec
    assert "MAX_SIZE_CURRENT_REUSABLE_NUMERIC=UNBOUND" in spec
    assert "FRESHNESS_POLICY=UNBOUND" in spec
    assert "HISTORICAL_RAW_OBSERVATION_IS_NOT_CURRENT_REUSABLE_NUMERIC=true" in spec
    assert "GET_1_MAX_LMT_SZ=100000000" in master
    assert "GET_1_MAX_MKT_SZ=100000" in master
    assert "MAXLMTSZ_IS_NOT_MAXMKTSZ=true" in spec
    assert "MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true" in spec
    assert "FAMILY_SCOPED_TIER_MAXSZ_IS_NOT_INSTRUMENT_MAXLMTSZ=true" in spec
    assert "EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true" in spec
    assert "ORDER_PLAN_QTY_MINSZ_IS_NOT_VENUE_MAX_SIZE=true" in spec
    assert "NO_UNIT_CONVERSION_APPLIED_IS_NOT_UNIT_PROOF=true" in spec
    assert "MAX_SIZE_EQUALS_MAXLMTSZ_SEMANTIC_PROOF=UNBOUND" in spec


def test_existing_owner_does_not_consume_max_size_fields() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    baseline = ECONOMIC_BASELINE.read_text(encoding="utf-8")
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    assert "FUTURE_MAX_SIZE_CONSUMER_CURRENTLY_BOUND=false" in spec
    assert "MAX_NOTIONAL_MUST_EQUAL_MIN_EXECUTABLE" in exposure
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source
    assert "maxLmtSz" not in baseline
    assert extract_instrument_constraints_v1 is not None
    assert build_canary_exposure_binding_v1 is not None
    query = public_instruments_query_path_v1()
    assert query == ("/api/v5/public/instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404")


def test_required_metadata_edge_counts_and_peer_not_required() -> None:
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
    assert "EDGE_ID=MAX_MKT_SZ" in spec
    assert "CURRENT_STATUS=NOT_REQUIRED" in spec
    assert "NOT_REQUIRED_PEER_EDGE_IDS=MAX_MKT_SZ" in spec
    assert "CURRENT_STATUS=UNBOUND" in spec
    assert "CURRENT_STATUS=CONFLICTED" not in spec
    assert "CURRENT_STATUS=PROVEN" not in spec


def test_network_get_is_identified_and_not_performed() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "NETWORK_GET_REQUIRED=true" in text
        assert "NETWORK_GET_PERFORMED=false" in text
        assert "NETWORK_POST_PERFORMED=false" in text
    assert "AUTH_REQUIRED=false" in spec
    assert "QUERY_GRAMMAR=instType=FUTURES&instId=SUI-USD_UM_XPERP-310404" in spec
    assert "MUTATION_EXPECTED=false" in spec
    assert "NEXT_DISTINCT_SURFACE=EXACT_VENUE_METADATA_GET" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "PUBLIC_VENUE_GET=NOT_THIS_SLICE" in spec
    assert "NETWORK_GET=NOT_THIS_SLICE" in spec


def test_non_equivalence_and_live_flags_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "VENUE_METADATA_EXISTENCE_IS_NOT_GATE_BINDING=true" in spec
    assert "STATIC_FIELD_EXISTENCE_IS_NOT_RUNTIME_VALIDATION=true" in spec
    assert "MIN_SIZE_IS_NOT_MAX_SIZE=true" in spec
    assert EMPTY_DATA_IS_NOT_ZERO is True
    assert ABSENT_TARGET_ROW_IS_NOT_ZERO is True
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False


def test_owner_graph_and_prior_slices_remain_closed() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    limit_gates = LIMIT_GATES_SPEC.read_text(encoding="utf-8")
    live_safety = LIVE_SAFETY_SPEC.read_text(encoding="utf-8")
    accounting = ACCOUNTING_SPEC.read_text(encoding="utf-8")
    sim_exec = SIM_EXEC_SPEC.read_text(encoding="utf-8")
    remaining = REMAINING_P0_SPEC.read_text(encoding="utf-8")
    parallel = PARALLEL_OWNER_SPEC.read_text(encoding="utf-8")
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    for text in (spec, section):
        assert "SECOND_COMPUTE_OWNER_EXISTS=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "SECOND_INTENT_OWNER_EXISTS=false" in text
        assert "SECOND_EXECUTION_OWNER_EXISTS=false" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
    assert "CLOSED_OWNER_GRAPH_PRESERVED=true" in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in limit_gates
    assert "ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED" in limit_gates
    assert "LIVE_SAFETY_GATES_COMPLETE=true" in live_safety
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting
    assert "SIMULATED_EXECUTION_PIPELINE_COMPLETE=true" in sim_exec
    assert "VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1=true" in section
    assert "LIVE_SAFETY_GATES_ADJUDICATION_V1=true" in section
    assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT=NOT_THIS_SLICE" in limit_gates
    assert _SEE_ALSO in limit_gates
    assert _SEE_ALSO in remaining
    assert _SEE_ALSO in parallel
    assert _SEE_ALSO in accounting
    assert _SEE_ALSO in sim_exec
    assert _SEE_ALSO in live_safety
    assert "VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_PRESERVED=true" in parent
    assert "MAX_SIZE_BINDING_REMAINS_PARTIALLY_BOUND=true" in parent
    assert "MAX_SIZE_REMAINS_EARLIEST_UNRESOLVED_EDGE=true" in parent
    assert (
        "PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1"
        in mot
    )
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot


def test_preexisting_call_graph_drift_remains_label_only_and_unrepaired() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    preexisting = PREEXISTING_CALL_GRAPH_TEST.read_text(encoding="utf-8")
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in section
    assert "assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH" in preexisting
    assert "xfail" not in preexisting.lower()
    assert "pytest.skip" not in preexisting


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    limit_gates = _REUSED_GUARDS[13].read_text(encoding="utf-8")
    canary = _REUSED_GUARDS[16].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert "ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED" in limit_gates
    assert "build_minimum_valid_canary_order_plan_v1" in canary
