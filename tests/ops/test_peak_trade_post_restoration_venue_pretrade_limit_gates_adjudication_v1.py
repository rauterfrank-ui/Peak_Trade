"""Post-restoration venue pretrade limit gates adjudication v1.

Static/docs/source-order guards. Reuses existing owner tests; does not
duplicate their runtime proofs. Does not repair the preexisting Cap 3.1
CALL_GRAPH tuple equality test. No core runtime mutation. No live authority.
No metadata-runtime binding. No GET/POST.
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
    DEFAULT_TD_MODE,
    DEMO_XPERP_INSTRUMENT_ID,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    build_canary_exposure_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
    quantize_limit_price_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    ABSENT_TARGET_ROW_IS_NOT_ZERO,
    EMPTY_DATA_IS_NOT_ZERO,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
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
    REPO_ROOT / "tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py",
    REPO_ROOT / "tests/ops/test_capability_11_9_live_canary_order_execution_v1.py",
    REPO_ROOT / "tests/ops/test_section_11_13_5_canary_submit_transport_v1.py",
)

_SEE_ALSO = (
    "SEE_ALSO_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION="
    "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md"
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
        assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false" in text
        assert "EARLIEST_INCOMPLETE_VENUE_PRETRADE_EDGE=MAX_SIZE" in text
        assert "SECOND_VENUE_PRETRADE_OWNER_EXISTS=false" in text
        assert "BYPASS_PATH_CONFLICT=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "RUNTIME_MUTATION_JUSTIFIED=false" in text
        assert "RESTORATION_REOPEN_REQUIRED=false" in text
        assert (
            "ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED" in text
            or "VENUE_PRETRADE_ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED"
            in text
        )
    assert "VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md"
        in section
    )
    assert "NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false" in spec
    assert "VENUE_PRETRADE_GATE_COUNT=12" in spec
    assert "PRODUCTIVELY_REACHABLE_VENUE_PRETRADE_GATES=0" in spec
    assert (
        "VENUE_PRETRADE_OWNER_MODEL=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_OWNER_NOT_A_SECOND_CORE_RISK_OR_SAFETY_OWNER"
        in spec
    )
    assert (
        "CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1"
        in spec
    )
    assert "ADJUDICATION_RESULT=VENUE_PRETRADE_LIMIT_GATES_ALREADY_COMPLETE" not in spec
    assert "ADJUDICATION_RESULT=DUPLICATE_VENUE_PRETRADE_OWNER_CONFLICT" not in spec
    assert "ADJUDICATION_RESULT=VENUE_PRETRADE_BYPASS_CONFLICT" not in spec
    assert "ADJUDICATION_RESULT=VENUE_PRETRADE_RUNTIME_ALIGNMENT_REQUIRED" not in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=true" not in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=true" not in section
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "METADATA_BINDING_ALIGNMENT_REQUIRED_IS_NOT_RUNTIME_MUTATION_AUTHORIZATION=true" in spec
    assert "METADATA_BINDING_ALIGNMENT_REQUIRED_IS_NOT_RUNTIME_MUTATION_NECESSITY=true" in spec


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
    assert DEFAULT_INSTRUMENT_ID != HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID
    assert "BTC_MUST_NOT_BE_CURRENT_INSTRUMENT_RESURRECTED=true" in spec
    assert "NO_BTC_TO_SUI_EVIDENCE_SUBSTITUTION=true" in spec
    assert "CURRENT_SELECTED_INSTRUMENT=BTC-USD_UM_XPERP-310404" not in spec
    assert "CURRENT_VENUE=KRAKEN" not in spec
    assert "CURRENT_VENUE=KRAKEN" not in section


def test_kraken_is_not_current_canonical_venue_or_okx_metadata_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    assert "KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true" in spec
    assert "KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true" in parent
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in spec
    assert "KRAKEN_CURRENT_CANONICAL_ROLE=NONE" in section
    assert "KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false" in spec
    assert "KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true" in spec
    assert "PIPELINE_KRAKEN=LEGACY_OR_ALTERNATE_HOST_FAMILY" in spec
    assert "PIPELINE_KRAKEN_CURRENT_OKX_VENUE_METADATA_AUTHORITY=false" in spec
    assert "KRAKEN_NOT_CURRENT_CANONICAL_VENUE=true" in parent
    assert REUSED_BINDING_VENUE != "KRAKEN"
    assert KRAKEN_LIVE.is_file()
    kraken = KRAKEN_LIVE.read_text(encoding="utf-8")
    assert "def place_order(" in kraken
    assert "lotSz" not in kraken
    assert "maxAvailSize" not in kraken


def test_existing_bound_gates_remain_described_as_bound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "INSTRUMENT_BIND=true" in spec
    assert "INST_TYPE=true" in spec
    assert "RULE_TYPE=true" in spec
    assert "MIN_SIZE=true" in spec
    assert "LOT_SIZE=true" in spec
    assert "TICK_SIZE=true" in spec
    assert "PRICE_ALIGNMENT=true" in spec
    assert "LIMIT_PRICE_REQUIRED=true" in spec
    assert "LIMIT_ONLY_ENTRY=true" in spec
    assert "NO_ENTRY_REDUCE_ONLY=true" in spec
    assert "INSTRUMENT_BIND=false" not in spec
    assert "MIN_SIZE=false" not in spec
    assert "LOT_SIZE=false" not in spec
    assert "TICK_SIZE=false" not in spec
    assert "PRICE_ALIGNMENT=false" not in spec
    assert "def extract_instrument_constraints_v1(" in order_plan
    assert "def quantize_limit_price_v1(" in order_plan
    assert "def build_minimum_valid_canary_order_plan_v1(" in order_plan
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in order_plan
    assert "def build_canary_exposure_binding_v1(" in exposure
    assert "QUANTITY_BELOW_MIN_SZ" in exposure
    assert "QUANTITY_NOT_MULTIPLE_OF_LOT_SZ" in exposure
    assert "build_minimum_valid_canary_order_plan_v1" in transport
    assert extract_instrument_constraints_v1 is not None
    assert build_canary_exposure_binding_v1 is not None
    assert quantize_limit_price_v1 is not None


def test_incomplete_gates_remain_unresolved() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    exposure = EXPOSURE.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "MAX_SIZE=false" in spec
    assert "MAX_AVAILABLE=false" in spec
    assert "PRICE_BAND=false" in spec
    assert "LEVERAGE=false" in spec
    assert "POS_MODE=false" in spec
    assert "MARGIN_MODE=false" in spec
    assert "AVAILABLE_MARGIN=false" in spec
    assert "INSTRUMENT_STATE=false" in spec
    assert "MAX_LMT_SZ_CONSUMER_BOUND=false" in spec
    assert "MAX_MKT_SZ_CONSUMER_BOUND=false" in spec
    assert "MAX_AVAIL_SIZE_CONSUMER_BOUND=false" in spec
    assert "ACCOUNT_MODE_CURRENT_SUI_PROOF_COMPLETE=false" in spec
    assert "SUI_LEVERAGE_PROOF_COMPLETE=false" in spec
    assert "PRICE_BAND_PROOF_COMPLETE=false" in spec
    assert "INSTRUMENT_STATE_RUNTIME_PROOF_COMPLETE=false" in spec
    assert "POS_SIDE=partial" in spec
    assert "TD_MODE=partial" in spec
    assert "ORDER_FIELD_COMPATIBILITY=partial" in spec
    assert "EXCHANGE_ACCEPTANCE=NOT_INTERNALLY_PROVABLE" in spec
    assert "EARLIEST_INCOMPLETE_VENUE_PRETRADE_EDGE=MAX_SIZE" in spec
    for source in (order_plan, exposure, transport):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
        assert "maxAvailSize" not in source


def test_non_equivalence_contracts_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "LIVE_ADMISSION_IS_NOT_VENUE_PRETRADE_VALIDITY=true" in spec
    assert "VENUE_METADATA_EXISTENCE_IS_NOT_GATE_BINDING=true" in spec
    assert "STATIC_FIELD_EXISTENCE_IS_NOT_RUNTIME_VALIDATION=true" in spec
    assert "INSTRUMENT_BIND_IS_NOT_SIZE_VALIDITY=true" in spec
    assert "MIN_SIZE_IS_NOT_MAX_SIZE=true" in spec
    assert "LOT_SIZE_IS_NOT_MAX_AVAILABLE=true" in spec
    assert "TICK_ALIGNMENT_IS_NOT_PRICE_BAND_VALIDITY=true" in spec
    assert "DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true" in spec
    assert "HISTORICAL_BTC_LEVERAGE_IS_NOT_SUI_LEVERAGE=true" in spec
    assert "HISTORICAL_ACCOUNT_GET_IS_NOT_CURRENT_SUI_REOBSERVATION=true" in spec
    assert "RISK_ENVELOPE_IS_NOT_VENUE_PRETRADE_OWNER=true" in spec
    assert "EXCHANGE_ACCEPTANCE_IS_NOT_INTERNALLY_PROVEN=true" in spec
    assert DEFAULT_TD_MODE == "cross"
    assert EMPTY_DATA_IS_NOT_ZERO is True
    assert ABSENT_TARGET_ROW_IS_NOT_ZERO is True
    assert "POSITION_ABSENCE_IS_NOT_ZERO=true" in spec
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False


def test_owner_graph_and_prior_slices_remain_closed() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
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
    assert "VENUE_PRETRADE_IS_NOT_REPLAY_SAFETY=true" in spec
    assert "VENUE_PRETRADE_IS_NOT_CORE_RISK_AUTHORITY=true" in spec
    assert "VENUE_PRETRADE_IS_NOT_EXECUTION_AUTHORITY=true" in spec
    assert "VENUE_PRETRADE_IS_DOWNSTREAM_OF_LIVE_SAFETY=true" in spec
    assert "VENUE_PRETRADE_IS_UPSTREAM_OF_POST=true" in spec
    assert "FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true" in spec
    assert "LIVE_SAFETY_GATES_COMPLETE=true" in live_safety
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting
    assert "SIMULATED_EXECUTION_PIPELINE_COMPLETE=true" in sim_exec
    assert "LIVE_SAFETY_GATES_ADJUDICATION_V1=true" in section
    assert "SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1=true" in section
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1=true" in section
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in remaining
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in parallel
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in accounting
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in sim_exec
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in live_safety
    assert _SEE_ALSO in remaining
    assert _SEE_ALSO in parallel
    assert _SEE_ALSO in accounting
    assert _SEE_ALSO in sim_exec
    assert _SEE_ALSO in live_safety
    assert "VENUE_PRETRADE_ADJUDICATION_PRESERVED=true" in parent
    assert "VENUE_PRETRADE_RUNTIME_REWIRE_REQUIRED=false" in parent
    assert "CURRENT_OKX_VENUE_IDENTITY_PRESERVED=true" in parent
    assert "MAX_SIZE_REMAINS_EARLIEST_UNRESOLVED_EDGE=true" in parent
    assert "LIVE_SAFETY_GATES_ADJUDICATION_PRESERVED=true" in parent
    assert "PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot


def test_host_families_remain_classified_without_bypass_conflict() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "OKX_EEA_CANARY=CURRENT_VENUE_PRETRADE_SURFACE" in spec
    assert "NETWORKED_ONRAMP=FAIL_CLOSED_NETWORKLESS" in spec
    assert "CAP11_FIXTURES=DECLARED_UNREACHABLE" in spec
    assert "FLATTEN=SEPARATE_EMERGENCY_AUTHORITY" in spec
    assert "INDEPENDENT_PRETRADE_KERNEL=NON_AUTHORIZING_QUARANTINED" in spec
    assert "BYPASS_PATH_CONFLICT=false" in spec
    assert "OKX_EEA_CANARY_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING" in spec
    assert "PIPELINE_KRAKEN_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING" in spec


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
    live_safety = _REUSED_GUARDS[12].read_text(encoding="utf-8")
    empty = _REUSED_GUARDS[13].read_text(encoding="utf-8")
    canary = _REUSED_GUARDS[15].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_LIVE_SAFETY_RESPONSIBILITIES" in live_safety
    assert "test_empty_data_array_is_not_observed_not_zero" in empty
    assert "build_minimum_valid_canary_order_plan_v1" in canary
